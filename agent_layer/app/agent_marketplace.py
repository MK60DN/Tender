# -*- coding: utf-8 -*-
"""Expert-agent factory and marketplace for the C-end Tender app."""
from __future__ import annotations
import hashlib, json, sqlite3, pathlib, uuid
from datetime import datetime, timezone
from typing import Any

from .agent_runtime import execute_agent
from .daoql import write_audit

DB = pathlib.Path(__file__).resolve().parent.parent / "tender_agent.db"


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat()


def _conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


def init_db() -> None:
    with _conn() as c:
        c.execute("""
        CREATE TABLE IF NOT EXISTS expert_agents (
            agent_id TEXT PRIMARY KEY,
            owner_id TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            category TEXT NOT NULL,
            price_cents INTEGER NOT NULL DEFAULT 0,
            currency TEXT NOT NULL DEFAULT 'CNY',
            visibility TEXT NOT NULL DEFAULT 'private',
            status TEXT NOT NULL DEFAULT 'draft',
            spec_json TEXT NOT NULL,
            version TEXT NOT NULL DEFAULT '0.1.0',
            safety_rating REAL NOT NULL DEFAULT 0.0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """)
        c.execute("""
        CREATE TABLE IF NOT EXISTS agent_purchases (
            purchase_id TEXT PRIMARY KEY,
            agent_id TEXT NOT NULL,
            buyer_id TEXT NOT NULL,
            seller_id TEXT NOT NULL,
            price_cents INTEGER NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(agent_id, buyer_id)
        )
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_expert_agents_market ON expert_agents(visibility,status,category)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_agent_purchases_buyer ON agent_purchases(buyer_id,created_at)")


FIXED_AGENTS = [
    {
        "agent_id": "fixed_mentalization_companion",
        "name": "心智化陪伴",
        "category": "mentalization",
        "description": "持续解释此刻的认知状态、情绪上下文与可能卡点，并给出最低必要支持。",
        "data_scopes": ["self_reflection", "authorized_summary", "aggregated_tender_state"],
        "always_on": True,
    },
    {
        "agent_id": "fixed_cognition_emotion_regulator",
        "name": "认知—情绪调节",
        "category": "emotion_cognition",
        "description": "当情绪负荷可能占用学习资源时，调整任务粒度、节奏与恢复方式。",
        "data_scopes": ["self_reflection", "emotion_context", "authorized_summary"],
        "always_on": True,
    },
    {
        "agent_id": "fixed_reflection_coach",
        "name": "反思教练",
        "category": "metacognition",
        "description": "用一次一个的问题帮助用户校准预测、策略与真实表现。",
        "data_scopes": ["self_reflection", "metacognition_summary"],
        "always_on": True,
    },
    {
        "agent_id": "fixed_family_bridge",
        "name": "家庭桥接",
        "category": "family_support",
        "description": "把个人记录转成经授权的最小必要支持摘要，默认不共享原始对话。",
        "data_scopes": ["approved_family_summary"],
        "always_on": True,
    },
    {
        "agent_id": "fixed_safety_guardian",
        "name": "安全与保护",
        "category": "safety",
        "description": "后台常驻识别高风险信号，按规则转人工支持，不承担案件调查。",
        "data_scopes": ["minimal_safety_signals"],
        "always_on": True,
    },
]

CATEGORY_KEYWORDS = {
    "learning_support": ["学习", "计划", "策略", "效率", "拖延", "复习", "安排"],
    "metacognition": ["元认知", "预测", "复盘", "反思", "不确定", "以为自己会"],
    "emotion_cognition": ["焦虑", "紧张", "压力", "挫败", "疲惫", "走神", "情绪"],
    "psychology": ["心理", "心理咨询", "情绪困扰", "求助", "支持性访谈", "心理教育"],
    "family_support": ["家庭", "父母", "沟通", "冲突", "陪伴", "监护"],
    "career": ["职业", "生涯", "转行", "发展", "实习", "选择"],
    "health": ["睡眠", "活动", "恢复", "头痛", "健康", "心率"],
    "nutrition": ["饮食", "营养", "早餐", "糖", "蔬菜", "体重"],
    "neurocognitive": ["注意", "工作记忆", "执行", "专注", "认知负荷"],
    "safety": ["霸凌", "诈骗", "威胁", "自伤", "自杀", "不当接触"],
}


HIGH_RISK_CATEGORIES = {"safety", "health", "psychology", "nutrition"}


def _infer_category(need: str, requested: str | None = None) -> str:
    if requested and requested != "auto":
        if requested not in CATEGORY_KEYWORDS:
            raise ValueError("unsupported agent category")
        return requested
    text = need or ""
    best, score = "learning_support", 0
    for category, words in CATEGORY_KEYWORDS.items():
        current = sum(1 for word in words if word in text)
        if current > score:
            best, score = category, current
    return best


def generate_agent_spec(owner_id: str, need: str, category: str = "auto") -> dict:
    resolved = _infer_category(need, category)
    return {
        "spec_version": "1.0",
        "agent_id": "draft_" + uuid.uuid4().hex[:10],
        "owner_id": owner_id,
        "category": resolved,
        "mission": need.strip(),
        "trigger": {
            "type": "intent_or_state_threshold",
            "examples": ["用户主动请求", "相关状态连续出现", "用户授权摘要进入"],
        },
        "inputs": {
            "default": ["authorized_summary", "self_reflection"],
            "optional": ["aggregated_tender_state", "emotion_context"],
            "never_default": ["raw_conversation", "other_learner_data"],
        },
        "tools": ["reflection_prompt", "support_plan", "state_explanation"],
        "output_schema": {
            "summary": "string",
            "evidence_refs": "array[string]",
            "confidence": "number",
            "next_action": "string",
            "boundary": "string",
        },
        "approval": {
            "human_review_required": resolved in HIGH_RISK_CATEGORIES,
            "seller_certification_required": resolved in HIGH_RISK_CATEGORIES,
        },
        "prohibited": [
            "clinical diagnosis",
            "fixed personality labels",
            "raw conversation sharing",
            "unauthorized data access",
            "claims of guaranteed outcomes",
        ],
        "evaluation": [
            "evidence citation rate",
            "user correction rate",
            "safety escalation precision",
            "support usefulness feedback",
        ],
        "sandbox": {"status": "required", "fallback": "fixed_mentalization_companion"},
    }


def create_expert_agent(owner_id: str, need: str, name: str = "", description: str = "",
                        category: str = "auto", price_cents: int = 0,
                        visibility: str = "private") -> dict:
    init_db()
    if not owner_id.strip():
        raise ValueError("owner_id is required")
    if not need.strip():
        raise ValueError("need is required")
    if price_cents < 0:
        raise ValueError("price_cents must be >= 0")
    visibility = visibility if visibility in {"private", "unlisted", "marketplace"} else "private"
    spec = generate_agent_spec(owner_id, need, category)
    agent_id = "agent_" + uuid.uuid4().hex[:12]
    now = _now()
    resolved_name = name.strip() or f"{spec['category']} 专家 Agent"
    desc = description.strip() or need.strip()[:240]
    high_risk = spec["category"] in HIGH_RISK_CATEGORIES
    safety_rating = 0.60 if high_risk else 0.72
    status = "pending_review" if visibility == "marketplace" and high_risk else ("published" if visibility == "marketplace" else "draft")
    with _conn() as c:
        c.execute(
            "INSERT INTO expert_agents(agent_id,owner_id,name,description,category,price_cents,currency,visibility,status,spec_json,version,safety_rating,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (agent_id, owner_id, resolved_name, desc, spec["category"], int(price_cents), "CNY",
             visibility, status, json.dumps(spec, ensure_ascii=False), "0.1.0", safety_rating, now, now),
        )
    return get_agent(agent_id)


def _decode(row: sqlite3.Row) -> dict:
    d = dict(row)
    d["spec"] = json.loads(d.pop("spec_json") or "{}")
    d["price"] = round(d["price_cents"] / 100.0, 2)
    d["currency"] = d.get("currency", "CNY")
    return d


def get_agent(agent_id: str) -> dict:
    init_db()
    with _conn() as c:
        row = c.execute("SELECT * FROM expert_agents WHERE agent_id=?", (agent_id,)).fetchone()
    if not row:
        raise KeyError("agent not found")
    return _decode(row)


def list_marketplace(query: str = "", category: str = "") -> dict:
    init_db()
    sql = "SELECT * FROM expert_agents WHERE visibility='marketplace' AND status='published'"
    args: list[Any] = []
    if category:
        sql += " AND category=?"
        args.append(category)
    if query:
        sql += " AND (name LIKE ? OR description LIKE ? OR category LIKE ?)"
        q = f"%{query}%"
        args.extend([q, q, q])
    sql += " ORDER BY safety_rating DESC, created_at DESC LIMIT 100"
    with _conn() as c:
        rows = c.execute(sql, args).fetchall()
    return {"fixed_agents": FIXED_AGENTS, "expert_agents": [_decode(r) for r in rows],
            "note": "专家 Agent 默认只访问授权摘要；购买是能力授权，不转移模型权重或原始数据。"}


def _purchase_payload(row: Any, agent: dict, already_owned: bool) -> dict:
    price_cents = int(row["price_cents"])
    seller_share = int(round(price_cents * 0.8))
    platform_share = price_cents - seller_share
    return {
        "purchase_id": row["purchase_id"],
        "agent_id": row["agent_id"],
        "buyer_id": row["buyer_id"],
        "seller_id": row["seller_id"],
        "price": round(price_cents / 100.0, 2),
        "seller_share": round(seller_share / 100.0, 2),
        "platform_share": round(platform_share / 100.0, 2),
        "payment_status": row["status"],
        "license_status": "active" if row["status"] in {"simulated_paid", "active"} else row["status"],
        "data_scope": "authorized_summary_only",
        "already_owned": already_owned,
    }


def purchase_agent(agent_id: str, buyer_id: str) -> dict:
    init_db()
    if not (buyer_id or "").strip():
        raise ValueError("buyer_id is required")
    agent = get_agent(agent_id)
    if buyer_id == agent["owner_id"]:
        raise ValueError("owner cannot purchase own agent")
    if agent["visibility"] != "marketplace" or agent["status"] != "published":
        raise ValueError("agent is not available in marketplace")
    with _conn() as c:
        existing = c.execute(
            "SELECT * FROM agent_purchases WHERE agent_id=? AND buyer_id=?",
            (agent_id, buyer_id),
        ).fetchone()
        if existing:
            return _purchase_payload(existing, agent, already_owned=True)
        purchase_id = "purchase_" + uuid.uuid4().hex[:12]
        created_at = _now()
        try:
            c.execute(
                "INSERT INTO agent_purchases(purchase_id,agent_id,buyer_id,seller_id,price_cents,status,created_at) VALUES(?,?,?,?,?,?,?)",
                (purchase_id, agent_id, buyer_id, agent["owner_id"], agent["price_cents"], "simulated_paid", created_at),
            )
        except sqlite3.IntegrityError:
            row = c.execute(
                "SELECT * FROM agent_purchases WHERE agent_id=? AND buyer_id=?",
                (agent_id, buyer_id),
            ).fetchone()
            if row is None:
                raise
            return _purchase_payload(row, agent, already_owned=True)
        row = c.execute("SELECT * FROM agent_purchases WHERE purchase_id=?", (purchase_id,)).fetchone()
    return _purchase_payload(row, agent, already_owned=False)


def list_entitlements(buyer_id: str) -> dict:
    init_db()
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM agent_purchases WHERE buyer_id=? AND status IN ('simulated_paid','active') ORDER BY created_at DESC",
            (buyer_id,),
        ).fetchall()
    items = []
    for row in rows:
        item = dict(row)
        try:
            agent = get_agent(item["agent_id"])
            item["agent"] = {k: agent[k] for k in ("agent_id", "name", "description", "category", "version", "owner_id", "safety_rating")}
        except KeyError:
            item["agent"] = None
        items.append(item)
    return {"buyer_id": buyer_id, "fixed_agents": FIXED_AGENTS, "purchased_agents": items}


def has_agent_access(agent_id: str, user_id: str) -> bool:
    agent = get_agent(agent_id)
    if not (user_id or "").strip():
        return False
    if agent["owner_id"] == user_id:
        return True
    if agent["visibility"] != "marketplace" or agent["status"] != "published":
        return False
    with _conn() as c:
        row = c.execute(
            "SELECT 1 FROM agent_purchases WHERE agent_id=? AND buyer_id=? AND status IN ('simulated_paid','active')",
            (agent_id, user_id),
        ).fetchone()
    return bool(row)


def get_agent_for_viewer(agent_id: str, actor_id: str | None = None) -> dict:
    """Return a private agent only to its owner; public agents remain discoverable."""
    agent = get_agent(agent_id)
    if actor_id and agent["owner_id"] == actor_id:
        return agent
    if agent["visibility"] == "marketplace" and agent["status"] == "published":
        return agent
    raise PermissionError("agent is not available")


def _authorized_tender_summary(tender_state: dict) -> dict:
    """Build the only state object an expert agent may receive by default."""
    state = tender_state or {}
    knowledge = state.get("knowledge", {}) or {}
    meta = state.get("metacognition", {}) or {}
    emotion = state.get("emotion", {}) or {}
    baseline = state.get("baseline", {}) or {}
    cognitive = state.get("cognitive", {}) or {}

    def number(value):
        try:
            return round(float(value), 4)
        except (TypeError, ValueError):
            return None

    summary = {
        "scope": "authorized_summary_only",
        "knowledge": {"mastery": number(knowledge.get("mastery"))},
        "metacognition": {
            "jol_bias": number(meta.get("jol_bias")),
            "hesitation": number(meta.get("hesitation")),
            "uncertainty": number(cognitive.get("uncertainty")),
        },
        "emotion_context": {
            "valence": number(emotion.get("valence")),
            "arousal": number(emotion.get("arousal")),
            "confidence": number(emotion.get("confidence")),
            "label": emotion.get("label"),
        },
        "baseline": {"arrangement_fit": number(baseline.get("arrangement_fit"))},
        "event_count": int(state.get("n_events", 0) or 0),
        "state_timestamp": state.get("timestamp"),
    }
    return summary


def invoke_expert_agent(agent_id: str, actor_id: str, message: str, tender_state: dict) -> dict:
    """Execute a purchased expert agent with an authorized, minimized state summary."""
    agent = get_agent(agent_id)
    if not has_agent_access(agent_id, actor_id):
        write_audit(
            "agent_marketplace:" + (actor_id or "anonymous"),
            "agent.invoke.denied",
            agent_id,
            {"reason": "agent_license_required", "message_chars": len(message or "")},
        )
        raise PermissionError("agent license is required")

    spec = agent["spec"]
    summary = _authorized_tender_summary(tender_state)
    mastery = float(summary["knowledge"].get("mastery") or 0.5)
    jol_bias = float(summary["metacognition"].get("jol_bias") or 0.0)
    hesitation = float(summary["metacognition"].get("hesitation") or 0.0)
    next_action = "先确认卡点，再给一个最小支持"
    if abs(jol_bias) >= 0.15:
        next_action = "先预测、再作答、后复盘，比较预测与实际"
    elif hesitation >= 0.55:
        next_action = "把任务拆成更小一步，并保留短暂恢复"
    elif mastery < 0.55:
        next_action = "先确认缺失连接，再用最小提示继续"

    evidence_refs = []
    for key in ("event_id", "timestamp"):
        value = tender_state.get(key)
        if value:
            evidence_refs.append(str(value))

    runtime_text = None
    runtime_meta = {
        "provider": "agent-runtime",
        "model": None,
        "fallback_used": False,
        "fallback_reason": None,
    }
    try:
        cfg = {
            "id": agent_id,
            "role": spec.get("mission", agent.get("description", "专家 Agent")),
            "tools": spec.get("tools", []),
            "policy": spec.get("approval", {}),
            "input": spec.get("inputs", {}),
            "output": spec.get("output_schema", {}),
        }
        out = execute_agent(
            cfg,
            message or "请给出一个最低必要支持。",
            summary,
            {"spec": spec, "data_scope": "authorized_summary_only"},
        )
        runtime_text = out.get("text")
        runtime_meta = {
            "provider": "agent-runtime",
            "model": out.get("model"),
            "fallback_used": False,
            "fallback_reason": None,
        }
    except Exception:
        runtime_meta = {
            "provider": "agent-runtime",
            "model": None,
            "fallback_used": True,
            "fallback_reason": "agent_runtime_unavailable",
        }

    result = {
        "from_agent": agent_id,
        "agent_type": "expert_marketplace",
        "owner_id": agent["owner_id"],
        "actor_id": actor_id,
        "action": {
            "summary": f"按 {agent['category']} AgentSpec 生成学习支持建议",
            "next_action": next_action,
            "text": runtime_text or next_action,
            "evidence_refs": evidence_refs,
            "confidence": 0.60,
            "boundary": "不构成心理或医学诊断；不访问未授权原始对话。",
        },
        "llm": runtime_meta,
        "spec": {
            "version": spec.get("spec_version"),
            "inputs": spec.get("inputs"),
            "output_schema": spec.get("output_schema"),
            "prohibited": spec.get("prohibited"),
        },
        "license": {
            "actor_id": actor_id,
            "status": "active",
            "data_scope": "authorized_summary_only",
        },
        "status": "proposed",
    }
    write_audit(
        "agent_marketplace:" + actor_id,
        "agent.invoke",
        agent_id,
        {
            "message_chars": len(message or ""),
            "message_sha256": hashlib.sha256((message or "").encode("utf-8")).hexdigest(),
            "fallback_used": runtime_meta["fallback_used"],
            "fallback_reason": runtime_meta["fallback_reason"],
        },
    )
    return result
