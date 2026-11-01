"""Tender Agent Layer 完整 MVP API + 产品网站。"""
from __future__ import annotations
import hashlib, json, os, pathlib
from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import FastAPI, HTTPException, Query, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Any

from .daoql import (insert_event, list_events, insert_edge, causal_path, event_graph,
                    list_audit, count_events, write_audit, all_events, verify_audit_chain)
from .tender import compute_state
from .metameta_cartographer import (annotate_and_store, decompose_and_store, build_metameta_annotation_map, extract_text, region_catalog)
from .agent_runtime import list_agents, invoke, get_agent as get_runtime_agent, runtime_status, plan_workforce
from .reports import student_report, teacher_report, parent_report, org_report
from .rag import search, ingest_text, build_index
from .workbench import (AGENT_CATALOG, AUDIENCE_PROFILES, create_thread, list_threads,
                         get_thread as get_workbench_thread, orchestrate as orchestrate_workbench,
                         decide_approval, stop_thread, for_viewer, experimental_status)
from .roster import ROSTER, students_in_class
from .advisor_router import EXPERTS as ADVISOR_EXPERTS, route as route_advisors, share_signal
from .mentalization import build_mentalization
from .agent_marketplace import FIXED_AGENTS, create_expert_agent, get_agent, get_agent_for_viewer, list_marketplace, purchase_agent, list_entitlements as list_agent_entitlements, invoke_expert_agent, has_agent_access
from .agent_catalog import agent_catalog
from .identity import Principal, principal_from_headers, authorize_learner, seed_demo_consents, set_current_principal, reset_current_principal, get_current_principal, request_guardian_relation, verify_guardian_relation, list_guardian_requests, revoke_consent
from .auth import create_session, verify_session, revoke_session, revoke_actor_sessions, list_sessions
from .safety_queue import create_ticket, list_tickets, get_ticket, update_ticket
from .decision_loop import (
    create_loop as create_decision_loop,
    get_loop as get_decision_loop,
    list_loops as list_decision_loops,
    record_action as record_decision_action,
    record_result as record_decision_result,
)
from .benchmark import tender_theta_benchmark
from .cognitive_constructs import assess_construct, construct_catalog
from .ambient import (plan_ambient_card, record_ambient_feedback, ambient_status, reply_to_ambient,
                      list_ambient_personas, get_ambient_persona, select_ambient_persona,
                      get_ambient_ensemble, select_ambient_ensemble)
from .tenant_api import router as tenant_router
from .knowledge_api import router as knowledge_router
from .language_api import router as language_router
from .governance_phases import CURRENT_PHASE, PHASE_POLICIES, TRANSITION_REQUIREMENTS, governance_phase_policy
from .neuro_learning_evidence import catalog_summary, get_claim_boundary, get_integration_layers, list_datasets, list_research
from .preassessment import (
    big_five_change_state, big_five_pulse_items, latest_big_five_pulse,
    latest_preassessment, preassessment_items, submit_big_five_pulse, submit_preassessment,
)
from .tender_context import build_tender_context
from .world_tree import build_world_tree
from .golden_bias import build_golden_bias
from .group_chat import (
    create_group_session, list_group_sessions, join_group_session, get_group_session,
    ingest_group_event, list_group_events, create_peer_view_grant, list_peer_view_grants,
    revoke_peer_view_grant, build_peer_model, create_shared_branch, approve_shared_branch,
    list_shared_branches, build_group_model, create_group_draft, record_group_outcome,
    list_group_outcomes,
)

STATIC = pathlib.Path(__file__).resolve().parent / "static"
STATIC.mkdir(parents=True, exist_ok=True)
GUIDE = pathlib.Path(__file__).resolve().parents[2] / "site"

DEV_DOCS = os.getenv("TENDER_ENABLE_DEV_DOCS", "0") == "1"
app = FastAPI(
    title="Tender C-End Mentalization Learning App",
    version="7.0.0",
    docs_url="/docs" if DEV_DOCS else None,
    redoc_url=None,
    openapi_url="/openapi.json" if DEV_DOCS else None,
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(tenant_router)
app.include_router(knowledge_router)
app.include_router(language_router)
seed_demo_consents([r["student_id"] for r in ROSTER])

PUBLIC_PATHS = {"/health", "/preassessment/items", "/preassessment/pulse/items", "/governance/policy", "/research/neuro-learning/catalog", "/research/neuro-learning/datasets", "/research/neuro-learning/research", "/research/neuro-learning/claim", "/roles", "/agents", "/agents/fixed", "/agents/marketplace", "/agents/catalog", "/agent-runtime/status", "/benchmark/tender-theta", "/cognition/constructs", "/ambient/personas", "/openapi.json", "/docs", "/auth/demo-session", "/tenant/demo-session"}
SENSITIVE_PREFIXES = ("/preassessment/", "/auth/me", "/cognition/", "/metameta/", "/ambient/", "/auth/logout", "/auth/logout-all", "/auth/sessions", "/guardian/", "/safety/", "/agents/catalog", "/workforce/", "/learner/", "/decision-loops", "/daoql/", "/tender/", "/world-tree/", "/golden-bias/", "/group-sessions/", "/group-sessions", "/peer-view-grants", "/peer-view-grants/", "/peer-models/", "/shared-branches/", "/reports/", "/audit", "/agents/generate", "/agents/entitlements/", "/workforce/", "/head_teacher", "/sales", "/institution", "/teaching", "/dorm", "/workflow", "/workbench", "/advisors", "/rag/ingest", "/tenant/")


def _target_learner(path: str) -> str | None:
    parts = [p for p in path.split("/") if p]
    if not parts:
        return None
    if parts[0] == "learner" and len(parts) >= 3:
        return parts[-1]
    if parts[0] == "daoql" and len(parts) >= 3 and parts[1] in {"events", "graph"}:
        return parts[2]
    if parts[0] == "tender" and len(parts) >= 3:
        return parts[2]
    if parts[0] == "world-tree" and len(parts) >= 2:
        return parts[1]
    if parts[0] == "golden-bias" and len(parts) >= 2:
        return parts[1]
    if parts[0] == "preassessment" and len(parts) >= 3:
        if parts[-1] == "items":
            return None
        return parts[-1]
    if parts[0] == "reports" and len(parts) >= 3 and parts[1] in {"parent", "student"}:
        return parts[-1]
    if parts[0] == "agents" and len(parts) >= 3 and parts[1] == "entitlements":
        return parts[-1]
    return None


@app.middleware("http")
async def identity_guard(request: Request, call_next):
    if request.method == "OPTIONS" or request.url.path.startswith("/ui/"):
        return await call_next(request)
    if request.url.path == "/roles" and request.query_params.get("surface", "consumer") != "consumer":
        authorization = request.headers.get("Authorization", "")
        payload = verify_session(authorization[7:].strip()) if authorization.startswith("Bearer ") else None
        if not payload or str(payload.get("role")) not in {"admin", "auditor"}:
            return JSONResponse(status_code=403, content={"detail": "internal_role_catalog_requires_admin"})
        return await call_next(request)
    if request.url.path in PUBLIC_PATHS:
        return await call_next(request)
    if not any(request.url.path.startswith(prefix) for prefix in SENSITIVE_PREFIXES):
        return await call_next(request)
    authorization = request.headers.get("Authorization", "")
    principal = None
    if authorization.startswith("Bearer "):
        payload = verify_session(authorization[7:].strip())
        if payload:
            principal = Principal(
                actor_id=str(payload.get("sub", "")),
                role=str(payload.get("role", "learner")),
                learner_id=payload.get("learner_id"),
                tenant_id=payload.get("tenant_id"),
            )
    if principal is None and os.getenv("TENDER_ALLOW_HEADER_IDENTITY", "0") == "1":
        principal = principal_from_headers(
            request.headers.get("X-Tender-Actor"),
            request.headers.get("X-Tender-Role"),
            request.headers.get("X-Tender-Learner"),
            request.headers.get("X-Tender-Tenant"),
        )
    if principal is None:
        return JSONResponse(status_code=401, content={"detail": "identity_required", "hint": "请先建立学习者、家庭或管理员身份。"})
    request.state.principal = principal
    request.state.session_payload = payload if authorization.startswith("Bearer ") else None
    context_token = set_current_principal(principal)
    try:
        if request.url.path.startswith("/audit") and principal.role not in {"admin", "auditor"}:
            return JSONResponse(status_code=403, content={"detail": "audit_access_denied"})
        learner_id = _target_learner(request.url.path)
        if learner_id:
            allowed, reason = authorize_learner(principal, learner_id)
            if not allowed:
                return JSONResponse(status_code=403, content={"detail": "object_access_denied", "reason": reason})
        return await call_next(request)
    finally:
        reset_current_principal(context_token)


class PreassessmentSubmission(BaseModel):
    responses: dict[str, int]
    consent: bool = False


class BigFivePulseSubmission(BaseModel):
    responses: dict[str, int]
    context: dict[str, Any] = Field(default_factory=dict)
    consent: bool = False


class SafetyTicketUpdate(BaseModel):
    status: str
    assignee: str | None = None
    resolution: str | None = None


class GuardianRequestCreate(BaseModel):
    learner_id: str
    guardian_id: str
    evidence: str = ""


class GuardianVerifyRequest(BaseModel):
    scopes: list[str] = Field(default_factory=lambda: ["learning_support", "family_summary"])


class DemoSessionRequest(BaseModel):
    actor_id: str
    role: str = "learner"
    learner_id: str | None = None


class GroupSessionCreateRequest(BaseModel):
    platform: str = "group_chat"
    purpose: str
    tenant_id: str | None = None


class GroupJoinRequest(BaseModel):
    role: str = "member"
    consent_scopes: list[str] = Field(default_factory=lambda: ["group_public.read"])


class GroupEventRequest(BaseModel):
    event_type: str = "message"
    content: str = ""
    visibility: str = "group_public"
    consent_ref: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class PeerViewGrantRequest(BaseModel):
    viewer_id: str
    group_id: str
    purpose: str = "collaboration"
    scopes: list[str]
    evidence_refs: list[str] = Field(default_factory=list)
    valid_hours: int = Field(default=24, ge=1, le=720)


class SharedBranchCreateRequest(BaseModel):
    category: str
    content: dict[str, Any]
    participant_ids: list[str]
    evidence_refs: list[str] = Field(default_factory=list)
    visibility: str | None = None


class GroupDraftRequest(BaseModel):
    intent: str = "clarify"


class GroupOutcomeRequest(BaseModel):
    decision: str
    commitments: list[dict[str, Any]] = Field(default_factory=list)
    unresolved: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)


@app.post("/auth/demo-session")
def demo_session(request: DemoSessionRequest):
    if os.getenv("TENDER_DEMO_MODE", "1") != "1":
        raise HTTPException(status_code=404, detail="demo_session_disabled")
    if request.role not in {"learner", "parent", "admin", "auditor", "advisor"}:
        raise HTTPException(status_code=400, detail="invalid_role")
    return create_session(request.actor_id, request.role, request.learner_id)


@app.post("/guardian/requests")
def guardian_request(request: GuardianRequestCreate):
    principal = get_current_principal()
    if principal is None:
        raise HTTPException(status_code=401, detail="identity_required")
    if principal.role not in {"admin", "auditor"} and principal.actor_id != request.guardian_id:
        raise HTTPException(status_code=403, detail="guardian_identity_mismatch")
    try:
        result = request_guardian_relation(request.learner_id, request.guardian_id, request.evidence)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    write_audit("guardian:" + request.guardian_id, "guardian.request", request.learner_id, {"guardian_id": request.guardian_id})
    return result


@app.get("/guardian/requests")
def guardian_requests():
    principal = get_current_principal()
    if principal is None or principal.role not in {"admin", "auditor"}:
        raise HTTPException(status_code=403, detail="admin_required")
    return {"requests": list_guardian_requests()}


@app.post("/guardian/requests/{learner_id}/{guardian_id}/verify")
def guardian_verify(learner_id: str, guardian_id: str, request: GuardianVerifyRequest):
    principal = get_current_principal()
    if principal is None or principal.role not in {"admin", "auditor"}:
        raise HTTPException(status_code=403, detail="admin_required")
    try:
        result = verify_guardian_relation(learner_id, guardian_id, principal.actor_id, request.scopes)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    write_audit("admin:" + principal.actor_id, "guardian.verify", learner_id, {"guardian_id": guardian_id, "scopes": request.scopes})
    return result


@app.post("/guardian/requests/{learner_id}/{guardian_id}/revoke")
def guardian_revoke(learner_id: str, guardian_id: str):
    principal = get_current_principal()
    if principal is None:
        raise HTTPException(status_code=401, detail="identity_required")
    if principal.role not in {"admin", "auditor"} and principal.actor_id != guardian_id:
        raise HTTPException(status_code=403, detail="guardian_identity_mismatch")
    try:
        result = revoke_consent(learner_id, guardian_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    write_audit("guardian:" + guardian_id, "guardian.revoke", learner_id, {"guardian_id": guardian_id})
    return result


@app.post("/auth/logout")
def auth_logout(request: Request):
    principal = get_current_principal()
    payload = getattr(request.state, "session_payload", None) or {}
    if principal is None or not payload.get("jti"):
        raise HTTPException(status_code=401, detail="identity_required")
    revoked = revoke_session(payload["jti"])
    write_audit(principal.actor_id, "auth.logout", payload["jti"])
    return {"status": "revoked" if revoked else "already_revoked"}


@app.post("/auth/logout-all")
def auth_logout_all():
    principal = get_current_principal()
    if principal is None:
        raise HTTPException(status_code=401, detail="identity_required")
    count = revoke_actor_sessions(principal.actor_id)
    write_audit(principal.actor_id, "auth.logout_all", principal.actor_id, {"revoked": count})
    return {"status": "revoked", "count": count}


@app.get("/auth/sessions")
def auth_sessions(request: Request, include_revoked: bool = False):
    principal = get_current_principal()
    if principal is None:
        raise HTTPException(status_code=401, detail="identity_required")
    actor_id = request.query_params.get("actor_id")
    if actor_id and actor_id != principal.actor_id and principal.role not in {"admin", "auditor"}:
        raise HTTPException(status_code=403, detail="cross_actor_denied")
    return {"sessions": list_sessions(actor_id or principal.actor_id, include_revoked=include_revoked)}


@app.get("/auth/me")
def auth_me(request: Request):
    principal = getattr(request.state, "principal", None)
    if principal is None:
        raise HTTPException(status_code=401, detail="identity_required")
    return {"actor_id": principal.actor_id, "role": principal.role, "learner_id": principal.learner_id, "tenant_id": principal.tenant_id}


class DAOQLEvent(BaseModel):
    event_type: str
    student_id: str
    session_id: str | None = None
    timestamp: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    source: str = "unknown"
    provenance: dict[str, Any] = Field(default_factory=dict)




class MetametaAnnotateRequest(BaseModel):
    message: str
    event_type: str = "user_input"
    source_event_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)

class CausalEdge(BaseModel):
    source_event_id: str
    target_event_id: str
    relation: str = "causes"
    confidence: float = 0.5
    evidence: dict[str, Any] = Field(default_factory=dict)


class AgentInvoke(BaseModel):
    student_id: str
    message: str = ""
    intent: str = "general"
    actor_id: str | None = None


class RAGQuery(BaseModel):
    query: str
    top_k: int = 5


class RAGIngest(BaseModel):
    name: str
    text: str


class WorkbenchThreadCreate(BaseModel):
    title: str
    objective: str
    student_id: str
    class_id: str = "理科班"
    task_type: str = "grammar_cloze"
    created_by_role: str = "teacher"
    audience_role: str = "parent"
    audience_config: dict[str, Any] = Field(default_factory=dict)
    context: dict[str, Any] = Field(default_factory=dict)


class WorkbenchOrchestrate(BaseModel):
    focus_students: list[str] = Field(default_factory=list)
    context_overrides: dict[str, Any] = Field(default_factory=dict)


class WorkbenchApprovalDecision(BaseModel):
    decision: str
    reason: str = ""
    actor: str = "teacher"


class WorkbenchStop(BaseModel):
    reason: str = ""
    actor: str = "teacher"

class ReflectionCreate(BaseModel):
    prompt: str = ""
    answer: str
    mood: str | None = None
    consent_scopes: list[str] = Field(default_factory=lambda: ["self_reflection", "learning_support"])


class AgentGenerateRequest(BaseModel):
    owner_id: str
    need: str
    name: str = ""
    description: str = ""
    category: str = "auto"
    price_cents: int = 0
    visibility: str = "private"


class WorkforceRequest(BaseModel):
    task: str
    agent_ids: list[str] = Field(default_factory=lambda: [
        "fixed_mentalization_companion",
        "fixed_reflection_coach",
        "fixed_safety_guardian",
    ], min_length=1, max_length=5)
    execute: bool = False


class AgentPurchaseRequest(BaseModel):
    buyer_id: str


class DecisionLoopCreateRequest(BaseModel):
    learner_id: str
    goal: str
    options: list[dict[str, Any]] = Field(default_factory=list)
    selected_option_id: str
    choice_reason: str
    state: dict[str, Any] = Field(default_factory=dict)


class DecisionLoopActionRequest(BaseModel):
    action: str
    expected_outcome: str
    state: dict[str, Any] = Field(default_factory=dict)


class DecisionLoopResultRequest(BaseModel):
    actual_result: str
    responsibility_owner: str
    reflection: str = ""
    state: dict[str, Any] = Field(default_factory=dict)


class CognitiveAssessmentRequest(BaseModel):
    construct_id: str
    evidence: dict[str, Any] = Field(default_factory=dict)
    threshold: float | None = None


class AmbientPlanRequest(BaseModel):
    signals: dict[str, Any] = Field(default_factory=dict)
    force: bool = False


class AmbientFeedbackRequest(BaseModel):
    card_id: str
    feedback: str


class AmbientReplyRequest(BaseModel):
    card_id: str
    message: str
    scenario: str = "score_improvement"
    persona_id: str | None = None
    ensemble_ids: list[str] | None = None
    agent_id: str | None = None
    agent_ids: list[str] | None = None


class AmbientPersonaRequest(BaseModel):
    persona_id: str


class AmbientEnsembleRequest(BaseModel):
    persona_ids: list[str]


class AdvisorRouteRequest(BaseModel):
    message: str
    student_id: str
    role: str = "learner"
    consent_scopes: list[str] = Field(default_factory=list)


class AdvisorShareRequest(BaseModel):
    student_id: str
    from_advisor: str
    to_advisor: str
    purpose: str
    summary: str
    evidence_refs: list[str] = Field(default_factory=list)
    consent_scopes: list[str] = Field(default_factory=list)


ROLE_APPS = [
    {"id": "learner", "name": "学习者端", "audience": "学习者", "default_page": "learner",
     "scope": "只看自己的学习记录；可导出、可撤回授权；可在协作任务中查看交付给自己的学习产物",
     "nav": [{"page": "learner", "icon": "⌂", "label": "此刻与我"},
             {"page": "timeline", "icon": "↗", "label": "心智时间线"},
             {"page": "market", "icon": "◇", "label": "Agent 市场"},
             {"page": "lifelong", "icon": "∞", "label": "学习路径"},
             {"page": "workbench", "icon": "⌘", "label": "协作任务"},
             {"page": "agent", "icon": "◈", "label": "心智化伙伴"},
             {"page": "student", "icon": "▤", "label": "学习证据"}]},
    {"id": "parent", "name": "家庭端", "audience": "学习者 / 监护人", "default_page": "parent",
     "scope": "只看被授权子女的成长证据；仅显示已经审批、发给家长的对外沟通；不展示原始对话",
     "nav": [{"page": "parent", "icon": "⌂", "label": "家庭概览"},
             {"page": "workbench", "icon": "⌘", "label": "成长协作"}]},
    {"id": "teacher", "name": "教师端", "audience": "独立教师 / 机构任课教师",
     "scope": "一个教师身份，按教学模式切换独立教学或机构协作；可向授权学生发布任务，并通过多 Agent 完成批改、复习和对外沟通草稿",
     "modes": [
         {"id": "independent", "label": "独立教师", "scope": "自有学生、个人品牌、自主定价与个人交付"},
         {"id": "institution", "label": "机构任课教师", "scope": "所授班级、课时履约、班主任协同与机构授权范围"}
     ],
     "default_page": "subjectteacher",
     "nav": [{"page": "subjectteacher", "icon": "⌂", "label": "教师工作台"},
             {"page": "workbench", "icon": "⌘", "label": "多 Agent 协作"},
             {"page": "agent", "icon": "◈", "label": "教学 AI 助手"},
             {"page": "student", "icon": "▤", "label": "学生证据"}]},
    {"id": "health_advisor", "name": "健康顾问端", "audience": "认证健康顾问", "default_page": "advisor",
     "scope": "看睡眠、活动、身体状态与健康风险筛查；不做疾病诊断，异常需转介合格专业人员",
     "nav": [{"page": "advisor", "icon": "♡", "label": "健康工作台"},
             {"page": "workbench", "icon": "⌘", "label": "健康协作"},
             {"page": "student", "icon": "▤", "label": "学生证据"}]},
    {"id": "nutrition_advisor", "name": "营养顾问端", "audience": "认证营养顾问", "default_page": "advisor",
     "scope": "看饮食结构、能量、纤维、钠、钾和添加糖；输出营养模式建议，不做医学营养治疗",
     "nav": [{"page": "advisor", "icon": "◒", "label": "营养工作台"},
             {"page": "workbench", "icon": "⌘", "label": "营养协作"},
             {"page": "student", "icon": "▤", "label": "学生证据"}]},
    {"id": "neurocognitive_advisor", "name": "神经认知顾问端", "audience": "认知教练 / 神经心理专业人员", "default_page": "advisor",
     "scope": "看注意、工作记忆、执行功能与任务切换特征；只做学习支持画像，不做临床诊断",
     "nav": [{"page": "advisor", "icon": "◉", "label": "认知工作台"},
             {"page": "workbench", "icon": "⌘", "label": "认知协作"},
             {"page": "student", "icon": "▤", "label": "学生证据"}]},
    {"id": "psychology_advisor", "name": "心理学顾问端", "audience": "授权支持人员", "default_page": "advisor",
     "scope": "看压力、情绪、注意与求助信号；只做支持分级和转介建议，不输出抑郁/焦虑等临床诊断",
     "nav": [{"page": "advisor", "icon": "◌", "label": "心理支持台"},
             {"page": "workbench", "icon": "⌘", "label": "支持协作"},
             {"page": "student", "icon": "▤", "label": "学生证据"}]},
    {"id": "learning_science_advisor", "name": "学习科学顾问端", "audience": "学习科学 / 认知情绪建模", "default_page": "advisor",
     "scope": "整合 Tender 状态、RoleMind、健康/营养/认知/心理信号；解释 Bloch 球与量子认知模型，但不宣称真实量子效应",
     "nav": [{"page": "advisor", "icon": "◇", "label": "学习解释台"},
             {"page": "workbench", "icon": "⌘", "label": "整合协作"},
             {"page": "student", "icon": "▤", "label": "状态证据"}]},
    {"id": "career_advisor", "name": "生涯与职业顾问端", "audience": "生涯规划 / 职业发展", "default_page": "advisor",
     "scope": "结合学习护照、能力证据、兴趣和职业信息做路径探索；不承诺就业，不替用户决定人生",
     "nav": [{"page": "advisor", "icon": "↗", "label": "生涯工作台"},
             {"page": "workbench", "icon": "⌘", "label": "生涯协作"},
             {"page": "student", "icon": "▤", "label": "能力证据"}]},
    {"id": "safety_advisor", "name": "安全与保护顾问端", "audience": "安全支持 / 未成年人保护", "default_page": "advisor",
     "scope": "识别霸凌、诈骗、不当关系、自伤和突发安全风险；只做风险分级、成人升级和紧急转介，不调查案件",
     "nav": [{"page": "advisor", "icon": "!", "label": "安全保护台"},
             {"page": "workbench", "icon": "⌘", "label": "保护协作"},
             {"page": "student", "icon": "▤", "label": "风险证据"}]},
    {"id": "head_teacher", "name": "班主任端", "audience": "班主任", "default_page": "headteacher",
     "scope": "看班级风险、家长沟通草稿和作业分流；不替代班主任判断",
     "nav": [{"page": "headteacher", "icon": "⌂", "label": "班主任工作台"},
             {"page": "workbench", "icon": "⌘", "label": "协作工作台"},
             {"page": "teacher", "icon": "◎", "label": "班级报告"},
             {"page": "student", "icon": "▤", "label": "学生证据"},
             {"page": "agent", "icon": "◈", "label": "班主任 AI"}]},
    {"id": "institution", "name": "机构管理端", "audience": "执行校长/管理员", "default_page": "institution",
     "scope": "看聚合运营数据、权限、合规和连接器；不默认获得个体原始对话",
     "nav": [{"page": "institution", "icon": "⌂", "label": "机构总览"},
             {"page": "workbench", "icon": "⌘", "label": "协作审计"},
             {"page": "dashboard", "icon": "▦", "label": "系统指标"},
             {"page": "reports", "icon": "▤", "label": "机构报告"},
             {"page": "headteacher", "icon": "▣", "label": "班主任管理"},
             {"page": "sales", "icon": "◎", "label": "销售管理"},
             {"page": "teacher", "icon": "◉", "label": "教师管理"},
             {"page": "workflow", "icon": "⚙", "label": "产品工作流"},
             {"page": "daoql", "icon": "⌘", "label": "数据与审计"}]},
    {"id": "sales", "name": "销售端", "audience": "课程顾问", "default_page": "sales",
     "scope": "只使用脱敏后的教学证据和跟进建议；不直接查看原始对话",
     "nav": [{"page": "sales", "icon": "⌂", "label": "销售作战台"},
             {"page": "reports", "icon": "▤", "label": "机构报告"}]},
]


CONSUMER_ROLE_IDS = {"learner", "parent"}
ADVISOR_RUNTIME_ROLE_IDS = {
    "health_advisor", "nutrition_advisor", "neurocognitive_advisor", "psychology_advisor",
    "learning_science_advisor", "career_advisor", "safety_advisor",
}


@app.get("/roles")
def roles(surface: str = "consumer"):
    """Role catalog by product surface.

    Consumer C-end UI exposes learner and parent only. Advisors are runtime
    capabilities invoked through MoA, not role accounts the learner must manage.
    Legacy organization roles remain available only through surface=all for
    compatibility and historical tests.
    """
    catalog = []
    for role in ROLE_APPS:
        if role["id"] in CONSUMER_ROLE_IDS:
            role_surface = "consumer"
        elif role["id"] in ADVISOR_RUNTIME_ROLE_IDS:
            role_surface = "advisor_runtime"
        else:
            role_surface = "legacy"
        if surface == "all" or surface == role_surface:
            catalog.append({**role, "surface": role_surface})
    return {"roles": catalog, "current": "learner", "surface": surface,
            "product": "C端心智化终身学习App",
            "rbac_status": "preview_only",
            "note": "C端只展示学习者与家庭入口；专业顾问按 MoA 路由出现，旧组织角色不进入默认产品路径。"}
class WorkflowRequirementCreate(BaseModel):
    title: str
    owner: str = "product"
    priority: str = "P1"
    stage: str = "discovery"
    evidence: str = ""
    due_at: str | None = None


class WorkflowReviewCreate(BaseModel):
    requirement_id: str
    review_type: str = "business"
    decision: str = "approved"
    owner: str = "reviewer"
    notes: str = ""


class WorkflowIncidentCreate(BaseModel):
    title: str
    severity: str = "P1"
    impact: str = ""
    owner: str = "product"
    action: str = ""


class WorkflowDelayCreate(BaseModel):
    title: str
    reason: str
    impact: str = ""
    mitigation: str = ""
    owner: str = "product"
    new_due_at: str | None = None


class WorkflowAcceptanceCreate(BaseModel):
    release_name: str
    owner: str = "product"
    checklist: dict[str, bool] = Field(default_factory=dict)
    conclusion: str = "pending"

class FinanceEstimateInput(BaseModel):
    group_students: int = Field(default=0, ge=0)
    group_sessions: float = Field(default=0, ge=0)
    one_on_one_tier: int = 500
    one_on_one_sessions: float = Field(default=0, ge=0)
    assistant_class_count: int = Field(default=1, ge=0)
    assistant_sessions_60: float = Field(default=0, ge=0)
    assistant_sessions_80: float = Field(default=0, ge=0)
    assistant_sessions_100: float = Field(default=0, ge=0)
    assistant_sessions_120: float = Field(default=0, ge=0)
    assistant_one_on_one_sessions: float = Field(default=0, ge=0)
    referral_payment_base: float = Field(default=0, ge=0)
    new_student_count: int = Field(default=0, ge=0)
    new_student_bonus_per_person: float = Field(default=1000, ge=1000, le=5000)
class TeacherScheduleCreate(BaseModel):
    teacher_id: str
    teacher_name: str = ""
    class_id: str
    weekday: int = Field(ge=1, le=7)
    start_time: str
    end_time: str
    course: str
    room: str = ""
class HeadTeacherNote(BaseModel):
    student_id: str
    category: str = "general"
    text: str = Field(min_length=1, max_length=1000)
    visibility: str = "teacher_private"
class StudentStatusUpdate(BaseModel):
    student_id: str
    status: str
    effective_at: str | None = None
    expected_return: str | None = None
    note: str = ""


class TeachingTaskCreate(BaseModel):
    class_id: str
    teacher_id: str = "teacher_demo"
    subject: str
    title: str
    instructions: str = ""
    due_at: str | None = None
    student_ids: list[str] = Field(default_factory=list)


class TeachingTaskComplete(BaseModel):
    completed_by: str = "head_teacher"
    note: str = ""


class DormRollCallCreate(BaseModel):
    class_id: str
    expected_ids: list[str] = Field(default_factory=list)
    actual_ids: list[str] = Field(default_factory=list)
    exceptions: list[dict[str, Any]] = Field(default_factory=list)
    note: str = ""

@app.get("/preassessment/items")
def get_preassessment_items():
    return preassessment_items()


@app.post("/preassessment/submit/{learner_id}")
def post_preassessment(learner_id: str, submission: PreassessmentSubmission):
    try:
        return submit_preassessment(learner_id, submission.responses, consent=submission.consent)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/preassessment/profile/{learner_id}")
def get_preassessment_profile(learner_id: str):
    profile = latest_preassessment(learner_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="preassessment_not_found")
    return profile


@app.get("/preassessment/pulse/items")
def get_big_five_pulse_items():
    return big_five_pulse_items()


@app.post("/preassessment/pulse/{learner_id}")
def post_big_five_pulse(learner_id: str, submission: BigFivePulseSubmission):
    try:
        return submit_big_five_pulse(
            learner_id, submission.responses, consent=submission.consent, context=submission.context
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/preassessment/pulse/{learner_id}")
def get_big_five_pulse(learner_id: str):
    latest = latest_big_five_pulse(learner_id)
    if latest is None:
        raise HTTPException(status_code=404, detail="big_five_pulse_not_found")
    return {"latest": latest, "change": big_five_change_state(learner_id)}
@app.get("/research/neuro-learning/catalog")
def neuro_learning_catalog():
    return {
        "summary": catalog_summary(),
        "datasets": list_datasets(),
        "research": list_research(),
        "integration_layers": get_integration_layers(),
        "notice": "神经数据仅用于离线研究校准和构念验证；当前不进行运行时脑解码。",
    }


@app.get("/research/neuro-learning/datasets")
def neuro_learning_datasets(
    stage: str | None = Query(default=None),
    modality: str | None = Query(default=None),
    access: str | None = Query(default=None),
    record_type: str | None = Query(default=None),
):
    return {
        "filters": {
            "stage": stage,
            "modality": modality,
            "access": access,
            "record_type": record_type,
        },
        "datasets": list_datasets(
            stage=stage,
            modality=modality,
            access=access,
            record_type=record_type,
        ),
    }


@app.get("/research/neuro-learning/research")
def neuro_learning_research(construct: str | None = Query(default=None)):
    return {"construct": construct, "research": list_research(construct)}


@app.get("/research/neuro-learning/claim/{claim_type}")
def neuro_learning_claim_boundary(claim_type: str):
    try:
        return get_claim_boundary(claim_type)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/governance/policy")
def governance_policy():
    return {
        "current_phase": CURRENT_PHASE.value,
        "current_policy": governance_phase_policy(),
        "phases": [governance_phase_policy(phase) for phase in PHASE_POLICIES],
        "transition_requirements": {
            phase.value: requirements
            for phase, requirements in TRANSITION_REQUIREMENTS.items()
        },
        "notice": "当前处于链下专家议会阶段；BFT 与链上写入默认关闭，联盟阶段必须逐项满足准入条件。",
    }


@app.get("/health")
def health():
    return {"status": "ok", "events": count_events()}


@app.get("/overview")
def overview():
    classes = {}
    for r in ROSTER:
        classes.setdefault(r["class"], 0)
        classes[r["class"]] += 1
    return {"events": count_events(), "agents": len(list_agents()),
            "students": len(ROSTER), "classes": classes,
            "rag": build_index()}


@app.get("/students")
def students():
    return ROSTER


@app.get("/agents")
def agents():
    fixed_ids = [item["agent_id"] for item in FIXED_AGENTS]
    return [config for config in (get_runtime_agent(agent_id) for agent_id in fixed_ids) if config]


@app.get("/agents/catalog")
def agents_catalog():
    principal = get_current_principal()
    if principal is None or principal.role not in {"admin", "auditor"}:
        raise HTTPException(status_code=403, detail="admin_required")
    return agent_catalog()


@app.get("/agent-runtime/status")
def agent_runtime_status():
    return runtime_status()


@app.post("/workforce/plan")
def plan_workforce_endpoint(req: WorkforceRequest):
    if len(set(req.agent_ids)) != len(req.agent_ids):
        raise HTTPException(status_code=400, detail="duplicate agents are not allowed")
    fixed_ids = {item["agent_id"] for item in FIXED_AGENTS}
    unknown = [agent_id for agent_id in req.agent_ids if agent_id not in fixed_ids]
    if unknown:
        raise HTTPException(status_code=404, detail={"error": "runtime_agent_not_found", "agent_ids": unknown})
    configs = []
    for agent_id in req.agent_ids:
        config = get_runtime_agent(agent_id)
        if not config:
            raise HTTPException(status_code=404, detail={"error": "runtime_agent_not_found", "agent_ids": [agent_id]})
        configs.append(config)
    try:
        result = plan_workforce(req.task, configs, execute=req.execute)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError:
        write_audit(
            "agent_runtime",
            "workforce.execute" if req.execute else "workforce.plan",
            "workforce",
            {"agent_ids": req.agent_ids, "task_chars": len(req.task or ""), "outcome": "unavailable"},
        )
        raise HTTPException(status_code=503, detail="agent runtime execution unavailable") from None
    write_audit(
        "agent_runtime",
        "workforce.execute" if req.execute else "workforce.plan",
        "workforce",
        {
            "agent_ids": req.agent_ids,
            "task_chars": len(req.task or ""),
            "mode": result.get("mode"),
            "outcome": "completed" if result.get("mode") in {"plan_only", "executed"} else "blocked",
        },
    )
    return result


@app.get("/agents/fixed")
def fixed_agents():
    catalog = agent_catalog()
    return {
        "agents": catalog["fixed_consumer_agents"],
        "integrity": catalog["integrity"],
        "note": "固定辅助 Agent 始终可用，优先保证连续记录与安全边界。",
    }


@app.get("/agents/marketplace")
def marketplace(query: str = "", category: str = ""):
    return list_marketplace(query=query, category=category)


@app.post("/agents/generate")
def generate_expert_agent(request: AgentGenerateRequest):
    principal = get_current_principal()
    if principal and principal.role not in {"admin", "auditor"} and request.owner_id != principal.actor_id:
        raise HTTPException(status_code=403, detail="owner_identity_mismatch")
    try:
        agent = create_expert_agent(
            owner_id=request.owner_id,
            need=request.need,
            name=request.name,
            description=request.description,
            category=request.category,
            price_cents=request.price_cents,
            visibility=request.visibility,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    write_audit("agent_factory:" + request.owner_id, "agent.generate", agent["agent_id"],
                {"category": agent["category"], "visibility": agent["visibility"]})
    return {"status": agent["status"], "agent": agent,
            "note": "生成的是受控 AgentSpec；默认只访问授权摘要，高风险类别需要认证与人工审阅。"}


@app.get("/agents/{agent_id}/spec")
def expert_agent_spec(agent_id: str, actor_id: str | None = None):
    try:
        return get_agent_for_viewer(agent_id, actor_id)
    except KeyError:
        raise HTTPException(status_code=404, detail={"error": "agent_not_found"}) from None
    except PermissionError:
        raise HTTPException(status_code=403, detail={"error": "agent_not_available"}) from None


@app.post("/agents/{agent_id}/purchase")
def buy_expert_agent(agent_id: str, request: AgentPurchaseRequest):
    principal = get_current_principal()
    if principal and principal.role not in {"admin", "auditor"} and request.buyer_id != principal.actor_id:
        raise HTTPException(status_code=403, detail="buyer_identity_mismatch")
    try:
        out = purchase_agent(agent_id, request.buyer_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    write_audit("agent_marketplace:" + request.buyer_id, "agent.purchase", agent_id,
                {"price": out.get("price", 0), "already_owned": out.get("already_owned", False)})
    return out


@app.get("/agents/entitlements/{buyer_id}")
def agent_entitlements(buyer_id: str):
    return list_agent_entitlements(buyer_id)


def _group_actor() -> str:
    principal = get_current_principal()
    if principal is None:
        raise HTTPException(status_code=401, detail="identity_required")
    return principal.actor_id


def _group_call(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc).strip("'")) from None
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from None
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None


@app.get("/group-sessions")
def group_sessions():
    return {"sessions": list_group_sessions(_group_actor())}


@app.post("/group-sessions")
def create_group(payload: GroupSessionCreateRequest):
    actor_id = _group_actor()
    tenant_id = payload.tenant_id or (get_current_principal().tenant_id if get_current_principal() else None)
    return _group_call(create_group_session, payload.platform, payload.purpose, actor_id, tenant_id)


@app.post("/group-sessions/{group_id}/join")
def join_group(group_id: str, payload: GroupJoinRequest):
    return _group_call(join_group_session, group_id, _group_actor(), payload.role, payload.consent_scopes)


@app.get("/group-sessions/{group_id}")
def group_session_detail(group_id: str):
    return _group_call(get_group_session, group_id, _group_actor())


@app.post("/group-sessions/{group_id}/events")
def group_event(group_id: str, payload: GroupEventRequest):
    return _group_call(
        ingest_group_event, group_id, _group_actor(), payload.event_type, payload.content,
        payload.visibility, payload.consent_ref, payload.payload,
    )


@app.get("/group-sessions/{group_id}/events")
def group_events(group_id: str, limit: int = Query(100, ge=1, le=500)):
    return {"events": _group_call(list_group_events, group_id, _group_actor(), limit)}


@app.get("/group-sessions/{group_id}/model")
def group_model(group_id: str):
    return _group_call(build_group_model, group_id, _group_actor())


@app.post("/group-sessions/{group_id}/drafts")
def group_draft(group_id: str, payload: GroupDraftRequest):
    return _group_call(create_group_draft, group_id, _group_actor(), payload.intent)


@app.post("/group-sessions/{group_id}/outcomes")
def group_outcome(group_id: str, payload: GroupOutcomeRequest):
    return _group_call(
        record_group_outcome, group_id, _group_actor(), payload.decision,
        payload.commitments, payload.unresolved, payload.evidence_refs,
    )


@app.get("/group-sessions/{group_id}/outcomes")
def group_outcomes(group_id: str):
    return {"outcomes": _group_call(list_group_outcomes, group_id, _group_actor())}


@app.post("/peer-view-grants")
def peer_view_grant(payload: PeerViewGrantRequest):
    return _group_call(
        create_peer_view_grant, _group_actor(), payload.viewer_id, payload.group_id,
        payload.purpose, payload.scopes, payload.evidence_refs, payload.valid_hours,
    )


@app.get("/peer-view-grants")
def peer_view_grants(group_id: str | None = None):
    return {"grants": list_peer_view_grants(_group_actor(), group_id)}


@app.delete("/peer-view-grants/{grant_id}")
def peer_view_revoke(grant_id: str):
    return _group_call(revoke_peer_view_grant, grant_id, _group_actor())


@app.get("/peer-models/{observer_id}/{subject_id}")
def peer_model(observer_id: str, subject_id: str, group_id: str):
    principal = get_current_principal()
    if principal is None:
        raise HTTPException(status_code=401, detail="identity_required")
    if observer_id != principal.actor_id and principal.role not in {"admin", "auditor"}:
        raise HTTPException(status_code=403, detail="peer_model_observer_identity_mismatch")
    return _group_call(build_peer_model, observer_id, subject_id, group_id)


@app.post("/group-sessions/{group_id}/shared-branches")
def shared_branch_create(group_id: str, payload: SharedBranchCreateRequest):
    return _group_call(
        create_shared_branch, group_id, _group_actor(), payload.category,
        payload.content, payload.participant_ids, payload.evidence_refs, payload.visibility,
    )


@app.get("/group-sessions/{group_id}/shared-branches")
def shared_branches(group_id: str, status: str | None = None):
    return {"branches": _group_call(list_shared_branches, group_id, _group_actor(), status)}


@app.post("/shared-branches/{branch_id}/approve")
def shared_branch_approve(branch_id: str):
    return _group_call(approve_shared_branch, branch_id, _group_actor())


def _require_decision_learner_access(learner_id: str):
    principal = get_current_principal()
    if principal is None:
        raise HTTPException(status_code=401, detail="identity_required")
    allowed, reason = authorize_learner(principal, learner_id)
    if not allowed:
        raise HTTPException(
            status_code=403,
            detail={"error": "object_access_denied", "reason": reason},
        )
    return principal


def _require_decision_loop_access(loop_id: str):
    try:
        loop = get_decision_loop(loop_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="decision_loop_not_found") from exc
    principal = _require_decision_learner_access(loop["learner_id"])
    return loop, principal


@app.post("/decision-loops")
def create_decision_loop_endpoint(request: DecisionLoopCreateRequest):
    principal = _require_decision_learner_access(request.learner_id)
    try:
        loop = create_decision_loop(
            learner_id=request.learner_id,
            goal=request.goal,
            options=request.options,
            selected_option_id=request.selected_option_id,
            choice_reason=request.choice_reason,
            state=request.state,
            actor_id=principal.actor_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"status": "created", "decision_loop": loop}


@app.post("/decision-loops/{loop_id}/actions")
def record_decision_action_endpoint(
    loop_id: str, request: DecisionLoopActionRequest
):
    _loop, principal = _require_decision_loop_access(loop_id)
    try:
        loop = record_decision_action(
            loop_id,
            action=request.action,
            expected_outcome=request.expected_outcome,
            state=request.state,
            actor_id=principal.actor_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"status": "acted", "decision_loop": loop}


@app.post("/decision-loops/{loop_id}/results")
def record_decision_result_endpoint(
    loop_id: str, request: DecisionLoopResultRequest
):
    _loop, principal = _require_decision_loop_access(loop_id)
    try:
        loop = record_decision_result(
            loop_id,
            actual_result=request.actual_result,
            responsibility_owner=request.responsibility_owner,
            reflection=request.reflection,
            state=request.state,
            actor_id=principal.actor_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"status": "completed", "decision_loop": loop}


@app.get("/decision-loops/{loop_id}")
def get_decision_loop_endpoint(loop_id: str):
    loop, _principal = _require_decision_loop_access(loop_id)
    return {"decision_loop": loop}


@app.get("/decision-loops")
def list_decision_loops_endpoint(
    learner_id: str = Query(...), limit: int = Query(50, ge=1, le=200)
):
    _require_decision_learner_access(learner_id)
    loops = list_decision_loops(learner_id, limit)
    return {"learner_id": learner_id, "items": loops, "count": len(loops)}


@app.get("/benchmark/tender-theta")
def benchmark_tender_theta():
    return tender_theta_benchmark()


@app.get("/cognition/constructs")
def cognitive_constructs_catalog():
    return construct_catalog()


@app.post("/ambient/plan/{student_id}")
def ambient_plan(student_id: str, request: AmbientPlanRequest):
    principal = _require_decision_learner_access(student_id)
    return plan_ambient_card(student_id, request.signals, actor_id=principal.actor_id, force=request.force)


@app.post("/ambient/feedback/{student_id}")
def ambient_feedback(student_id: str, request: AmbientFeedbackRequest):
    principal = _require_decision_learner_access(student_id)
    try:
        return record_ambient_feedback(student_id, request.card_id, request.feedback, actor_id=principal.actor_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/ambient/personas")
def ambient_personas():
    return list_ambient_personas()


@app.get("/ambient/persona/{student_id}")
def ambient_persona(student_id: str):
    _require_decision_learner_access(student_id)
    return get_ambient_persona(student_id)


@app.get("/ambient/ensemble/{student_id}")
def ambient_ensemble(student_id: str):
    _require_decision_learner_access(student_id)
    return get_ambient_ensemble(student_id)


@app.post("/ambient/ensemble/{student_id}")
def ambient_ensemble_select(student_id: str, request: AmbientEnsembleRequest):
    principal = _require_decision_learner_access(student_id)
    try:
        return select_ambient_ensemble(student_id, request.persona_ids, actor_id=principal.actor_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/ambient/persona/{student_id}")
def ambient_persona_select(student_id: str, request: AmbientPersonaRequest):
    principal = _require_decision_learner_access(student_id)
    try:
        return select_ambient_persona(student_id, request.persona_id, actor_id=principal.actor_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/ambient/reply/{student_id}")
def ambient_reply(student_id: str, request: AmbientReplyRequest):
    principal = _require_decision_learner_access(student_id)
    try:
        return reply_to_ambient(student_id, request.card_id, request.message, actor_id=principal.actor_id, scenario=request.scenario, persona_id=request.agent_id or request.persona_id, ensemble_ids=request.agent_ids or request.ensemble_ids)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/ambient/status/{student_id}")
def ambient_user_status(student_id: str):
    _require_decision_learner_access(student_id)
    return ambient_status(student_id)


@app.post("/cognition/assessments/{student_id}")
def create_cognitive_assessment(student_id: str, request: CognitiveAssessmentRequest):
    principal = _require_decision_learner_access(student_id)
    try:
        assessment = assess_construct(request.construct_id, request.evidence, request.threshold)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    event_id = insert_event({
        "event_type": "cognitive_construct_assessment",
        "student_id": student_id,
        "payload": {
            "construct": request.construct_id,
            "assessment": assessment,
            "input_evidence": dict(request.evidence),
        },
        "source": "tender-cognitive-model",
        "provenance": {
            "actor_id": principal.actor_id,
            "model_version": assessment.get("model_version"),
        },
    })
    write_audit(
        principal.actor_id,
        f"cognition.assess.{request.construct_id}",
        student_id,
        {"event_id": event_id, "score": assessment.get("score"), "status": assessment.get("status")},
    )
    return {"status": "assessed", "event_id": event_id, "assessment": assessment}


@app.get("/cognition/assessments/{student_id}")
def list_cognitive_assessments(student_id: str):
    _require_decision_learner_access(student_id)
    items = [
        event for event in list_events(student_id)
        if event.get("event_type") == "cognitive_construct_assessment"
    ]
    return {"student_id": student_id, "count": len(items), "assessments": items}


@app.post("/daoql/events")
def write_event(event: DAOQLEvent):
    principal = get_current_principal()
    if principal and principal.role not in {"parent", "admin", "auditor"} and event.student_id != principal.actor_id:
        raise HTTPException(status_code=403, detail="cross_learner_denied")
    eid = insert_event(event.model_dump())
    metameta_decomposition = None
    text = extract_text(event.payload)
    if event.event_type != "metameta_annotation" and (text or event.event_type in {"answer", "response", "metacognition_jol", "reflection", "teacher_prediction"}):
        try:
            metameta_decomposition = annotate_and_store(
                event.student_id,
                text,
                source_event_id=eid,
                source_event_type=event.event_type,
                payload=event.payload,
                actor_id=principal.actor_id if principal else "api",
            )
        except Exception as exc:
            metameta_decomposition = {"status": "error", "error": str(exc)}
    write_audit("api", "daoql.write_event", event.student_id, {"event_type": event.event_type, "metameta_event_id": (metameta_decomposition or {}).get("event_id")})
    return {"event_id": eid, "status": "stored", "metameta_decomposition": metameta_decomposition}


@app.get("/daoql/events/{student_id}")
def read_events(student_id: str):
    return list_events(student_id)


@app.post("/daoql/edges")
def write_edge(edge: CausalEdge):
    eid = insert_edge(edge.source_event_id, edge.target_event_id, edge.relation,
                      edge.confidence, edge.evidence)
    return {"edge_id": eid, "status": "stored"}


@app.get("/daoql/graph/{student_id}")
def graph(student_id: str):
    return event_graph(student_id)


@app.get("/daoql/causal_path")
def cpath(source: str = Query(...), target: str = Query(...), max_depth: int = 6):
    return causal_path(source, target, max_depth)


@app.post("/metameta/annotate/{student_id}")
def metameta_annotate(student_id: str, request: MetametaAnnotateRequest):
    _require_decision_learner_access(student_id)
    try:
        return decompose_and_store(
            student_id,
            request.message,
            source_event_id=request.source_event_id,
            source_event_type=request.event_type,
            payload=request.payload,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None


@app.post("/metameta/decompose/{student_id}")
def metameta_decompose(student_id: str, request: MetametaAnnotateRequest):
    return metameta_annotate(student_id, request)


@app.get("/metameta/map/{student_id}")
def metameta_map(student_id: str):
    _require_decision_learner_access(student_id)
    return {
        "student_id": student_id,
        "regions": region_catalog(),
        "map": build_metameta_annotation_map(list_events(student_id)),
    }


@app.get("/tender/context/{student_id}")
def tender_context(student_id: str, message: str | None = Query(default=None)):
    _require_decision_learner_access(student_id)
    return build_tender_context(student_id, user_message=message)


@app.get("/world-tree/{student_id}")
def world_tree(student_id: str):
    _require_decision_learner_access(student_id)
    return build_world_tree(student_id)

@app.get("/golden-bias/{student_id}")
def golden_bias(student_id: str):
    _require_decision_learner_access(student_id)
    return build_golden_bias(student_id)

@app.get("/tender/state/{student_id}")
def tender_state(student_id: str):
    return compute_state(student_id, list_events(student_id))


@app.get("/reports/student/{student_id}")
def report_student(student_id: str):
    return student_report(compute_state(student_id, list_events(student_id)))


@app.get("/reports/teacher/{class_id}")
def report_teacher(class_id: str):
    ids = students_in_class(class_id)
    states = [compute_state(sid, list_events(sid)) for sid in ids]
    out = teacher_report(states)
    out["class_id"] = class_id
    return out


@app.get("/reports/parent/{student_id}")
def report_parent(student_id: str):
    return parent_report(compute_state(student_id, list_events(student_id)))


@app.get("/reports/org")
def report_org():
    states = [compute_state(r["student_id"], list_events(r["student_id"])) for r in ROSTER]
    return org_report(states)


@app.post("/agents/{agent_id}/invoke")
def agent_invoke(agent_id: str, req: AgentInvoke):
    principal = get_current_principal()
    if principal:
        if req.actor_id and req.actor_id != principal.actor_id:
            raise HTTPException(status_code=403, detail="actor_identity_mismatch")
        if principal.role not in {"parent", "admin", "auditor"} and req.student_id != principal.actor_id:
            raise HTTPException(status_code=403, detail="cross_learner_denied")
    events = list_events(req.student_id)
    state = compute_state(req.student_id, events)
    fixed_ids = {item["agent_id"] for item in FIXED_AGENTS}
    if agent_id in fixed_ids:
        result = invoke(agent_id, req.student_id, req.message, state)
        if "error" in result:
            raise HTTPException(status_code=404, detail={"error": "unknown_agent", "agent_id": agent_id})
        return result
    actor_id = req.actor_id or req.student_id
    try:
        return invoke_expert_agent(agent_id, actor_id, req.message, state)
    except KeyError:
        raise HTTPException(status_code=404, detail={"error": "unknown_agent", "agent_id": agent_id}) from None
    except PermissionError:
        raise HTTPException(status_code=403, detail={"error": "agent_license_required"}) from None


@app.get("/workbench/experimental/status")
def workbench_experimental_status():
    return experimental_status()


@app.get("/workbench/agents")
def workbench_agents():
    return {"agents": AGENT_CATALOG, "mode": "collaboration_not_chatroom",
            "note": "Agent 围绕同一线程协作；高风险动作必须由真人审批。"}


@app.get("/workbench/audiences")
def workbench_audiences():
    return {"audiences": [{"id": k, **v} for k, v in AUDIENCE_PROFILES.items()],
            "note": "接收方角色决定沟通目标、结构、语气和隐私边界；发送前必须真人审批。"}


@app.get("/workbench/threads")
def workbench_threads(limit: int = 50, student_id: str | None = None,
                      class_id: str | None = None, role: str | None = None):
    return {"threads": list_threads(limit=limit, student_id=student_id,
                                   class_id=class_id, role=role)}


@app.post("/workbench/threads")
def workbench_create_thread(req: WorkbenchThreadCreate):
    roster_item = next((x for x in ROSTER if x["student_id"] == req.student_id), None)
    if roster_item is None:
        raise HTTPException(status_code=404, detail="student not found")
    state = compute_state(req.student_id, list_events(req.student_id))
    meta = state.get("metacognition", {})
    context = {
        "student_name": roster_item.get("name", req.student_id),
        "mastery": state.get("knowledge", {}).get("mastery", 0.5),
        "jol_bias": meta.get("jol_bias", 0.0),
        "hesitation": meta.get("hesitation", 0.0),
        "event_count": len(list_events(req.student_id)),
        **req.context,
    }
    try:
        thread = create_thread(req.title, req.objective, req.student_id, req.class_id,
                               req.created_by_role, req.task_type, context,
                               audience_role=req.audience_role,
                               audience_config=req.audience_config)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return thread


@app.get("/workbench/threads/{thread_id}")
def workbench_thread_detail(thread_id: str, viewer_role: str = "subject_teacher"):
    try:
        return for_viewer(get_workbench_thread(thread_id), viewer_role)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="thread not found") from exc


@app.post("/workbench/threads/{thread_id}/orchestrate")
def workbench_orchestrate(thread_id: str, req: WorkbenchOrchestrate):
    thread = None
    try:
        thread = get_workbench_thread(thread_id)
        state = compute_state(thread["student_id"], list_events(thread["student_id"]))
        meta = state.get("metacognition", {})
        roster_item = next((x for x in ROSTER if x["student_id"] == thread["student_id"]), {})
        context = {
            "student_name": roster_item.get("name", thread["student_id"]),
            "mastery": state.get("knowledge", {}).get("mastery", 0.5),
            "jol_bias": meta.get("jol_bias", 0.0),
            "hesitation": meta.get("hesitation", 0.0),
            "event_count": len(list_events(thread["student_id"])),
            **req.context_overrides,
        }
        return orchestrate_workbench(thread_id, context, req.focus_students)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="thread not found") from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/workbench/approvals/{approval_id}/decide")
def workbench_decide_approval(approval_id: str, req: WorkbenchApprovalDecision):
    try:
        return decide_approval(approval_id, req.decision, req.reason, req.actor)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="approval not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/workbench/threads/{thread_id}/stop")
def workbench_stop_thread(thread_id: str, req: WorkbenchStop):
    try:
        return stop_thread(thread_id, req.actor, req.reason)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="thread not found") from exc


@app.get("/advisors/catalog")
def advisor_catalog():
    return {"experts": ADVISOR_EXPERTS, "policy": "select a small advisor set; one unified reply; summary-only collaboration"}


@app.get("/safety/tickets")
def safety_tickets(status: str | None = None, limit: int = 100):
    principal = get_current_principal()
    if principal is None or principal.role not in {"admin", "auditor"}:
        raise HTTPException(status_code=403, detail="admin_required")
    return {"tickets": list_tickets(status=status, limit=limit)}


@app.get("/safety/tickets/{ticket_id}")
def safety_ticket(ticket_id: str):
    principal = get_current_principal()
    if principal is None or principal.role not in {"admin", "auditor"}:
        raise HTTPException(status_code=403, detail="admin_required")
    try:
        return get_ticket(ticket_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/safety/tickets/{ticket_id}/update")
def safety_ticket_update(ticket_id: str, request: SafetyTicketUpdate):
    principal = get_current_principal()
    if principal is None or principal.role not in {"admin", "auditor"}:
        raise HTTPException(status_code=403, detail="admin_required")
    try:
        return update_ticket(ticket_id, request.status, principal.actor_id, request.assignee, request.resolution)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/advisors/route")
def advisor_route(req: AdvisorRouteRequest):
    state = compute_state(req.student_id, list_events(req.student_id))
    tender = {"knowledge": state.get("knowledge", {}), "metacognition": state.get("metacognition", {})}
    result = route_advisors(req.message, req.role, tender, req.consent_scopes)
    event_id = insert_event({"event_type": "advisor_route", "student_id": req.student_id,
                             "payload": {"route_id": result["route_id"], "role": req.role,
                                         "selected_experts": result["selected_experts"], "safety_level": result["safety_level"]},
                             "source": "advisor_moe_router"})
    result["event_id"] = event_id
    if result.get("safety_level") in {"review", "emergency"}:
        ticket = create_ticket(
            student_id=req.student_id,
            source_agent="advisor_router",
            risk_level=result["safety_level"],
            reason="advisor_safety_level",
            evidence_refs=[event_id],
            message_hash=hashlib.sha256((req.message or "").encode("utf-8")).hexdigest(),
        )
        result["safety_ticket_id"] = ticket["ticket_id"]
    return result


@app.post("/advisors/collaborate")
def advisor_collaborate(req: AdvisorShareRequest):
    try:
        return share_signal(req.student_id, req.from_advisor, req.to_advisor, req.purpose,
                            req.summary, req.evidence_refs, req.consent_scopes)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/advisors/collaborations/{student_id}")
def advisor_collaborations(student_id: str):
    rows = [e for e in all_events() if e.get("student_id") == student_id and e.get("event_type") == "advisor_collaboration"]
    return {"collaborations": rows, "count": len(rows)}


def _public_audit_value(value):
    if isinstance(value, dict):
        return {_public_audit_key(key): _public_audit_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_public_audit_value(item) for item in value]
    if isinstance(value, str) and "camel" in value.lower():
        return "agent-runtime"
    return value


def _public_audit_key(key: str) -> str:
    if "camel" in key.lower():
        return "runtime_metadata"
    return key


@app.get("/audit")
def audit(limit: int = 100):
    return [_public_audit_value(row) for row in list_audit(limit)]


@app.get("/audit/verify")
def audit_verify(limit: int = 10000):
    return verify_audit_chain(limit)


@app.post("/rag/search")
def rag_search(q: RAGQuery):
    return search(q.query, q.top_k)


@app.post("/rag/ingest")
def rag_ingest(x: RAGIngest):
    p = ingest_text(x.name, x.text)
    return {"path": p, "index": build_index()}


@app.get("/rag/stats")
def rag_stats():
    return build_index()



@app.get("/reports/head_teacher/{class_id}")
def report_head_teacher(class_id: str):
    """班主任作战台：把规则执行、学习闭环、家校沟通、关怀和协作边界压成一个工作台。"""
    ids = students_in_class(class_id)
    events_by_student = {sid: list_events(sid) for sid in ids}
    states = []
    for sid in ids:
        st = compute_state(sid, events_by_student[sid])
        mastery = st.get("knowledge", {}).get("mastery", 0.5)
        bias = st.get("metacognition", {}).get("jol_bias", 0.0) or 0.0
        hesitation = st.get("metacognition", {}).get("hesitation", 0.0) or 0.0
        fit = st.get("baseline", {}).get("arrangement_fit", 0.5) or 0.5
        risk = (1 - mastery) + abs(bias) + hesitation + (1 - fit)
        reasons = []
        if mastery < 0.6:
            reasons.append("掌握度偏低")
        if abs(bias) > 0.15:
            reasons.append("JOL 偏差大")
        if hesitation > 0.6:
            reasons.append("犹豫偏高")
        if fit < 0.5:
            reasons.append("安排匹配低")
        states.append({"student_id": sid, "mastery": round(mastery, 4),
                       "jol_bias": round(bias, 4), "hesitation": round(hesitation, 4),
                       "arrangement_fit": round(fit, 4), "risk": round(risk, 4),
                       "reasons": reasons or ["状态稳定"]})
    states.sort(key=lambda x: x["risk"], reverse=True)
    priority = states[:3]
    focus = [s["student_id"] for s in priority]

    parent_messages = []
    for s in priority:
        parent_messages.append({
            "student_id": s["student_id"],
            "draft": "本周我们注意到孩子在" + "、".join(s["reasons"]) + "方面有变化。建议在家做一个 10 分钟的“先预测、再作答、后复盘”练习。",
            "status": "待班主任确认",
            "channel": "微信/电话",
            "facts_only": True,
        })
    answer_events = sum(1 for evs in events_by_student.values() for e in evs if e["event_type"] == "answer")
    risk_alerts = [s for s in states if s["hesitation"] > 0.8 or s["mastery"] < 0.3]

    # 标准 SOP 以时间轴展示；状态只是当天进度提示，不代表出勤事实已经自动采集。
    schedule_defs = [
        {"start": "06:55", "end": "08:10", "title": "叫醒、手机入袋、早读与早餐", "category": "纪律/学习", "deliverable": "出勤与早读证据", "automation": "未打卡提醒", "human_required": True},
        {"start": "08:10", "end": "08:30", "title": "晨检考勤与异常同步", "category": "考勤", "deliverable": "异常清单", "automation": "硬件/网络异常汇总", "human_required": True},
        {"start": "08:30", "end": "11:50", "title": "跟班听课、课间抽背、课堂状态记录", "category": "学习/秩序", "deliverable": "跟课记录", "automation": "作业初筛、背诵评分", "human_required": True},
        {"start": "11:50", "end": "14:20", "title": "午餐纪律、午自习与查寝", "category": "纪律/关怀", "deliverable": "午间异常记录", "automation": "异常提醒", "human_required": True},
        {"start": "14:30", "end": "18:10", "title": "下午考勤、跟班听讲、突发处理与例会", "category": "学习/协作", "deliverable": "问题清单", "automation": "工单路由", "human_required": True},
        {"start": "18:10", "end": "22:30", "title": "晚自习、作业批改、统一答疑与手机收缴", "category": "学习闭环", "deliverable": "作业与答疑证据", "automation": "客观题预批、错题聚合", "human_required": True},
        {"start": "22:40", "end": "23:30", "title": "通关测试、二次抽背与查寝", "category": "学习/纪律", "deliverable": "通关名单", "automation": "语音/文本初筛", "human_required": True},
        {"start": "23:30", "end": "24:00", "title": "家长今日总结与明日提醒", "category": "家校沟通", "deliverable": "家长摘要", "automation": "事实摘要草稿", "human_required": True},
    ]
    now = datetime.now(ZoneInfo("Asia/Shanghai"))
    current_minute = now.hour * 60 + now.minute
    schedule = []
    current_block = "非标准时段"
    for item in schedule_defs:
        sm = int(item["start"][:2]) * 60 + int(item["start"][3:])
        em = int(item["end"][:2]) * 60 + int(item["end"][3:])
        status = "upcoming" if current_minute < sm else "done"
        if sm <= current_minute < em:
            status = "current"
            current_block = item["title"]
        schedule.append({**item, "status": status})

    collaboration_tickets = [
        {"ticket_id": "HT-01", "title": "与任课教师对齐今日重点学生", "owner": "班主任",
         "collaborator": "任课教师", "due": "今日 17:30", "status": "待处理",
         "evidence": focus, "boundary": "班主任负责协调，任课教师负责学科判断"},
        {"ticket_id": "HT-02", "title": "确认家长沟通草稿", "owner": "班主任",
         "collaborator": "家长", "due": "今日 20:00", "status": "待确认",
         "evidence": focus, "boundary": "只发送已确认事实，不做诊断和承诺"},
        {"ticket_id": "HT-03", "title": "补齐今日出勤、作业与关怀事实", "owner": "班主任",
         "collaborator": "助教/宿管", "due": "今日 22:00", "status": "待录入",
         "evidence": [], "boundary": "事实记录与判断解释分开保存"},
    ]
    responsibility_matrix = [
        {"role": "班主任", "owns": ["班级运行", "家长沟通确认", "学生关怀", "风险升级"], "not_owns": ["学科专业判断", "医疗诊断"]},
        {"role": "任课教师", "owns": ["学科教学", "作业标准", "学科反馈"], "not_owns": ["家长授权", "学生终身数据"]},
        {"role": "助教", "owns": ["答疑执行", "作业初筛", "资料准备"], "not_owns": ["最终评价", "家长沟通"]},
        {"role": "宿管", "owns": ["查寝", "门禁", "生活异常上报"], "not_owns": ["学习判断", "家长营销"]},
        {"role": "机构管理员", "owns": ["权限", "合规", "财务与合同"], "not_owns": ["学习者终身护照"]},
        {"role": "家长", "owns": ["监护授权", "家庭配合", "离校交接"], "not_owns": ["教师专业判断", "学生隐私全部访问"]},
    ]
    care_board = [
        {"student_id": s["student_id"], "type": "学习状态关注", "signal": "、".join(s["reasons"]),
         "suggested_action": "先核对最近作业、出勤和课堂事实，再进行短沟通；不贴标签",
         "owner": "班主任", "needs_human": True}
        for s in risk_alerts[:3]
    ]
    if not care_board:
        care_board = [{"student_id": "", "type": "暂无高风险信号", "signal": "当前数据未触发",
                       "suggested_action": "继续按日常节奏记录事实", "owner": "班主任", "needs_human": False}]
    handoff_templates = [
        {"scenario": "新生入营", "required": ["学习资料", "账号/权限", "监护授权", "健康/用药备注（如适用）", "首次基线"], "owner": "班主任", "status": "模板"},
        {"scenario": "教师更换", "required": ["交接清单", "学生证据", "未完成工单", "家长沟通状态"], "owner": "班主任", "status": "模板"},
        {"scenario": "离校/返校", "required": ["离校时间", "交接人", "家长确认", "返校提醒"], "owner": "班主任", "status": "模板"},
        {"scenario": "健康/关怀事件", "required": ["事实记录", "时间", "已采取措施", "升级对象"], "owner": "班主任/宿管", "status": "模板"},
        {"scenario": "账单争议", "required": ["消费明细", "通知记录", "家长确认", "处理结果"], "owner": "机构财务/班主任", "status": "待接入"},
    ]
    automation_opportunities = [
        {"name": "考勤异常汇总", "value": "减少人工核实", "status": "待接入"},
        {"name": "家长消息结构化", "value": "把学情、通知、账单分开", "status": "可先做"},
        {"name": "作业客观题预批", "value": "释放批改时间", "status": "已具备基础"},
        {"name": "关怀提醒", "value": "减少依赖人脑记忆", "status": "待接入"},
        {"name": "协作工单与事实日志", "value": "减少甩锅和信息丢失", "status": "已具备基础"},
    ]

    return {
        "class_id": class_id,
        "n_students": len(states),
        "priority": priority,
        "parent_messages": parent_messages,
        "homework": {"answer_events": answer_events,
                     "agent_processed": answer_events,
                     "teacher_review": len(priority)},
        "teacher_coordination": {"summary": "建议今天用 5 分钟和科任老师对齐 3 个重点学生。",
                                  "focus": focus},
        "risk_alerts": risk_alerts,
        "shift": {"timezone": "Asia/Shanghai", "current_time": now.isoformat(),
                  "current_block": current_block, "schedule": schedule},
        "collaboration": {"tickets": collaboration_tickets,
                           "responsibility_matrix": responsibility_matrix},
        "care_board": care_board,
        "handoff_templates": handoff_templates,
        "automation_opportunities": automation_opportunities,
        "finance": {"status": "not_connected", "note": "校内消费/代收账单尚未接入，不在本模块伪造数据。"},
        "time_saved_minutes": 35 + 5 * len(priority),
        "note": "这是班主任 Copilot 的聚合视图，不替代班主任判断；事实、建议和升级动作分开记录。"
    }


@app.post("/head_teacher/{class_id}/notes")
def write_head_teacher_note(class_id: str, note: HeadTeacherNote):
    """记录可核实的班主任事实，不写入诊断或人格标签。"""
    ids = students_in_class(class_id)
    if note.student_id not in ids:
        raise HTTPException(status_code=403, detail="student is outside this class scope")
    event_id = insert_event({
        "event_type": "head_teacher_note",
        "student_id": note.student_id,
        "payload": {"class_id": class_id, "category": note.category,
                    "text": note.text, "visibility": note.visibility},
        "source": "head_teacher_workspace",
    })
    write_audit("head_teacher", "head_teacher.note", note.student_id,
                {"class_id": class_id, "category": note.category, "visibility": note.visibility})
    return {"event_id": event_id, "status": "stored",
            "note": "已记录事实；请勿填写诊断、人格标签或未经核实的判断。"}

LIFELONG_STAGES = [
    {"stage": "小学", "focus": "习惯、兴趣、情绪安全", "pain": "注意力短、家长焦虑、习惯未建立",
     "agents": ["班主任 Copilot", "习惯教练", "家长沟通", "安全护栏"],
     "metrics": ["出勤", "作业提交", "阅读量", "情绪安全", "家长参与"],
     "intervention": ["积分", "习惯打卡", "亲子沟通模板"]},
    {"stage": "初中", "focus": "学科方法、元认知、青春期", "pain": "学科分化、叛逆、偏科、中考压力",
     "agents": ["班主任 Copilot", "Metacognition Coach", "Assessment", "Group Facilitator"],
     "metrics": ["学科均衡", "错题消解", "JOL 校准", "情绪稳定"],
     "intervention": ["四象限讲评", "错题本", "学习计划"]},
    {"stage": "高中", "focus": "高考、专业选择、自驱", "pain": "压力、焦虑、选科、志愿",
     "agents": ["学习教练", "志愿规划", "班主任 Copilot", "家长沟通"],
     "metrics": ["成绩曲线", "目标达成", "压力指数", "元认知"],
     "intervention": ["目标拆解", "压力管理", "志愿工作坊"]},
    {"stage": "大学", "focus": "自主学习、通识/专业、职业规划", "pain": "自律、方向感、实习、信息过载",
     "agents": ["学术教练", "项目教练", "职业教练", "RAG 助手"],
     "metrics": ["课程完成", "项目作品", "实习", "技能图谱"],
     "intervention": ["项目制学习", "导师匹配", "实习追踪"]},
    {"stage": "硕士", "focus": "研究方法、文献、论文", "pain": "文献焦虑、方法不熟、导师沟通",
     "agents": ["文献 Agent", "方法教练", "论文项目管理", "导师沟通"],
     "metrics": ["文献阅读", "方法掌握", "论文进度", "导师反馈"],
     "intervention": ["文献综述", "方法工作坊", "周报"]},
    {"stage": "博士", "focus": "原创研究、学术身份、发表", "pain": "孤独、拖延、发表压力、职业不确定",
     "agents": ["研究项目 Agent", "发表管道", "学术网络", "心理支持"],
     "metrics": ["论文进度", "投稿", "会议", "学术网络"],
     "intervention": ["里程碑", "写作小组", "职业路径"]},
    {"stage": "职业/成人", "focus": "技能更新、转行、终身学习", "pain": "时间碎片、动机、认证、家庭/工作平衡",
     "agents": ["技能差距分析", "微学习教练", "职业教练", "社群"],
     "metrics": ["技能差距", "学习时长", "证书", "转行进度"],
     "intervention": ["微证书", "项目作品", "导师网络"]},
]


@app.get("/lifelong/stages")
def lifelong_stages():
    return {"stages": LIFELONG_STAGES, "passport": "学习者拥有、可携带、可验证的学习记录"}


TRANSITIONS = [
    {"from": "小学", "to": "初中", "problem": "习惯没迁移、学科变多、青春期", "action": "过渡诊断 + 学习方法 + 情绪陪伴"},
    {"from": "初中", "to": "高中", "problem": "选科、压力、偏科、中考后松懈", "action": "选科建议 + 压力管理 + 目标拆解"},
    {"from": "高中", "to": "大学", "problem": "专业选择、自主学习、离家", "action": "专业探索 + 自主学习计划 + 职业启蒙"},
    {"from": "大学", "to": "硕士", "problem": "研究方法、导师匹配、学术写作", "action": "研究方法 + 文献入门 + 导师沟通"},
    {"from": "硕士", "to": "博士", "problem": "原创性、长期项目、孤独", "action": "研究项目管理 + 写作小组 + 心理支持"},
    {"from": "博士", "to": "职业", "problem": "学术/产业选择、求职、身份转换", "action": "职业路径 + 学术网络 + 产业对接"},
    {"from": "职业", "to": "再学习", "problem": "技能过时、转行、时间碎片", "action": "技能差距 + 微学习 + 项目作品"},
]


@app.get("/lifelong/transitions")
def lifelong_transitions():
    return {"transitions": TRANSITIONS}


@app.get("/lifelong/passport/{learner_id}")
def lifelong_passport(learner_id: str):
    events = list_events(learner_id)
    st = compute_state(learner_id, events)
    return {
        "learner_id": learner_id,
        "current_stage": "高中",
        "skills": st.get("knowledge", {}),
        "metacognition": st.get("metacognition", {}),
        "rhythm": st.get("baseline", {}).get("rhythm", {}),
        "learning_events": events[-20:],
        "projects": [],
        "credentials": [],
        "publications": [],
        "mentor_feedback": st.get("observer", {}).get("teacher_metameta", {}),
        "career_milestones": [],
        "privacy": {"stage_consent": "待接入", "portable": True, "revocable": True},
        "note": "项目、证书、论文、职业里程碑为护照预留字段，等待真实数据接入；不编造。"
    }


@app.get("/sales/ammunition/{class_id}")
def sales_ammunition(class_id: str):
    ids = students_in_class(class_id)
    events_by_student = {sid: list_events(sid) for sid in ids}
    states = []
    for sid in ids:
        st = compute_state(sid, events_by_student[sid])
        mastery = float(st.get("knowledge", {}).get("mastery", 0.5) or 0.5)
        bias = float(st.get("metacognition", {}).get("jol_bias", 0.0) or 0.0)
        hesitation = float(st.get("metacognition", {}).get("hesitation", 0.0) or 0.0)
        fit = float(st.get("baseline", {}).get("arrangement_fit", 0.5) or 0.5)
        renewal = max(0.0, min(1.0, 0.5 + 0.3*(mastery-0.5) - 0.2*abs(bias) - 0.2*hesitation + 0.1*(fit-0.5)))
        referral = max(0.0, min(1.0, 0.5 + 0.3*(mastery-0.5) + 0.2*(fit-0.5) - 0.2*hesitation))
        risk = max(0.0, min(1.0, 1.0 - renewal))
        states.append({"student_id": sid, "mastery": round(mastery,4), "jol_bias": round(bias,4),
                       "hesitation": round(hesitation,4), "arrangement_fit": round(fit,4),
                       "renewal_probability": round(renewal,4), "referral_score": round(referral,4),
                       "churn_risk": round(risk,4)})
    churn_top = sorted(states, key=lambda x: x["churn_risk"], reverse=True)[:3]
    renewal_top = sorted(states, key=lambda x: x["renewal_probability"], reverse=True)[:3]
    referral_top = sorted(states, key=lambda x: x["referral_score"], reverse=True)[:3]
    actions = []
    for s in churn_top[:2]:
        actions.append({"priority": "P0", "student_id": s["student_id"], "type": "risk",
                        "signal": "流失风险高 / 犹豫高", "action": "24 小时内回访",
                        "script": "最近观察到孩子在学习节奏上有些变化，我想先了解是不是时间冲突，我们一起调整。"})
    for s in renewal_top[:2]:
        actions.append({"priority": "P1", "student_id": s["student_id"], "type": "renewal",
                        "signal": "续费优先级最高", "action": "本周五前联系家长续费",
                        "script": "这阶段孩子进步比较明显，建议趁热打铁进入下一阶段，我可以把学习报告发您。"})
    for s in referral_top[:2]:
        actions.append({"priority": "P2", "student_id": s["student_id"], "type": "referral",
                        "signal": "转介绍优先级最高", "action": "请求推荐 1 位家长",
                        "script": "您对这段时间反馈很好，如果身边有同样需要提升的孩子，可以推荐，我们优先安排。"})
    seen = set(); uniq = []
    for a in actions:
        key = (a["student_id"], a["type"])
        if key not in seen:
            seen.add(key); uniq.append(a)
    selected = []
    for s in [churn_top[0], renewal_top[0], referral_top[0]]:
        if s["student_id"] not in {x["student_id"] for x in selected}:
            selected.append(s)
    student_pages = []
    for s in selected:
        evs = events_by_student[s["student_id"]]
        answers = [e for e in evs if e["event_type"] == "answer"]
        student_pages.append({
            "student_id": s["student_id"],
            "attendance": "待接入",
            "homework": {"answer_events": len(answers), "completion": "待接入"},
            "progress": {"mastery": s["mastery"], "jol_bias": s["jol_bias"]},
            "parent_feedback": "待接入",
            "renewal_probability": s["renewal_probability"],
            "churn_risk": s["churn_risk"],
            "script": "这阶段孩子的掌握度是 " + str(s["mastery"]) + "，JOL 偏差是 " + str(s["jol_bias"]) + "，建议先做一次学习复盘。"
        })
    class_page = {
        "n_students": len(states),
        "avg_mastery": round(sum(x["mastery"] for x in states)/len(states),4) if states else 0,
        "renewal_opportunities": len(renewal_top),
        "churn_risks": len(churn_top),
        "referral_leads": len(referral_top),
        "note": "班级一页纸用于销售作战，不替代教学判断。"
    }

    scripts = {
        "progress": "这阶段孩子进步比较明显，建议趁热打铁进入下一阶段。",
        "risk": "最近观察到孩子在学习节奏上有些变化，我想先了解是不是时间冲突。",
        "renewal": "根据学习报告，孩子已经达到阶段目标，建议进入下一阶段。",
        "referral": "如果身边有同样需要提升的孩子，可以推荐，我们优先安排。"
    }
    return {"class_id": class_id, "kpis": class_page, "actions": uniq,
            "student_pages": student_pages, "class_page": class_page, "scripts": scripts,
            "note": "销售赋能工具，不替代销售，不抢销售客户。"}


@app.get("/learner/home/{learner_id}")
def learner_home(learner_id: str):
    """C-end learner home: understand, support, reflect, and keep the evidence."""
    events = list_events(learner_id)
    st = compute_state(learner_id, events)
    profile = next((r for r in ROSTER if r["student_id"] == learner_id),
                   {"student_id": learner_id, "name": learner_id, "class": "学习者"})
    member = build_mentalization(learner_id, st, events)
    mastery = float(st.get("knowledge", {}).get("mastery", 0.5) or 0.5)
    bias = float(st.get("metacognition", {}).get("jol_bias", 0.0) or 0.0)
    hesitation = float(st.get("metacognition", {}).get("hesitation", 0.0) or 0.0)

    actions = []
    if mastery < 0.6:
        actions.append("先确认卡在哪个连接，再给最小提示和复述机会")
    if abs(bias) > 0.15:
        actions.append("先预测，再作答，后复盘：只比较预测与实际")
    if hesitation > 0.6:
        actions.append("先问卡点，再决定提示、拆解还是短暂停顿")
    actions = actions or ["保持当前节奏，做一次自我解释或迁移任务"]

    evidence = []
    for e in events[-8:]:
        payload = e.get("payload", {})
        if e.get("event_type") == "answer":
            summary = "作答记录：" + ("正确" if payload.get("correct") else "未通过")
        elif e.get("event_type") == "metacognition_jol":
            summary = f"预测 {payload.get('predicted_correct', 0)} / 实际 {payload.get('actual_correct', 0)}"
        elif e.get("event_type") == "reflection":
            summary = "自我反思：" + str(payload.get("answer", ""))[:80]
        else:
            summary = e.get("event_type", "学习事件")
        evidence.append({"event_id": e.get("event_id"), "event_type": e.get("event_type"),
                         "timestamp": e.get("timestamp"), "summary": summary})

    available_sources = sum([
        1 if events else 0,
        1 if st.get("knowledge") else 0,
        1 if st.get("metacognition") else 0,
        1 if st.get("baseline") else 0,
    ])
    portability_score = round(available_sources / 4.0, 4)
    support_network = [
        {"name": "学习科学顾问", "focus": "元认知、学习节律与支持策略", "status": "按需调用"},
        {"name": "神经认知顾问", "focus": "注意、工作记忆与认知负荷", "status": "按需调用"},
        {"name": "心理支持顾问", "focus": "压力与情绪支持，非临床诊断", "status": "高风险时升级"},
        {"name": "健康与营养顾问", "focus": "睡眠、活动、恢复与饮食上下文", "status": "授权后调用"},
        {"name": "生涯与职业顾问", "focus": "长期学习路径与发展探索", "status": "按需调用"},
        {"name": "安全与保护顾问", "focus": "风险识别与人工升级", "status": "后台常驻"},
    ]
    return {
        "learner_id": learner_id,
        "profile": profile,
        "tender_id": "TENDER-" + learner_id,
        "current_stage": "持续学习者",
        "data_ownership": "学习者拥有",
        "privacy": {"guardian_required": True, "exportable": True, "revocable": True,
                    "note": "未成年人需要监护人授权；家庭只查看经授权的最小必要摘要，不共享原始对话。"},
        "passport": {
            "skills": st.get("knowledge", {}),
            "metacognition": st.get("metacognition", {}),
            "baseline": st.get("baseline", {}),
            "emotion_context": member.get("emotion_context", {}),
            "learning_events": len(events),
            "evidence": evidence,
            "credentials": [],
            "portfolio": {"evidence_count": len(evidence), "status": "待积累"},
        },
        "mentalization": member,
        "plan": {
            "next_actions": actions,
            "mastery": round(mastery, 4),
            "estimated_minutes": 10 + 5 * len(actions),
            "mode": "连续记录 + 最低必要提示 + 可撤回授权",
        },
        "ai_coach": {
            "provider": "Tender",
            "model": "mentalization-runtime",
            "suggestion": member.get("summary", "先理解此刻的状态，再选择最小支持。"),
            "prompt": member.get("reflection_prompt", "此刻最值得被理解的是什么？"),
        },
        "support_network": support_network,
        "teachers": [],
        "marketplace": {"status": "planned", "independent_teacher_slots": 0,
                        "note": "专业支持网络按需开放；不以绑定老师或组织为使用前提。"},
        "community": {"groups": [], "note": "家庭与学习共同体摘要待接入；个人记录默认不共享。"},
        "portability": {"score": portability_score, "label": "数据可携带度",
                        "note": "只表示记录覆盖程度，不评价学习者。"},
        "note": "C端心智化学习：理解状态、提供支持、验证结果，并把长期证据归还学习者。",
    }


@app.get("/learner/mentalization/{learner_id}")
def learner_mentalization(learner_id: str):
    """Return the current evidence-backed, non-clinical mentalization card."""
    events = list_events(learner_id)
    state = compute_state(learner_id, events)
    return build_mentalization(learner_id, state, events)


@app.post("/learner/mentalization/snapshot/{learner_id}")
def record_mentalization_snapshot(learner_id: str):
    """Persist a timestamped cognitive-emotion snapshot for long-term causality."""
    events = list_events(learner_id)
    state = compute_state(learner_id, events)
    member = build_mentalization(learner_id, state, events)
    event_id = insert_event({
        "event_type": "mentalization_snapshot",
        "student_id": learner_id,
        "payload": {
            "summary": member["summary"],
            "confidence": member["confidence"],
            "hypotheses": member["hypotheses"][:3],
            "emotion_context": member["emotion_context"],
            "state_snapshot": member["state_snapshot"],
            "reflection_prompt": member["reflection_prompt"],
            "boundary": member["boundary"],
        },
        "source": "c_end_app",
    })
    write_audit("learner:" + learner_id, "mentalization.snapshot", event_id,
                {"summary": member["summary"], "confidence": member["confidence"]})
    return {"status": "recorded", "event_id": event_id, "snapshot": member}


@app.get("/learner/mentalization/timeline/{learner_id}")
def mentalization_timeline(learner_id: str):
    """Build a long-term timeline and causal transitions from DAOQL events."""
    events = list_events(learner_id)
    points = []
    last_summary = None
    last_point_event_id = None
    for index in range(1, len(events) + 1):
        event = events[index - 1]
        event_type = event.get("event_type")
        if event_type not in {"answer", "response", "metacognition_jol", "reflection", "mentalization_snapshot", "baseline"} and index != len(events):
            continue
        prefix = events[:index]
        state = compute_state(learner_id, prefix)
        member = build_mentalization(learner_id, state, prefix)
        if event_type in {"reflection", "mentalization_snapshot"} or member["summary"] != last_summary:
            point = {
                "event_id": event.get("event_id"),
                "timestamp": event.get("timestamp"),
                "event_type": event_type,
                "summary": member["summary"],
                "confidence": member["confidence"],
                "state": member["state_snapshot"],
                "emotion": member["emotion_context"],
                "hypotheses": member["hypotheses"][:3],
                "previous_event_id": last_point_event_id,
            }
            points.append(point)
            last_point_event_id = event.get("event_id")
            last_summary = member["summary"]
    causal_links = []
    for i, event in enumerate(events):
        if event.get("event_type") != "reflection":
            continue
        prior = next((p for p in reversed(points) if p["timestamp"] <= event.get("timestamp", "")), None)
        next_answer = next((e for e in events[i + 1:] if e.get("event_type") in {"answer", "response"}), None)
        if prior:
            causal_links.append({"source": prior["event_id"], "target": event.get("event_id"),
                                 "relation": "informed_reflection", "confidence": prior["confidence"]})
        if next_answer:
            causal_links.append({"source": event.get("event_id"), "target": next_answer.get("event_id"),
                                 "relation": "reflection_before_outcome", "confidence": 0.45})
    return {"learner_id": learner_id, "points": points, "causal_links": causal_links,
            "note": "因果关系是时间顺序与证据引用形成的可审计假设，不等同于统计因果识别。"}


@app.post("/learner/reflection/{learner_id}")
def record_reflection(learner_id: str, request: ReflectionCreate):
    """Record a learner reflection and immediately recompute the mentalization card."""
    answer = (request.answer or "").strip()
    if not answer:
        raise HTTPException(status_code=400, detail="reflection answer is required")
    if len(answer) > 4000:
        raise HTTPException(status_code=400, detail="reflection answer is too long")
    event_id = insert_event({
        "event_type": "reflection",
        "student_id": learner_id,
        "payload": {
            "prompt": request.prompt,
            "answer": answer,
            "mood": request.mood,
            "consent_scopes": request.consent_scopes,
        },
        "source": "c_end_app",
    })
    write_audit("learner:" + learner_id, "reflection.create", event_id,
                {"prompt": request.prompt, "answer_chars": len(answer)})
    events = list_events(learner_id)
    state = compute_state(learner_id, events)
    member = build_mentalization(learner_id, state, events)
    return {"status": "recorded", "event_id": event_id, "mentalization": member}


@app.get("/learner/export/{learner_id}")
def export_learner_data(learner_id: str):
    """导出学习者自己的 JSON 记录，体现数据可携带。"""
    payload = learner_home(learner_id)
    return JSONResponse(
        payload,
        headers={"Content-Disposition": f'attachment; filename="tender-{learner_id}.json"'},
    )
STATUS_LABELS = {
    "in_school": "在校",
    "dorm": "在寝",
    "leave": "请假",
    "external_training": "外出集训",
    "commuting": "跑校",
    "absent": "未归/异常",
    "unknown": "未登记",
}


def _student_statuses(class_id: str):
    ids = students_in_class(class_id)
    latest = {sid: {"student_id": sid, "status": "unknown", "status_label": "未登记",
                    "updated_at": None, "note": "", "effective_at": None,
                    "expected_return": None} for sid in ids}
    profiles = {r["student_id"]: r for r in ROSTER}
    for e in all_events():
        if e.get("event_type") != "student_status" or e.get("student_id") not in latest:
            continue
        payload = e.get("payload", {})
        if payload.get("class_id") not in (class_id, "all", None):
            continue
        status = payload.get("status", "unknown")
        latest[e["student_id"]] = {
            "student_id": e["student_id"],
            "name": profiles.get(e["student_id"], {}).get("name", e["student_id"]),
            "class": profiles.get(e["student_id"], {}).get("class", ""),
            "status": status,
            "status_label": STATUS_LABELS.get(status, status),
            "updated_at": e.get("timestamp"),
            "note": payload.get("note", ""),
            "effective_at": payload.get("effective_at"),
            "expected_return": payload.get("expected_return"),
        }
    for sid, item in latest.items():
        item.setdefault("name", profiles.get(sid, {}).get("name", sid))
        item.setdefault("class", profiles.get(sid, {}).get("class", ""))
    return list(latest.values())


def _status_board(class_id: str):
    items = _student_statuses(class_id)
    counts = {"in_school": 0, "dorm": 0, "leave": 0, "external_training": 0,
              "commuting": 0, "absent": 0, "unknown": 0}
    for item in items:
        counts[item["status"]] = counts.get(item["status"], 0) + 1
    expected = [x["student_id"] for x in items if x["status"] in ("in_school", "dorm")]
    pending = [x["student_id"] for x in items if x["status"] == "unknown"]
    excused = [x["student_id"] for x in items if x["status"] in ("leave", "external_training", "commuting")]
    exceptions = [x["student_id"] for x in items if x["status"] == "absent"]
    return {"class_id": class_id, "counts": counts, "students": items,
            "expected_in_dorm_ids": expected, "pending_verification_ids": pending,
            "excused_ids": excused, "exception_ids": exceptions,
            "source": "latest student_status events; unknown is not treated as present."}


def _teaching_tasks(class_id: str):
    events = [e for e in all_events() if e.get("event_type") in ("teaching_task", "teaching_task_update")
              and e.get("payload", {}).get("class_id") == class_id]
    tasks = {}
    for e in events:
        p = e.get("payload", {})
        if e["event_type"] == "teaching_task":
            tasks[e["event_id"]] = {
                "task_event_id": e["event_id"], "class_id": class_id,
                "teacher_id": p.get("teacher_id"), "subject": p.get("subject"),
                "title": p.get("title"), "instructions": p.get("instructions", ""),
                "due_at": p.get("due_at"), "student_ids": p.get("student_ids", []),
                "status": p.get("status", "assigned"), "updated_at": e.get("timestamp"),
                "completed_by": None, "completion_note": "",
            }
        elif p.get("task_event_id") in tasks:
            task = tasks[p["task_event_id"]]
            task["status"] = p.get("status", task["status"])
            task["updated_at"] = e.get("timestamp")
            task["completed_by"] = p.get("completed_by")
            task["completion_note"] = p.get("note", "")
    return sorted(tasks.values(), key=lambda x: x.get("updated_at") or "", reverse=True)


@app.get("/student-status/{class_id}")
def student_status_board(class_id: str):
    return _status_board(class_id)


@app.post("/student-status/{class_id}")
def update_student_status(class_id: str, update: StudentStatusUpdate):
    ids = students_in_class(class_id)
    if update.student_id not in ids:
        raise HTTPException(status_code=403, detail="student outside class scope")
    if update.status not in STATUS_LABELS:
        raise HTTPException(status_code=422, detail="unknown student status")
    event_id = insert_event({
        "event_type": "student_status", "student_id": update.student_id,
        "payload": {"class_id": class_id, "status": update.status,
                    "effective_at": update.effective_at, "expected_return": update.expected_return,
                    "note": update.note}, "source": "student_status_change",
    })
    write_audit("student_status", "student_status.update", update.student_id,
                {"class_id": class_id, "status": update.status})
    return {"event_id": event_id, "status": "stored", "board": _status_board(class_id)}


@app.get("/teaching/tasks/{class_id}")
def list_teaching_tasks(class_id: str):
    return {"class_id": class_id, "tasks": _teaching_tasks(class_id)}


@app.post("/teaching/tasks/{class_id}")
def create_teaching_task(class_id: str, task: TeachingTaskCreate):
    ids = students_in_class(class_id)
    if task.class_id != class_id:
        raise HTTPException(status_code=422, detail="class_id mismatch")
    if any(sid not in ids for sid in task.student_ids):
        raise HTTPException(status_code=403, detail="task includes student outside class scope")
    event_id = insert_event({
        "event_type": "teaching_task", "student_id": "CLASS:" + class_id,
        "payload": {"class_id": class_id, "teacher_id": task.teacher_id, "subject": task.subject,
                    "title": task.title, "instructions": task.instructions, "due_at": task.due_at,
                    "student_ids": task.student_ids, "status": "assigned"},
        "source": "subject_teacher_workspace",
    })
    write_audit("subject_teacher", "teaching_task.create", event_id,
                {"class_id": class_id, "subject": task.subject, "title": task.title})
    return {"event_id": event_id, "status": "assigned"}


@app.post("/teaching/tasks/{class_id}/{task_event_id}/complete")
def complete_teaching_task(class_id: str, task_event_id: str, completion: TeachingTaskComplete):
    task_event = next((e for e in all_events() if e["event_id"] == task_event_id
                       and e.get("event_type") == "teaching_task"), None)
    if not task_event or task_event.get("payload", {}).get("class_id") != class_id:
        raise HTTPException(status_code=404, detail="task not found")
    event_id = insert_event({
        "event_type": "teaching_task_update", "student_id": "CLASS:" + class_id,
        "payload": {"class_id": class_id, "task_event_id": task_event_id,
                    "status": "completed", "completed_by": completion.completed_by,
                    "note": completion.note}, "source": "head_teacher_workspace",
    })
    write_audit("head_teacher", "teaching_task.complete", task_event_id,
                {"class_id": class_id, "completion_event_id": event_id})
    return {"event_id": event_id, "status": "completed"}


@app.get("/dorm/board/{class_id}")
def dorm_board(class_id: str):
    board = _status_board(class_id)
    return {"class_id": class_id, "board": board,
            "dorm_status": "待接入真实查寝硬件/名单",
            "note": "unknown 状态不会被当作在寝；宿管必须人工确认。"}


@app.post("/dorm/rollcall/{class_id}")
def write_dorm_rollcall(class_id: str, call: DormRollCallCreate):
    ids = students_in_class(class_id)
    if call.class_id != class_id or any(x not in ids for x in call.expected_ids + call.actual_ids):
        raise HTTPException(status_code=403, detail="rollcall contains student outside class scope")
    event_id = insert_event({
        "event_type": "dorm_rollcall", "student_id": "CLASS:" + class_id,
        "payload": {"class_id": class_id, "expected_ids": call.expected_ids,
                    "actual_ids": call.actual_ids, "exceptions": call.exceptions, "note": call.note},
        "source": "dorm_supervisor_workspace",
    })
    write_audit("dorm_supervisor", "dorm.rollcall", "CLASS:" + class_id,
                {"expected": len(call.expected_ids), "actual": len(call.actual_ids),
                 "exceptions": len(call.exceptions)})
    report = f"今日宿舍巡查结束：应查 {len(call.expected_ids)} 人，实到 {len(call.actual_ids)} 人，异常 {len(call.exceptions)} 人。"
    return {"event_id": event_id, "status": "stored", "report": report}

def _class_scoped_events(class_id: str):
    return [e for e in all_events() if e.get("payload", {}).get("class_id") == class_id]


def _schedule_items(class_id: str | None = None):
    out = []
    for e in all_events():
        if e.get("event_type") != "teacher_schedule":
            continue
        p = e.get("payload", {})
        if class_id and class_id != "all" and p.get("class_id") != class_id:
            continue
        out.append({"schedule_event_id": e["event_id"], "teacher_id": p.get("teacher_id"),
                    "teacher_name": p.get("teacher_name", ""), "class_id": p.get("class_id"),
                    "weekday": p.get("weekday"), "start_time": p.get("start_time"),
                    "end_time": p.get("end_time"), "course": p.get("course"),
                    "room": p.get("room", ""), "created_at": e.get("timestamp")})
    return sorted(out, key=lambda x: (x.get("weekday") or 0, x.get("start_time") or ""))


def _minutes(value: str) -> int:
    try:
        h, m = value.split(":")
        return int(h) * 60 + int(m)
    except Exception:
        raise HTTPException(status_code=422, detail="time must be HH:MM")


def _find_schedule_conflict(item: TeacherScheduleCreate):
    start, end = _minutes(item.start_time), _minutes(item.end_time)
    if start >= end:
        raise HTTPException(status_code=422, detail="start_time must be before end_time")
    for existing in _schedule_items():
        if existing["teacher_id"] != item.teacher_id or int(existing["weekday"]) != item.weekday:
            continue
        e_start, e_end = _minutes(existing["start_time"]), _minutes(existing["end_time"])
        if max(start, e_start) < min(end, e_end):
            return existing
    return None


def _head_teacher_performance(class_id: str):
    tasks = _teaching_tasks(class_id)
    report = report_head_teacher(class_id)
    risk_ids = {s["student_id"] for s in report.get("risk_alerts", [])}
    events = _class_scoped_events(class_id)
    notes = [e for e in events if e.get("event_type") == "head_teacher_note"]
    followed_ids = {e.get("student_id") for e in notes}
    task_total = len(tasks)
    task_done = sum(1 for t in tasks if t.get("status") == "completed")
    task_closure = round(task_done / task_total, 4) if task_total else None
    risk_followup = round(min(1.0, len(risk_ids & followed_ids) / len(risk_ids)), 4) if risk_ids else None
    statuses = _student_statuses(class_id)
    known = sum(1 for s in statuses if s["status"] != "unknown")
    status_completeness = round(known / len(statuses), 4) if statuses else None
    documentation_rate = round(min(1.0, len(notes) / max(1, len(risk_ids) + task_total)), 4) if (notes or risk_ids or task_total) else None
    metrics = [
        {"id": "task_closure", "label": "教学任务闭环率", "value": task_closure, "weight": 0.30,
         "source": "teaching_task / teaching_task_update"},
        {"id": "risk_followup", "label": "风险学生事实跟进率", "value": risk_followup, "weight": 0.35,
         "source": "head_teacher_note × risk_alerts"},
        {"id": "status_completeness", "label": "学生状态登记完整率", "value": status_completeness, "weight": 0.20,
         "source": "student_status"},
        {"id": "documentation_rate", "label": "事实记录覆盖率", "value": documentation_rate, "weight": 0.15,
         "source": "head_teacher_note"},
    ]
    available = [m for m in metrics if m["value"] is not None]
    total_weight = sum(m["weight"] for m in available)
    coverage = round(total_weight / sum(m["weight"] for m in metrics), 4)
    score = round(sum((m["value"] or 0) * m["weight"] for m in available) / total_weight * 100, 1) if total_weight else None
    return {
        "class_id": class_id,
        "head_teacher_label": class_id + "班主任",
        "review_period": "最近可用学习/协作事件",
        "score": score if coverage >= 0.5 else None,
        "data_coverage": coverage,
        "level": "可复核" if coverage >= 0.5 else "证据不足",
        "metrics": metrics,
        "workload": {"students": report.get("n_students", 0), "risk_alerts": len(report.get("risk_alerts", [])),
                     "priority_students": len(report.get("priority", [])), "pending_parent_messages": len(report.get("parent_messages", [])),
                     "teaching_tasks": task_total},
        "excluded_dimensions": ["原始对话", "情绪推断", "单一考试分数", "销售续费结果", "未经核实的人格判断"],
        "decision_rule": "仅用于执行校长复核和支持，不自动用于处罚、解雇或公开排名。",
    }


@app.get("/institution/performance/{class_id}")
def institution_performance(class_id: str):
    return _head_teacher_performance(class_id)


@app.get("/institution/schedule")
def institution_schedule(class_id: str = "all"):
    items = _schedule_items(class_id)
    return {"class_id": class_id, "items": items, "count": len(items),
            "note": "排课数据来自 teacher_schedule 事件；没有记录时不伪造课表。"}


@app.post("/institution/schedule")
def create_schedule(item: TeacherScheduleCreate):
    conflict = _find_schedule_conflict(item)
    if conflict:
        raise HTTPException(status_code=409, detail={"message": "teacher schedule conflict", "conflict": conflict})
    event_id = insert_event({
        "event_type": "teacher_schedule", "student_id": "INSTITUTION",
        "payload": item.model_dump(), "source": "institution_schedule",
    })
    write_audit("institution_admin", "institution.schedule.create", event_id,
                {"teacher_id": item.teacher_id, "class_id": item.class_id,
                 "weekday": item.weekday, "start_time": item.start_time, "end_time": item.end_time})
    return {"schedule_event_id": event_id, "status": "stored", "item": item.model_dump()}


@app.get("/institution/teacher-availability/{teacher_id}")
def teacher_availability(teacher_id: str):
    items = [x for x in _schedule_items() if x["teacher_id"] == teacher_id]
    return {"teacher_id": teacher_id, "items": items,
            "note": "这只是已登记排课，不代表教师全部可用时间；正式排课需接入日历。"}

FINANCE_RULES = {
    "teacher_group_rate_per_student_per_session": 70,
    "teacher_one_on_one_tiers": [480, 500, 600],
    "assistant_base_one_class": 3000,
    "assistant_base_two_or_more_classes": 4000,
    "assistant_class_session_tiers": [60, 80, 100, 120],
    "assistant_one_on_one_rate": 100,
    "head_teacher_base": 3000,
    "referral_rate": 0.05,
    "new_student_bonus_range": [1000, 5000],
    "currency": "CNY",
    "settlement_status": "estimate_only",
    "exclusions": ["个税", "社保", "公积金", "加班费", "考勤扣款", "退费冲减", "跨月结算", "地区最低工资校验"],
}


@app.get("/institution/finance/rules")
def finance_rules():
    return {"rules": FINANCE_RULES,
            "note": "这里是薪酬预算计算规则，不是最终工资单；实际结算需财务/HR/法务确认。"}


@app.post("/institution/finance/estimate")
def estimate_finance(x: FinanceEstimateInput):
    if x.one_on_one_tier not in FINANCE_RULES["teacher_one_on_one_tiers"]:
        raise HTTPException(status_code=422, detail="teacher one-on-one tier must be 480, 500 or 600")
    teacher_group_pay = round(x.group_students * x.group_sessions * 70, 2)
    teacher_one_on_one_pay = round(x.one_on_one_sessions * x.one_on_one_tier, 2)
    assistant_base = 0 if x.assistant_class_count <= 0 else (3000 if x.assistant_class_count == 1 else 4000)
    assistant_class_pay = round(
        x.assistant_sessions_60 * 60 + x.assistant_sessions_80 * 80 +
        x.assistant_sessions_100 * 100 + x.assistant_sessions_120 * 120, 2)
    assistant_one_on_one_pay = round(x.assistant_one_on_one_sessions * 100, 2)
    referral_pay = round(x.referral_payment_base * 0.05, 2)
    new_student_pay = round(x.new_student_count * x.new_student_bonus_per_person, 2)
    teacher_total = round(teacher_group_pay + teacher_one_on_one_pay, 2)
    assistant_total = round(assistant_base + assistant_class_pay + assistant_one_on_one_pay, 2)
    head_teacher_total = round(3000 + referral_pay + new_student_pay, 2)
    grand_total = round(teacher_total + assistant_total + head_teacher_total, 2)
    return {
        "currency": "CNY",
        "settlement_status": "estimate_only",
        "teacher": {
            "group_pay": teacher_group_pay,
            "group_formula": f"{x.group_students} 人 × {x.group_sessions} 节 × 70 元",
            "one_on_one_pay": teacher_one_on_one_pay,
            "one_on_one_formula": f"{x.one_on_one_sessions} 节 × {x.one_on_one_tier} 元",
            "total": teacher_total,
        },
        "assistant": {
            "base": assistant_base,
            "class_session_pay": assistant_class_pay,
            "class_session_formula": f"60档 {x.assistant_sessions_60} 节 + 80档 {x.assistant_sessions_80} 节 + 100档 {x.assistant_sessions_100} 节 + 120档 {x.assistant_sessions_120} 节，不按人头计算",
            "one_on_one_pay": assistant_one_on_one_pay,
            "one_on_one_formula": f"{x.assistant_one_on_one_sessions} 节 × 100 元",
            "total": assistant_total,
        },
        "head_teacher": {
            "base": 3000,
            "referral_pay": referral_pay,
            "referral_formula": f"{x.referral_payment_base} 元 × 5%",
            "new_student_pay": new_student_pay,
            "new_student_formula": f"{x.new_student_count} 人 × {x.new_student_bonus_per_person} 元",
            "total": head_teacher_total,
        },
        "grand_total": grand_total,
        "assumptions": ["班课教师 70 元/人/节", "教师 1 对 1 仅允许 480/500/600 元/节",
                        "助教 1 个班底薪 3000，2 个及以上班底薪 4000", "助教班课按 60/80/100/120 档位/节，不按人头",
                        "班主任底薪 3000", "转介绍按付费 5%", "拉新按 1000—5000 元/人"],
        "exclusions": FINANCE_RULES["exclusions"],
        "note": "预算结果仅供内部测算，不构成工资承诺；实际结算需财务、HR 和法务复核。",
    }

WORKFLOW_STAGES = [
    {"id": "discovery", "label": "业务熟悉 / 需求发现"},
    {"id": "business_review", "label": "业务评审"},
    {"id": "design", "label": "需求设计"},
    {"id": "tech_review", "label": "技术评审"},
    {"id": "ui_review", "label": "UI / 交互评审"},
    {"id": "acceptance", "label": "功能验收"},
    {"id": "launch", "label": "上线与回滚"},
    {"id": "retro", "label": "数据 / 事故复盘"},
]


def _workflow_events():
    return [e for e in all_events() if e.get("student_id") == "WORKFLOW"]


def _workflow_board():
    events = _workflow_events()
    requirements, reviews, incidents, delays, acceptances = [], [], [], [], []
    for e in events:
        p = e.get("payload", {})
        if e.get("event_type") == "workflow_requirement":
            requirements.append({"requirement_id": e["event_id"], **p, "created_at": e.get("timestamp"),
                                 "status": "draft"})
        elif e.get("event_type") == "workflow_review":
            reviews.append({"review_id": e["event_id"], **p, "created_at": e.get("timestamp")})
        elif e.get("event_type") == "workflow_incident":
            incidents.append({"incident_id": e["event_id"], **p, "created_at": e.get("timestamp")})
        elif e.get("event_type") == "workflow_delay":
            delays.append({"delay_id": e["event_id"], **p, "created_at": e.get("timestamp")})
        elif e.get("event_type") == "workflow_acceptance":
            acceptances.append({"acceptance_id": e["event_id"], **p, "created_at": e.get("timestamp")})
    for req in requirements:
        related = [r for r in reviews if r.get("requirement_id") == req["requirement_id"]]
        if related:
            req["status"] = "in_review"
        if any(r.get("review_type") in ("business", "tech") and r.get("decision") == "approved" for r in related):
            req["status"] = "reviewed"
    reviewed_types = {r.get("review_type") for r in reviews if r.get("decision") == "approved"}
    accepted = any(a.get("conclusion") == "approved" for a in acceptances)
    stage_status = {
        "discovery": "done" if requirements else "pending",
        "business_review": "done" if "business" in reviewed_types else "pending",
        "design": "done" if requirements else "pending",
        "tech_review": "done" if "tech" in reviewed_types else "pending",
        "ui_review": "done" if "ui" in reviewed_types else "pending",
        "acceptance": "done" if acceptances else "pending",
        "launch": "done" if accepted else "pending",
        "retro": "done" if any("复盘" in (x.get("title", "") + x.get("reason", "")) for x in incidents + delays) else "pending",
    }
    return {
        "stages": [{**s, "status": stage_status.get(s["id"], "pending")} for s in WORKFLOW_STAGES],
        "requirements": sorted(requirements, key=lambda x: x.get("created_at") or "", reverse=True),
        "reviews": sorted(reviews, key=lambda x: x.get("created_at") or "", reverse=True),
        "incidents": sorted(incidents, key=lambda x: x.get("created_at") or "", reverse=True),
        "delays": sorted(delays, key=lambda x: x.get("created_at") or "", reverse=True),
        "acceptances": sorted(acceptances, key=lambda x: x.get("created_at") or "", reverse=True),
        "counts": {"requirements": len(requirements), "reviews": len(reviews),
                   "incidents": len(incidents), "delays": len(delays),
                   "acceptances": len(acceptances), "pending_reviews": sum(1 for r in requirements if r["status"] != "reviewed")},
        "note": "工作流数据来自 DAOQL；AI 输出不能替代人工评审和验收。",
    }


@app.get("/workflow/board")
def workflow_board():
    return _workflow_board()


@app.post("/workflow/requirements")
def create_workflow_requirement(req: WorkflowRequirementCreate):
    event_id = insert_event({"event_type": "workflow_requirement", "student_id": "WORKFLOW",
                             "payload": req.model_dump(), "source": "pm_workflow"})
    write_audit("product", "workflow.requirement.create", event_id, {"title": req.title})
    return {"requirement_id": event_id, "status": "stored"}


@app.post("/workflow/reviews")
def create_workflow_review(review: WorkflowReviewCreate):
    if review.review_type not in ("business", "tech", "ui", "acceptance", "risk"):
        raise HTTPException(status_code=422, detail="invalid review_type")
    event_id = insert_event({"event_type": "workflow_review", "student_id": "WORKFLOW",
                             "payload": review.model_dump(), "source": "pm_workflow"})
    write_audit("reviewer", "workflow.review.create", review.requirement_id,
                {"review_type": review.review_type, "decision": review.decision})
    return {"review_id": event_id, "status": "stored"}


@app.post("/workflow/incidents")
def create_workflow_incident(incident: WorkflowIncidentCreate):
    event_id = insert_event({"event_type": "workflow_incident", "student_id": "WORKFLOW",
                             "payload": incident.model_dump(), "source": "pm_workflow"})
    write_audit("product", "workflow.incident.create", event_id, {"severity": incident.severity})
    return {"incident_id": event_id, "status": "stored"}


@app.post("/workflow/delays")
def create_workflow_delay(delay: WorkflowDelayCreate):
    event_id = insert_event({"event_type": "workflow_delay", "student_id": "WORKFLOW",
                             "payload": delay.model_dump(), "source": "pm_workflow"})
    write_audit("product", "workflow.delay.create", event_id, {"owner": delay.owner})
    return {"delay_id": event_id, "status": "stored"}


@app.post("/workflow/acceptance")
def create_workflow_acceptance(acceptance: WorkflowAcceptanceCreate):
    event_id = insert_event({"event_type": "workflow_acceptance", "student_id": "WORKFLOW",
                             "payload": acceptance.model_dump(), "source": "pm_workflow"})
    write_audit("product", "workflow.acceptance.create", event_id, {"release_name": acceptance.release_name})
    return {"acceptance_id": event_id, "status": "stored"}


ADVISOR_ROLES = {"health_advisor", "nutrition_advisor", "neurocognitive_advisor", "psychology_advisor", "learning_science_advisor", "career_advisor", "safety_advisor"}

def _advisor_payload(role_id: str, student_id: str, class_id: str) -> dict:
    events = list_events(student_id)
    state = compute_state(student_id, events)
    repo_root = pathlib.Path(__file__).resolve().parents[2]
    report_path = repo_root / "experiments" / "advisor_bench" / "outputs" / "advisor_metrics.json"
    report = json.loads(report_path.read_text(encoding="utf-8")) if report_path.exists() else {}
    career_safety_path = repo_root / "experiments" / "advisor_bench" / "outputs" / "career_safety_metrics.json"
    career_safety = json.loads(career_safety_path.read_text(encoding="utf-8")) if career_safety_path.exists() else {}
    evidence = {"event_count": len(events), "knowledge": state.get("knowledge", {}), "metacognition": state.get("metacognition", {}),
                "rhythm": state.get("baseline", {}).get("rhythm", {}), "class_id": class_id}
    common = {"model_status": "public_data_baseline_requires_local_calibration", "evidence": evidence}
    if role_id == "health_advisor":
        metrics = report.get("health_advisor", {}).get("metrics", {})
        return {**common, "title": "健康顾问工作台", "signal": "睡眠、活动与膳食相关的高血压筛查代理",
                "metrics": metrics, "tier": "awaiting_health_logs",
                "recommendations": ["先记录睡眠与活动趋势", "异常血压需要复测，不由系统诊断", "涉及症状时转介校医或医生"],
                "boundary": "筛查代理，不是诊断，不替代血压测量或医疗建议"}
    if role_id == "nutrition_advisor":
        metrics = report.get("nutrition_advisor", {}).get("metrics", {})
        return {**common, "title": "营养顾问工作台", "signal": "纤维、钠、钾和添加糖构成的 0–100 营养模式评分",
                "metrics": metrics, "tier": "awaiting_diet_recall",
                "recommendations": ["优先选择一个可执行替换", "记录两日膳食再评分", "不把评分当作疾病诊断"],
                "boundary": "营养模式评分，不是医学营养治疗"}
    if role_id == "neurocognitive_advisor":
        profiles = report.get("neurocognitive_advisor", {}).get("cluster_profiles", [])
        return {**common, "title": "神经认知顾问工作台", "signal": "记忆、执行功能与注意画像",
                "profiles": profiles, "tier": "profile_requires_assessment",
                "recommendations": ["先调整任务负荷与提示层级", "不以单次测试贴标签", "明显异常转介专业评估"],
                "boundary": "研究型认知画像，不是神经心理诊断"}
    if role_id == "psychology_advisor":
        profiles = report.get("psychology_advisor", {}).get("cluster_profiles", [])
        return {**common, "title": "心理学顾问工作台", "signal": "压力、情绪与求助支持的问卷相关信号",
                "profiles": profiles, "tier": "support_signal_requires_human_review",
                "recommendations": ["使用支持性访谈，不使用诊断标签", "提供低压力求助入口", "出现安全风险立即升级给专业人员"],
                "boundary": "支持分级，不是临床诊断"}
    if role_id == "career_advisor":
        return {**common, "title": "生涯与职业顾问工作台", "signal": "学习护照、能力证据、兴趣和职业要求的路径探索", "metrics": career_safety.get("career_advisor", {}),
                "tier": "exploration_required",
                "recommendations": ["先明确目标方向与约束", "盘点可验证能力证据", "对比目标方向的要求和差距", "用小项目或信息访谈验证假设"],
                "boundary": "不承诺就业、不替用户决定人生、不把测评当作职业定论"}
    if role_id == "safety_advisor":
        return {**common, "title": "安全与保护顾问工作台", "signal": "霸凌、诈骗、不当关系、自伤和突发安全风险", "metrics": career_safety.get("safety_advisor", {}),
                "tier": "human_escalation_ready",
                "recommendations": ["有即时危险时先保护当事人并联系监护人或学校安全负责人", "紧急危险联系 110/120 或当地急救", "记录事实和时间线，避免公开传播敏感信息", "由受过培训的成人进行调查和处置"],
                "boundary": "不做案件调查、不做心理诊断、不替代警方、学校或医疗机构"}
    fusion = report.get("learning_science_advisor", {})
    return {**common, "title": "学习科学顾问工作台", "signal": "Tender 状态 + RoleMind + 四类专业顾问的整合解释", "tier": "explanation_requires_human_review",
            "fusion_config": fusion, "tender_state": state,
            "recommendations": ["先解释证据和不确定性，再给下一步", "量子认知是建模语法，不宣称真实量子效应", "高影响建议必须由教师或专业人员复核"],
            "boundary": "整合解释，不替代教师、心理老师或医生"}

@app.get("/roles/{role_id}/home")
def role_home(role_id: str, student_id: str = "S01", class_id: str = "理科班",
              teacher_mode: str = "independent"):
    """按角色返回不同数据范围的最小工作台载荷。"""
    role_id = {"tutor": "teacher", "subject_teacher": "teacher", "dorm_supervisor": "health_advisor"}.get(role_id, role_id)
    teacher_mode = teacher_mode if teacher_mode in {"independent", "institution"} else "independent"
    role = next((r for r in ROLE_APPS if r["id"] == role_id), None)
    if role is None:
        raise HTTPException(status_code=404, detail="unknown role")
    if role_id == "learner":
        data = {"learner": learner_home(student_id)}
    elif role_id == "parent":
        data = {"parent_report": parent_report(compute_state(student_id, list_events(student_id))),
                "child": learner_home(student_id)}
    elif role_id == "teacher":
        ids = students_in_class(class_id)
        states = [compute_state(sid, list_events(sid)) for sid in ids]
        mode_meta = next(m for m in role["modes"] if m["id"] == teacher_mode)
        data = {"teacher_mode": teacher_mode,
                "teacher_mode_meta": mode_meta,
                "teacher_report": teacher_report(states),
                "tasks": _teaching_tasks(class_id),
                "status_board": _status_board(class_id),
                "students": ids,
                "sample_learner": learner_home(student_id)}
    elif role_id in ADVISOR_ROLES:
        data = {"advisor": _advisor_payload(role_id, student_id, class_id), "status_board": _status_board(class_id)}
    elif role_id == "head_teacher":
        data = {"head_teacher": report_head_teacher(class_id)}
    elif role_id == "institution":
        data = {"overview": overview(), "org_report": report_org(),
                "performance": [_head_teacher_performance("理科班"), _head_teacher_performance("文科班")],
                "schedule": _schedule_items("all"), "finance_rules": FINANCE_RULES, "workflow": _workflow_board()}
    elif role_id == "sales":
        data = {"sales": sales_ammunition(class_id)}
    else:
        data = {}
    return {
        "role": role,
        "context": {"student_id": student_id, "class_id": class_id, "teacher_mode": teacher_mode if role_id == "teacher" else None},
        "data": data,
        "rbac_status": "preview_only",
        "note": "角色界面已拆分；生产环境需要服务端鉴权、最小权限和审计。",
    }
app.mount("/ui", StaticFiles(directory=str(STATIC), html=True), name="ui")
if GUIDE.exists():
    app.mount("/guide", StaticFiles(directory=str(GUIDE), html=True), name="guide")


@app.get("/")
def root():
    return RedirectResponse("/ui/")
