from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
required = [
    ROOT / "README.md",
    ROOT / "LICENSE",
    ROOT / "VERSION",
    ROOT / "requirements-research.txt",
    ROOT / "docs/whitepaper/Tender-Whitepaper-v2.2.pdf",
    ROOT / "docs/whitepaper/Tender-Whitepaper-v2.2.docx",
    ROOT / "docs/whitepaper/Tender-Whitepaper-v2.2.tex",
    ROOT / "docs/whitepaper/Tender-DAOQL-Data-Water-Whitepaper-v1.0.md",
    ROOT / "docs/whitepaper/Tender-DAOQL-Data-Water-Whitepaper-v1.0.pdf",
    ROOT / "docs/research/Tender-Golden-Bias-Experiment-v1.0.pdf",
    ROOT / "docs/research/Tender-Rhythm-Phase-Experiment-v1.0.pdf",
    ROOT / "docs/research/Tender-Neuro-Learning-Evidence-v1.0.pdf",
    ROOT / "docs/research/Tender-Preassessment-v1.1.pdf",
    ROOT / "experiments/golden_bias_regulation/results.json",
    ROOT / "experiments/rhythm_phase_detection/results.json",
    ROOT / "experiments/knowledge_tracing_bench/outputs/analysis_summary.json",
    ROOT / "modeling/app/__init__.py",
    ROOT / "modeling/app/tender.py",
    ROOT / "modeling/app/tender_models.py",
    ROOT / "modeling/app/mentalization.py",
    ROOT / "modeling/app/world_tree.py",
    ROOT / "modeling/app/golden_bias.py",
    ROOT / "modeling/schemas/tender_state.json",
    ROOT / "modeling/schemas/daoql_event.json",
]
missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
if missing:
    raise SystemExit("missing required research files:\n" + "\n".join(missing))

forbidden = [
    ROOT / "agent_layer",
    ROOT / "site",
    ROOT / "docs/product",
    ROOT / "docs/teaching",
    ROOT / "Dockerfile",
    ROOT / "render.yaml",
]
still_present = [str(path.relative_to(ROOT)) for path in forbidden if path.exists()]
if still_present:
    raise SystemExit("product paths must live in Tender-Product:\n" + "\n".join(still_present))

checks = {
    "k12_nodes": (ROOT / "knowledge_data/db_k12.sqlite", "SELECT COUNT(*) FROM knowledge_nodes", 1075),
    "majors": (ROOT / "knowledge_data/db_university.sqlite", "SELECT COUNT(*) FROM majors", 875),
    "courses": (ROOT / "knowledge_data/db_university_courses.sqlite", "SELECT COUNT(*) FROM major_courses", 319),
    "occupations": (ROOT / "knowledge_data/db_career.sqlite", "SELECT COUNT(*) FROM occupations", 1016),
}
for name, (path, sql, expected) in checks.items():
    with sqlite3.connect(path) as con:
        actual = con.execute(sql).fetchone()[0]
    if actual != expected:
        raise SystemExit(f"{name}: expected {expected}, got {actual}")
    print(f"ok {name}={actual}")

version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
print(f"ok version={version}")
print("ok whitepapers=present")
print("ok research-reports=present")
print("ok experiments=present")
print("ok reference-models=present")
print("ok product-split=clean")
print("research repository verification passed")
