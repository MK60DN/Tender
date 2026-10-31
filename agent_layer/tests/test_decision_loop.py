# -*- coding: utf-8 -*-
from uuid import uuid4

from fastapi.testclient import TestClient

from app.benchmark import tender_theta_benchmark
from app.daoql import causal_path, list_audit
from app.decision_loop import create_loop, get_loop, record_action, record_result
from app.main import app


def _session(client, actor_id, role="learner", learner_id=None):
    response = client.post(
        "/auth/demo-session",
        json={"actor_id": actor_id, "role": role, "learner_id": learner_id or actor_id},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": "Bearer " + response.json()["token"]}


def test_decision_loop_and_benchmark():
    benchmark = tender_theta_benchmark()
    assert len(benchmark["models"]) == 4
    assert benchmark["dataset"]["cleaned_records"] == 273364
    model_by_id = {item["id"]: item for item in benchmark["models"]}
    assert model_by_id["tender_default"]["auc"] == 0.6895
    assert model_by_id["tender_default"]["log_loss"] == 1.1155
    assert model_by_id["bkt"]["auc"] == 0.6794
    assert model_by_id["bkt"]["log_loss"] == 0.5910
    assert benchmark["headline_model_id"] == "logistic"
    assert benchmark["tender_default_recommended"] is False
    assert benchmark["comparison_status"] == "tender_not_superior"
    assert benchmark["claim_status"] == "mixed_results_not_a_win"
    assert {"confidence_interval", "repeated_splits", "significance_test", "calibration_ece_brier"} <= set(benchmark["pending_validation"])
    assert "未表现出" in benchmark["disclaimer"]

    learner_id = "DL_DIRECT_" + uuid4().hex[:8]
    loop = create_loop(
        learner_id=learner_id,
        goal="决定今晚如何推进一项学习任务",
        options=[
            {"id": "small_step", "label": "先完成十分钟最小步骤"},
            {"id": "review", "label": "先回看昨天的错误"},
        ],
        selected_option_id="small_step",
        choice_reason="当前任务较大，需要先恢复可控感。",
        state={"load": "high", "confidence": 0.42},
        actor_id=learner_id,
    )
    assert loop["status"] == "planned"
    assert loop["create_event_id"].startswith("evt_")
    loop = record_action(
        loop["loop_id"],
        action="完成十分钟最小步骤",
        expected_outcome="能开始并形成下一步线索",
        state={"load": "medium", "confidence": 0.55},
        actor_id=learner_id,
    )
    assert loop["status"] == "acted"
    assert loop["action_event_id"].startswith("evt_")
    loop = record_result(
        loop["loop_id"],
        actual_result="完成十二分钟，并发现卡点来自任务边界不清。",
        responsibility_owner=learner_id,
        reflection="下次先把任务边界写成一句可检验的话。",
        state={"load": "low", "confidence": 0.68},
        actor_id=learner_id,
    )
    assert loop["status"] == "completed"
    assert loop["actual_result"]
    assert loop["responsibility_owner"] == learner_id
    assert loop["reflection"]
    assert loop["state"]["confidence"] == 0.68
    assert get_loop(loop["loop_id"])["loop_id"] == loop["loop_id"]
    path = causal_path(loop["create_event_id"], loop["result_event_id"])
    assert path["found"] is True
    audits = [item for item in list_audit(limit=500) if item["target"] == loop["loop_id"]]
    assert {item["action"] for item in audits} >= {
        "decision_loop.create",
        "decision_loop.action",
        "decision_loop.result",
    }

    client = TestClient(app)
    assert client.post("/decision-loops", json={}).status_code == 401
    assert client.get("/benchmark/tender-theta").status_code == 200

    actor_id = "DL_HTTP_" + uuid4().hex[:8]
    headers = _session(client, actor_id)
    other = _session(client, "DL_OTHER_" + uuid4().hex[:8])
    payload = {
        "learner_id": actor_id,
        "goal": "选择下一步支持方式",
        "options": [
            {"id": "ask", "label": "先提出一个澄清问题"},
            {"id": "rest", "label": "先暂停十分钟"},
        ],
        "selected_option_id": "ask",
        "choice_reason": "信息不足，先澄清比盲目继续更合适。",
        "state": {"clarity": 0.35},
    }
    created = client.post("/decision-loops", headers=headers, json=payload)
    assert created.status_code == 200, created.text
    loop_id = created.json()["decision_loop"]["loop_id"]

    cross = client.get("/decision-loops/" + loop_id, headers=other)
    assert cross.status_code == 403
    assert client.post(
        f"/decision-loops/{loop_id}/actions",
        headers=other,
        json={"action": "越权行动", "expected_outcome": "不应成功"},
    ).status_code == 403

    acted = client.post(
        f"/decision-loops/{loop_id}/actions",
        headers=headers,
        json={
            "action": "提出澄清问题",
            "expected_outcome": "确认真正卡点",
            "state": {"clarity": 0.52},
        },
    )
    assert acted.status_code == 200, acted.text
    completed = client.post(
        f"/decision-loops/{loop_id}/results",
        headers=headers,
        json={
            "actual_result": "确认卡点来自任务定义不清。",
            "responsibility_owner": actor_id,
            "reflection": "先澄清再行动。",
            "state": {"clarity": 0.78},
        },
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["decision_loop"]["status"] == "completed"

    queried = client.get("/decision-loops/" + loop_id, headers=headers)
    assert queried.status_code == 200
    assert queried.json()["decision_loop"]["result_event_id"]
    listed = client.get(
        "/decision-loops", headers=headers, params={"learner_id": actor_id}
    )
    assert listed.status_code == 200
    assert listed.json()["count"] >= 1
    assert client.get(
        "/decision-loops", headers=other, params={"learner_id": actor_id}
    ).status_code == 403

    admin = _session(client, "admin", role="admin", learner_id="")
    chain = client.get("/audit/verify", headers=admin)
    assert chain.status_code == 200
    assert chain.json()["valid"] is True