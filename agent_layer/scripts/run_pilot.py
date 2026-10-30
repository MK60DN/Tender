"""端到端试点：种子 + RAG + Tender + Agent + 报告。"""
from __future__ import annotations
import sys, pathlib, json
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from app.rag import ingest_text, build_index
from app.daoql import list_events
from app.tender import compute_state
from app.agent_runtime import invoke
from app.reports import student_report, teacher_report, parent_report

if __name__ == "__main__":
    import scripts.seed_demo as seed
    seed.main()
    ingest_text("pilot_note", "Tender 试点：JOL 预测、犹豫检测、教师 metameta、群体拓扑。")
    print(build_index())
    events = list_events("S01")
    state = compute_state("S01", events)
    print("=== state ===")
    print(json.dumps(state, ensure_ascii=False, indent=2))
    print("=== student report ===")
    print(json.dumps(student_report(state), ensure_ascii=False, indent=2))
    print("=== metacognition coach ===")
    print(json.dumps(invoke("metacognition_coach", "S01", "我不确定这题对不对", state), ensure_ascii=False, indent=2))
