"""Codex-style multi-agent workbench for Tender.

This module persists task threads, agent runs, artifacts, approvals and handoffs.
It is a deterministic MVP that can later be replaced by real LLM/tool execution.
"""
from __future__ import annotations

import json
import pathlib
import sqlite3
import uuid
from datetime import datetime, timezone

from .daoql import insert_event, write_audit

DB = pathlib.Path(__file__).resolve().parent.parent / "tender_agent.db"

AGENT_CATALOG = [
    {"id": "coordinator", "name": "协调者", "scope": "拆解任务、分派、汇总、等待审批", "can_act": False},
    {"id": "content_curator", "name": "内容 Agent", "scope": "题库、讲义、重点词汇和句型抽取", "can_act": False},
    {"id": "assessment", "name": "评估 Agent", "scope": "批改、错因统计和学生状态更新", "can_act": False},
    {"id": "student_tutor", "name": "学生教练", "scope": "最小提示、复盘和复习安排", "can_act": False},
    {"id": "external_communication", "name": "对外沟通 Agent", "scope": "按接收方角色生成待审批的沟通草稿", "can_act": False},
    {"id": "safety_guardrail", "name": "安全护栏", "scope": "隐私、排名、越权和高风险语言检查", "can_act": False},
]

AUDIENCE_PROFILES = {
    "parent": {
        "label": "家长", "artifact_title": "成长周报草稿", "tone": "清晰、克制、不制造焦虑",
        "labels": ["完成情况", "已修复", "下一步建议"],
        "focus": ["学习投入", "重复错误", "家庭支持方式"],
        "privacy": ["不含排名", "不含其他学生信息", "不推断家庭责任"],
    },
    "mentor": {
        "label": "导师", "artifact_title": "导师同步草稿", "tone": "具体、诚实、聚焦问题",
        "labels": ["当前目标", "当前卡点", "请求支持"],
        "focus": ["目标", "障碍", "需要的指导"],
        "privacy": ["不含无关私生活", "不夸大成果"],
    },
    "employer": {
        "label": "用人单位", "artifact_title": "能力证据摘要", "tone": "结果导向、证据优先",
        "labels": ["学习投入", "已展示能力", "可迁移到工作"],
        "focus": ["可靠性", "问题解决", "协作证据"],
        "privacy": ["只提供授权证据", "不披露成绩排名"],
    },
    "admissions": {
        "label": "招生面试官", "artifact_title": "学习档案摘要", "tone": "真实、结构化、突出成长轨迹",
        "labels": ["学习轨迹", "项目证据", "下一步计划"],
        "focus": ["持续投入", "项目作品", "反思能力"],
        "privacy": ["不使用未经授权材料", "不虚构成果"],
    },
    "collaborator": {
        "label": "合作者", "artifact_title": "协作交接摘要", "tone": "简洁、行动导向",
        "labels": ["当前进度", "依赖", "交接事项"],
        "focus": ["任务状态", "风险", "下一步"],
        "privacy": ["只共享与协作相关信息"],
    },
    "client": {
        "label": "客户", "artifact_title": "学习服务报告", "tone": "透明、专业、不承诺提分",
        "labels": ["交付内容", "证据", "下一步"],
        "focus": ["服务完成度", "学习证据", "后续安排"],
        "privacy": ["不泄露其他客户信息", "不承诺未经验证的结果"],
    },
    "custom": {
        "label": "自定义对象", "artifact_title": "对外沟通草稿", "tone": "按配置生成",
        "labels": ["目标", "证据", "下一步"],
        "focus": ["沟通目的", "可验证证据", "期望回应"],
        "privacy": ["最小必要", "人工审批", "不越权"],
    },
}


def audience_profile(audience_role: str) -> dict:
    key = (audience_role or "parent").lower()
    return {"id": key, **AUDIENCE_PROFILES.get(key, AUDIENCE_PROFILES["custom"])}


def _conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat()


def _id(prefix: str) -> str:
    return prefix + "_" + uuid.uuid4().hex[:12]


def init_db():
    with _conn() as c:
        c.execute("""
        CREATE TABLE IF NOT EXISTS agent_threads (
            thread_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            objective TEXT NOT NULL,
            student_id TEXT NOT NULL,
            class_id TEXT NOT NULL,
            task_type TEXT NOT NULL,
            created_by_role TEXT NOT NULL,
            audience_role TEXT NOT NULL DEFAULT 'parent',
            audience_config_json TEXT NOT NULL DEFAULT '{}',
            status TEXT NOT NULL,
            context_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """)
        c.execute("""
        CREATE TABLE IF NOT EXISTS agent_runs (
            run_id TEXT PRIMARY KEY,
            thread_id TEXT NOT NULL,
            seq INTEGER NOT NULL,
            agent_id TEXT NOT NULL,
            agent_name TEXT NOT NULL,
            status TEXT NOT NULL,
            summary TEXT NOT NULL,
            plan_json TEXT NOT NULL,
            output_json TEXT NOT NULL,
            model_id TEXT,
            model_version TEXT,
            approval_required INTEGER DEFAULT 0,
            event_id TEXT,
            created_at TEXT NOT NULL
        )
        """)
        c.execute("""
        CREATE TABLE IF NOT EXISTS agent_artifacts (
            artifact_id TEXT PRIMARY KEY,
            thread_id TEXT NOT NULL,
            run_id TEXT,
            artifact_type TEXT NOT NULL,
            title TEXT NOT NULL,
            content_json TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            approved_at TEXT,
            event_id TEXT
        )
        """)
        c.execute("""
        CREATE TABLE IF NOT EXISTS agent_approvals (
            approval_id TEXT PRIMARY KEY,
            thread_id TEXT NOT NULL,
            artifact_id TEXT NOT NULL,
            requested_by TEXT NOT NULL,
            approver_role TEXT NOT NULL,
            status TEXT NOT NULL,
            reason TEXT,
            created_at TEXT NOT NULL,
            decided_at TEXT,
            event_id TEXT
        )
        """)
        c.execute("""
        CREATE TABLE IF NOT EXISTS agent_handoffs (
            handoff_id TEXT PRIMARY KEY,
            thread_id TEXT NOT NULL,
            from_agent TEXT NOT NULL,
            to_agent TEXT NOT NULL,
            reason TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            event_id TEXT
        )
        """)
        cols = {row[1] for row in c.execute("PRAGMA table_info(agent_threads)").fetchall()}
        if "audience_role" not in cols:
            c.execute("ALTER TABLE agent_threads ADD COLUMN audience_role TEXT NOT NULL DEFAULT 'parent'")
        if "audience_config_json" not in cols:
            c.execute("ALTER TABLE agent_threads ADD COLUMN audience_config_json TEXT NOT NULL DEFAULT '{}'")
        c.execute("CREATE INDEX IF NOT EXISTS idx_thread_scope ON agent_threads(student_id, class_id, updated_at)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_runs_thread ON agent_runs(thread_id, seq)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_artifacts_thread ON agent_artifacts(thread_id, created_at)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_approvals_thread ON agent_approvals(thread_id, status)")


def _decode(row, json_fields=()):
    d = dict(row)
    for f in json_fields:
        d[f[:-5] if f.endswith("_json") else f] = json.loads(d.pop(f) or "{}")
    return d


def create_thread(title: str, objective: str, student_id: str, class_id: str,
                  created_by_role: str = "subject_teacher", task_type: str = "grammar_cloze",
                  context: dict | None = None, audience_role: str = "parent",
                  audience_config: dict | None = None) -> dict:
    init_db()
    tid = _id("thread")
    now = _now()
    context = context or {}
    audience_config = audience_config or {}
    profile = audience_profile(audience_role)
    evt = insert_event({
        "event_type": "agent_thread_created",
        "student_id": student_id,
        "session_id": tid,
        "payload": {"thread_id": tid, "title": title, "objective": objective, "class_id": class_id,
                    "created_by_role": created_by_role, "task_type": task_type,
                    "audience_role": audience_role, "audience_label": profile["label"]},
        "source": "multi_agent_workbench",
    })
    with _conn() as c:
        c.execute(
            "INSERT INTO agent_threads(thread_id,title,objective,student_id,class_id,task_type,created_by_role,audience_role,audience_config_json,status,context_json,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (tid, title, objective, student_id, class_id, task_type, created_by_role,
             audience_role, json.dumps(audience_config, ensure_ascii=False), "draft",
             json.dumps(context, ensure_ascii=False), now, now),
        )
    write_audit(created_by_role, "workbench.thread.create", tid, {"student_id": student_id, "event_id": evt})
    return get_thread(tid)


def list_threads(limit: int = 50, student_id: str | None = None, class_id: str | None = None,
                 role: str | None = None) -> list[dict]:
    init_db()
    clauses, params = [], []
    if student_id:
        clauses.append("student_id=?")
        params.append(student_id)
    if class_id:
        clauses.append("class_id=?")
        params.append(class_id)
    if role:
        clauses.append("created_by_role=?")
        params.append(role)
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM agent_threads" + where + " ORDER BY updated_at DESC LIMIT ?",
            (*params, int(limit)),
        ).fetchall()
    out = []
    for row in rows:
        d = _decode(row, ("context_json", "audience_config_json"))
        d["audience_label"] = (d["audience_config"].get("recipient_label")
                               or audience_profile(d.get("audience_role") or "parent")["label"])
        with _conn() as c:
            pending = c.execute("SELECT COUNT(*) FROM agent_approvals WHERE thread_id=? AND status='pending'", (d["thread_id"],)).fetchone()[0]
            runs = c.execute("SELECT COUNT(*) FROM agent_runs WHERE thread_id=?", (d["thread_id"],)).fetchone()[0]
        d["pending_approvals"] = pending
        d["run_count"] = runs
        out.append(d)
    return out


def get_thread(thread_id: str) -> dict:
    init_db()
    with _conn() as c:
        row = c.execute("SELECT * FROM agent_threads WHERE thread_id=?", (thread_id,)).fetchone()
        if not row:
            raise KeyError("thread not found")
        thread = _decode(row, ("context_json", "audience_config_json"))
        runs = [_decode(r, ("plan_json", "output_json")) for r in c.execute(
            "SELECT * FROM agent_runs WHERE thread_id=? ORDER BY seq", (thread_id,)).fetchall()]
        artifacts = [_decode(a, ("content_json",)) for a in c.execute(
            "SELECT * FROM agent_artifacts WHERE thread_id=? ORDER BY created_at", (thread_id,)).fetchall()]
        approvals = [dict(a) for a in c.execute(
            "SELECT * FROM agent_approvals WHERE thread_id=? ORDER BY created_at", (thread_id,)).fetchall()]
        handoffs = [dict(h) for h in c.execute(
            "SELECT * FROM agent_handoffs WHERE thread_id=? ORDER BY created_at", (thread_id,)).fetchall()]
    thread["audience_role"] = thread.get("audience_role") or "parent"
    thread["audience_config"] = thread.get("audience_config") or {}
    thread["audience_label"] = (thread["audience_config"].get("recipient_label")
                               or audience_profile(thread["audience_role"])["label"])
    thread.update({"runs": runs, "artifacts": artifacts, "approvals": approvals, "handoffs": handoffs,
                   "pending_approvals": sum(1 for a in approvals if a["status"] == "pending")})
    return thread


def _add_run(thread: dict, seq: int, agent_id: str, agent_name: str, summary: str,
             plan: list, output: dict, approval_required: bool = False) -> dict:
    rid = _id("run")
    evt = insert_event({
        "event_type": "agent_run_completed", "student_id": thread["student_id"], "session_id": thread["thread_id"],
        "payload": {"run_id": rid, "thread_id": thread["thread_id"], "agent_id": agent_id, "summary": summary,
                    "approval_required": approval_required, "output": output},
        "source": "multi_agent_workbench",
    })
    with _conn() as c:
        c.execute(
            "INSERT INTO agent_runs(run_id,thread_id,seq,agent_id,agent_name,status,summary,plan_json,output_json,model_id,model_version,approval_required,event_id,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (rid, thread["thread_id"], seq, agent_id, agent_name, "completed", summary,
             json.dumps(plan, ensure_ascii=False), json.dumps(output, ensure_ascii=False),
             "tender-rolemind", "1.1.0", int(approval_required), evt, _now()),
        )
    return {"run_id": rid, "agent_id": agent_id, "agent_name": agent_name, "status": "completed",
            "summary": summary, "plan": plan, "output": output, "approval_required": approval_required, "event_id": evt}


def _add_artifact(thread: dict, run_id: str, artifact_type: str, title: str, content: dict,
                  status: str = "draft") -> dict:
    aid = _id("artifact")
    evt = insert_event({
        "event_type": "agent_artifact_created", "student_id": thread["student_id"], "session_id": thread["thread_id"],
        "payload": {"artifact_id": aid, "thread_id": thread["thread_id"], "run_id": run_id,
                    "artifact_type": artifact_type, "title": title, "status": status},
        "source": "multi_agent_workbench",
    })
    with _conn() as c:
        c.execute(
            "INSERT INTO agent_artifacts(artifact_id,thread_id,run_id,artifact_type,title,content_json,status,created_at,event_id) VALUES(?,?,?,?,?,?,?,?,?)",
            (aid, thread["thread_id"], run_id, artifact_type, title, json.dumps(content, ensure_ascii=False), status, _now(), evt),
        )
    return {"artifact_id": aid, "artifact_type": artifact_type, "title": title, "content": content,
            "status": status, "event_id": evt}


def _add_handoff(thread: dict, from_agent: str, to_agent: str, reason: str) -> dict:
    hid = _id("handoff")
    evt = insert_event({
        "event_type": "agent_handoff", "student_id": thread["student_id"], "session_id": thread["thread_id"],
        "payload": {"handoff_id": hid, "thread_id": thread["thread_id"], "from_agent": from_agent,
                    "to_agent": to_agent, "reason": reason},
        "source": "multi_agent_workbench",
    })
    with _conn() as c:
        c.execute(
            "INSERT INTO agent_handoffs(handoff_id,thread_id,from_agent,to_agent,reason,status,created_at,event_id) VALUES(?,?,?,?,?,?,?,?)",
            (hid, thread["thread_id"], from_agent, to_agent, reason, "completed", _now(), evt),
        )
    return {"handoff_id": hid, "from_agent": from_agent, "to_agent": to_agent, "reason": reason}


def _add_approval(thread: dict, artifact_id: str, requested_by: str, approver_role: str) -> dict:
    apid = _id("approval")
    evt = insert_event({
        "event_type": "agent_approval_requested", "student_id": thread["student_id"], "session_id": thread["thread_id"],
        "payload": {"approval_id": apid, "thread_id": thread["thread_id"], "artifact_id": artifact_id,
                    "approver_role": approver_role},
        "source": "multi_agent_workbench",
    })
    with _conn() as c:
        c.execute(
            "INSERT INTO agent_approvals(approval_id,thread_id,artifact_id,requested_by,approver_role,status,created_at,event_id) VALUES(?,?,?,?,?,?,?,?)",
            (apid, thread["thread_id"], artifact_id, requested_by, approver_role, "pending", _now(), evt),
        )
    return {"approval_id": apid, "artifact_id": artifact_id, "approver_role": approver_role,
            "status": "pending", "event_id": evt}


def for_viewer(thread: dict, viewer_role: str) -> dict:
    """Return a role-filtered view of a thread.

    This is a preview-level data minimization layer. Production must still
    enforce authentication and authorization on the server.
    """
    role = (viewer_role or "").lower()
    if role in {"teacher", "subject_teacher", "tutor", "head_teacher", "institution", "health_advisor", "nutrition_advisor", "neurocognitive_advisor", "psychology_advisor", "learning_science_advisor", "career_advisor", "safety_advisor"}:
        return thread
    out = dict(thread)
    if role == "learner":
        allowed = {"student_cards", "lesson_plan", "safety_check"}
        out["artifacts"] = [a for a in thread.get("artifacts", [])
                            if a.get("artifact_type") in allowed and a.get("status") in {"approved", "internal"}]
        out["approvals"] = []
        out["runs"] = [{k: r.get(k) for k in ("run_id", "agent_id", "agent_name", "status", "summary", "created_at")}
                       for r in thread.get("runs", []) if r.get("agent_id") in {"coordinator", "student_tutor", "safety_guardrail"}]
        out["visibility_note"] = "学生视图：只显示已批准的学习任务与复习卡，不显示家长报告和内部评估。"
    elif role in {"parent", "mentor", "employer", "admissions", "collaborator", "client"}:
        out["artifacts"] = [
            a for a in thread.get("artifacts", [])
            if a.get("status") == "approved" and (
                (a.get("artifact_type") == "external_communication"
                 and (a.get("content") or {}).get("recipient_role") == role)
                or (role == "parent" and a.get("artifact_type") == "family_report")
            )
        ]
        out["approvals"] = []
        out["runs"] = []
        out["handoffs"] = []
        label = audience_profile(role)["label"]
        out["visibility_note"] = f"对外沟通视图：只显示已经审批、发给{label}的内容。"
    else:
        out["artifacts"] = []
        out["approvals"] = []
        out["runs"] = []
        out["visibility_note"] = "未知角色：默认不显示内容。"
    return out


def orchestrate(thread_id: str, context: dict | None = None, focus_students: list[str] | None = None) -> dict:
    thread = get_thread(thread_id)
    if thread["runs"]:
        thread["already_orchestrated"] = True
        return thread
    context = context or {}
    focus_students = focus_students or [thread["student_id"]]
    mastery = round(float(context.get("mastery", 0.5) or 0.5), 3)
    jol = round(float(context.get("jol_bias", 0.0) or 0.0), 3)
    hesitation = round(float(context.get("hesitation", 0.0) or 0.0), 3)
    student_name = context.get("student_name") or thread["student_id"]
    class_id = thread["class_id"]
    objective = thread["objective"]
    audience_role = thread.get("audience_role") or "parent"
    audience_config = thread.get("audience_config") or {}
    profile = audience_profile(audience_role)
    if audience_config.get("recipient_label"):
        profile["label"] = str(audience_config["recipient_label"])
        if audience_role == "custom":
            profile["artifact_title"] = f"{profile['label']}沟通草稿"

    coordinator_output = {
        "goal": objective,
        "scope": {"student": student_name, "class_id": class_id, "focus_students": focus_students,
                  "external_audience": profile["label"]},
        "policy": ["不展示排名", "所有对外沟通必须真人审批", "学生只接收最小提示", "所有动作写入 DAOQL"],
    }
    r1 = _add_run(thread, 1, "coordinator", "协调者", "拆解教学任务并建立协作边界",
                  ["读取课程与学习证据", "分派内容/评估/学生/对外沟通/安全 Agent", "等待负责人审批后完成"],
                  coordinator_output)

    lesson_content = {
        "assignment": "语法填空练习：完成 56—65，并标记确定 / 不确定 / 猜的",
        "focus_words": ["context", "structure", "collaborate"],
        "focus_sentence": "先判断句子成分，再判断所填词的词性与形式。",
        "teaching_steps": ["3 分钟方法回顾", "12 分钟独立完成", "8 分钟错题讲解", "次日 5 分钟重测"],
    }
    r2 = _add_run(thread, 2, "content_curator", "内容 Agent", "抽取本次练习、重点词汇和重点句型",
                  ["读取语法填空讲义", "抽取 56—65", "整理重点词汇与句型"], lesson_content)
    a1 = _add_artifact(thread, r2["run_id"], "lesson_plan", "教学任务包", lesson_content, status="approved")

    assessment_content = {
        "student": student_name,
        "mastery": mastery,
        "jol_bias": jol,
        "hesitation": hesitation,
        "priority": "先复盘方法，再做最小提示",
        "watchouts": ["避免直接给答案", "不要用本次表现贴能力标签"],
    }
    r3 = _add_run(thread, 3, "assessment", "评估 Agent", "汇总当前学习状态并生成低风险干预建议",
                  ["读取 Tender 状态", "检查证据覆盖度", "生成干预优先级"], assessment_content)
    a2 = _add_artifact(thread, r3["run_id"], "assessment_brief", "学习状态摘要", assessment_content, status="internal")

    student_content = {
        "student": student_name,
        "cards": [
            {"title": "今天先做什么", "text": "先复述句子成分，再完成语法填空 56—65。"},
            {"title": "不会时怎么求助", "text": "先请求一级提示；仍不会再看老师讲解片段。"},
            {"title": "明天复习", "text": "重做今天标记为“不确定 / 猜的”的题目。"},
        ],
        "forbidden": ["直接展示答案", "排名", "人格标签"],
    }
    r4 = _add_run(thread, 4, "student_tutor", "学生教练", "生成学生自己的最小行动卡",
                  ["读取练习任务", "生成一级提示", "安排次日复习"], student_content)
    a3 = _add_artifact(thread, r4["run_id"], "student_cards", "学生复习卡", student_content, status="approved")

    purpose = audience_config.get("purpose") or objective
    tone = audience_config.get("tone") or profile["tone"]
    if audience_role == "parent":
        sections = [
            {"label": profile["labels"][0], "text": "本周按计划完成语法填空练习，并标记了不确定题。"},
            {"label": profile["labels"][1], "text": "能够先判断句子结构，再判断词性。"},
            {"label": profile["labels"][2], "text": "继续完成次日重测，重点观察重复错误。"},
        ]
    else:
        focus = "、".join(profile["focus"])
        sections = [
            {"label": profile["labels"][0], "text": f"本次沟通目的：{purpose}。"},
            {"label": profile["labels"][1], "text": f"已整理的可验证证据聚焦：{focus}。"},
            {"label": profile["labels"][2], "text": audience_config.get("next_step") or "继续补充可验证证据，并约定下一次同步。"},
        ]
    external_content = {
        "title": profile["artifact_title"],
        "student": student_name,
        "recipient_role": audience_role,
        "recipient_label": profile["label"],
        "purpose": purpose,
        "tone": tone,
        "format": audience_config.get("format", "structured_report"),
        "sections": sections,
        "privacy_note": "；".join(profile["privacy"]),
        "audience_config": audience_config,
    }
    r5 = _add_run(thread, 5, "external_communication", "对外沟通 Agent",
                  f"生成面向{profile['label']}的沟通草稿，等待真人批准",
                  ["读取已批准证据", f"按{profile['label']}角色调整结构与语气", "移除越权和不该披露的信息"],
                  external_content, approval_required=True)
    a4 = _add_artifact(thread, r5["run_id"], "external_communication", profile["artifact_title"], external_content)
    ap = _add_approval(thread, a4["artifact_id"], "external_communication", thread["created_by_role"])

    safety_content = {
        "checks": [
            {"name": "未成年人隐私", "status": "pass"},
            {"name": "排名与同伴对比", "status": "pass"},
            {"name": "人格诊断", "status": "pass"},
            {"name": "对外接收人与发送审批", "status": "pending_human_approval"},
        ],
        "decision": "allow_draft_only",
    }
    r6 = _add_run(thread, 6, "safety_guardrail", "安全护栏", "检查隐私、排名和高风险语言",
                  ["扫描 Artifact", "检查角色权限", "标记待审批动作"], safety_content)
    a5 = _add_artifact(thread, r6["run_id"], "safety_check", "安全检查", safety_content, status="approved")

    _add_handoff(thread, "coordinator", "content_curator", "提取课程内容")
    _add_handoff(thread, "coordinator", "assessment", "读取学习状态")
    _add_handoff(thread, "assessment", "student_tutor", "生成个性化复习卡")
    _add_handoff(thread, "assessment", "external_communication", f"生成面向{profile['label']}的沟通草稿")
    _add_handoff(thread, "external_communication", "safety_guardrail", "发送前隐私与越权检查")

    with _conn() as c:
        c.execute("UPDATE agent_threads SET status='waiting_approval', updated_at=? WHERE thread_id=?",
                  (_now(), thread_id))
    write_audit("coordinator", "workbench.thread.orchestrate", thread_id,
                {"runs": 6, "artifacts": 5, "pending_approvals": 1})
    return get_thread(thread_id)


def decide_approval(approval_id: str, decision: str, reason: str = "", actor: str = "teacher") -> dict:
    if decision not in {"approved", "rejected", "changes_requested"}:
        raise ValueError("invalid decision")
    init_db()
    with _conn() as c:
        row = c.execute("SELECT * FROM agent_approvals WHERE approval_id=?", (approval_id,)).fetchone()
        if not row:
            raise KeyError("approval not found")
        approval = dict(row)
        thread = _decode(c.execute("SELECT * FROM agent_threads WHERE thread_id=?", (approval["thread_id"],)).fetchone(),
                         ("context_json",))
        artifact_status = "approved" if decision == "approved" else ("rejected" if decision == "rejected" else "needs_revision")
        c.execute("UPDATE agent_approvals SET status=?, reason=?, decided_at=? WHERE approval_id=?",
                  (decision, reason, _now(), approval_id))
        c.execute("UPDATE agent_artifacts SET status=?, approved_at=? WHERE artifact_id=?",
                  (artifact_status, _now() if decision == "approved" else None, approval["artifact_id"]))
        pending = c.execute("SELECT COUNT(*) FROM agent_approvals WHERE thread_id=? AND status='pending'",
                            (approval["thread_id"],)).fetchone()[0]
        thread_status = "completed" if decision == "approved" and pending == 0 else (
            "needs_revision" if decision in {"rejected", "changes_requested"} else "waiting_approval")
        c.execute("UPDATE agent_threads SET status=?, updated_at=? WHERE thread_id=?",
                  (thread_status, _now(), approval["thread_id"]))
    evt = insert_event({
        "event_type": "agent_approval_decided", "student_id": thread["student_id"], "session_id": thread["thread_id"],
        "payload": {"approval_id": approval_id, "thread_id": approval["thread_id"], "artifact_id": approval["artifact_id"],
                    "decision": decision, "reason": reason, "actor": actor},
        "source": "multi_agent_workbench",
    })
    write_audit(actor, "workbench.approval.decide", approval_id, {"decision": decision, "reason": reason, "event_id": evt})
    return get_thread(approval["thread_id"])


def stop_thread(thread_id: str, actor: str = "teacher", reason: str = "") -> dict:
    init_db()
    thread = get_thread(thread_id)
    with _conn() as c:
        c.execute("UPDATE agent_threads SET status='stopped', updated_at=? WHERE thread_id=?",
                  (_now(), thread_id))
    evt = insert_event({
        "event_type": "agent_thread_stopped", "student_id": thread["student_id"], "session_id": thread_id,
        "payload": {"thread_id": thread_id, "reason": reason, "actor": actor},
        "source": "multi_agent_workbench",
    })
    write_audit(actor, "workbench.thread.stop", thread_id, {"reason": reason, "event_id": evt})
    return get_thread(thread_id)
