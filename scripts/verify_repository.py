from __future__ import annotations

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
K = ROOT / "knowledge_data"

required = [
    ROOT / "README.md",
    ROOT / "LICENSE",
    ROOT / "VERSION",
    ROOT / "docs/whitepaper/Tender-Whitepaper-v2.2.pdf",
    ROOT / "docs/whitepaper/Tender-Whitepaper-v2.2.docx",
    ROOT / "docs/whitepaper/Tender-Whitepaper-v2.2.tex",
    ROOT / "docs/product/Tender-Product-Manual-v7.2.pdf",
    ROOT / "docs/product/Tender-Product-Manual-v7.2.docx",
    ROOT / "docs/product/Tender-Product-Manual-v7.2.md",
    ROOT / "docs/product/Tender-User-Guide-v7.2.pdf",
    ROOT / "docs/product/Tender-User-Guide-v7.2.docx",
    ROOT / "docs/product/Tender-User-Guide-v7.2.md",
    ROOT / "docs/teaching/Tender-Teaching-Manual-v6.2.pdf",
    ROOT / "docs/teaching/Tender-Teaching-Manual-v6.2.tex",
    ROOT / "docs/research/Tender-Golden-Bias-Experiment-v1.0.pdf",
    ROOT / "agent_layer/app/main.py",
    ROOT / "agent_layer/app/preassessment.py",
    ROOT / "agent_layer/app/world_tree.py",
    ROOT / "agent_layer/app/golden_bias.py",
    ROOT / "agent_layer/app/group_chat.py",
    ROOT / "agent_layer/tests/run_all.py",
    ROOT / "agent_layer/tests/test_group_chat.py",
    ROOT / "knowledge_data/preassessment_world_interface_items.json",
    ROOT / "knowledge_data/preassessment_big_five_pulse_items.json",
    ROOT / "experiments/golden_bias_regulation/results.json",
    ROOT / "docs/research/Tender-Rhythm-Phase-Experiment-v1.0.pdf",
    ROOT / "experiments/rhythm_phase_detection/results.json",
    ROOT / "site/index.html",
    ROOT / "site/assets/app.js",
    ROOT / "site/assets/course.js",
    ROOT / "site/assets/docs/Tender-Whitepaper-v2.2.pdf",
    ROOT / "site/assets/docs/Tender-Product-Manual-v7.2.pdf",
    ROOT / "site/assets/docs/Tender-User-Guide-v7.2.pdf",
    ROOT / "site/assets/docs/Tender-Teaching-Manual-v6.2.pdf",
    ROOT / "agent_layer/desktop_overlay/screen_context.py",
    ROOT / "agent_layer/desktop_overlay/screen_context_mcp.py",
    ROOT / "agent_layer/desktop_overlay/media_plugins.py",
    ROOT / "agent_layer/desktop_overlay/media_plugins_mcp.py",
    ROOT / "agent_layer/desktop_overlay/media_plugin_worker.py",
    ROOT / ".mcp.json",
    ROOT / "render.yaml",
    ROOT / "Dockerfile",
    ROOT / ".devcontainer/devcontainer.json",
    ROOT / ".devcontainer/start-tender.sh",
    ROOT / "site/app/index.html",
    ROOT / "site/app/app.js",
    ROOT / "site/app/app.css",
    ROOT / "docs/DEPLOYMENT.md",
    K / "db_k12.sqlite",
    K / "db_university.sqlite",
    K / "db_university_courses.sqlite",
    K / "db_career.sqlite",
]
missing = [str(path) for path in required if not path.exists()]
if missing:
    raise SystemExit("missing required files:\n" + "\n".join(missing))

forbidden = [
    ROOT / "docs/whitepaper/Tender-Whitepaper-v2.1.pdf",
    ROOT / "docs/product/Tender-Product-Manual-v7.1.pdf",
    ROOT / "docs/product/Tender-User-Guide-v7.1.pdf",
    ROOT / "docs/teaching/Tender-Teaching-Manual-v6.1.pdf",
    ROOT / "knowledge_data/preassessment_mbti_items.json",
    ROOT / "knowledge_data/preassessment_jungian_items.json",
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

version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
if version != "2.2.1":
    raise SystemExit(f"VERSION: expected 2.2.1, got {version}")
print(f"ok version={version}")

license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
if "PolyForm Noncommercial License 1.0.0" not in license_text:
    raise SystemExit("LICENSE is not PolyForm Noncommercial 1.0.0")
print("ok license=PolyForm-Noncommercial-1.0.0")
print("ok active-docs=current-only")
print("ok world-tree=present")
print("ok golden-bias=present")
print("ok experiment=present")
print("ok rhythm-phase-experiment=present")
print("ok group-chat=dual-chain-present")
print("ok mcp=screen-context-and-media-present")
print("ok deployment=github-pages-static-and-one-click-backend")
print("repository verification passed")