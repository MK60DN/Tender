# -*- coding: utf-8 -*-
"""Project historical Yanwen student/contact records into the 2026 school year.

Projection is deliberately separate from verified source records. Each derived
row keeps source identity, year/grade evidence, confidence and review status.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import sqlite3
import sys
import uuid
from datetime import datetime, timezone
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.tenant_security import TenantCipher, tenant_db_path
from app.tenant_store import init_tenant_db, now, write_tenant_audit

TENANT_ID = "yanwen"
TENANT_NAME = "言文升学"
RULES_VERSION = "2026.1"
GRADE_PATTERNS = [
    (r"小学一年级|一年级", 1),
    (r"小学二年级|二年级", 2),
    (r"小学三年级|三年级", 3),
    (r"小学四年级|四年级", 4),
    (r"小学五年级|五年级", 5),
    (r"小学六年级|六年级", 6),
    (r"初一|七年级|7年级", 7),
    (r"初二|八年级|8年级", 8),
    (r"初三|九年级|9年级", 9),
    (r"高一|十年级|10年级", 10),
    (r"高二|十一年级|11年级", 11),
    (r"高三|十二年级|12年级", 12),
]
STAGE_NAMES = {
    1: "小学一年级", 2: "小学二年级", 3: "小学三年级", 4: "小学四年级",
    5: "小学五年级", 6: "小学六年级", 7: "初一", 8: "初二", 9: "初三",
    10: "高一", 11: "高二", 12: "高三",
}


def _text(value: Any) -> str:
    return str(value or "").strip()


def _grade_from_text(value: str) -> int | None:
    matches: list[tuple[int, int]] = []
    for pattern, grade in GRADE_PATTERNS:
        for match in re.finditer(pattern, value):
            matches.append((match.start(), grade))
    if not matches:
        return None
    return max(matches, key=lambda item: item[0])[1]


def _birth_date_grade(raw: Any, target_year: int) -> tuple[int | None, int | None, int | None]:
    if not isinstance(raw, dict):
        return None, None, None
    for value in raw.values():
        text = _text(value)
        match = re.fullmatch(r"(20\d{2})[年./\-](\d{1,2})[月./\-](\d{1,2})日?", text)
        if not match:
            continue
        year, month, day = map(int, match.groups())
        if not (2000 <= year <= target_year) or not (1 <= month <= 12 and 1 <= day <= 31):
            continue
        first_grade_year = year + 6 + (1 if month >= 9 else 0)
        grade = target_year - first_grade_year + 1
        return grade, year, month
    return None, None, None


def _year_month(value: str, fallback_iso: str | None = None) -> tuple[int | None, int | None, str]:
    matches = list(re.finditer(r"(20\d{2})[年./\-](\d{1,2})", value))
    if matches:
        year, month = matches[-1].groups()
        month_i = int(month)
        if 1 <= month_i <= 12:
            return int(year), month_i, "source_path"
    years = list(re.finditer(r"(20\d{2})", value))
    if years:
        return int(years[-1].group(1)), 9, "source_path_year_only"
    if fallback_iso:
        try:
            dt = datetime.fromisoformat(fallback_iso)
            return dt.year, dt.month, "file_modified_at"
        except ValueError:
            pass
    return None, None, "unknown"


def _source_ay_start(year: int | None, month: int | None) -> int | None:
    if year is None:
        return None
    month = month or 9
    return year if month >= 9 else year - 1


def _stage_for(grade: int | None) -> str:
    if grade is None:
        return "待核验年级"
    if grade > 12:
        return "已毕业/离校"
    if grade < 1:
        return "学龄前"
    return STAGE_NAMES.get(grade, f"{grade}年级")


def project_grade(base_grade: int | None, source_year: int | None, source_month: int | None,
                  target_year: int) -> tuple[int | None, int | None, str, int | None]:
    ay = _source_ay_start(source_year, source_month)
    if base_grade is None or ay is None:
        return None, ay, "grade_or_year_missing", None
    delta = max(0, target_year - ay)
    projected = base_grade + delta
    method = f"school_year_progression:+{delta}"
    return projected, ay, method, delta


def confidence_for(grade: int | None, source_year: int | None, source_month: int | None,
                   year_method: str, grade_method: str) -> tuple[float, str]:
    if grade is None:
        return 0.15, "grade_unknown"
    if source_year is None:
        return 0.30, "needs_confirmation"
    if grade_method == "birth_date_age":
        return 0.65, "age_projected"
    if year_method == "source_path" and grade_method in {"source_grade", "source_text"}:
        return 0.85, "auto_projected"
    if year_method.startswith("source_path") and grade_method in {"source_grade", "source_text"}:
        return 0.70, "needs_confirmation"
    return 0.45, "needs_confirmation"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tenant-id", default=TENANT_ID)
    parser.add_argument("--tenant-name", default=TENANT_NAME)
    parser.add_argument("--year", type=int, default=2026)
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--actor", default="yanwen-admin")
    parser.add_argument("--report", default="")
    args = parser.parse_args()

    init_tenant_db(args.tenant_id, args.tenant_name)
    db_path = tenant_db_path(args.tenant_id)
    cipher = TenantCipher(args.tenant_id)
    conn = sqlite3.connect(db_path, timeout=60)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=60000")

    run_id = "proj_" + uuid.uuid4().hex[:16]
    started = now()
    conn.execute(
        "INSERT INTO projection_runs(projection_run_id,tenant_id,projection_year,rules_version,status,created_at) "
        "VALUES(?,?,?,?, 'running', ?)",
        (run_id, args.tenant_id, args.year, RULES_VERSION, started),
    )
    if args.reset:
        conn.execute(
            "DELETE FROM projected_students WHERE tenant_id=? AND projection_year=?",
            (args.tenant_id, args.year),
        )
    conn.commit()

    file_cache: dict[str, dict[str, Any]] = {}
    for row in conn.execute("SELECT file_id,relative_path_enc,modified_at FROM source_files WHERE tenant_id=?", (args.tenant_id,)):
        file_cache[row["file_id"]] = {
            "path": cipher.decrypt_text(row["relative_path_enc"]),
            "modified_at": row["modified_at"],
        }

    counts = {"sources": 0, "projected": 0, "review_required": 0, "graduated": 0, "unknown": 0}
    by_stage: dict[str, int] = {}
    by_status: dict[str, int] = {}

    rows: list[dict[str, Any]] = []
    for row in conn.execute("SELECT * FROM leads WHERE tenant_id=? ORDER BY lead_id", (args.tenant_id,)):
        rows.append({"source_type": "lead", "row": row})
    for row in conn.execute("SELECT * FROM students WHERE tenant_id=? ORDER BY student_id", (args.tenant_id,)):
        rows.append({"source_type": "student", "row": row})

    for item in rows:
        counts["sources"] += 1
        source_type = item["source_type"]
        row = item["row"]
        source_file_id = row["source_file_id"]
        source_file = file_cache.get(source_file_id, {})
        source_path = source_file.get("path", "")
        raw_text = ""
        raw_obj: Any = {}
        if source_type == "lead":
            try:
                raw_obj = cipher.decrypt_json(row["raw_enc"]) or {}
                raw_text = json.dumps(raw_obj, ensure_ascii=False)
            except Exception:
                raw_obj = {}
                raw_text = ""
        else:
            try:
                raw_obj = cipher.decrypt_json(row["profile_enc"]) or {}
                raw_text = json.dumps(raw_obj, ensure_ascii=False)
            except Exception:
                raw_obj = {}
                raw_text = ""

        source_grade_text = _text(row["grade"]) if source_type == "lead" else _text(row["grade"])
        grade = _grade_from_text(source_grade_text)
        grade_method = "source_grade" if grade is not None else ""
        if grade is None:
            grade = _grade_from_text(source_path + " " + _text(row["source_sheet"] if source_type == "lead" else "") + " " + raw_text[:4000])
            grade_method = "source_text" if grade is not None else "unknown"

        year, month, year_method = _year_month(source_path, source_file.get("modified_at"))
        birth_grade, birth_year, birth_month = _birth_date_grade(raw_obj, args.year)
        if grade is None and birth_grade is not None:
            grade = birth_grade
            year, month = args.year, 9
            year_method = "birth_date_target_year"
            grade_method = "birth_date_age"
        projected_grade, ay, progression_method, delta = project_grade(grade, year, month, args.year)
        stage = _stage_for(projected_grade)
        confidence, review_status = confidence_for(grade, year, month, year_method, grade_method)
        if projected_grade is not None and projected_grade > 12:
            review_status = "graduated_or_left"
            counts["graduated"] += 1
        if grade is None:
            counts["unknown"] += 1
        if review_status not in {"auto_projected", "graduated_or_left"}:
            counts["review_required"] += 1

        method = f"{progression_method};grade={grade_method};year={year_method}"
        name_enc = row["student_name_enc"] if source_type == "lead" else row["display_name_enc"]
        if not name_enc:
            name_enc = cipher.encrypt_text("未命名联系人")
        phone_enc = row["phone_enc"] if source_type == "lead" else None
        school_enc = row["school_enc"]
        campus_id = row["campus_id"] or "unassigned"
        source_record_id = row["lead_id"] if source_type == "lead" else row["student_id"]
        projection_id = "projrow_" + hashlib.sha256(
            f"{args.tenant_id}:{args.year}:{source_type}:{source_record_id}".encode("utf-8")
        ).hexdigest()[:20]
        profile = {
            "source_type": source_type,
            "source_record_id": source_record_id,
            "source_grade_text": source_grade_text,
            "source_year": year,
            "source_month": month,
            "school_year_start": ay,
            "year_delta": delta,
            "projection_rules_version": RULES_VERSION,
            "synthetic": True,
            "explicit_warning": "This row is a grade-year projection, not a confirmed current student.",
        }
        conn.execute(
            """
            INSERT INTO projected_students(projection_id,tenant_id,projection_year,projection_run_id,source_type,
                source_record_id,source_file_id,campus_id,display_name_enc,phone_enc,school_enc,source_grade,
                projected_grade,projected_stage,source_year,source_month,inference_method,confidence,review_status,
                is_synthetic,profile_enc,created_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,1,?,?)
            ON CONFLICT(tenant_id,projection_year,source_type,source_record_id) DO UPDATE SET
              projection_run_id=excluded.projection_run_id, source_file_id=excluded.source_file_id,
              campus_id=excluded.campus_id, display_name_enc=excluded.display_name_enc,
              phone_enc=excluded.phone_enc, school_enc=excluded.school_enc, source_grade=excluded.source_grade,
              projected_grade=excluded.projected_grade, projected_stage=excluded.projected_stage,
              source_year=excluded.source_year, source_month=excluded.source_month,
              inference_method=excluded.inference_method, confidence=excluded.confidence,
              review_status=excluded.review_status, profile_enc=excluded.profile_enc,
              created_at=excluded.created_at
            """,
            (
                projection_id, args.tenant_id, args.year, run_id, source_type, source_record_id,
                source_file_id, campus_id, name_enc, phone_enc, school_enc, source_grade_text,
                projected_grade, stage, year, month, method, confidence, review_status,
                cipher.encrypt_json(profile), now(),
            ),
        )
        counts["projected"] += 1
        by_stage[stage] = by_stage.get(stage, 0) + 1
        by_status[review_status] = by_status.get(review_status, 0) + 1

    conn.execute(
        "UPDATE projection_runs SET status='completed',source_cutoff=?,total_source_records=?,projected_records=?,"
        "review_required=?,graduated_records=?,finished_at=? WHERE projection_run_id=?",
        ("2026-10-25", counts["sources"], counts["projected"], counts["review_required"], counts["graduated"], now(), run_id),
    )
    conn.commit()
    conn.close()
    write_tenant_audit(args.tenant_id, args.actor, "tenant.projection.run", run_id, {
        "year": args.year, **counts, "by_stage": by_stage, "by_status": by_status,
    })
    report = {
        "tenant_id": args.tenant_id,
        "projection_year": args.year,
        "projection_run_id": run_id,
        "rules_version": RULES_VERSION,
        "counts": counts,
        "by_stage": by_stage,
        "by_review_status": by_status,
        "notice": "推算数据与原始事实分层保存，不能直接当作已核实学生。",
    }
    if args.report:
        path = pathlib.Path(args.report)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
