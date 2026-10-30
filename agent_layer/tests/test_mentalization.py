from uuid import uuid4
from app.main import learner_mentalization, record_reflection, ReflectionCreate, record_mentalization_snapshot, mentalization_timeline


def test_c_end_mentalization_and_reflection():
    sid = "C_END_TEST_" + uuid4().hex[:8]
    state = learner_mentalization(sid)
    assert state["student_id"] == sid
    assert state["hypotheses"]
    assert state["reflection_prompt"]
    assert "不是心理或医学诊断" in state["boundary"]
    out = record_reflection(sid, ReflectionCreate(prompt="此刻最值得被理解的是什么？", answer="我卡在不知道如何开始，也有点焦虑。"))
    assert out["status"] == "recorded"
    assert out["event_id"].startswith("evt_")
    assert out["mentalization"]["emotion_context"]["evidence_count"] >= 1
    assert out["mentalization"]["state_snapshot"]["event_count"] >= 1
    snap = record_mentalization_snapshot(sid)
    assert snap["status"] == "recorded"
    assert snap["event_id"].startswith("evt_")
    timeline = mentalization_timeline(sid)
    assert timeline["points"]
    assert timeline["points"][-1]["summary"]
