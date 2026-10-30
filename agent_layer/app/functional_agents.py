"""Functional multi-agent room for Tender ambient assistance."""
from __future__ import annotations
from typing import Any
from uuid import uuid4
from .triage_agent import triage, route_messages

AGENTS = [
    {"id":"learning_strategist","name":"学习策略师","mark":"策略","role":"任务拆解、优先级与复习节奏"},
    {"id":"subject_expert","name":"学科专家","mark":"学科","role":"知识点、先修关系与错因定位"},
    {"id":"neuro_cognition","name":"神经认知师","mark":"认知","role":"注意力、工作记忆与认知负荷"},
    {"id":"psychologist","name":"心理调节师","mark":"心理","role":"焦虑、回避、动机与自我评价"},
    {"id":"nutritionist","name":"营养健康师","mark":"营养","role":"睡眠、饮食、补水与身体能量"},
    {"id":"career_advisor","name":"生涯规划师","mark":"生涯","role":"专业兴趣、目标路径与长期证据"},
    {"id":"safety_officer","name":"安全保护官","mark":"安全","role":"隐私、身心安全与求助边界"},
    {"id":"metacognition_coach","name":"元认知教练","mark":"元认知","role":"策略觉察、监控与复盘"},
]
DEFAULT_AGENTS=[x["id"] for x in AGENTS]
_BY_ID={x["id"]:x for x in AGENTS}

def normalize_agents(ids: list[str] | None) -> list[str]:
    valid=set(_BY_ID); out=[]
    for aid in ids or []:
        if aid in valid and aid not in out: out.append(aid)
    return out or list(DEFAULT_AGENTS)

def agent_catalog(): return [dict(x) for x in AGENTS]
def get_agent(aid: str | None): return dict(_BY_ID.get(aid or "",AGENTS[0]))

def _category(kind: str, signals: dict[str,Any]) -> str:
    if "registration" in kind: return "registration"
    if kind in {"behavior_deep_focus","recovery"}: return "focus"
    if kind in {"stuck","behavior_dialogue_support"} or "dialogue_scaffold" in kind: return "stuck"
    if kind in {"behavior_attention_drift","attention_shift"}: return "drift"
    if kind.startswith("dialogue_rest"): return "rest"
    if kind.startswith("dialogue_"): return "dialogue"
    if signals.get("explicit_need"): return "explicit"
    return "generic"

def _topic(signals: dict[str,Any]) -> str:
    hint=str(signals.get("task_hint") or "").strip()
    return hint if hint and hint not in {"python","codex","chatgpt"} else "当前学习任务"

MESSAGES={
 "drift":{
  "learning_strategist":"把任务缩成两分钟：只开一个页面，写下第一步。",
  "subject_expert":"回到{topic}，只做一道基础题或一个最小例题。",
  "neuro_cognition":"切窗会产生注意力残留。停二十秒，只留一个窗口。",
  "psychologist":"先分清是逃避还是疲劳；逃避就只做一个最小动作，疲劳就休息。",
  "nutritionist":"若同时困、饿、头痛或眼疲劳，先喝水和离开屏幕。",
  "career_advisor":"目标专业需要持续投入的证据；现在只记录一次回到任务。",
  "safety_officer":"若走神伴随明显身体不适或情绪失控，先停止并求助。",
  "metacognition_coach":"写下刚才为什么切走，以及下一次的替代动作。",
 },
 "focus":{
  "learning_strategist":"停止加新内容，用三个关键词复述主干。",
  "subject_expert":"做一道同类迁移题，只看能否识别第一步和条件。",
  "neuro_cognition":"专注后先休息六十秒，降低负荷，再做短提取。",
  "psychologist":"记录让你进入专注的环境、任务大小和时间段。",
  "nutritionist":"站起来喝水、放松肩颈和眼睛；超过四十分钟就活动一下。",
  "career_advisor":"把这段专注记为目标专业相关的能力证据。",
  "safety_officer":"若出现头晕、心悸或明显不适，立即停止。",
  "metacognition_coach":"复盘：理解了什么、卡在哪里、下一步是什么。",
 },
}
MESSAGES.update({
 "registration":{
  "learning_strategist":"一次只处理一个报名节点，完成后再看下一项。",
  "subject_expert":"报名优先于复习；核对专业和选科时再调用学科信息。",
  "neuro_cognition":"每核对一项停两秒确认，不要连续跳页。",
  "psychologist":"焦虑时先写三项清单，只做第一项。",
  "nutritionist":"长时间盯页面会眼疲劳，定时看远处并补水。",
  "career_advisor":"检查专业、城市、选科和长期目标是否一致，但不临场改目标。",
  "safety_officer":"不要在弹幕或公共聊天展示证件号、住址、照片、支付信息或验证码。",
  "metacognition_coach":"每完成一项就打勾，并记录为什么确认通过。",
 },
 "stuck":{
  "learning_strategist":"把题拆成已知、目标、下一步三栏，只填确定部分。",
  "subject_expert":"判断卡点属于概念、公式、条件、计算还是表达。",
  "neuro_cognition":"工作记忆可能过载。先写已知条件，暂时不要扫整题。",
  "psychologist":"卡住不等于能力差，先把失败归因于策略或信息不足。",
  "nutritionist":"若伴随头痛、困倦或饥饿，先补能量，硬撑更慢。",
  "career_advisor":"这类基础能力与目标专业相关，但现在只处理一个阻塞点。",
  "safety_officer":"允许求助；涉及身心安全时优先找可信任的成人。",
  "metacognition_coach":"说出当前策略，以及它是否让问题更清楚。",
 },
 "rest":{
  "learning_strategist":"休息是计划的一部分，回来只接一个两分钟动作。",
  "subject_expert":"保留题目位置，疲劳时不做最终判断。",
  "neuro_cognition":"离开屏幕、走动或闭眼，让注意力和视觉负荷恢复。",
  "psychologist":"休息不需要内疚，不要在休息时继续反刍表现。",
  "nutritionist":"补水、合适进食、活动肩颈；长期睡眠不足先调睡眠。",
  "career_advisor":"长期路径不靠一次硬撑，恢复能力也是学习能力。",
  "safety_officer":"疲劳已影响身体或情绪时，停止学习并寻求支持。",
  "metacognition_coach":"记录休息后注意力是否恢复，用来校准学习时长。",
 },
 "explicit":{
  "learning_strategist":"给我一个最小卡点或第一步，我只处理这个范围。",
  "subject_expert":"给我一个条件、概念或原文，我先判断缺哪块知识。",
  "neuro_cognition":"先把问题缩成一句话，减少工作记忆负担。",
  "psychologist":"不用把问题说完整，先说最明显的感受或最难的一步。",
  "nutritionist":"如果现在困、饿、头痛或眼睛不舒服，先说身体状态。",
  "career_advisor":"先回答：这项目标专业真的需要它吗，还是只是焦虑？",
  "safety_officer":"涉及隐私、健康或人身安全时，先说明风险，不公开敏感资料。",
  "metacognition_coach":"先说你在用什么策略，再说它哪里没起作用。",
 },
 "dialogue":{
  "learning_strategist":"把下一步限定为一个动作：写第一步、标一个词或做一道同类题。",
  "subject_expert":"把卡点落到具体知识层：概念、条件、公式还是计算？",
  "neuro_cognition":"先停顿、写一个已知条件，再继续，不要同时追多个问题。",
  "psychologist":"把“不会”改写成“哪一步还没有信息或策略”。",
  "nutritionist":"若有困、饿、头痛或眼疲劳，先处理身体状态。",
  "career_advisor":"把它连回长期目标：这项能力是否真的重要，优先级如何？",
  "safety_officer":"涉及隐私、健康或安全时停止公开信息并寻求支持。",
  "metacognition_coach":"记录这次策略和结果，下一次知道该保留还是替换。",
 },
 "generic":{
  "learning_strategist":"只选一个最小动作，并明确完成条件。",
  "subject_expert":"把问题落到一个知识点、条件或错因上。",
  "neuro_cognition":"先减少同时进行的任务数量。",
  "psychologist":"先降低羞耻和压力，再做可完成的小动作。",
  "nutritionist":"检查睡眠、饮水、进食和身体不适。",
  "career_advisor":"判断这件事与长期目标的关系，只保留真正重要的一步。",
  "safety_officer":"任何建议都必须服从隐私、健康和安全边界。",
  "metacognition_coach":"说出当前策略、证据和下一步。",
 },
})
_PRIMARY={
 "drift":"neuro_cognition","focus":"neuro_cognition","registration":"safety_officer",
 "stuck":"subject_expert","rest":"psychologist","explicit":"learning_strategist",
 "dialogue":"metacognition_coach","generic":"learning_strategist",
}

def _text(aid: str, category: str, signals: dict[str,Any]) -> str:
    return MESSAGES[category].get(aid,MESSAGES["generic"].get(aid,"")).format(topic=_topic(signals))

def build_ensemble(card: dict[str,Any], agent_ids: list[str] | None, signals: dict[str,Any]) -> dict[str,Any]:
    members=normalize_agents(agent_ids)
    triage_signals={**signals,"kind":card.get("kind","generic")}
    triage_result=triage(str(signals.get("user_message") or ""),triage_signals)
    category=_category(str(card.get("kind","generic")),signals)
    all_messages=[]
    for aid in members:
        agent=get_agent(aid); text=_text(aid,category,signals)
        all_messages.append({"agent_id":aid,"name":agent["name"],"mark":agent["mark"],"role":agent["role"],"text":text})
    messages=route_messages(all_messages,triage_result,members)
    if not messages:
        messages=all_messages[:2]
    primary_message=messages[0]
    speaking_ids={m["agent_id"] for m in messages}
    room=[{"id":aid,"name":get_agent(aid)["name"],"mark":get_agent(aid)["mark"],"role":get_agent(aid)["role"],"speaking":aid in speaking_ids} for aid in members]
    result=dict(card)
    result.update({"agent_id":primary_message["agent_id"],"agent_name":primary_message["name"],"agent_mark":primary_message["mark"],"text":primary_message["text"],"agent_ids":members,"routed_agent_ids":[m["agent_id"] for m in messages],"room":room,"ensemble_messages":messages,"triage":triage_result.to_dict()})
    return result




NATURAL_REPLIES = {
 "anxiety_emotion": {
  "psychologist": "我听到了，你现在很焦虑。先不用急着把学习问题全部解决，焦虑本身会挤占注意力和工作记忆。你可以先告诉我：现在最担心发生什么？我们只处理其中能控制的一小步。",
  "neuro_cognition": "焦虑和频繁切换窗口会一起加重认知负荷。先停三十秒，把其他窗口收起来，慢慢呼气三次，再写下你眼前最具体的一步。你现在最先要做的是哪一步？",
  "nutritionist": "焦虑有时会和睡眠、进食、咖啡因或身体紧张一起出现。先喝点水，确认今天有没有好好吃饭和睡觉；如果心慌、失眠或身体不适持续，找可信任的成人或专业人员一起看。",
  "learning_strategist": "我们把事情缩小，不追求一次做完整。先选一个两分钟内能完成的动作，比如打开材料、写下一个已知条件，或列出一道题的第一步。",
  "metacognition_coach": "先不评价自己。说出你现在的想法、身体感觉和准备采取的动作，我们看看其中哪一步最值得调整。",
 },
 "fatigue_health": {
  "nutritionist": "先别硬撑。告诉我你现在是困、饿、头痛、眼睛疲劳，还是睡得太少？如果是身体状态，先补水和短暂休息，再决定要不要继续学习。",
  "neuro_cognition": "疲劳会让注意控制和提取都变差，继续加时通常不划算。先离开屏幕几分钟，回来只做一个很小的复习动作。",
  "psychologist": "如果疲劳背后还有压力或情绪消耗，先允许自己停一下。休息不是偷懒，而是恢复行动能力。",
 },
 "attention_focus": {
  "neuro_cognition": "现在的问题更像注意力入口太多，而不是你不想学。只保留一个窗口，关掉其他标签页，给自己两分钟重新进入。你想先回到哪一个任务？",
  "learning_strategist": "把任务缩到两分钟：打开材料、写第一步、然后停一下看看是否还想继续。不要一上来要求自己进入完整学习状态。",
  "psychologist": "先分清是逃避、疲劳，还是任务太大。三种情况的处理不同；你更接近哪一种？",
 },
 "knowledge_gap": {
  "subject_expert": "先别急着看完整答案。把题目或卡点发我，我会先判断你是卡在概念、条件、公式、计算还是表达。你也可以只写一句：你确定到哪一步？",
  "learning_strategist": "我们先做最小诊断，不铺开整章：找一道同类题，只做第一步，看看错误从哪一层出现。",
  "metacognition_coach": "把“我不会”改成“我卡在哪个具体位置”。请写下你已经知道什么、下一步想做什么，以及哪里开始不确定。",
 },
 "registration_process": {
  "safety_officer": "先只核对流程状态，确保证件号、住址、照片和支付信息留在官方页面。你现在最需要确认的是截止时间、确认状态、缴费还是照片审核？",
  "learning_strategist": "我们按清单一项一项来。先完成当前最紧急的一项，其他页面暂时收起来，避免信息混淆。",
  "career_advisor": "如果此时涉及专业或选科选择，先核对官方要求，再把长期目标和当前选项对上，不临场凭焦虑改目标。",
 },
 "career_path": {
  "career_advisor": "我们先分开两件事：你喜欢的活动，和目标专业真正要求的课程与能力。你愿意先说说最近哪类内容让你愿意持续投入吗？",
  "learning_strategist": "把长期目标拆回今天：选一个和目标专业相关的最小能力点，用一次真实学习或作品来验证兴趣。",
 },
 "acute_safety": {
  "safety_officer": "我需要先确认你现在是否安全。请立刻联系身边可信任的成人、家人或当地紧急服务，并远离可能伤害自己的物品。你现在身边有人吗？",
  "psychologist": "你的安全优先于学习。先和可信任的人待在一起，必要时联系当地紧急服务或危机干预。不要独自处理这一刻。",
 },
 "state_review": {
  "metacognition_coach": "我先根据Tender最近的记录和你这句话给一个暂时判断：现在更像是任务入口不清加上注意被其他线索带走，而不是你能力不行。我们先只做一个最小动作，再看结果会不会改变这个判断。",
  "neuro_cognition": "从近期证据看，当前可能同时有任务切换和负荷升高的成分。先只保留一个窗口和一个下一步，给自己两分钟重新进入；如果仍然卡住，我们再区分是知识、情绪还是疲劳。",
  "learning_strategist": "先不解决全部问题。写出你眼前任务的下一步，只做两分钟；完成后告诉我有没有更容易进入。这个结果会反过来修正Tender对你状态的判断。",
 },
 "unclear": {
  "learning_strategist": "我还需要一点信息才能判断。你现在是卡在不会做、开始不了、情绪太重、身体不舒服，还是不知道目标？选一个最接近的。",
  "metacognition_coach": "先用一句话描述：发生了什么、你当时在想什么、你希望下一步变成什么。我们从一个最小信息开始。",
 },
}

def _natural_reply(agent_id: str, problem_type: str, user_message: str, fallback: str) -> str:
    category=NATURAL_REPLIES.get(problem_type,{})
    if agent_id in category:
        return category[agent_id]
    agent=get_agent(agent_id)
    return f"我从{agent['name']}的角度接住这件事。{fallback} 你愿意先给我一个最小的具体信息吗？"

def build_reply(kind: str, user_message: str, agent_ids: list[str] | None, scenario: str, tender_context: dict[str,Any] | None = None) -> dict[str,Any]:
    base={"card_id":"ambient_"+uuid4().hex[:12],"kind":kind,"action":"Ctrl+Alt+R 继续回复","why":"功能型多 Agent 回应。","scenario":scenario}
    category="stuck" if kind=="dialogue_scaffold" else "dialogue"
    members=normalize_agents(agent_ids)
    triage_signals={"kind":kind}
    if tender_context: triage_signals["tender_context"]=tender_context
    triage_result=triage(user_message,triage_signals)
    all_messages=[]
    for aid in members:
        agent=get_agent(aid)
        text=_natural_reply(aid,triage_result.problem_type,user_message,MESSAGES[category].get(aid,MESSAGES["dialogue"][aid]))
        if kind=="dialogue_transfer": text="换一道同类题验证迁移，不只重复刚才那道。"
        if kind=="dialogue_rest": text=MESSAGES["rest"].get(aid,text)
        if kind=="dialogue_silence": text="收到静默请求，我先停止主动出现。"
        all_messages.append({"agent_id":aid,"name":agent["name"],"mark":agent["mark"],"role":agent["role"],"text":text})
    messages=route_messages(all_messages,triage_result,members)
    if not messages: messages=all_messages[:2]
    primary_message=messages[0]
    speaking_ids={m["agent_id"] for m in messages}
    room=[{"id":aid,"name":get_agent(aid)["name"],"mark":get_agent(aid)["mark"],"role":get_agent(aid)["role"],"speaking":aid in speaking_ids} for aid in members]
    result=dict(base)
    result.update({"text":primary_message["text"],"agent_id":primary_message["agent_id"],"agent_name":primary_message["name"],"agent_mark":primary_message["mark"],"agent_ids":members,"routed_agent_ids":[m["agent_id"] for m in messages],"room":room,"ensemble_messages":messages,"triage":triage_result.to_dict()})
    return result


def preview(agent_ids: list[str] | None) -> dict[str,Any]:
    base={"card_id":"ambient_agent_preview","kind":"behavior_attention_drift","action":"Ctrl+Alt+B 用当前行为测试","why":"功能型 Agent 圆桌预览。","scenario":"score_improvement"}
    return build_ensemble(base,agent_ids,{"task_hint":"当前学习任务","app_category":"video"})



