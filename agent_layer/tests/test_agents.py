import app.agent_runtime as runtime_module
from app.agent_runtime import invoke, list_agents
from app.guardrails import check_text


def test_agents():
    assert len(list_agents()) >= 15
    state = {
        "student_id": "T_AGENT",
        "n_events": 3,
        "knowledge": {"mastery": 0.4},
        "metacognition": {"jol_bias": 0.2, "hesitation": 0.6},
        "baseline": {"arrangement_fit": 0.6, "habit_change": 0.1},
        "group": {"clustering": 0.7, "bridge_ratio": 0.1},
        "timestamp": "now",
    }

    captured = {}

    def fake_execute(config, message, tender_state, context=None):
        captured[config["id"]] = tender_state
        return {"text": "由测试运行时返回", "provider": "agent-runtime", "model": "unit-test", "runtime": "tender-agent-runtime"}

    original_execute = runtime_module.execute_agent
    runtime_module.execute_agent = fake_execute
    try:
        out = invoke("metacognition_coach", "T_AGENT", "我不确定", state)
        fixed = invoke("fixed_reflection_coach", "T_AGENT", "我有点不确定", state)
        family = invoke("fixed_family_bridge", "T_AGENT", "请生成家庭支持摘要", state)
    finally:
        runtime_module.execute_agent = original_execute

    def failing_execute(config, message, tender_state, context=None):
        raise RuntimeError("internal adapter detail")

    def fake_chat(messages):
        return {"provider": "configured-model", "model": "unit-fallback", "text": "回退建议"}

    original_chat = runtime_module.chat
    runtime_module.execute_agent = failing_execute
    runtime_module.chat = fake_chat
    try:
        fallback = invoke("fixed_reflection_coach", "T_AGENT", "继续", state)
    finally:
        runtime_module.execute_agent = original_execute
        runtime_module.chat = original_chat

    assert out["from_agent"] == "metacognition_coach"
    assert out["llm"]["provider"] == "agent-runtime"
    assert out["llm"]["fallback_used"] is False
    assert fixed["from_agent"] == "fixed_reflection_coach"
    assert "quadrant" in fixed["action"]["rule"]
    assert family["policy"]["requires_human_approval"] is True
    assert fallback["llm"]["provider"] == "agent-runtime"
    assert fallback["llm"]["fallback_used"] is True
    assert fallback["llm"]["fallback_reason"] == "agent_runtime_execution_failed"
    assert "internal adapter detail" not in str(fallback)
    assert captured["fixed_reflection_coach"]["scope"] == "metacognition_summary"
    assert captured["fixed_family_bridge"]["scope"] == "approved_family_summary"
    assert "group" not in captured["fixed_family_bridge"]
    assert check_text("正常内容")["allowed"] is True
