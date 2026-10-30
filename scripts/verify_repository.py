from __future__ import annotations

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
K = ROOT / "knowledge_data"

required = [
    ROOT / "README.md",
    ROOT / "LICENSE",
    ROOT / "VERSION",
    ROOT / "docs/whitepaper/Tender-Whitepaper-v1.6.pdf",
    ROOT / "docs/product/Tender-Product-Manual-v6.20.pdf",
    ROOT / "docs/product/Tender-User-Guide-v6.8.pdf",
    ROOT / "docs/teaching/Tender-Teaching-Manual-v5.3.pdf",
    ROOT / "agent_layer/app/main.py",
    ROOT / "agent_layer/tests/run_all.py",
    ROOT / "site/index.html",
    ROOT / "site/assets/app.js",
    ROOT / "site/assets/course.js",
    ROOT / "site/assets/docs/Tender-Whitepaper-v1.6.pdf",
    ROOT / "site/assets/docs/Tender-Product-Manual-v6.20.pdf",
    ROOT / "site/assets/docs/Tender-User-Guide-v6.8.pdf",
    ROOT / "site/assets/docs/Tender-Teaching-Manual-v5.3.pdf",
    K / "db_k12.sqlite",
    K / "db_university.sqlite",
    K / "db_university_courses.sqlite",
    K / "db_career.sqlite",
]
missing = [str(path) for path in required if not path.exists()]
if missing:
    raise SystemExit("missing required files:\n" + "\n".join(missing))

forbidden = [
    ROOT / "legacy_analysis_engine",
    ROOT / "docs/whitepaper/Tender-Whitepaper-v1.5.pdf",
    ROOT / "docs/whitepaper/Tender-Whitepaper-v1.5.docx",
    ROOT / "docs/whitepaper/Tender-Whitepaper-v1.5.tex",
    ROOT / "docs/product/Tender-Product-Manual-v6.19.pdf",
    ROOT / "docs/product/Tender-Product-Manual-v6.19.md",
    ROOT / "docs/product/Tender-User-Guide-v6.7.pdf",
    ROOT / "docs/product/Tender-User-Guide-v6.7.md",
    ROOT / "docs/teaching/Tender-Teaching-Manual-v5.2.pdf",
    ROOT / "docs/teaching/Tender-Teaching-Manual-v5.2.tex",
    ROOT / "site/assets/docs/Tender-Whitepaper-v1.5.pdf",
    ROOT / "site/assets/docs/Tender-Product-Manual-v6.19.pdf",
    ROOT / "site/assets/docs/Tender-User-Guide-v6.7.pdf",
    ROOT / "site/assets/docs/Tender-Teaching-Manual-v5.2.pdf",
]
present_forbidden = [str(path) for path in forbidden if path.exists()]
if present_forbidden:
    raise SystemExit("superseded files must not be active:\n" + "\n".join(present_forbidden))

checks = {
    "k12_nodes": (K / "db_k12.sqlite", "SELECT COUNT(*) FROM knowledge_nodes", 1075),
    "majors": (K / "db_university.sqlite", "SELECT COUNT(*) FROM majors", 875),
    "courses": (K / "db_university_courses.sqlite", "SELECT COUNT(*) FROM major_courses", 319),
    "occupations": (K / "db_career.sqlite", "SELECT COUNT(*) FROM occupations", 1016),
}
for name, (path, sql, expected) in checks.items():
    with sqlite3.connect(path) as con:
        actual = con.execute(sql).fetchone()[0]
    if actual != expected:
        raise SystemExit(f"{name}: expected {expected}, got {actual}")
    print(f"ok {name}={actual}")

for artifact in [ROOT / ".env", ROOT / "agent_layer/tender_agent.db", ROOT / "agent_layer/tenant_data"]:
    if artifact.exists():
        print(f"warning runtime artifact exists locally: {artifact}")

version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
if version != "1.6.1":
    raise SystemExit(f"VERSION: expected 1.6.1, got {version}")
print(f"ok version={version}")

license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
if "PolyForm Noncommercial License 1.0.0" not in license_text:
    raise SystemExit("LICENSE is not PolyForm Noncommercial 1.0.0")
print("ok license=PolyForm-Noncommercial-1.0.0")
print("ok active-docs=current-only")
print("repository verification passed")