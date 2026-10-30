# -*- coding: utf-8 -*-
"""Import the D:\言文 corpus into a physically isolated Tender tenant database.

The importer stores every file manifest, an encrypted full-text copy for files
that can be parsed, encrypted spreadsheet rows, normalized student records and
lead/contact records. Original binary files are referenced by encrypted source
locator; they are not duplicated into SQLite.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import io
import json
import mimetypes
import os
import pathlib
import re
import sqlite3
import sys
import traceback
import uuid
import zipfile
from datetime import date, datetime, timezone
from typing import Any, Iterable
from xml.etree import ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.tenant_security import TenantCipher, sha256_file, tenant_db_path
from app.tenant_store import (
    SENSITIVE_CLASSIFICATIONS,
    init_tenant_db,
    create_membership,
    now,
    write_tenant_audit,
)

TENANT_ID = "yanwen"
TENANT_NAME = "言文升学"
SOURCE_ROOT = pathlib.Path(r"D:\言文")
BATCH_CHUNK = 20
MAX_TEXT_BYTES = 120 * 1024 * 1024
FTS_CHARS = 200_000
CAMPUSES = [
    ("unassigned", "待归属校区"),
    ("qingshan", "青山校区"),
    ("sizhong", "四中校区"),
    ("main", "总校/公共资料"),
]
SEARCHABLE = {"content", "marketing", "policy", "planning", "general"}

FIELD_ALIASES = {
    "student_name": {"学生姓名", "学员姓名", "学生", "学员", "姓名", "名字"},
    "parent_name": {"家长姓名", "家长", "监护人", "父亲", "母亲"},
    "phone": {"电话", "手机号", "手机", "联系电话", "联系方式", "家长电话", "学生电话", "父亲电话", "母亲电话"},
    "school": {"学校", "学校名称", "就读学校", "在读学校", "所在学校", "毕业学校"},
    "grade": {"年级", "年級", "届别", "学生年级"},
    "class_name": {"班级", "班型", "训练班", "培训班级"},
    "id_number": {"身份证", "身份证号", "身份证号码"},
}
NAME_RE = re.compile(r"^[\u3400-\u9fffA-Za-z·•.\- ]{2,30}$")


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    text = str(value).replace("\x00", "").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _norm_label(value: Any) -> str:
    return re.sub(r"[\s:：()（）_\-]+", "", _clean_text(value)).lower()


def file_id_for(relative_path: str) -> str:
    return "file_" + hashlib.sha256(f"{TENANT_ID}:{relative_path}".encode("utf-8")).hexdigest()[:20]


def campus_for(relative_path: str) -> str:
    value = relative_path.replace("\\", "/")
    if "四中" in value:
        return "sizhong"
    if "青山" in value or "青二" in value:
        return "qingshan"
    if value.startswith(("2024年化学", "化学资料2025年", "新建文件夹", "初中知识点汇总")):
        return "main"
    return "unassigned"


def classify_file(relative_path: str) -> tuple[str, str]:
    value = relative_path.replace("\\", "/")
    name = pathlib.Path(value).name
    ext = pathlib.Path(value).suffix.lower()
    if "高报网站" in name or "账号" in name and "密码" in name:
        return "credential", "credential"
    if value.startswith("财务资料/"):
        return "finance", "finance"
    if value.startswith("行政招聘/") or any(k in name for k in ("员工手册", "工资", "保险", "招聘")):
        return "hr", "hr"
    if "/学员档案/" in value or "集训学员信息表" in value or "入学协议" in value or "食宿协议" in value:
        return "student_record" if "协议" not in name else "contract", "student_record"
    if "销售资料/" in value:
        return "lead", "lead"
    if value.startswith("市场资料/") and ext in {".xls", ".xlsx", ".csv"}:
        return "lead", "lead"
    if value.startswith("市场资料/"):
        return "marketing", "marketing"
    if value.startswith("新媒体内容/"):
        return "marketing", "marketing"
    if value.startswith("学业规划/"):
        if any(token in name for token in ("付智韬", "杨子怡", "赵敏如", "袁嘉旭")):
            return "student_record", "student_record"
        return "planning", "planning"
    if value.startswith(("日常部制度/", "2026年集训制度/")):
        return "policy", "policy"
    if any(value.startswith(prefix) for prefix in ("2024年化学/", "化学资料2025年/", "初中知识点汇总/", "新建文件夹/")):
        return "content", "content"
    return "general", "general"


def _xml_text(xml_bytes: bytes, paragraph_tag: str | None = None) -> str:
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return ""
    if paragraph_tag:
        paragraphs = []
        for node in root.iter():
            if node.tag.endswith("}" + paragraph_tag) or node.tag == paragraph_tag:
                text = "".join(t.text or "" for t in node.iter() if t.tag.endswith("}t") or t.tag == "t")
                if text.strip():
                    paragraphs.append(text.strip())
        return "\n".join(paragraphs)
    return "\n".join(t.strip() for t in root.itertext() if t and t.strip())


def extract_docx(path: pathlib.Path) -> str:
    out: list[str] = []
    with zipfile.ZipFile(path) as zf:
        names = [n for n in zf.namelist() if re.match(r"word/(document|header\d*|footer\d*)\.xml$", n)]
        for name in sorted(names):
            out.append(_xml_text(zf.read(name), "p"))
    return "\n\n".join(x for x in out if x)


def extract_pptx(path: pathlib.Path) -> str:
    out: list[str] = []
    with zipfile.ZipFile(path) as zf:
        slides = [n for n in zf.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", n)]
        slides.sort(key=lambda n: int(re.search(r"slide(\d+)", n).group(1)))
        for name in slides:
            text = _xml_text(zf.read(name), "p")
            if text:
                out.append(f"--- {pathlib.Path(name).name} ---\n{text}")
    return "\n\n".join(out)


def extract_generic_zip(path: pathlib.Path) -> str:
    out: list[str] = []
    try:
        with zipfile.ZipFile(path) as zf:
            for info in zf.infolist():
                if info.file_size > 8 * 1024 * 1024 or info.is_dir():
                    continue
                if not info.filename.lower().endswith((".xml", ".json", ".txt", ".md", ".html")):
                    continue
                raw = zf.read(info)
                text = raw.decode("utf-8", errors="ignore")
                if info.filename.lower().endswith((".xml", ".html")):
                    text = html.unescape(re.sub(r"<[^>]+>", " ", text))
                if text.strip():
                    out.append(text.strip())
                if sum(len(x) for x in out) > MAX_TEXT_BYTES:
                    break
    except (zipfile.BadZipFile, OSError):
        return ""
    return "\n\n".join(out)


def _spreadsheet_rows_xlsx(path: pathlib.Path) -> list[tuple[str, int, list[Any]]]:
    import openpyxl
    rows: list[tuple[str, int, list[Any]]] = []
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        for ws in wb.worksheets:
            for number, row in enumerate(ws.iter_rows(values_only=True), 1):
                values = [_clean_text(v) for v in row]
                while values and not values[-1]:
                    values.pop()
                if any(values):
                    rows.append((ws.title, number, values))
    finally:
        wb.close()
    return rows


def _spreadsheet_rows_xls(path: pathlib.Path) -> list[tuple[str, int, list[Any]]]:
    import xlrd
    rows: list[tuple[str, int, list[Any]]] = []
    book = xlrd.open_workbook(str(path), on_demand=True)
    try:
        for sheet in book.sheets():
            for number in range(sheet.nrows):
                values = [_clean_text(sheet.cell_value(number, col)) for col in range(sheet.ncols)]
                while values and not values[-1]:
                    values.pop()
                if any(values):
                    rows.append((sheet.name, number + 1, values))
    finally:
        book.release_resources()
    return rows


def extract_pdf(path: pathlib.Path) -> str:
    try:
        import pymupdf
        doc = pymupdf.open(path)
        try:
            if doc.needs_pass:
                return ""
            pages = []
            for page in doc:
                pages.append(page.get_text("text"))
            return "\n\n".join(pages)
        finally:
            doc.close()
    except Exception:
        return ""


def extract_legacy_doc(path: pathlib.Path) -> str:
    raw = path.read_bytes()
    candidates = []
    for codec in ("utf-16le", "gb18030"):
        try:
            text = raw.decode(codec, errors="ignore")
        except Exception:
            continue
        runs = re.findall(r"[\u3400-\u9fffA-Za-z0-9，。；：！？、“”‘’（）《》【】—…·:;,.!?()\s%+\-]{6,}", text)
        cleaned = "\n".join(r.strip() for r in runs if len(r.strip()) >= 6)
        score = len(re.findall(r"[\u4e00-\u9fff]", cleaned))
        candidates.append((score, cleaned))
    return max(candidates, default=(0, ""))[1]


def extract_rtf(path: pathlib.Path) -> str:
    raw = path.read_bytes()
    for encoding in ("utf-8", "gb18030", "latin-1"):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        return ""
    text = re.sub(r"\\u(-?\d+)\??", lambda m: chr(int(m.group(1)) % 65536), text)
    text = text.replace("\\par", "\n").replace("\\tab", "\t")
    text = re.sub(r"\\'[0-9a-fA-F]{2}", "", text)
    text = re.sub(r"\\[a-zA-Z]+-?\d* ?", "", text)
    text = text.replace("{", "").replace("}", "")
    return _clean_text(text)


def extract_plain(path: pathlib.Path) -> str:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "gb18030", "utf-16"):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        return ""
    if path.suffix.lower() in {".html", ".htm"}:
        text = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>", " ", text, flags=re.I)
        text = html.unescape(re.sub(r"<[^>]+>", " ", text))
    return _clean_text(text)


def extract_content(path: pathlib.Path) -> tuple[str, list[tuple[str, int, list[Any]]], str]:
    ext = path.suffix.lower()
    rows: list[tuple[str, int, list[Any]]] = []
    try:
        if ext == ".docx":
            return extract_docx(path), rows, "parsed"
        if ext == ".pptx":
            return extract_pptx(path), rows, "parsed"
        if ext == ".xlsx":
            rows = _spreadsheet_rows_xlsx(path)
            text = "\n".join("\t".join(r[2]) for r in rows)
            return text, rows, "parsed"
        if ext == ".xls":
            rows = _spreadsheet_rows_xls(path)
            text = "\n".join("\t".join(r[2]) for r in rows)
            return text, rows, "parsed"
        if ext == ".pdf":
            text = extract_pdf(path)
            return text, rows, "parsed" if text else "empty_or_scanned"
        if ext == ".doc":
            text = extract_legacy_doc(path)
            return text, rows, "partially_parsed" if text else "unsupported_legacy"
        if ext == ".rtf":
            return extract_rtf(path), rows, "parsed"
        if ext == ".csv":
            raw = path.read_bytes()
            for encoding in ("utf-8-sig", "gb18030"):
                try:
                    text = raw.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise UnicodeDecodeError("csv", raw, 0, 1, "unknown encoding")
            reader = csv.reader(io.StringIO(text))
            for number, row in enumerate(reader, 1):
                values = [_clean_text(v) for v in row]
                if any(values):
                    rows.append((path.stem, number, values))
            return text, rows, "parsed"
        if ext in {".txt", ".md", ".html", ".htm", ".json", ".xml"}:
            return extract_plain(path), rows, "parsed"
        if ext in {".xmind", ".emmx"}:
            return extract_generic_zip(path), rows, "partially_parsed"
        if ext in {".jpg", ".jpeg", ".png", ".bmp", ".gif"}:
            return "", rows, "ocr_pending"
        if ext in {".mp4", ".flv", ".mts", ".mov", ".avi"}:
            return "", rows, "media_pending"
        if ext in {".zip", ".rar", ".7z"}:
            return "", rows, "archive_not_expanded"
        if ext == ".swf":
            return "", rows, "legacy_binary"
        if ext in {".wps"}:
            return extract_legacy_doc(path), rows, "partially_parsed"
        if ext in {".pptx", ".pps", ".ppt"}:
            return "", rows, "unsupported_binary"
        return "", rows, "binary"
    except Exception as exc:
        return "", rows, f"error:{type(exc).__name__}:{str(exc)[:120]}"


def header_mapping(row: list[Any]) -> dict[str, int]:
    mapped: dict[str, int] = {}
    for index, value in enumerate(row):
        label = _norm_label(value)
        for field, aliases in FIELD_ALIASES.items():
            if label in {_norm_label(a) for a in aliases} and field not in mapped:
                mapped[field] = index
    return mapped


def find_header(rows: list[tuple[str, int, list[Any]]], start: int) -> tuple[int, dict[str, int]]:
    for idx in range(start, min(start + 15, len(rows))):
        mapping = header_mapping(rows[idx][2])
        if mapping.get("student_name") is not None or mapping.get("phone") is not None:
            return idx, mapping
    return -1, {}


def _valid_name(value: Any) -> bool:
    text = _clean_text(value)
    if not text or len(text) > 30 or not NAME_RE.fullmatch(text):
        return False
    if _norm_label(text) in {_norm_label(a) for aliases in FIELD_ALIASES.values() for a in aliases}:
        return False
    return True


def _json_safe(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def student_name_from_rows(rows: list[tuple[str, int, list[Any]]]) -> str:
    for _, _, row in rows[:40]:
        for index, cell in enumerate(row):
            if _norm_label(cell) in {_norm_label(x) for x in FIELD_ALIASES["student_name"]}:
                for candidate in row[index + 1:]:
                    if _valid_name(candidate):
                        return _clean_text(candidate)
    return ""


def upsert_student(conn: sqlite3.Connection, cipher: TenantCipher, *, name: str, campus_id: str,
                   class_id: str | None, school: str, grade: str, source_file_id: str,
                   source_ref: str, profile: dict[str, Any]) -> str:
    name_index = cipher.blind_index(name, "student-name")
    identity_key = "student:" + name_index
    student_id = "yw_stu_" + hashlib.sha256(identity_key.encode("utf-8")).hexdigest()[:16]
    timestamp = now()
    conn.execute(
        """
        INSERT INTO students(student_id,tenant_id,campus_id,class_id,display_name_enc,name_index,school_enc,
            grade,status,identity_key,source_file_id,source_ref,profile_enc,created_at,updated_at)
        VALUES(?,?,?,?,?,?,?,?,'source_recorded',?,?,?,?,?,?)
        ON CONFLICT(tenant_id, identity_key) DO UPDATE SET
          campus_id=excluded.campus_id,
          class_id=COALESCE(excluded.class_id, students.class_id),
          school_enc=CASE WHEN excluded.school_enc IS NOT NULL THEN excluded.school_enc ELSE students.school_enc END,
          grade=COALESCE(NULLIF(excluded.grade,''), students.grade),
          source_file_id=COALESCE(students.source_file_id, excluded.source_file_id),
          source_ref=COALESCE(students.source_ref, excluded.source_ref),
          profile_enc=excluded.profile_enc,
          updated_at=excluded.updated_at
        """,
        (
            student_id, TENANT_ID, campus_id, class_id, cipher.encrypt_text(name), name_index,
            cipher.encrypt_text(school) if school else None, grade, identity_key,
            source_file_id, source_ref, cipher.encrypt_json(profile), timestamp, timestamp,
        ),
    )
    return student_id


def extract_students(conn: sqlite3.Connection, cipher: TenantCipher, file_id: str,
                     relative_path: str, rows: list[tuple[str, int, list[Any]]], text: str) -> int:
    value = relative_path.replace("\\", "/")
    if not (value.startswith("学业规划/") or value == "财务资料/交费表.xls" or "集训学员信息表" in value or "/学员档案/" in value):
        return 0
    created = 0
    campus_id = campus_for(relative_path)
    candidates: list[tuple[str, dict[str, Any], str]] = []
    for sheet_name, row_number, row in rows:
        mapping = header_mapping(row)
        if mapping.get("student_name") is not None:
            idx = mapping["student_name"]
            name = row[idx + 1] if idx + 1 < len(row) else ""
            if _valid_name(name):
                profile = {
                    "_sheet": sheet_name,
                    "_row": row_number,
                    "_headers": {field: row[pos] for field, pos in mapping.items() if pos < len(row)},
                    "_values": {field: row[pos + 1] for field, pos in mapping.items() if pos + 1 < len(row)},
                }
                candidates.append((_clean_text(name), profile, f"{sheet_name}!{row_number}"))
    if rows:
        content_name = student_name_from_rows(rows)
        if content_name:
            candidates.append((content_name, {"_detected_from": "姓名/学生姓名字段"}, "name-field"))
    stem = pathlib.Path(relative_path).stem
    filename_name = re.split(r"[\s_\-（(]", stem, maxsplit=1)[0]
    if _valid_name(filename_name) and pathlib.Path(relative_path).suffix.lower() in {".xlsx", ".docx"}:
        candidates.append((filename_name, {"_detected_from": "filename"}, "filename"))
    seen = set()
    for name, profile, ref in candidates:
        if name in seen:
            continue
        seen.add(name)
        upsert_student(conn, cipher, name=name, campus_id=campus_id, class_id=None,
                       school="", grade="", source_file_id=file_id, source_ref=ref,
                       profile=profile)
        created += 1
    return created


def extract_leads(conn: sqlite3.Connection, cipher: TenantCipher, file_id: str, relative_path: str,
                  rows: list[tuple[str, int, list[Any]]]) -> int:
    value = relative_path.replace("\\", "/")
    if not (value.startswith("销售资料/") or value.startswith("市场资料/")):
        return 0
    campus_id = campus_for(relative_path)
    created = 0
    by_sheet: dict[str, list[tuple[int, list[Any]]]] = {}
    for sheet, number, row in rows:
        by_sheet.setdefault(sheet, []).append((number, row))
    for sheet, sheet_rows in by_sheet.items():
        header_index, mapping = find_header([(sheet, n, r) for n, r in sheet_rows], 0)
        if header_index < 0:
            continue
        header_row_number, _ = sheet_rows[header_index]
        for row_number, row in sheet_rows[header_index + 1:]:
            def get(field: str) -> str:
                pos = mapping.get(field)
                return _clean_text(row[pos]) if pos is not None and pos < len(row) else ""
            name = get("student_name")
            parent = get("parent_name")
            phone = get("phone")
            school = get("school")
            if not name and not phone:
                continue
            if name and not _valid_name(name):
                name = ""
            identity_basis = "\x1f".join([name, phone, school, get("grade"), sheet])
            identity_key = "lead:" + cipher.blind_index(identity_basis, "lead-identity")
            lead_id = "lead_" + hashlib.sha256(identity_key.encode("utf-8")).hexdigest()[:18]
            raw = {str(i): row[i] for i in range(len(row))}
            conn.execute(
                """
                INSERT INTO leads(lead_id,tenant_id,campus_id,source_file_id,source_sheet,source_row,
                    student_name_enc,parent_name_enc,phone_enc,school_enc,grade,class_name,identity_key,raw_enc,created_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(tenant_id, identity_key) DO UPDATE SET raw_enc=excluded.raw_enc
                """,
                (
                    lead_id, TENANT_ID, campus_id, file_id, sheet, row_number,
                    cipher.encrypt_text(name) if name else None,
                    cipher.encrypt_text(parent) if parent else None,
                    cipher.encrypt_text(phone) if phone else None,
                    cipher.encrypt_text(school) if school else None,
                    get("grade"), get("class_name"), identity_key,
                    cipher.encrypt_json(raw), now(),
                ),
            )
            created += 1
    return created


def insert_file(conn: sqlite3.Connection, cipher: TenantCipher, *, batch_id: str, path: pathlib.Path,
                relative_path: str, file_id: str, digest: str, text: str, rows: list[tuple[str, int, list[Any]]],
                text_status: str, category: str, sensitivity: str, campus_id: str) -> None:
    stat = path.stat()
    conn.execute(
        """
        INSERT INTO source_files(file_id,tenant_id,batch_id,filename_enc,relative_path_enc,extension,mime,
            size_bytes,modified_at,sha256,category,classification,sensitivity,campus_id,storage_mode,
            source_locator_enc,text_status,text_chars,created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,'manifest',?,?,?,?)
        """,
        (
            file_id, TENANT_ID, batch_id, cipher.encrypt_text(path.name), cipher.encrypt_text(relative_path),
            path.suffix.lower(), mimetypes.guess_type(path.name)[0] or "application/octet-stream",
            stat.st_size, datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(), digest,
            category, category, sensitivity, campus_id, cipher.encrypt_text(str(path.resolve())),
            text_status, len(text), now(),
        ),
    )
    if text:
        encoded = text.encode("utf-8", errors="ignore")
        conn.execute(
            "INSERT INTO file_texts(file_id,tenant_id,content_enc,content_sha256,created_at) VALUES(?,?,?,?,?)",
            (file_id, TENANT_ID, cipher.encrypt_bytes(encoded), hashlib.sha256(encoded).hexdigest(), now()),
        )
    for sheet_name, row_number, row in rows:
        payload = json.dumps({"sheet": sheet_name, "row": row_number, "values": row}, ensure_ascii=False, default=str)
        conn.execute(
            "INSERT INTO source_rows(tenant_id,file_id,sheet_name,row_number,row_enc,created_at) VALUES(?,?,?,?,?,?)",
            (TENANT_ID, file_id, sheet_name, row_number, cipher.encrypt_bytes(payload.encode("utf-8")), now()),
        )
    if category in SEARCHABLE and text:
        title = path.stem
        body = text[:FTS_CHARS]
        conn.execute(
            "INSERT INTO file_search(file_id,tenant_id,title,body,classification,campus_id) VALUES(?,?,?,?,?,?)",
            (file_id, TENANT_ID, title, body, category, campus_id),
        )


def main() -> int:
    global TENANT_ID, TENANT_NAME
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default=str(SOURCE_ROOT))
    parser.add_argument("--tenant-id", default=TENANT_ID)
    parser.add_argument("--tenant-name", default=TENANT_NAME)
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--admin-actor", default=os.getenv("TENDER_TENANT_ADMIN_ACTOR", "yanwen-admin"))
    parser.add_argument("--report", default=str(ROOT / "tenant_data" / TENANT_ID / "import_report.json"))
    args = parser.parse_args()

    TENANT_ID = args.tenant_id
    TENANT_NAME = args.tenant_name
    source_root = pathlib.Path(args.source)
    if not source_root.exists():
        print(f"source root not found: {source_root}", file=sys.stderr)
        return 2

    db_path = init_tenant_db(
        TENANT_ID,
        TENANT_NAME,
        reset=args.reset,
        admin_actor_id=args.admin_actor,
        campuses=CAMPUSES,
    )
    create_membership(TENANT_ID, "yanwen-auditor", "auditor", permissions=["*"], can_write=False)
    cipher = TenantCipher(TENANT_ID)
    conn = sqlite3.connect(db_path, timeout=60)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA foreign_keys=ON")

    batch_id = "batch_" + uuid.uuid4().hex[:16]
    started = now()
    conn.execute(
        "INSERT INTO import_batches(batch_id,tenant_id,source_root_enc,status,started_at) VALUES(?,?,?,'running',?)",
        (batch_id, TENANT_ID, cipher.encrypt_text(str(source_root.resolve())), started),
    )
    conn.commit()

    files = sorted(p for p in source_root.rglob("*") if p.is_file())
    counts = {"files": 0, "text": 0, "rows": 0, "students": 0, "leads": 0, "failed": 0}
    errors: list[dict[str, Any]] = []
    print(f"tenant={TENANT_ID} files={len(files)} db={db_path}", flush=True)
    try:
        for index, path in enumerate(files, 1):
            relative = str(path.relative_to(source_root))
            file_id = file_id_for(relative)
            try:
                digest = sha256_file(path)
                text, rows, text_status = extract_content(path)
                category, sensitivity = classify_file(relative)
                campus_id = campus_for(relative)
                insert_file(
                    conn, cipher, batch_id=batch_id, path=path, relative_path=relative, file_id=file_id,
                    digest=digest, text=text, rows=rows, text_status=text_status,
                    category=category, sensitivity=sensitivity, campus_id=campus_id,
                )
                counts["files"] += 1
                counts["text"] += int(bool(text))
                counts["rows"] += len(rows)
                counts["students"] += extract_students(conn, cipher, file_id, relative, rows, text)
                counts["leads"] += extract_leads(conn, cipher, file_id, relative, rows)
                if index % BATCH_CHUNK == 0:
                    conn.commit()
                    print(f"progress {index}/{len(files)} text={counts['text']} rows={counts['rows']} students={counts['students']} leads={counts['leads']}", flush=True)
            except Exception as exc:
                conn.rollback()
                counts["failed"] += 1
                item = {"path": relative, "error": f"{type(exc).__name__}: {str(exc)[:240]}"}
                errors.append(item)
                print(f"ERROR {relative}: {item['error']}", file=sys.stderr, flush=True)
        conn.execute(
            """
            UPDATE import_batches SET status='completed',total_files=?,imported_files=?,failed_files=?,
              extracted_text_files=?,source_rows=?,students=?,leads=?,finished_at=?,errors_json=?
            WHERE batch_id=?
            """,
            (
                len(files), counts["files"], counts["failed"], counts["text"], counts["rows"],
                counts["students"], counts["leads"], now(), json.dumps(errors, ensure_ascii=False), batch_id,
            ),
        )
        conn.commit()
        write_tenant_audit(TENANT_ID, args.admin_actor, "tenant.import", batch_id, {
            "source": str(source_root), "files": counts["files"], "failed": counts["failed"],
            "text_files": counts["text"], "rows": counts["rows"], "students": counts["students"], "leads": counts["leads"],
        })
        report = {
            "tenant_id": TENANT_ID,
            "batch_id": batch_id,
            "source_root": str(source_root),
            "database": str(db_path),
            "database_bytes": db_path.stat().st_size,
            "total_files": len(files),
            **counts,
            "completed_at": now(),
            "errors": errors[:200],
        }
        report_path = pathlib.Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)
        return 0
    except Exception:
        conn.rollback()
        conn.execute(
            "UPDATE import_batches SET status='failed',finished_at=?,errors_json=? WHERE batch_id=?",
            (now(), json.dumps(errors, ensure_ascii=False), batch_id),
        )
        conn.commit()
        traceback.print_exc()
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
