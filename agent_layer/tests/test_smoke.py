"""最小冒烟测试：不依赖 HTTP。"""
from app.store import insert_event, list_events
from app.tender import compute_state
from app.agents import list_agents, invoke


def test_pipeline():
    insert_event({"event_type":"answer","student_id":"TEST","timestamp":"2026-10-16T19:00:00+08:00","payload":{"correct":True},"source":"test"})
    insert_event({"event_type":"answer","student_id":"TEST","timestamp":"2026-10-16T19:01:00+08:00","payload":{"correct":False},"source":"test"})
    events = list_events("TEST")
    state = compute_state("TEST", events)
    assert 0.0 <= state["knowledge"]["mastery"] <= 1.0
    agents = list_agents()
    assert len(agents) >= 10
    assert len({agent["id"] for agent in agents}) == len(agents)
    out = invoke("metacognition_coach", "TEST", "我不确定", state)
    assert out["from_agent"] == "metacognition_coach"
