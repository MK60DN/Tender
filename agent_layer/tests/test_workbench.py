import sqlite3
from uuid import uuid4

from app.daoql import list_events
from app.workbench import DB, create_thread, orchestrate, decide_approval, for_viewer


def _cleanup(thread_id: str, student_id: str):
    with sqlite3.connect(DB) as c:
        approval_ids = [r[0] for r in c.execute("SELECT approval_id FROM agent_approvals WHERE thread_id=?", (thread_id,))]
        c.execute("DELETE FROM agent_handoffs WHERE thread_id=?", (thread_id,))
        c.execute("DELETE FROM agent_approvals WHERE thread_id=?", (thread_id,))
        c.execute("DELETE FROM agent_artifacts WHERE thread_id=?", (thread_id,))
        c.execute("DELETE FROM agent_runs WHERE thread_id=?", (thread_id,))
        c.execute("DELETE FROM agent_threads WHERE thread_id=?", (thread_id,))
        c.execute("DELETE FROM events WHERE session_id=?", (thread_id,))


def test_multi_agent_workbench():
    suffix = uuid4().hex[:8]
    sid = "WORKBENCH_TEST_" + suffix
    thread_id = None
    mentor_thread_id = None
    mentor_sid = "WORKBENCH_MENTOR_" + suffix
    try:
        thread = create_thread(
            title="多 Agent 协作测试-" + suffix,
            objective="完成语法填空、生成复习卡并等待老师批准家长周报",
            student_id=sid,
            class_id="理科班",
            created_by_role="teacher",
            context={"student_name": "测试学生", "mastery": 0.55},
            audience_role="parent",
            audience_config={"purpose": "同步本周学习证据", "tone": "清晰克制"},
        )
        thread_id = thread["thread_id"]
        assert thread["status"] == "draft"

        detail = orchestrate(
            thread_id,
            {"student_name": "测试学生", "mastery": 0.55, "jol_bias": 0.08, "hesitation": 0.2},
            [sid],
        )
        assert detail["status"] == "waiting_approval"
        assert len(detail["runs"]) == 6
        assert len(detail["artifacts"]) == 5
        assert len(detail["handoffs"]) >= 5
        pending = [a for a in detail["approvals"] if a["status"] == "pending"]
        assert len(pending) == 1

        completed = decide_approval(pending[0]["approval_id"], "approved", "测试审批", "test")
        assert completed["status"] == "completed"
        assert completed["approvals"][0]["status"] == "approved"
        external = next(a for a in completed["artifacts"] if a["artifact_type"] == "external_communication")
        assert external["status"] == "approved"
        assert external["content"]["recipient_role"] == "parent"

        event_types = [e["event_type"] for e in list_events(sid)]
        learner_view = for_viewer(completed, "learner")
        assert all(a["artifact_type"] != "external_communication" for a in learner_view["artifacts"])
        parent_view = for_viewer(completed, "parent")
        assert len(parent_view["artifacts"]) == 1 and parent_view["artifacts"][0]["artifact_type"] == "external_communication"
        sales_view = for_viewer(completed, "sales")
        assert sales_view["artifacts"] == [] and sales_view["runs"] == []

        assert "agent_thread_created" in event_types
        assert "agent_run_completed" in event_types
        assert "agent_approval_decided" in event_types

        mentor_thread = create_thread(
            title="导师同步测试-" + suffix,
            objective="向导师同步项目进展与卡点",
            student_id=mentor_sid,
            class_id="终身学习",
            created_by_role="teacher",
            context={"student_name": "测试学习者", "mastery": 0.7},
            audience_role="mentor",
            audience_config={"purpose": "同步项目卡点", "tone": "正式专业"},
        )
        mentor_thread_id = mentor_thread["thread_id"]
        mentor_detail = orchestrate(mentor_thread_id, {"student_name": "测试学习者", "mastery": 0.7}, [mentor_sid])
        mentor_pending = next(a for a in mentor_detail["approvals"] if a["status"] == "pending")
        mentor_done = decide_approval(mentor_pending["approval_id"], "approved", "测试审批", "test")
        mentor_artifact = next(a for a in mentor_done["artifacts"] if a["artifact_type"] == "external_communication")
        assert mentor_artifact["content"]["recipient_role"] == "mentor"
        assert len(for_viewer(mentor_done, "mentor")["artifacts"]) == 1
        assert for_viewer(mentor_done, "parent")["artifacts"] == []
    finally:
        if thread_id:
            _cleanup(thread_id, sid)
        if mentor_thread_id:
            _cleanup(mentor_thread_id, mentor_sid)
