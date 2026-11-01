from pathlib import Path
import os
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["TENDER_ALLOW_HEADER_IDENTITY"] = "1"

from fastapi.testclient import TestClient
from app.daoql import list_events
from app.main import app


def _headers(student_id: str) -> dict[str, str]:
    return {"X-Tender-Actor": student_id, "X-Tender-Role": "learner", "X-Tender-Learner": student_id}


def _responses(client: TestClient) -> dict[str, int]:
    catalog = client.get("/preassessment/items").json()
    responses: dict[str, int] = {}
    for section in ["big_five", "world_interface"]:
        responses.update({item["id"]: 3 for item in catalog[section]["items"]})
    return responses


def test_world_setup_precedes_profile_and_survives_preassessment():
    with TestClient(app) as client:
        learner = "world-api-" + uuid.uuid4().hex[:8]
        headers = _headers(learner)
        missing = client.get(f"/learner/world-setup/{learner}", headers=headers)
        assert missing.status_code == 404
        world = {
            "stage": "高中",
            "grade": "高二",
            "school": "示例中学",
            "major": "",
            "subjects": ["数学", "物理", "英语"],
            "target_subjects": ["数学", "物理"],
            "goal": "把数学提高到 105 分",
            "learning_mode": "学校课程",
        }
        no_consent = client.post(f"/learner/world-setup/{learner}", json={"world_context": world, "consent": False}, headers=headers)
        assert no_consent.status_code == 422
        saved = client.post(f"/learner/world-setup/{learner}", json={"world_context": world, "consent": True}, headers=headers)
        assert saved.status_code == 200
        assert saved.json()["world_context"]["target_subjects"] == ["数学", "物理"]
        fetched_world = client.get(f"/learner/world-setup/{learner}", headers=headers)
        assert fetched_world.status_code == 200
        submitted = client.post(
            f"/preassessment/submit/{learner}",
            json={"responses": _responses(client), "consent": True, "world_context": world},
            headers=headers,
        )
        assert submitted.status_code == 200
        profile = client.get(f"/preassessment/profile/{learner}", headers=headers)
        assert profile.status_code == 200
        assert profile.json()["world_context"]["grade"] == "高二"
        assert profile.json()["world_context"]["subjects"] == ["数学", "物理", "英语"]


def test_irreversible_learner_data_deletion_removes_events():
    with TestClient(app) as client:
        learner = "delete-api-" + uuid.uuid4().hex[:8]
        headers = _headers(learner)
        world = {"stage": "大学", "grade": "大二", "major": "计算机科学", "subjects": ["编程与数据"], "target_subjects": ["编程与数据"], "goal": "完成课程项目"}
        assert client.post(f"/learner/world-setup/{learner}", json={"world_context": world, "consent": True}, headers=headers).status_code == 200
        assert client.post(f"/preassessment/submit/{learner}", json={"responses": _responses(client), "consent": True, "world_context": world}, headers=headers).status_code == 200
        assert list_events(learner)
        refused = client.post(f"/learner/data/{learner}/delete", json={"confirmation": "wrong", "acknowledge_irreversible": True}, headers=headers)
        assert refused.status_code == 422
        deleted = client.post(f"/learner/data/{learner}/delete", json={"confirmation": learner, "acknowledge_irreversible": True}, headers=headers)
        assert deleted.status_code == 200
        assert deleted.json()["deleted_events"] >= 2
        assert list_events(learner) == []
        assert client.get(f"/preassessment/profile/{learner}", headers=headers).status_code == 404


def test_role_page_redirects_to_users_current_data_page():
    with TestClient(app) as client:
        response = client.get("/ui/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/ui/single.html"


def test_local_shutdown_writes_marker_without_killing_test_process(tmp_path, monkeypatch):
    monkeypatch.setenv("TENDER_DISABLE_PROCESS_EXIT", "1")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    with TestClient(app) as client:
        learner = "shutdown-api-" + uuid.uuid4().hex[:8]
        response = client.post("/system/shutdown", headers=_headers(learner))
        assert response.status_code == 200
        marker = tmp_path / "Tender" / "runtime" / "shutdown.request"
        assert marker.exists()
        assert response.json()["status"] == "shutting_down"


if __name__ == "__main__":
    test_world_setup_precedes_profile_and_survives_preassessment()
    test_irreversible_learner_data_deletion_removes_events()
    test_role_page_redirects_to_users_current_data_page()
    print("ok lifecycle API tests")
