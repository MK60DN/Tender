from uuid import uuid4
from app.agent_runtime import invoke
from app.safety_queue import get_ticket, list_tickets, update_ticket


def test_safety_ticket_workflow():
    sid = "SAFETY_TEST_" + uuid4().hex[:8]
    state = {"student_id": sid, "n_events": 1, "knowledge": {"mastery": 0.5}, "metacognition": {"jol_bias": 0, "hesitation": 0}}
    result = invoke("fixed_safety_guardian", sid, "我想自杀，不想活了", state)
    ticket_id = result["action"]["ticket_id"]
    assert ticket_id
    ticket = get_ticket(ticket_id)
    assert ticket["student_id"] == sid
    assert ticket["risk_level"] == "emergency"
    assert ticket["status"] == "open"
    reviewing = update_ticket(ticket_id, "reviewing", "reviewer_1", assignee="reviewer_1")
    assert reviewing["status"] == "reviewing"
    escalated = update_ticket(ticket_id, "escalated", "reviewer_1", resolution="human escalation")
    assert escalated["status"] == "escalated"
    closed = update_ticket(ticket_id, "closed", "reviewer_1", resolution="handled")
    assert closed["status"] == "closed"
    assert any(t["ticket_id"] == ticket_id for t in list_tickets(status="closed", limit=200))
