"""Persona voice layer for Tender ambient cards.

Personas change expression, not the underlying evidence thresholds or safety rules.
"""
from __future__ import annotations

import hashlib
from typing import Any

PERSONAS: list[dict[str, str]] = [
    {
        "id": "warm_coach",
        "role": "情绪调节与最小行动",
        "name": "温柔教练",
        "emoji": "🌱",
        "tagline": "不催你，但会陪你把下一步缩小",
        "sample": "先别急着做好，我们把下一步缩到两分钟。",
        "rules": "温和、具体、不空泛鼓励；不溺爱，不用羞耻感推动。",
    },
    {
        "id": "sassy_buddy",
        "role": "动力启动与去羞耻化",
        "name": "俏皮损友",
        "emoji": "🫠",
        "tagline": "可以吐槽你，但不攻击你",
        "sample": "喂，注意力又去隔壁串门了。回来，先做一个最小动作。",
        "rules": "轻松调侃，不攻击外貌、能力、家庭或人格；不制造羞耻。",
    },
    {
        "id": "calm_senior",
        "role": "任务拆解与优先级",
        "name": "冷静学长",
        "emoji": "🧊",
        "tagline": "只给判断和动作，不制造情绪起伏",
        "sample": "先停。现在只处理一个变量，其他都往后放。",
        "rules": "短句、稳定、低刺激；不冷漠羞辱。",
    },
    {
        "id": "cyber_detective",
        "role": "错因诊断与模式识别",
        "name": "赛博侦探",
        "emoji": "🕵️",
        "tagline": "把行为当成线索，帮你找到卡点",
        "sample": "线索更新：你不是不会，是入口开得太多。先关掉一个。",
        "rules": "像侦探一样描述线索，但不做诊断、不贴病理标签。",
    },
    {
        "id": "cat_supervisor",
        "role": "节奏监督与休息边界",
        "name": "猫系监工",
        "emoji": "🐈",
        "tagline": "轻轻盯着你，只允许一个最小动作",
        "sample": "喵。先做两分钟，做完我就放你走。",
        "rules": "轻度可爱和陪伴感；不幼稚化用户，不把学习变成惩罚游戏。",
    },
    {
        "id": "classical_tutor",
        "role": "记忆提取与结构化复述",
        "name": "老派塾师",
        "emoji": "📜",
        "tagline": "慢一点，先把一步立住",
        "sample": "且慢。先立一步，再谈全篇。",
        "rules": "简洁、有古意，但必须让现代用户一眼看懂；不故弄玄虚。",
    },
]

_BY_ID = {item["id"]: item for item in PERSONAS}


def normalize_persona(persona_id: str | None) -> str:
    return persona_id if persona_id in _BY_ID else "warm_coach"


def persona_catalog() -> list[dict[str, str]]:
    return [dict(item) for item in PERSONAS]


def get_persona(persona_id: str | None) -> dict[str, str]:
    return dict(_BY_ID[normalize_persona(persona_id)])


_CARD_VOICES: dict[str, dict[str, list[str]]] = {
    "warm_coach": {
        "behavior_attention_drift": ["注意力跑出去很正常。把它拉回来一点点：{base}", "没关系，我们只回来做一小步：{base}"],
        "behavior_deep_focus": ["你已经很专注了，先给大脑一个短短的回落：{base}", "这一段挺不容易的。现在用一个很小的动作收束：{base}"],
        "behavior_dialogue_support": ["我在。你不用把话想完整再说：{base}", "先不用组织得很漂亮，我在这里：{base}"],
        "behavior_registration_focus": ["先把这一件事稳稳完成，不用同时盯很多页面：{base}", "别急，我们只核对一个状态：{base}"],
        "default": ["我在。先不用急着做好，{base}", "先慢一点，{base}"],
    },
    "sassy_buddy": {
        "behavior_attention_drift": ["喂，注意力又去隔壁串门了。回来，{base}", "行，我抓到一次走神。没关系，现在回来：{base}"],
        "behavior_deep_focus": ["不错，没在假装努力。现在收个尾：{base}", "先别加戏，给刚才的专注一个落点：{base}"],
        "behavior_dialogue_support": ["来，把问题说人话就行，不用写论文：{base}", "别绕了，先抓一个最卡的词：{base}"],
        "behavior_registration_focus": ["报名页面不是逛商场，只处理眼前这一项：{base}", "先别开一堆标签页，逐个来：{base}"],
        "default": ["来，先别摆出要打一场仗的样子：{base}", "先把这一步做了，再决定要不要继续：{base}"],
    },
    "calm_senior": {
        "behavior_attention_drift": ["先停。把注意力收回到一个入口：{base}", "其他先放下。只做一个最小动作：{base}"],
        "behavior_deep_focus": ["暂时不增加内容。先提取一个结论：{base}", "保持低负荷，做一个短复述：{base}"],
        "behavior_dialogue_support": ["我在。先说最卡的一点：{base}", "不用完整解释，只描述阻塞位置：{base}"],
        "behavior_registration_focus": ["按顺序来。只核对当前状态：{base}", "先完成一个流程节点：{base}"],
        "default": ["先停一下。{base}", "只处理下一步：{base}"],
    },
    "cyber_detective": {
        "behavior_attention_drift": ["线索更新：注意力已经离开主任务。建议动作：{base}", "行为记录显示入口过多。先收束：{base}"],
        "behavior_deep_focus": ["线索更新：持续专注已形成。现在采集一次短提取：{base}", "检测到稳定投入。下一步是证据回收：{base}"],
        "behavior_dialogue_support": ["把当前卡点当成证词，先说一句就够：{base}", "我需要一个线索，不需要完整口供：{base}"],
        "behavior_registration_focus": ["当前任务已锁定为报名流程。只核对一个节点：{base}", "线索足够，先确认一个状态：{base}"],
        "default": ["先定位问题，再执行动作：{base}", "线索已经不少，现在只选一个可验证动作：{base}"],
    },
    "cat_supervisor": {
        "behavior_attention_drift": ["喵。注意力跑掉了，我轻轻叼回来：{base}", "喵～先回来一下，只做一个最小动作：{base}"],
        "behavior_deep_focus": ["喵，你已经坐稳一会儿了。现在轻轻收个尾：{base}", "不抢你的专注，只提醒你留一个脚印：{base}"],
        "behavior_dialogue_support": ["喵，我在。先说一个最卡的词就好：{base}", "不用全部说清，给我一个小线索：{base}"],
        "behavior_registration_focus": ["喵，报名这种事一项一项来：{base}", "先盯住一个状态，不要被页面牵走：{base}"],
        "default": ["喵。先做两分钟，做完我就不盯你：{base}", "轻轻的，但只往前一步：{base}"],
    },
    "classical_tutor": {
        "behavior_attention_drift": ["且慢。神思已散，先收一心：{base}", "心猿既起，先立一小步：{base}"],
        "behavior_deep_focus": ["且停笔。先以一语收束所见：{base}", "功已在前，今取其一得：{base}"],
        "behavior_dialogue_support": ["不必成篇。先道其一难：{base}", "一句足矣，先指其卡处：{base}"],
        "behavior_registration_focus": ["次第而行，勿乱其序：{base}", "先核一事，再及其余：{base}"],
        "default": ["且慢。先立一步，再谈全篇：{base}", "不求尽善，先成一事：{base}"],
    },
}

_REPLY_VOICES: dict[str, dict[str, list[str]]] = {
    "warm_coach": {
        "dialogue_scaffold": ["你说“{quote}”，那我们先不硬推。只写你确定的第一步，或者告诉我你卡在哪个词。"],
        "dialogue_transfer": ["这一步已经稳了。现在只换一道同类题，确认它真的变成你的，不用马上加量。"],
        "dialogue_ack": ["收到。我已经把它放进当前情境里。下一步只选一个最小动作，不把任务越滚越大。"],
        "dialogue_rest": ["可以休息，不需要补偿式加班。回来时只接一个两分钟动作。"],
        "dialogue_silence": ["好，我先安静。你想回来时再叫我。"],
    },
    "sassy_buddy": {
        "dialogue_scaffold": ["你说“{quote}”，行，不装了。先写你确定的第一步，卡住就报一个词，别硬撑。"],
        "dialogue_transfer": ["可以，说明这步不是假会。换一道同类题验一下，别急着开庆功宴。"],
        "dialogue_ack": ["收到，已记下。现在别把任务膨胀成连续剧，只做一个小动作。"],
        "dialogue_rest": ["准了，休息。别一边休息一边内疚，那不叫休息。"],
        "dialogue_silence": ["好，我闭嘴。需要时再按我出来。"],
    },
    "calm_senior": {
        "dialogue_scaffold": ["收到。停在这里，不跳到完整答案。只写第一步或一个阻塞词。"],
        "dialogue_transfer": ["已确认。进入迁移验证：同类题，只看第一步。"],
        "dialogue_ack": ["记录完成。下一步只做一个最小动作。"],
        "dialogue_rest": ["休息。不补课，不扩大任务。"],
        "dialogue_silence": ["好。静默 30 分钟。"],
    },
    "cyber_detective": {
        "dialogue_scaffold": ["线索“{quote}”已记录。当前假设：入口不清。先写第一步，或提供一个阻塞词。"],
        "dialogue_transfer": ["验证开始：换一道同类题。只观察你能否识别第一步。"],
        "dialogue_ack": ["记录入库。当前选择：只执行一个最小动作。"],
        "dialogue_rest": ["行为模式显示需要恢复。建议：短暂休息，回来只做一个两分钟动作。"],
        "dialogue_silence": ["收到停止信号。观察层静默 30 分钟。"],
    },
    "cat_supervisor": {
        "dialogue_scaffold": ["喵，你说“{quote}”。那先不硬推，写一个第一步，或者告诉我卡住的词。"],
        "dialogue_transfer": ["喵，这一步算坐稳了。换一道同类题看看还认不认得。"] ,
        "dialogue_ack": ["喵，记下了。接下来只做一个小动作。"],
        "dialogue_rest": ["准你休息。不要一边躺平一边自责，那不划算。"],
        "dialogue_silence": ["喵，我躲起来 30 分钟。"],
    },
    "classical_tutor": {
        "dialogue_scaffold": ["既云“{quote}”，先不求解全。书其一端，或指其阻塞处。"],
        "dialogue_transfer": ["此步已立。另取同类一题，验其是否真得。"],
        "dialogue_ack": ["已录。下一步只取一最小动作，不令其蔓。"],
        "dialogue_rest": ["可休。休后再取两分钟之事，不必补债。"],
        "dialogue_silence": ["诺。静默三十分钟。"],
    },
}


def _variant(persona_id: str, kind: str, card_id: str) -> str:
    voices = _CARD_VOICES[persona_id]
    options = voices.get(kind) or voices["default"]
    index = int(hashlib.sha1((card_id + kind).encode("utf-8")).hexdigest()[:8], 16) % len(options)
    return options[index]


def personalize_card(card: dict[str, Any], persona_id: str | None) -> dict[str, Any]:
    pid = normalize_persona(persona_id)
    persona = _BY_ID[pid]
    result = dict(card)
    base = str(card.get("text", "")).strip()
    kind = str(card.get("kind", "generic"))
    text = _variant(pid, kind, str(card.get("card_id", "ambient_preview"))).format(base=base)
    result["text"] = text
    result["persona_id"] = pid
    result["persona_name"] = persona["name"]
    result["persona_emoji"] = persona["emoji"]
    return result


def personalize_reply(card: dict[str, Any], persona_id: str | None, user_message: str) -> dict[str, Any]:
    pid = normalize_persona(persona_id)
    persona = _BY_ID[pid]
    result = dict(card)
    kind = str(card.get("kind", "dialogue_ack"))
    options = _REPLY_VOICES[pid].get(kind) or _REPLY_VOICES[pid]["dialogue_ack"]
    quote = str(user_message or "").strip()[:24]
    result["text"] = options[0].format(quote=quote)
    result["persona_id"] = pid
    result["persona_name"] = persona["name"]
    result["persona_emoji"] = persona["emoji"]
    return result


def preview_card(persona_id: str | None) -> dict[str, Any]:
    persona = get_persona(persona_id)
    base = {
        "card_id": "ambient_persona_preview_" + persona["id"],
        "kind": "behavior_attention_drift",
        "text": "先把自己拉回来，只做两分钟的最小动作。",
        "action": "Ctrl+Alt+B 用当前行为试一下",
        "why": "人设预览不会改变判断阈值。",
        "scenario": "score_improvement",
    }
    return personalize_card(base, persona["id"])


DEFAULT_ENSEMBLE = ["warm_coach", "calm_senior", "cyber_detective", "cat_supervisor"]
_SPEAKER_PREFERENCES = {
    "behavior_attention_drift": ["sassy_buddy", "cat_supervisor", "warm_coach"],
    "behavior_deep_focus": ["classical_tutor", "calm_senior", "warm_coach"],
    "behavior_dialogue_support": ["warm_coach", "cyber_detective", "calm_senior"],
    "behavior_registration_focus": ["cyber_detective", "calm_senior", "warm_coach"],
    "registration_deadline": ["cyber_detective", "calm_senior"],
    "registration_confirmation": ["cyber_detective", "calm_senior"],
    "registration_payment": ["calm_senior", "cyber_detective"],
    "registration_photo": ["cyber_detective", "calm_senior"],
    "score_improvement_priority": ["calm_senior", "warm_coach"],
    "stuck": ["warm_coach", "cyber_detective"],
    "attention_shift": ["cat_supervisor", "warm_coach"],
    "recovery": ["classical_tutor", "warm_coach"],
    "explicit_need": ["warm_coach", "calm_senior"],
    "registration_explicit_need": ["cyber_detective", "calm_senior"],
    "dialogue_scaffold": ["warm_coach", "calm_senior"],
    "dialogue_transfer": ["classical_tutor", "calm_senior"],
    "dialogue_rest": ["cat_supervisor", "warm_coach"],
    "dialogue_silence": ["calm_senior", "warm_coach"],
    "dialogue_ack": ["calm_senior", "warm_coach"],
}


def normalize_ensemble(persona_ids: list[str] | None) -> list[str]:
    valid = {item["id"] for item in PERSONAS}
    result = []
    for pid in persona_ids or []:
        if pid in valid and pid not in result:
            result.append(pid)
    return result or list(DEFAULT_ENSEMBLE)


def select_speaker(persona_ids: list[str] | None, kind: str) -> str:
    ensemble = normalize_ensemble(persona_ids)
    for candidate in _SPEAKER_PREFERENCES.get(kind, []):
        if candidate in ensemble:
            return candidate
    return ensemble[0]


def ensemble_room(persona_ids: list[str] | None, speaker_id: str) -> list[dict[str, str]]:
    room = []
    for pid in normalize_ensemble(persona_ids):
        item = get_persona(pid)
        room.append({
            "id": pid,
            "name": item["name"],
            "emoji": item["emoji"],
            "role": item.get("role", ""),
            "speaking": pid == speaker_id,
        })
    return room
