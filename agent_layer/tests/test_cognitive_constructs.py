# -*- coding: utf-8 -*-
from uuid import uuid4

from fastapi.testclient import TestClient

from app.cognitive_constructs import assess_bloom, assess_forest, assess_result
from app.main import app


def _session(client, actor_id, role="learner", learner_id=None):
    response = client.post(
        "/auth/demo-session",
        json={"actor_id": actor_id, "role": role, "learner_id": learner_id or actor_id},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": "Bearer " + response.json()["token"]}


def test_cognitive_constructs_and_api():
    bloom = assess_bloom({
        "retention_24h": 0.88,
        "retention_7d": 0.82,
        "retention_30d": 0.74,
        "transfer_score": 0.78,
        "schema_coherence": 0.81,
        "cognitive_load": 0.25,
    })
    assert bloom["construct"] == "bloom"
    assert bloom["status"] == "supported"
    assert bloom["components"]["retention_index"] > 0.75

    weak_bloom = assess_bloom({
        "retention_24h": 0.92,
        "retention_7d": 0.31,
        "retention_30d": 0.18,
        "transfer_score": 0.80,
        "schema_coherence": 0.70,
        "cognitive_load": 0.30,
    })
    assert weak_bloom["status"] == "insufficient_evidence"

    synthesis = assess_result({
        "individual_novelty": [0.58, 0.61, 0.55],
        "group_novelty": 0.88,
        "synthesis": 0.82,
        "utility": 0.84,
        "tms": 0.78,
        "relationship_conflict": 0.18,
    })
    assert synthesis["status"] == "supported"
    assert synthesis["components"]["novelty_gain"] > 0

    aggregation = assess_result({
        "individual_novelty": [0.80, 0.64, 0.60],
        "group_novelty": 0.80,
        "synthesis": 0.10,
        "utility": 0.82,
        "tms": 0.55,
        "relationship_conflict": 0.10,
    })
    assert aggregation["status"] == "insufficient_evidence"

    forest = assess_forest({
        "cognitive_diversity": 0.82,
        "tms": 0.81,
        "contribution_entropy": 0.76,
        "recombination_history": 0.70,
        "homogenization": 0.18,
    })
    assert forest["status"] == "supported"

    client = TestClient(app)
    catalog = client.get("/cognition/constructs")
    assert catalog.status_code == 200
    assert catalog.json()["model_version"] == "cognitive-constructs-1.0"
    assert {item["id"] for item in catalog.json()["constructs"]} == {"bloom", "result", "forest"}

    learner_id = "CC_" + uuid4().hex[:8]
    headers = _session(client, learner_id)
    other = _session(client, "CC_OTHER_" + uuid4().hex[:8])
    payload = {"construct_id": "bloom", "evidence": {
        "retention_24h": 0.86,
        "retention_7d": 0.80,
        "retention_30d": 0.75,
        "transfer_score": 0.76,
        "schema_coherence": 0.78,
        "cognitive_load": 0.24,
    }}
    assert client.post(f"/cognition/assessments/{learner_id}", json=payload).status_code == 401
    created = client.post(f"/cognition/assessments/{learner_id}", headers=headers, json=payload)
    assert created.status_code == 200, created.text
    assert created.json()["assessment"]["status"] == "supported"
    assert created.json()["event_id"].startswith("evt_")
    listed = client.get(f"/cognition/assessments/{learner_id}", headers=headers)
    assert listed.status_code == 200
    assert listed.json()["count"] >= 1
    denied = client.get(f"/cognition/assessments/{learner_id}", headers=other)
    assert denied.status_code == 403
