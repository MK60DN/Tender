"""Ambient assistance planner for Tender.

The ambient layer is intentionally quiet: it emits at most one short card,
respects cooldown and silence windows, and records why each prompt appeared.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Mapping
from uuid import uuid4

from .daoql import insert_event, list_events, write_audit
from .functional_agents import (agent_catalog, build_ensemble, build_reply, normalize_agents, preview, get_agent, DEFAULT_AGENTS)
from .llm_dialogue import enrich_reply
from .tender_context import build_tender_context
from .metameta_cartographer import annotate_and_store

DAILY_LIMIT = 8
COOLDOWN_SECONDS = 180
DEFAULT_SILENCE_MINUTES = 30


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _ambient_events(student_id: str) -> list[dict[str, Any]]:
    return [event for event in list_events(student_id) if str(event.get("event_type", "")).startswith("ambient_")]


def _number(signals: Mapping[str, Any], key: str, default: float = 0.0) -> float:
    try:
        return max(0.0, float(signals.get(key, default)))
    except (TypeError, ValueError):
        return default


def _silence_until(events: list[dict[str, Any]]) -> datetime | None:
    latest = None
    for event in events:
        if event.get("event_type") != "ambient_feedback":
            continue
        payload = event.get("payload") or {}
        if payload.get("feedback") != "silence":
            continue
        until = _parse_ts(payload.get("silence_until"))
        if until and (latest is None or until > latest):
            latest = until
    return latest


def _status(student_id: str) -> dict[str, Any]:
    events = _ambient_events(student_id)
    now = _now()
    cards_today = []
    last_card = None
    for event in events:
        if event.get("event_type") != "ambient_card_shown":
            continue
        ts = _parse_ts(event.get("timestamp"))
        if ts and ts.date() == now.date():
            cards_today.append(event)
        if ts and (last_card is None or ts > last_card):
            last_card = ts
    silence = _silence_until(events)
    quiet = bool(silence and silence > now)
    recent_first = min(len(cards_today), DAILY_LIMIT)
    agent_ids = list(DEFAULT_AGENTS)
    for event in events:
        payload = event.get("payload") or {}
        if event.get("event_type") == "ambient_ensemble_selected":
            agent_ids = normalize_agents(payload.get("agent_ids") or payload.get("persona_ids"))
    primary_agent = get_agent(agent_ids[0])
    return {
        "student_id": student_id,
        "quiet": quiet,
        "agent_ids": agent_ids,
        "agent_count": len(agent_ids),
        "primary_agent_id": primary_agent["id"],
        "primary_agent_name": primary_agent["name"],
        "silence_until": silence.isoformat() if quiet and silence else None,
        "cards_today": recent_first,
        "daily_limit": DAILY_LIMIT,
        "last_card_at": last_card.isoformat() if last_card else None,
        "cooldown_seconds": COOLDOWN_SECONDS,
        "event_count": len(events),
    }


def _candidate(signals: Mapping[str, Any]) -> dict[str, Any] | None:
    scenario = str(signals.get("scenario") or "score_improvement")
    if signals.get("explicit_need"):
        if scenario == "gaokao_registration":
            return {
                "priority": 100,
                "kind": "registration_explicit_need",
                "text": "我在。先只检查高考报名里最紧急的一项，不展示任何证件号码。",
                "action": "打开报名清单",
                "why": "你主动请求了报名流程帮助。",
                "scenario": scenario,
            }
        return {
            "priority": 100,
            "kind": "explicit_need",
            "text": "我在。告诉我现在最卡的一句话，我只给你一个最小动作。",
            "action": "输入：我卡在……",
            "why": "你主动请求了帮助。",
            "scenario": scenario,
        }

    if scenario == "gaokao_registration":
        missing_items = int(_number(signals, "missing_items"))
        deadline_hours = _number(signals, "deadline_hours", 999)
        if missing_items > 0 and deadline_hours <= 24:
            return {
                "priority": 96,
                "kind": "registration_deadline",
                "text": f"报名截止前还有 {missing_items} 项未确认。先处理最紧急的一项，不在这里展示证件号码。",
                "action": "打开报名清单",
                "why": "截止时间临近且仍有未确认事项。",
                "scenario": scenario,
            }
        if signals.get("confirmation_pending"):
            return {
                "priority": 88,
                "kind": "registration_confirmation",
                "text": "报名信息可能还没最终确认。先核对状态和确认凭证。",
                "action": "核对确认状态",
                "why": "检测到最终确认仍未完成。",
                "scenario": scenario,
            }
        if signals.get("payment_pending"):
            return {
                "priority": 82,
                "kind": "registration_payment",
                "text": "还有一项报名流程未完成。先确认缴费状态，不需要在弹幕里展示支付信息。",
                "action": "确认缴费状态",
                "why": "存在待确认的报名流程事项。",
                "scenario": scenario,
            }
        if signals.get("photo_pending"):
            return {
                "priority": 76,
                "kind": "registration_photo",
                "text": "报名照片可能还没通过。先检查规格和审核状态。",
                "action": "检查照片状态",
                "why": "照片审核状态尚未确认。",
                "scenario": scenario,
            }
        return None

    days_to_target = _number(signals, "days_to_target", 999)
    weak_skill_count = int(_number(signals, "weak_skill_count"))
    if days_to_target <= 7 and weak_skill_count >= 2:
        return {
            "priority": 78,
            "kind": "score_improvement_priority",
            "text": "时间不多，先不要铺开复习。今天只处理一个最常错、最影响分数的小点。",
            "action": "选一个错点做 10 分钟",
            "why": "目标时间临近，且存在多个薄弱点。",
            "scenario": scenario,
        }
    app_category = str(signals.get("app_category") or "unknown")[:24]
    task_hint = str(signals.get("task_hint") or "")[:40]
    activity_rate = _number(signals, "activity_events_per_min")
    focus_minutes = _number(signals, "focus_minutes")

    if scenario == "gaokao_registration" and "报名" in task_hint and focus_minutes >= 2:
        return {
            "priority": 74,
            "kind": "behavior_registration_focus",
            "text": "报名页面已经打开。下一步只核对一个状态，不要在多个页面之间来回切。",
            "action": "核对最紧急的一项",
            "why": "实时行为显示当前任务与高考报名相关。",
            "scenario": scenario,
        }
    if app_category in {"video", "game"} and focus_minutes >= 2:
        label = "视频" if app_category == "video" else "游戏"
        return {
            "priority": 58,
            "kind": "behavior_attention_drift",
            "text": f"你已经在{label}上停留了一会儿。先做一个 20 秒的选择：继续休息，或切回今天最小的学习动作。",
            "action": "选：继续休息 / 回到任务",
            "why": "实时行为显示当前前台应用偏离学习任务。",
            "scenario": scenario,
        }
    if app_category == "chat" and focus_minutes >= 2:
        return {
            "priority": 54,
            "kind": "behavior_dialogue_support",
            "text": "你现在在对话或求助窗口。先把问题压成一句话，我可以只帮你决定下一步。",
            "action": "Ctrl+Alt+R 回复我",
            "why": "实时行为显示当前处于交流或求助情境。",
            "scenario": scenario,
        }
    if app_category in {"study", "document", "coding"} and focus_minutes >= 12 and activity_rate <= 3:
        return {
            "priority": 66,
            "kind": "behavior_deep_focus",
            "text": "你已经在这份内容上持续了一会儿。先不要增加新内容，用一句话说出刚才最关键的结论。",
            "action": "做一次 30 秒复述",
            "why": "实时行为显示持续专注且输入活动较低，适合做短提取。",
            "scenario": scenario,
        }

    hesitation = _number(signals, "hesitation")
    repeated_errors = _number(signals, "repeated_errors")
    if hesitation >= 0.65 or repeated_errors >= 2:
        return {
            "priority": 82,
            "kind": "stuck",
            "text": "先别做完整答案。只写下你觉得最可能的第一步。",
            "action": "做一个最小步骤",
            "why": "连续卡住或同类错误反复出现，先把任务缩小。",
            "scenario": scenario,
        }
    visibility_switches = _number(signals, "visibility_switches")
    idle_seconds = _number(signals, "idle_seconds")
    if visibility_switches >= 4 or idle_seconds >= 90:
        return {
            "priority": 62,
            "kind": "attention_shift",
            "text": "你已经停了一会儿。要么把任务缩成两分钟，要么先休息一分钟。",
            "action": "缩成两分钟版本",
            "why": "检测到离屏、无操作或多次切换窗口。",
            "scenario": scenario,
        }
    if focus_minutes >= 20:
        return {
            "priority": 45,
            "kind": "recovery",
            "text": "先停 30 秒，用一句话说出你刚学到的。",
            "action": "做一次口头复述",
            "why": "连续专注较久，适合做一次短提取。",
            "scenario": scenario,
        }
    return None


def plan_ambient_card(student_id: str, signals: Mapping[str, Any], *, actor_id: str = "ambient", force: bool = False) -> dict[str, Any]:
    status = _status(student_id)
    candidate = _candidate(signals)
    if candidate is None:
        return {"status": "quiet", "card": None, "ambient": status, "reason": "no_trigger"}
    if status["quiet"] and not force:
        return {"status": "silenced", "card": None, "ambient": status, "reason": "silence_window"}
    last_card = _parse_ts(status["last_card_at"])
    if not force and last_card and (_now() - last_card).total_seconds() < COOLDOWN_SECONDS and candidate["priority"] < 90:
        return {"status": "cooling_down", "card": None, "ambient": status, "reason": "cooldown"}
    if not force and status["cards_today"] >= DAILY_LIMIT and candidate["priority"] < 90:
        return {"status": "daily_limit", "card": None, "ambient": status, "reason": "daily_limit"}

    agent_ids = normalize_agents(signals.get("agent_ids") or signals.get("ensemble_ids") or status.get("agent_ids"))
    candidate = build_ensemble(candidate, agent_ids, dict(signals))
    card_id = "ambient_" + uuid4().hex[:12]
    card = {**candidate, "card_id": card_id, "created_at": _now().isoformat()}
    insert_event({
        "event_type": "ambient_card_shown",
        "student_id": student_id,
        "payload": {"card": card, "signals": dict(signals)},
        "source": "tender-ambient-layer",
        "provenance": {"actor_id": actor_id, "policy": "one_card_cooldown_daily_limit"},
    })
    write_audit(actor_id, "ambient.card.shown", student_id, {"card_id": card_id, "kind": card["kind"], "priority": card["priority"]})
    return {"status": "shown", "card": card, "ambient": _status(student_id), "reason": card["why"]}


def record_ambient_feedback(student_id: str, card_id: str, feedback: str, *, actor_id: str = "ambient") -> dict[str, Any]:
    allowed = {"useful", "wrong", "silence", "dismiss"}
    if feedback not in allowed:
        raise ValueError("invalid_feedback")
    if not card_id.startswith("ambient_"):
        raise ValueError("invalid_card_id")
    silence_until = None
    if feedback == "silence":
        silence_until = (_now() + timedelta(minutes=DEFAULT_SILENCE_MINUTES)).isoformat()
    payload = {"card_id": card_id, "feedback": feedback}
    if silence_until:
        payload["silence_until"] = silence_until
    event_id = insert_event({
        "event_type": "ambient_feedback",
        "student_id": student_id,
        "payload": payload,
        "source": "tender-ambient-layer",
        "provenance": {"actor_id": actor_id},
    })
    write_audit(actor_id, f"ambient.feedback.{feedback}", student_id, {"card_id": card_id, "event_id": event_id})
    return {"status": "recorded", "event_id": event_id, "feedback": feedback, "silence_until": silence_until, "ambient": _status(student_id)}


def ambient_status(student_id: str) -> dict[str, Any]:
    return _status(student_id)


def _dialogue_history(student_id: str) -> list[dict[str, str]]:
    history = []
    for event in list_events(student_id):
        if event.get("event_type") != "ambient_dialogue_reply":
            continue
        payload = event.get("payload") or {}
        user_message = str(payload.get("user_message") or "").strip()
        if user_message:
            history.append({"role": "user", "content": user_message})
        reply_card = payload.get("reply_card") or {}
        for message in (reply_card.get("ensemble_messages") or [])[:2]:
            text = str(message.get("text") or "").strip()
            if text:
                history.append({"role": "assistant", "content": f"[{message.get('name','Agent')}] {text}"})
    return history[-10:]


def reply_to_ambient(student_id: str, card_id: str, message: str, *, actor_id: str = "ambient", scenario: str = "score_improvement", persona_id: str | None = None, ensemble_ids: list[str] | None = None) -> dict[str, Any]:
    """Create one bounded functional multi-agent dialogue turn."""
    if not card_id.startswith("ambient_"):
        raise ValueError("invalid_card_id")
    text = " ".join(str(message or "").strip().split())
    if not text:
        raise ValueError("empty_reply")
    if len(text) > 240:
        text = text[:240]
    low = text.lower()
    payload_extra = {}
    if any(word in low for word in ("静默", "别提醒", "安静", "闭嘴")):
        silence_until = (_now() + timedelta(minutes=DEFAULT_SILENCE_MINUTES)).isoformat()
        kind = "dialogue_silence"
        payload_extra = {"silence_until": silence_until}
    elif any(word in low for word in ("不会", "卡", "难", "不懂", "怎么办")):
        kind = "dialogue_scaffold"
    elif any(word in low for word in ("完成", "做完", "懂了", "会了", "有用")):
        kind = "dialogue_transfer"
    elif any(word in low for word in ("休息", "累了", "困", "暂停")):
        kind = "dialogue_rest"
    else:
        kind = "dialogue_ack"
    active_status = _status(student_id)
    agents = normalize_agents(ensemble_ids or active_status.get("agent_ids"))
    tender_context = build_tender_context(student_id, user_message=text)
    reply_card = build_reply(kind, text, agents, scenario, tender_context=tender_context)
    reply_card = enrich_reply(reply_card, text, _dialogue_history(student_id), max_agents=2, tender_context=tender_context)
    reply_card["tender_context_used"] = tender_context.get("digest", {})
    reply_card["action"] = "Ctrl+Alt+R 继续回复"
    reply_card["why"] = "这是对用户主动回复的功能型多 Agent 回应。"
    event_id = insert_event({
        "event_type": "ambient_dialogue_reply",
        "student_id": student_id,
        "payload": {"source_card_id": card_id, "user_message": text, "reply_card": reply_card, "tender_context_digest": tender_context.get("digest", {}), **payload_extra},
        "source": "tender-ambient-layer",
        "provenance": {"actor_id": actor_id, "policy": "bounded_functional_multi_agent_dialogue"},
    })
    try:
        metameta_decomposition = annotate_and_store(
            student_id,
            text,
            source_event_id=event_id,
            source_event_type="ambient_dialogue_reply",
            payload={"message": text},
            actor_id=actor_id,
        )
    except Exception as exc:
        metameta_decomposition = {"status": "error", "error": str(exc)}
    write_audit(actor_id, "ambient.dialogue.reply", student_id, {"event_id": event_id, "source_card_id": card_id, "kind": kind, "agent_ids": agents, "tender_context": tender_context.get("digest", {}), "metameta_event_id": metameta_decomposition.get("event_id")})
    return {"status": "replied", "event_id": event_id, "reply_card": reply_card, "metameta_decomposition": metameta_decomposition, **payload_extra}


def _agent_room(agent_ids: list[str]) -> list[dict[str, Any]]:
    ids = normalize_agents(agent_ids)
    return [
        {"id": aid, "name": get_agent(aid)["name"], "mark": get_agent(aid)["mark"], "role": get_agent(aid)["role"], "speaking": index == 0}
        for index, aid in enumerate(ids)
    ]


def list_ambient_personas() -> dict[str, Any]:
    catalog = agent_catalog()
    return {"count": len(catalog), "agents": catalog, "personas": catalog}


def get_ambient_persona(student_id: str) -> dict[str, Any]:
    status = _status(student_id)
    ids = normalize_agents(status.get("agent_ids"))
    return {"student_id": student_id, "agent_ids": ids, "agents": [get_agent(aid) for aid in ids], "room": _agent_room(ids)}


def select_ambient_persona(student_id: str, persona_id: str, *, actor_id: str = "ambient") -> dict[str, Any]:
    return select_ambient_ensemble(student_id, [persona_id], actor_id=actor_id)


def get_ambient_ensemble(student_id: str) -> dict[str, Any]:
    status = _status(student_id)
    ids = normalize_agents(status.get("agent_ids"))
    return {"student_id": student_id, "agent_ids": ids, "persona_ids": ids, "room": _agent_room(ids)}


def select_ambient_ensemble(student_id: str, persona_ids: list[str], *, actor_id: str = "ambient") -> dict[str, Any]:
    valid = {item["id"] for item in agent_catalog()}
    if not persona_ids or any(pid not in valid for pid in persona_ids):
        raise ValueError("invalid_ensemble")
    ids = normalize_agents(persona_ids)
    event_id = insert_event({
        "event_type": "ambient_ensemble_selected",
        "student_id": student_id,
        "payload": {"agent_ids": ids, "persona_ids": ids},
        "source": "tender-ambient-layer",
        "provenance": {"actor_id": actor_id, "policy": "functional_multi_agent_room"},
    })
    write_audit(actor_id, "ambient.ensemble.selected", student_id, {"event_id": event_id, "agent_ids": ids})
    return {"status": "selected", "event_id": event_id, "agent_ids": ids, "persona_ids": ids, "room": _agent_room(ids), "preview": preview(ids)}
