"""最小演示：写入事件、计算 Tender 状态、调用 Agent。"""
from __future__ import annotations
import json
from app.store import insert_event, list_events
from app.tender import compute_state
from app.agents import invoke

SAMPLE = [
    {"event_type":"answer","student_id":"S01","session_id":"ses1","timestamp":"2026-10-16T19:00:00+08:00","payload":{"correct":False},"source":"platform"},
    {"event_type":"answer","student_id":"S01","session_id":"ses1","timestamp":"2026-10-16T19:02:00+08:00","payload":{"correct":True},"source":"platform"},
    {"event_type":"answer","student_id":"S01","session_id":"ses1","timestamp":"2026-10-16T19:05:00+08:00","payload":{"correct":False},"source":"platform"},
    {"event_type":"metacognition_jol","student_id":"S01","session_id":"ses1","timestamp":"2026-10-16T18:55:00+08:00","payload":{"predicted_correct":7,"actual_correct":4,"n_items":10},"source":"teacher_card"},
    {"event_type":"response","student_id":"S01","session_id":"ses1","timestamp":"2026-10-16T19:01:00+08:00","payload":{"response_time_ms":42000},"source":"platform"},
    {"event_type":"baseline","student_id":"S01","session_id":"ses1","timestamp":"2026-10-16T19:00:00+08:00","payload":{"arrangement_fit":0.82,"habit_change":0.10},"source":"scheduler"},
    {"event_type":"group_interaction","student_id":"S01","session_id":"ses1","timestamp":"2026-10-16T19:10:00+08:00","payload":{"clustering":0.62,"bridge_ratio":0.18},"source":"survey"},
]

if __name__ == "__main__":
    for e in SAMPLE:
        insert_event(e)
    events = list_events("S01")
    state = compute_state("S01", events)
    print("=== Tender State ===")
    print(json.dumps(state, ensure_ascii=False, indent=2))
    for agent_id in ["metacognition_coach","student_tutor","teacher_copilot","group_facilitator","safety_guardrail","data_steward"]:
        print("=== " + agent_id + " ===")
        print(json.dumps(invoke(agent_id, "S01", "我卡在这道题", state), ensure_ascii=False, indent=2))
