from uuid import uuid4
from app.main import (
    workflow_board, create_workflow_requirement, WorkflowRequirementCreate,
    create_workflow_review, WorkflowReviewCreate,
    create_workflow_incident, WorkflowIncidentCreate,
    create_workflow_delay, WorkflowDelayCreate,
    create_workflow_acceptance, WorkflowAcceptanceCreate,
)


def test_workflow_ops():
    suffix = uuid4().hex[:8]
    req = create_workflow_requirement(WorkflowRequirementCreate(
        title="测试需求-" + suffix, owner="product", priority="P1", evidence="测试证据"))
    assert req["status"] == "stored"
    review = create_workflow_review(WorkflowReviewCreate(
        requirement_id=req["requirement_id"], review_type="tech", decision="approved", notes="测试技术评审"))
    assert review["status"] == "stored"
    incident = create_workflow_incident(WorkflowIncidentCreate(
        title="测试事故-" + suffix, severity="P1", impact="测试影响", action="已修复"))
    assert incident["status"] == "stored"
    delay = create_workflow_delay(WorkflowDelayCreate(
        title="测试延期-" + suffix, reason="依赖未确认", mitigation="重新排期"))
    assert delay["status"] == "stored"
    acceptance = create_workflow_acceptance(WorkflowAcceptanceCreate(
        release_name="test-release-" + suffix,
        checklist={"function": True, "data": True, "permission": True, "ai_safety": True, "rollback": True},
        conclusion="approved"))
    assert acceptance["status"] == "stored"
    board = workflow_board()
    assert board["counts"]["requirements"] >= 1
    assert any(x["requirement_id"] == req["requirement_id"] for x in board["requirements"])
    assert any(x["acceptance_id"] == acceptance["acceptance_id"] for x in board["acceptances"])