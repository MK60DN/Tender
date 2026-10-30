# -*- coding: utf-8 -*-
"""Physical-tenant SQLite store with scoped access and audit.

Every tenant owns a separate database. Membership scopes are evaluated inside
this module; client-supplied tenant or campus IDs never select a database.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable

from .tenant_security import (
    TenantCipher,
    tenant_db_path,
    tenant_dir,
    validate_tenant_id,
    harden_path,
)

SENSITIVE_CLASSIFICATIONS = {"credential", "finance", "hr", "lead", "student_record", "contract", "private"}
SEARCHABLE_CLASSIFICATIONS = {"content", "marketing", "policy", "planning", "general"}
ALL_SCOPE = "*"
SENSITIVE_READ_PERMISSIONS = {"people:read", "files:read_sensitive", "finance:read"}


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat()


def _conn(tenant_id: str) -> sqlite3.Connection:
    tenant_id = validate_tenant_id(tenant_id)
    path = tenant_db_path(tenant_id)
    if not path.exists():
        raise FileNotFoundError("tenant database not found")
    conn = sqlite3.connect(path, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute("PRAGMA secure_delete=ON")
    row = conn.execute("SELECT tenant_id FROM tenant_meta WHERE singleton=1").fetchone()
    if not row or row["tenant_id"] != tenant_id:
        conn.close()
        raise PermissionError("tenant database identity mismatch")
    return conn


SCHEMA = """
CREATE TABLE IF NOT EXISTS tenant_meta (
    singleton INTEGER PRIMARY KEY CHECK(singleton=1),
    tenant_id TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    schema_version INTEGER NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS campuses (
    campus_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL,
    UNIQUE(tenant_id, campus_id)
);

CREATE TABLE IF NOT EXISTS memberships (
    membership_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    actor_id TEXT NOT NULL,
    role TEXT NOT NULL,
    campus_ids_json TEXT NOT NULL DEFAULT '[]',
    class_ids_json TEXT NOT NULL DEFAULT '[]',
    student_ids_json TEXT NOT NULL DEFAULT '[]',
    permissions_json TEXT NOT NULL DEFAULT '[]',
    can_write INTEGER NOT NULL DEFAULT 0,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(tenant_id, actor_id)
);

CREATE TABLE IF NOT EXISTS students (
    student_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    campus_id TEXT NOT NULL,
    class_id TEXT,
    display_name_enc TEXT NOT NULL,
    name_index TEXT NOT NULL,
    school_enc TEXT,
    grade TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    identity_key TEXT NOT NULL,
    source_file_id TEXT,
    source_ref TEXT,
    profile_enc TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(tenant_id, identity_key)
);

CREATE TABLE IF NOT EXISTS guardians (
    guardian_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    student_id TEXT NOT NULL,
    display_name_enc TEXT,
    phone_enc TEXT,
    relation TEXT,
    evidence_enc TEXT,
    verified INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS leads (
    lead_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    campus_id TEXT NOT NULL,
    source_file_id TEXT NOT NULL,
    source_sheet TEXT,
    source_row INTEGER,
    student_name_enc TEXT,
    parent_name_enc TEXT,
    phone_enc TEXT,
    school_enc TEXT,
    grade TEXT,
    class_name TEXT,
    identity_key TEXT NOT NULL,
    raw_enc TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(tenant_id, identity_key)
);

CREATE TABLE IF NOT EXISTS projection_runs (
    projection_run_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    projection_year INTEGER NOT NULL,
    source_cutoff TEXT,
    rules_version TEXT NOT NULL,
    status TEXT NOT NULL,
    total_source_records INTEGER NOT NULL DEFAULT 0,
    projected_records INTEGER NOT NULL DEFAULT 0,
    review_required INTEGER NOT NULL DEFAULT 0,
    graduated_records INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    finished_at TEXT
);

CREATE TABLE IF NOT EXISTS projected_students (
    projection_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    projection_year INTEGER NOT NULL,
    projection_run_id TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_record_id TEXT NOT NULL,
    source_file_id TEXT,
    campus_id TEXT NOT NULL,
    display_name_enc TEXT NOT NULL,
    phone_enc TEXT,
    school_enc TEXT,
    source_grade TEXT,
    projected_grade INTEGER,
    projected_stage TEXT NOT NULL,
    source_year INTEGER,
    source_month INTEGER,
    inference_method TEXT NOT NULL,
    confidence REAL NOT NULL,
    review_status TEXT NOT NULL,
    is_synthetic INTEGER NOT NULL DEFAULT 1,
    profile_enc TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(tenant_id, projection_year, source_type, source_record_id)
);

CREATE TABLE IF NOT EXISTS source_files (
    file_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    batch_id TEXT NOT NULL,
    filename_enc TEXT NOT NULL,
    relative_path_enc TEXT NOT NULL,
    extension TEXT,
    mime TEXT,
    size_bytes INTEGER NOT NULL,
    modified_at TEXT,
    sha256 TEXT NOT NULL,
    category TEXT NOT NULL,
    classification TEXT NOT NULL,
    sensitivity TEXT NOT NULL,
    campus_id TEXT NOT NULL,
    storage_mode TEXT NOT NULL DEFAULT 'manifest',
    source_locator_enc TEXT,
    text_status TEXT NOT NULL DEFAULT 'pending',
    text_chars INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS file_texts (
    file_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    content_enc BLOB NOT NULL,
    content_sha256 TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS source_rows (
    row_id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id TEXT NOT NULL,
    file_id TEXT NOT NULL,
    sheet_name TEXT,
    row_number INTEGER,
    row_enc BLOB NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS import_batches (
    batch_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    source_root_enc TEXT NOT NULL,
    status TEXT NOT NULL,
    total_files INTEGER NOT NULL DEFAULT 0,
    imported_files INTEGER NOT NULL DEFAULT 0,
    failed_files INTEGER NOT NULL DEFAULT 0,
    extracted_text_files INTEGER NOT NULL DEFAULT 0,
    source_rows INTEGER NOT NULL DEFAULT 0,
    students INTEGER NOT NULL DEFAULT 0,
    leads INTEGER NOT NULL DEFAULT 0,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    errors_json TEXT NOT NULL DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS tenant_audit (
    audit_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    actor_id TEXT NOT NULL,
    action TEXT NOT NULL,
    target TEXT,
    payload_enc TEXT,
    prev_hash TEXT,
    record_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE VIRTUAL TABLE IF NOT EXISTS file_search USING fts5(
    file_id UNINDEXED,
    tenant_id UNINDEXED,
    title,
    body,
    classification UNINDEXED,
    campus_id UNINDEXED
);

CREATE INDEX IF NOT EXISTS idx_students_scope ON students(tenant_id, campus_id, class_id);
CREATE INDEX IF NOT EXISTS idx_students_name_index ON students(tenant_id, name_index);
CREATE INDEX IF NOT EXISTS idx_leads_scope ON leads(tenant_id, campus_id, source_file_id);
CREATE INDEX IF NOT EXISTS idx_source_files_scope ON source_files(tenant_id, campus_id, classification);
CREATE INDEX IF NOT EXISTS idx_source_rows_file ON source_rows(file_id, sheet_name, row_number);
CREATE INDEX IF NOT EXISTS idx_tenant_audit_created ON tenant_audit(tenant_id, created_at);
CREATE INDEX IF NOT EXISTS idx_projected_scope ON projected_students(tenant_id, projection_year, campus_id, projected_stage);
CREATE INDEX IF NOT EXISTS idx_projected_source ON projected_students(tenant_id, source_type, source_record_id);
"""


def _install_scope_triggers(conn: sqlite3.Connection) -> None:
    tables = [
        "campuses", "memberships", "students", "guardians", "leads",
        "source_files", "file_texts", "source_rows", "import_batches", "tenant_audit",
        "projection_runs", "projected_students",
    ]
    for table in tables:
        conn.execute(f"""
        CREATE TRIGGER IF NOT EXISTS trg_{table}_tenant_insert
        BEFORE INSERT ON {table}
        WHEN NEW.tenant_id IS NULL OR NEW.tenant_id <> (SELECT tenant_id FROM tenant_meta WHERE singleton=1)
        BEGIN SELECT RAISE(ABORT, 'tenant_scope_violation'); END
        """)
        conn.execute(f"""
        CREATE TRIGGER IF NOT EXISTS trg_{table}_tenant_update
        BEFORE UPDATE OF tenant_id ON {table}
        WHEN NEW.tenant_id <> OLD.tenant_id OR NEW.tenant_id <> (SELECT tenant_id FROM tenant_meta WHERE singleton=1)
        BEGIN SELECT RAISE(ABORT, 'tenant_scope_violation'); END
        """)


def init_tenant_db(
    tenant_id: str,
    display_name: str,
    *,
    reset: bool = False,
    admin_actor_id: str | None = None,
    campuses: Iterable[tuple[str, str]] | None = None,
) -> pathlib.Path:
    tenant_id = validate_tenant_id(tenant_id)
    directory = tenant_dir(tenant_id, create=True)
    path = tenant_db_path(tenant_id)
    if reset:
        for suffix in ("", "-wal", "-shm"):
            candidate = pathlib.Path(str(path) + suffix)
            if candidate.parent == directory and candidate.exists():
                candidate.unlink()
    conn = sqlite3.connect(path, timeout=30)
    try:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA secure_delete=ON")
        conn.executescript(SCHEMA)
        existing = conn.execute("SELECT tenant_id FROM tenant_meta WHERE singleton=1").fetchone()
        if existing and existing["tenant_id"] != tenant_id:
            raise PermissionError("tenant database already belongs to another tenant")
        if not existing:
            conn.execute(
                "INSERT INTO tenant_meta(singleton,tenant_id,display_name,schema_version,created_at) VALUES(1,?,?,?,?)",
                (tenant_id, display_name, 1, now()),
            )
        else:
            conn.execute("UPDATE tenant_meta SET display_name=? WHERE singleton=1", (display_name,))
        _install_scope_triggers(conn)
        for campus_id, name in campuses or []:
            conn.execute(
                "INSERT INTO campuses(campus_id,tenant_id,name,status,created_at) VALUES(?,?,?,'active',?) "
                "ON CONFLICT(campus_id) DO UPDATE SET name=excluded.name, status='active'",
                (campus_id, tenant_id, name, now()),
            )
        if admin_actor_id:
            create_membership(
                tenant_id,
                admin_actor_id,
                "tenant_admin",
                permissions=["*"],
                can_write=True,
                conn=conn,
                commit=False,
            )
        conn.commit()
    finally:
        conn.close()
    harden_path(directory)
    return path


def create_membership(
    tenant_id: str,
    actor_id: str,
    role: str,
    *,
    campus_ids: Iterable[str] = (),
    class_ids: Iterable[str] = (),
    student_ids: Iterable[str] = (),
    permissions: Iterable[str] = (),
    can_write: bool = False,
    conn: sqlite3.Connection | None = None,
    commit: bool = True,
) -> dict[str, Any]:
    tenant_id = validate_tenant_id(tenant_id)
    own = conn is None
    conn = conn or _conn(tenant_id)
    try:
        current = conn.execute(
            "SELECT membership_id, created_at FROM memberships WHERE tenant_id=? AND actor_id=?",
            (tenant_id, actor_id),
        ).fetchone()
        membership_id = current["membership_id"] if current else "mem_" + uuid.uuid4().hex
        created_at = current["created_at"] if current else now()
        conn.execute(
            """
            INSERT INTO memberships(membership_id,tenant_id,actor_id,role,campus_ids_json,class_ids_json,
                                    student_ids_json,permissions_json,can_write,active,created_at,updated_at)
            VALUES(?,?,?,?,?,?,?,?,?,1,?,?)
            ON CONFLICT(tenant_id, actor_id) DO UPDATE SET
              role=excluded.role, campus_ids_json=excluded.campus_ids_json,
              class_ids_json=excluded.class_ids_json, student_ids_json=excluded.student_ids_json,
              permissions_json=excluded.permissions_json, can_write=excluded.can_write,
              active=1, updated_at=excluded.updated_at
            """,
            (
                membership_id, tenant_id, actor_id, role,
                json.dumps(sorted(set(campus_ids)), ensure_ascii=False),
                json.dumps(sorted(set(class_ids)), ensure_ascii=False),
                json.dumps(sorted(set(student_ids)), ensure_ascii=False),
                json.dumps(sorted(set(permissions)), ensure_ascii=False),
                int(can_write), created_at, now(),
            ),
        )
        if commit:
            conn.commit()
        return {
            "membership_id": membership_id,
            "tenant_id": tenant_id,
            "actor_id": actor_id,
            "role": role,
            "campus_ids": sorted(set(campus_ids)),
            "class_ids": sorted(set(class_ids)),
            "student_ids": sorted(set(student_ids)),
            "permissions": sorted(set(permissions)),
            "can_write": bool(can_write),
        }
    finally:
        if own:
            conn.close()


@dataclass(frozen=True)
class TenantMember:
    tenant_id: str
    membership_id: str
    actor_id: str
    role: str
    campus_ids: tuple[str, ...]
    class_ids: tuple[str, ...]
    student_ids: tuple[str, ...]
    permissions: frozenset[str]
    can_write: bool

    @property
    def all_scope(self) -> bool:
        return self.role in {"tenant_admin", "auditor"} or ALL_SCOPE in self.campus_ids

    @property
    def can_read_sensitive(self) -> bool:
        return self.role in {"tenant_admin", "auditor"} or bool(self.permissions & SENSITIVE_READ_PERMISSIONS)


def resolve_tenant_member(tenant_id: str, actor_id: str) -> TenantMember:
    tenant_id = validate_tenant_id(tenant_id)
    conn = _conn(tenant_id)
    try:
        row = conn.execute(
            "SELECT * FROM memberships WHERE tenant_id=? AND actor_id=? AND active=1",
            (tenant_id, actor_id),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        raise PermissionError("tenant_membership_required")
    return TenantMember(
        tenant_id=tenant_id,
        membership_id=row["membership_id"],
        actor_id=row["actor_id"],
        role=row["role"],
        campus_ids=tuple(json.loads(row["campus_ids_json"] or "[]")),
        class_ids=tuple(json.loads(row["class_ids_json"] or "[]")),
        student_ids=tuple(json.loads(row["student_ids_json"] or "[]")),
        permissions=frozenset(json.loads(row["permissions_json"] or "[]")),
        can_write=bool(row["can_write"]),
    )


def tenant_context(tenant_id: str) -> dict[str, Any]:
    conn = _conn(tenant_id)
    try:
        meta = dict(conn.execute("SELECT tenant_id,display_name,schema_version,created_at FROM tenant_meta WHERE singleton=1").fetchone())
        meta["campuses"] = [dict(r) for r in conn.execute("SELECT campus_id,name,status FROM campuses ORDER BY name")]
        return meta
    finally:
        conn.close()


def _student_scope(member: TenantMember, alias: str = "s") -> tuple[str, list[Any]]:
    clauses = [f"{alias}.tenant_id=?"]
    params: list[Any] = [member.tenant_id]
    if member.all_scope:
        return " AND ".join(clauses), params
    if member.role == "campus_admin":
        values = list(member.campus_ids)
        if not values:
            return "1=0", []
        clauses.append(f"{alias}.campus_id IN ({','.join('?' for _ in values)})")
        params.extend(values)
        return " AND ".join(clauses), params
    if member.role == "head_teacher":
        values = list(member.class_ids)
        if not values:
            return "1=0", []
        clauses.append(f"{alias}.class_id IN ({','.join('?' for _ in values)})")
        params.extend(values)
        return " AND ".join(clauses), params
    values = list(member.student_ids)
    if not values:
        return "1=0", []
    clauses.append(f"{alias}.student_id IN ({','.join('?' for _ in values)})")
    params.extend(values)
    return " AND ".join(clauses), params


def _row_to_student(row: sqlite3.Row, cipher: TenantCipher) -> dict[str, Any]:
    return {
        "student_id": row["student_id"],
        "campus_id": row["campus_id"],
        "class_id": row["class_id"],
        "name": cipher.decrypt_text(row["display_name_enc"]),
        "school": cipher.decrypt_text(row["school_enc"]),
        "grade": row["grade"],
        "status": row["status"],
        "source_file_id": row["source_file_id"],
        "source_ref": row["source_ref"],
        "profile": cipher.decrypt_json(row["profile_enc"]) or {},
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def list_students(member: TenantMember, *, campus_id: str | None = None, class_id: str | None = None,
                  query: str | None = None, limit: int = 200) -> list[dict[str, Any]]:
    conn = _conn(member.tenant_id)
    cipher = TenantCipher(member.tenant_id)
    try:
        clause, params = _student_scope(member)
        if campus_id:
            clause += " AND s.campus_id=?"
            params.append(campus_id)
        if class_id:
            clause += " AND s.class_id=?"
            params.append(class_id)
        if query:
            clause += " AND s.name_index=?"
            params.append(cipher.blind_index(query, "student-name"))
        rows = conn.execute(
            f"SELECT s.* FROM students s WHERE {clause} ORDER BY s.updated_at DESC LIMIT ?",
            [*params, max(1, min(int(limit), 1000))],
        ).fetchall()
        return [_row_to_student(r, cipher) for r in rows]
    finally:
        conn.close()


def get_student(member: TenantMember, student_id: str) -> dict[str, Any]:
    conn = _conn(member.tenant_id)
    cipher = TenantCipher(member.tenant_id)
    try:
        clause, params = _student_scope(member)
        row = conn.execute(f"SELECT s.* FROM students s WHERE {clause} AND s.student_id=?", [*params, student_id]).fetchone()
        if not row:
            raise PermissionError("student_access_denied")
        return _row_to_student(row, cipher)
    finally:
        conn.close()


def _lead_scope(member: TenantMember) -> tuple[str, list[Any]]:
    clauses = ["l.tenant_id=?"]
    params: list[Any] = [member.tenant_id]
    if member.all_scope:
        return " AND ".join(clauses), params
    if member.role == "campus_admin":
        values = list(member.campus_ids)
        if not values:
            return "1=0", []
        clauses.append(f"l.campus_id IN ({','.join('?' for _ in values)})")
        params.extend(values)
    else:
        return "1=0", []
    return " AND ".join(clauses), params


def list_leads(member: TenantMember, *, campus_id: str | None = None, limit: int = 200) -> list[dict[str, Any]]:
    if not member.can_read_sensitive:
        raise PermissionError("sensitive_people_access_denied")
    conn = _conn(member.tenant_id)
    cipher = TenantCipher(member.tenant_id)
    try:
        clause, params = _lead_scope(member)
        if campus_id:
            clause += " AND l.campus_id=?"
            params.append(campus_id)
        rows = conn.execute(
            f"SELECT l.* FROM leads l WHERE {clause} ORDER BY l.created_at DESC LIMIT ?",
            [*params, max(1, min(int(limit), 1000))],
        ).fetchall()
        return [{
            "lead_id": r["lead_id"],
            "campus_id": r["campus_id"],
            "student_name": cipher.decrypt_text(r["student_name_enc"]),
            "parent_name": cipher.decrypt_text(r["parent_name_enc"]),
            "phone": cipher.decrypt_text(r["phone_enc"]),
            "school": cipher.decrypt_text(r["school_enc"]),
            "grade": r["grade"],
            "class_name": r["class_name"],
            "source_file_id": r["source_file_id"],
            "source_sheet": r["source_sheet"],
            "source_row": r["source_row"],
        } for r in rows]
    finally:
        conn.close()


def _file_scope(member: TenantMember) -> tuple[str, list[Any]]:
    clauses = ["f.tenant_id=?"]
    params: list[Any] = [member.tenant_id]
    if member.all_scope:
        return " AND ".join(clauses), params
    if member.role in {"campus_admin", "head_teacher"}:
        values = list(member.campus_ids)
        if values:
            clauses.append(f"f.campus_id IN ({','.join('?' for _ in values)})")
            params.extend(values)
        else:
            clauses.append("f.campus_id='unassigned'")
    else:
        return "1=0", []
    return " AND ".join(clauses), params


def list_files(member: TenantMember, *, classification: str | None = None, campus_id: str | None = None,
               limit: int = 200) -> list[dict[str, Any]]:
    conn = _conn(member.tenant_id)
    cipher = TenantCipher(member.tenant_id)
    try:
        clause, params = _file_scope(member)
        classes = [classification] if classification else sorted(SEARCHABLE_CLASSIFICATIONS | SENSITIVE_CLASSIFICATIONS)
        if not member.can_read_sensitive:
            classes = [c for c in classes if c not in SENSITIVE_CLASSIFICATIONS]
        if not classes:
            return []
        clause += f" AND f.classification IN ({','.join('?' for _ in classes)})"
        params.extend(classes)
        if campus_id:
            clause += " AND f.campus_id=?"
            params.append(campus_id)
        rows = conn.execute(
            f"SELECT f.* FROM source_files f WHERE {clause} ORDER BY f.modified_at DESC LIMIT ?",
            [*params, max(1, min(int(limit), 1000))],
        ).fetchall()
        return [{
            "file_id": r["file_id"],
            "filename": cipher.decrypt_text(r["filename_enc"]),
            "relative_path": cipher.decrypt_text(r["relative_path_enc"]),
            "extension": r["extension"],
            "mime": r["mime"],
            "size_bytes": r["size_bytes"],
            "modified_at": r["modified_at"],
            "sha256": r["sha256"],
            "category": r["category"],
            "classification": r["classification"],
            "campus_id": r["campus_id"],
            "text_status": r["text_status"],
            "text_chars": r["text_chars"],
        } for r in rows]
    finally:
        conn.close()


def search_files(member: TenantMember, query: str, *, limit: int = 50) -> list[dict[str, Any]]:
    text = (query or "").strip()
    if len(text) < 2:
        raise ValueError("query_too_short")
    conn = _conn(member.tenant_id)
    try:
        allowed = sorted(SEARCHABLE_CLASSIFICATIONS)
        rows = conn.execute(
            """
            SELECT fs.file_id, fs.title, snippet(file_search, 3, '[', ']', ' … ', 24) AS snippet,
                   f.extension, f.classification, f.size_bytes, f.modified_at
            FROM file_search fs
            JOIN source_files f ON f.file_id=fs.file_id
            WHERE file_search MATCH ? AND fs.tenant_id=?
              AND fs.classification IN (""" + ",".join("?" for _ in allowed) + ") "
            "ORDER BY rank LIMIT ?",
            [text, member.tenant_id, *allowed, max(1, min(int(limit), 200))],
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def tenant_stats(member: TenantMember) -> dict[str, Any]:
    conn = _conn(member.tenant_id)
    try:
        student_clause, student_params = _student_scope(member)
        student_count = conn.execute(f"SELECT COUNT(*) FROM students s WHERE {student_clause}", student_params).fetchone()[0]
        lead_count = 0
        if member.can_read_sensitive:
            lead_clause, lead_params = _lead_scope(member)
            lead_count = conn.execute(f"SELECT COUNT(*) FROM leads l WHERE {lead_clause}", lead_params).fetchone()[0]
        file_clause, file_params = _file_scope(member)
        if not member.can_read_sensitive:
            file_clause += " AND f.classification NOT IN (" + ",".join("?" for _ in SENSITIVE_CLASSIFICATIONS) + ")"
            file_params.extend(sorted(SENSITIVE_CLASSIFICATIONS))
        file_stats = conn.execute(
            f"SELECT COUNT(*) AS files, COALESCE(SUM(f.size_bytes),0) AS bytes FROM source_files f WHERE {file_clause}",
            file_params,
        ).fetchone()
        batches = [dict(r) for r in conn.execute(
            "SELECT batch_id,status,total_files,imported_files,failed_files,extracted_text_files,source_rows,students,leads,started_at,finished_at "
            "FROM import_batches ORDER BY started_at DESC"
        )]
        return {
            "tenant_id": member.tenant_id,
            "students": student_count,
            "leads": lead_count,
            "files": file_stats["files"],
            "file_bytes": file_stats["bytes"],
            "import_batches": batches,
            "sensitive_access": member.can_read_sensitive,
        }
    finally:
        conn.close()


def _projection_scope(member: TenantMember) -> tuple[str, list[Any]]:
    clauses = ["p.tenant_id=?"]
    params: list[Any] = [member.tenant_id]
    if member.all_scope:
        return " AND ".join(clauses), params
    if member.role == "campus_admin":
        values = list(member.campus_ids)
        if not values:
            return "1=0", []
        clauses.append(f"p.campus_id IN ({','.join('?' for _ in values)})")
        params.extend(values)
        return " AND ".join(clauses), params
    return "1=0", []


def list_projected_students(
    member: TenantMember,
    *,
    year: int = 2026,
    stage: str | None = None,
    review_status: str | None = None,
    campus_id: str | None = None,
    limit: int = 500,
) -> list[dict[str, Any]]:
    if not member.can_read_sensitive:
        raise PermissionError("sensitive_people_access_denied")
    conn = _conn(member.tenant_id)
    cipher = TenantCipher(member.tenant_id)
    try:
        clause, params = _projection_scope(member)
        clause += " AND p.projection_year=?"
        params.append(int(year))
        if stage:
            clause += " AND p.projected_stage=?"
            params.append(stage)
        if review_status:
            clause += " AND p.review_status=?"
            params.append(review_status)
        if campus_id:
            clause += " AND p.campus_id=?"
            params.append(campus_id)
        rows = conn.execute(
            f"SELECT p.* FROM projected_students p WHERE {clause} "
            "ORDER BY p.projected_grade DESC, p.review_status, p.created_at LIMIT ?",
            [*params, max(1, min(int(limit), 2000))],
        ).fetchall()
        return [{
            "projection_id": r["projection_id"],
            "projection_year": r["projection_year"],
            "source_type": r["source_type"],
            "source_record_id": r["source_record_id"],
            "source_file_id": r["source_file_id"],
            "campus_id": r["campus_id"],
            "name": cipher.decrypt_text(r["display_name_enc"]),
            "phone": cipher.decrypt_text(r["phone_enc"]),
            "school": cipher.decrypt_text(r["school_enc"]),
            "source_grade": r["source_grade"],
            "projected_grade": r["projected_grade"],
            "projected_stage": r["projected_stage"],
            "source_year": r["source_year"],
            "source_month": r["source_month"],
            "inference_method": r["inference_method"],
            "confidence": r["confidence"],
            "review_status": r["review_status"],
            "is_synthetic": bool(r["is_synthetic"]),
            "profile": cipher.decrypt_json(r["profile_enc"]) or {},
            "created_at": r["created_at"],
        } for r in rows]
    finally:
        conn.close()


def projection_stats(member: TenantMember, year: int = 2026) -> dict[str, Any]:
    if not member.can_read_sensitive:
        raise PermissionError("sensitive_people_access_denied")
    conn = _conn(member.tenant_id)
    try:
        clause, params = _projection_scope(member)
        clause += " AND p.projection_year=?"
        params.append(int(year))
        total = conn.execute(f"SELECT COUNT(*) FROM projected_students p WHERE {clause}", params).fetchone()[0]
        by_stage = {r["projected_stage"]: r["n"] for r in conn.execute(
            f"SELECT p.projected_stage, COUNT(*) n FROM projected_students p WHERE {clause} GROUP BY p.projected_stage ORDER BY n DESC",
            params,
        )}
        by_review = {r["review_status"]: r["n"] for r in conn.execute(
            f"SELECT p.review_status, COUNT(*) n FROM projected_students p WHERE {clause} GROUP BY p.review_status ORDER BY n DESC",
            params,
        )}
        run = conn.execute(
            "SELECT * FROM projection_runs WHERE tenant_id=? AND projection_year=? ORDER BY created_at DESC LIMIT 1",
            (member.tenant_id, int(year)),
        ).fetchone()
        return {
            "projection_year": int(year),
            "total": total,
            "by_stage": by_stage,
            "by_review_status": by_review,
            "run": dict(run) if run else None,
            "synthetic_data_notice": "推算数据不是已验证学生事实，不得直接用于联系、收费或对外披露。",
        }
    finally:
        conn.close()


def write_tenant_audit(tenant_id: str, actor_id: str, action: str, target: str | None = None,
                       payload: dict[str, Any] | None = None) -> str:
    conn = _conn(tenant_id)
    cipher = TenantCipher(tenant_id)
    try:
        last = conn.execute("SELECT record_hash FROM tenant_audit ORDER BY rowid DESC LIMIT 1").fetchone()
        prev = last["record_hash"] if last else ""
        created = now()
        payload_enc = cipher.encrypt_json(payload or {}) if payload is not None else None
        material = json.dumps([prev, tenant_id, actor_id, action, target or "", payload_enc or "", created], ensure_ascii=False)
        record_hash = hashlib.sha256(material.encode("utf-8")).hexdigest()
        audit_id = "aud_" + uuid.uuid4().hex
        conn.execute(
            "INSERT INTO tenant_audit(audit_id,tenant_id,actor_id,action,target,payload_enc,prev_hash,record_hash,created_at) "
            "VALUES(?,?,?,?,?,?,?,?,?)",
            (audit_id, tenant_id, actor_id, action, target, payload_enc, prev, record_hash, created),
        )
        conn.commit()
        return audit_id
    finally:
        conn.close()
