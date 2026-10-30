# -*- coding: utf-8 -*-
"""Physical tenant and object-scope isolation tests."""
from __future__ import annotations

import shutil
import sqlite3
import uuid
from datetime import datetime, timezone

from app.tenant_security import TenantCipher, sha256_file, tenant_dir, tenant_db_path
from app.tenant_store import (
    create_membership,
    init_tenant_db,
    resolve_tenant_member,
    list_students,
    get_student,
    list_files,
)


def _insert_student(path, tenant_id: str, student_id: str, campus_id: str, class_id: str, name: str):
    cipher = TenantCipher(tenant_id)
    stamp = datetime.now(timezone.utc).isoformat()
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            """
            INSERT INTO students(student_id,tenant_id,campus_id,class_id,display_name_enc,name_index,
                school_enc,grade,status,identity_key,source_file_id,source_ref,profile_enc,created_at,updated_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                student_id, tenant_id, campus_id, class_id, cipher.encrypt_text(name),
                cipher.blind_index(name, "student-name"), cipher.encrypt_text("测试学校"), "高三",
                "active", student_id, "file_test", "test", cipher.encrypt_json({"x": 1}), stamp, stamp,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def test_physical_tenant_and_scope_isolation():
    suffix = uuid.uuid4().hex[:8]
    tenant_a = "pytest_a_" + suffix
    tenant_b = "pytest_b_" + suffix
    dirs = [tenant_dir(tenant_a, create=True), tenant_dir(tenant_b, create=True)]
    try:
        path_a = init_tenant_db(tenant_a, "隔离测试 A", reset=True, admin_actor_id="admin-a", campuses=[("c1", "一校区"), ("c2", "二校区")])
        path_b = init_tenant_db(tenant_b, "隔离测试 B", reset=True, admin_actor_id="admin-b", campuses=[("c1", "一校区")])
        assert path_a != path_b

        _insert_student(path_a, tenant_a, "s1", "c1", "class-1", "张三")
        _insert_student(path_a, tenant_a, "s2", "c2", "class-2", "李四")
        _insert_student(path_b, tenant_b, "s3", "c1", "class-1", "王五")

        create_membership(tenant_a, "campus-a", "campus_admin", campus_ids=["c1"], permissions=["people:read"])
        create_membership(tenant_a, "head-a", "head_teacher", class_ids=["class-2"], permissions=["people:read"])
        create_membership(tenant_a, "advisor-a", "advisor", student_ids=["s1"])

        assert [s["student_id"] for s in list_students(resolve_tenant_member(tenant_a, "campus-a"))] == ["s1"]
        assert [s["student_id"] for s in list_students(resolve_tenant_member(tenant_a, "head-a"))] == ["s2"]
        assert [s["student_id"] for s in list_students(resolve_tenant_member(tenant_a, "advisor-a"))] == ["s1"]
        assert set(s["student_id"] for s in list_students(resolve_tenant_member(tenant_a, "admin-a"))) == {"s1", "s2"}

        try:
            resolve_tenant_member(tenant_b, "admin-a")
            raise AssertionError("cross-tenant membership unexpectedly succeeded")
        except PermissionError:
            pass

        try:
            get_student(resolve_tenant_member(tenant_a, "campus-a"), "s3")
            raise AssertionError("cross-tenant student unexpectedly readable")
        except PermissionError:
            pass

        conn = sqlite3.connect(path_a)
        try:
            encrypted = conn.execute("SELECT display_name_enc FROM students WHERE student_id='s1'").fetchone()[0]
            assert "张三" not in encrypted
            try:
                conn.execute(
                    "INSERT INTO students(student_id,tenant_id,campus_id,display_name_enc,name_index,status,identity_key,created_at,updated_at) "
                    "VALUES('bad','wrong-tenant','c1','x','x','active','bad','x','x')"
                )
                conn.commit()
                raise AssertionError("tenant trigger unexpectedly allowed wrong tenant_id")
            except sqlite3.IntegrityError:
                conn.rollback()
        finally:
            conn.close()
    finally:
        for directory in dirs:
            if directory.exists():
                shutil.rmtree(directory, ignore_errors=True)


def test_sensitive_file_visibility():
    suffix = uuid.uuid4().hex[:8]
    tenant_id = "pytest_files_" + suffix
    directory = tenant_dir(tenant_id, create=True)
    try:
        path = init_tenant_db(tenant_id, "文件隔离测试", reset=True, admin_actor_id="admin-files", campuses=[("c1", "一校区")])
        create_membership(tenant_id, "teacher-files", "head_teacher", campus_ids=["c1"], class_ids=["class-1"])
        cipher = TenantCipher(tenant_id)
        conn = sqlite3.connect(path)
        try:
            conn.execute(
                """
                INSERT INTO source_files(file_id,tenant_id,batch_id,filename_enc,relative_path_enc,extension,mime,
                    size_bytes,modified_at,sha256,category,classification,sensitivity,campus_id,storage_mode,
                    source_locator_enc,text_status,text_chars,created_at)
                VALUES('f1',?,'b1',?,?,'.xlsx','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    10,'2026-01-01T00:00:00+08:00','abc','finance','finance','finance','c1','manifest',?,'parsed',10,?)
                """,
                (tenant_id, cipher.encrypt_text("财务.xlsx"), cipher.encrypt_text("财务资料/财务.xlsx"), cipher.encrypt_text("D:/finance.xlsx"), datetime.now(timezone.utc).isoformat()),
            )
            conn.commit()
        finally:
            conn.close()
        teacher = resolve_tenant_member(tenant_id, "teacher-files")
        assert list_files(teacher, classification="finance") == []
        admin = resolve_tenant_member(tenant_id, "admin-files")
        assert len(list_files(admin, classification="finance")) == 1
    finally:
        if directory.exists():
            shutil.rmtree(directory, ignore_errors=True)


def test_2026_projection_rules():
    from scripts.project_yanwen_2026 import _grade_from_text, _birth_date_grade, project_grade
    assert _grade_from_text("2025年9月初二733") == 8
    assert _grade_from_text("高三") == 12
    grade, birth_year, birth_month = _birth_date_grade({"date": "2017/1/9"}, 2026)
    assert (grade, birth_year, birth_month) == (4, 2017, 1)
    projected, school_year_start, method, delta = project_grade(8, 2025, 9, 2026)
    assert projected == 9
    assert school_year_start == 2025
    assert delta == 1
    assert method.startswith("school_year_progression")
