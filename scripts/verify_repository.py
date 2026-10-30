from __future__ import annotations

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
K = ROOT / "knowledge_data"

required = [
    ROOT / "README.md",
    ROOT / "LICENSE",
    ROOT / "docs/whitepaper/Tender-Whitepaper-v1.5.pdf",
    ROOT / "agent_layer/app/main.py",
    ROOT / "agent_layer/tests/run_all.py",
    K / "db_k12.sqlite",
    K / "db_university.sqlite",
    K / "db_university_courses.sqlite",
    K / "db_career.sqlite",
]
missing = [str(path) for path in required if not path.exists()]
if missing:
    raise SystemExit("missing required files:\n" + "\n".join(missing))

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

for forbidden in [ROOT / ".env", ROOT / "agent_layer/tender_agent.db", ROOT / "agent_layer/tenant_data"]:
    if forbidden.exists():
        print(f"warning runtime artifact exists locally: {forbidden}")
print("repository verification passed")
