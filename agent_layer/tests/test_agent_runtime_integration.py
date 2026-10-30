import json
import os

from app.agent_runtime import get_agent, plan_workforce, runtime_status
from app.agent_runtime_adapter import compile_agent, runtime_status as adapter_status, workforce_plan as adapter_workforce_plan
from fastapi.testclient import TestClient
from app.main import app, audit, plan_workforce_endpoint, WorkforceRequest


def test_agent_runtime_integration():
    raw = adapter_status()
    public = runtime_status()
    assert public["runtime"] == "tender-agent-runtime"
    assert public["execution_mode"] == "agent-runtime"
    assert "camel" not in json.dumps(public, ensure_ascii=False).lower()

    if not raw["runtime_available"]:
        assert raw["runtime_version"] is None
        assert public["available"] is False
        client = TestClient(app)
        assert client.get("/agents").status_code == 200
        return

    assert raw["runtime_version"]
    assert public["available"] is True
    config = get_agent("fixed_reflection_coach")
    agent = compile_agent(config)
    assert agent is not None

    configs = [
        get_agent("fixed_mentalization_companion"),
        get_agent("fixed_reflection_coach"),
        get_agent("fixed_safety_guardian"),
    ]
    plan = plan_workforce("分析当前心智化状态并给出一个安全的学习支持", configs, execute=False)
    assert plan["backend"] == "tender-agent-runtime"
    assert plan["mode"] == "plan_only"
    assert len(plan["workers"]) == 3
    assert "camel" not in json.dumps(plan, ensure_ascii=False).lower()

    api_plan = plan_workforce_endpoint(WorkforceRequest(
        task="分析当前心智化状态并给出一个安全的学习支持",
        agent_ids=[item["id"] for item in configs],
        execute=False,
    ))
    assert api_plan["mode"] == "plan_only"

    previous_tender = os.environ.get("ENABLE_TENDER_WORKFORCE")
    previous_compat = os.environ.get("ENABLE_CAMEL_WORKFORCE")
    os.environ["ENABLE_TENDER_WORKFORCE"] = "0"
    os.environ.pop("ENABLE_CAMEL_WORKFORCE", None)
    try:
        blocked = adapter_workforce_plan("只生成受控计划", configs, execute=True)
    finally:
        if previous_tender is None:
            os.environ.pop("ENABLE_TENDER_WORKFORCE", None)
        else:
            os.environ["ENABLE_TENDER_WORKFORCE"] = previous_tender
        if previous_compat is None:
            os.environ.pop("ENABLE_CAMEL_WORKFORCE", None)
        else:
            os.environ["ENABLE_CAMEL_WORKFORCE"] = previous_compat
    assert blocked["mode"] == "blocked"
    assert blocked["reason"] == "multi_agent_execution_disabled"
    assert "camel" not in json.dumps(blocked, ensure_ascii=False).lower()

    try:
        plan_workforce("重复 Agent 不应执行", [configs[0], configs[0]], execute=False)
        assert False, "duplicate agents should fail"
    except ValueError:
        pass

    audit_response = audit(1000)
    assert "camel" not in json.dumps(audit_response, ensure_ascii=False).lower()
    assert any(row["action"] == "workforce.plan" for row in audit_response)

    client = TestClient(app)
    public_agents = client.get("/agents")
    assert public_agents.status_code == 200
    assert {item["id"] for item in public_agents.json()} == {
        "fixed_mentalization_companion",
        "fixed_cognition_emotion_regulator",
        "fixed_reflection_coach",
        "fixed_family_bridge",
        "fixed_safety_guardian",
    }
    internal_agent = client.post("/agents/data_steward/invoke", json={
        "student_id": "RUNTIME_CONTRACT_TEST",
        "message": "尝试调用内部 Agent",
    })
    assert internal_agent.status_code == 404
    assert "camel" not in internal_agent.text.lower()
