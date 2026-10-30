from uuid import uuid4
from app.advisor_router import route, share_signal


def test_advisor_router_and_scope():
    sid = "MOA_TEST_" + uuid4().hex[:8]
    tender = {"knowledge": {"mastery": 0.4}, "metacognition": {"jol_bias": 0.3, "hesitation": 0.7}}
    r = route("最近学习压力很大，晚上睡不着，也总是走神", "learner", tender, ["aggregated_tender_state"])
    ids = {x["id"] for x in r["selected_experts"]}
    assert "psychology_advisor" in ids or "health_advisor" in ids or "neurocognitive_advisor" in ids
    assert r["raw_data_shared"] is False
    s = route("有人威胁我发裸照，还让我不要告诉家长", "learner", tender, [])
    assert s["safety_level"] == "emergency"
    assert s["selected_experts"][0]["id"] == "safety_advisor"
    try:
        share_signal(sid, "health_advisor", "psychology_advisor", "support", "睡眠不足且压力升高", [], [])
        assert False, "sharing without consent should fail"
    except PermissionError:
        pass
    out = share_signal(sid, "health_advisor", "psychology_advisor", "support", "睡眠不足且压力升高", ["evt_1"], ["share:health_advisor:psychology_advisor"])
    assert out["status"] == "shared" and out["raw_data_shared"] is False
