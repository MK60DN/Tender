"""First-stage triage agent for Tender ambient support."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any

@dataclass
class TriageResult:
    problem_type: str
    label: str
    confidence: float
    risk_level: str
    agent_ids: list[str]
    evidence: list[str]
    alternative: str
    rationale: str
    def to_dict(self) -> dict[str, Any]: return asdict(self)

RISK_WORDS=("自杀","不想活","伤害自己","自残","结束生命","杀了我","被打","家暴","虐待","活不下去")
ANXIETY_WORDS=("焦虑","紧张","害怕","恐慌","慌","崩溃","压力好大","压力太大","心慌","担心","不放心","不安","情绪")
SUBJECT_WORDS=("不会","不懂","错题","概念","公式","数学","物理","化学","生物","英语","语文","历史","地理","政治","题目","知识点","先修")
FATIGUE_WORDS=("困","累","疲劳","头痛","头晕","恶心","失眠","没睡","没吃饭","饿","眼睛疼","眼睛酸","身体不舒服")
ATTENTION_WORDS=("走神","注意力","专注","刷视频","刷手机","切窗","静不下","拖延","开始不了","坐不住","分心")
PLANNING_WORDS=("计划","安排","优先级","时间不够","复习","目标","进度","怎么开始","下一步","先做","执行","排一周","保住","最小连续","按计划","完不成")
STATE_REVIEW_WORDS=("我的状态","我现在","我怎么了","帮我看看","怎么办","当前状态","状态是","综合我的","综合我","是否在改善")
REFLECTIVE_WORDS=("发现","觉得","担心","害怕","做不到","完不成","卡住","按计划","尝试","改善","变化","不同","一样","算不算","是不是","为什么","说明","复盘","迁移","模式","效率","节奏","节律","下一步","怎么","如何","反馈","记不住")
CAREER_WORDS=("专业","志愿","职业","职业方向","未来","选科","大学","就业","转行","产品经理","作品集","实习","能力验证")
REGISTRATION_WORDS=("报名","确认","缴费","照片","高考报名","截止")

def triage(user_message: str = "", signals: dict[str,Any] | None = None) -> TriageResult:
    text=" ".join(str(user_message or "").split()); signals=signals or {}; evidence=[]
    if any(w in text for w in RISK_WORDS):
        return TriageResult("acute_safety","高风险安全",.95,"high",["safety_officer","psychologist"],["消息包含高风险安全词"],"也可能是在转述他人的风险；需要先确认对象与即时安全性。","安全风险优先于学习建议，先进入保护与人工升级流程。")
    if any(w in text for w in ANXIETY_WORDS):
        agents=["psychologist","neuro_cognition"]; evidence=["消息包含焦虑/情绪线索"]
        if any(w in text for w in ("睡不着","没吃饭","头痛","心慌","身体")):
            agents.append("nutritionist"); evidence.append("同时出现身体状态线索")
        return TriageResult("anxiety_emotion","焦虑与情绪负荷",.86,"medium" if "崩溃" in text or "恐慌" in text else "low",agents,evidence,"也可能是任务不清或知识卡点引发的焦虑；先降低负荷，再定位学习问题。","先由心理调节师处理威胁与回避，再由神经认知师降低负荷；学科专家暂不介入。")
    if any(w in text for w in FATIGUE_WORDS):
        return TriageResult("fatigue_health","疲劳与身体状态",.82,"low",["nutritionist","neuro_cognition"],["消息包含疲劳/身体状态线索"],"也可能只是短暂停顿；结合睡眠、饮食和持续时间继续确认。","先检查睡眠、饮食、补水和恢复，再决定是否继续学习。")
    if any(w in text for w in ATTENTION_WORDS):
        return TriageResult("attention_focus","注意力与任务启动",.84,"low",["neuro_cognition","learning_strategist"],["消息包含注意力/启动困难线索"],"也可能是任务过大或情绪回避；结合焦虑和任务粒度继续确认。","先缩小入口、降低切换成本，再由学习策略师设计最小行动。")
    if any(w in text for w in REGISTRATION_WORDS):
        return TriageResult("registration_process","报名与高利害流程",.9,"medium",["safety_officer","learning_strategist","career_advisor"],["消息包含报名/流程线索"],"也可能是单纯查询流程；仍需保护隐私并逐项核对。","安全保护官负责隐私和流程边界，策略师负责逐项完成，生涯规划师只在专业选择相关时介入。")
    context = signals.get("tender_context") or {}
    state_review = any(word in text for word in STATE_REVIEW_WORDS)
    if context and not state_review and ("我" in text or "这" in text):
        state_review = any(word in text for word in REFLECTIVE_WORDS)
    if context and state_review:
        pre = context.get("preassessment") or {}
        attention = pre.get("attention_profile") or {}
        mental = context.get("mentalization") or {}
        agents = ["metacognition_coach", "neuro_cognition", "learning_strategist"]
        evidence = ["用户询问当前状态或下一步"]
        if attention.get("leakage"):
            evidence.append("预检测提供注意泄漏先验")
        if mental.get("summary"):
            evidence.append(f"Tender当前主要假设：{mental.get('summary')}")
        return TriageResult(
            "state_review",
            "状态回顾与下一步",
            0.78,
            "low",
            agents,
            evidence,
            "Tender模型是带不确定性的假设，仍需要用户的真实反馈和行动结果校准。",
            "先用Tender建模证据给出1–2个状态假设，再由元认知教练和策略师给出一个最小行动。",
        )

    if any(w in text for w in CAREER_WORDS):
        return TriageResult("career_path","专业与生涯路径",.8,"low",["career_advisor","learning_strategist"],["消息包含专业/生涯线索"],"也可能是对当前学习任务的焦虑；先区分长期目标与当下卡点。","先澄清目标与兴趣证据，再把目标拆成当前学习动作。")
    if any(w in text for w in SUBJECT_WORDS):
        return TriageResult("knowledge_gap","知识或错因卡点",.83,"low",["subject_expert","learning_strategist","metacognition_coach"],["消息包含知识点/错题线索"],"也可能是注意力或情绪造成暂时做不出；需要结合状态继续确认。","先由学科专家判断概念、条件、公式或计算，再由策略师缩小练习。")
    if any(w in text for w in PLANNING_WORDS):
        return TriageResult("planning","计划与优先级",.78,"low",["learning_strategist","metacognition_coach"],["消息包含计划/优先级线索"],"也可能是目标不清或情绪负荷；先确认当前最小任务。","先把计划缩小为可执行动作，再用元认知复盘检验策略。")
    category=str(signals.get("app_category") or ""); kind=str(signals.get("kind") or "")
    if "deep_focus" in kind or "recovery" in kind:
        return TriageResult("focus_recovery","专注后的恢复",.65,"low",["neuro_cognition","nutritionist","metacognition_coach"],["深度专注信号"],"也可能只是正常持续推进。","优先做短提取与恢复，不调用学科专家。")
    if category in {"video","game"} or "attention" in kind:
        return TriageResult("attention_focus","注意力与任务切换",.68,"low",["neuro_cognition","learning_strategist"],["检测到偏离或切换信号"],"也可能是在主动休息。","先降低切换成本，不调用学科专家。")
    return TriageResult("unclear","问题尚不明确",.35,"low",["learning_strategist","metacognition_coach"],["信息不足"],"可能是知识、情绪、注意力或任务设计问题。","先问一个最小澄清问题，不贸然调用专业 Agent。")

def route_messages(messages: list[dict[str,Any]], result: TriageResult, available_agent_ids: list[str]) -> list[dict[str,Any]]:
    available=set(available_agent_ids)
    by_id={m.get("agent_id"):m for m in messages}
    routed=[aid for aid in result.agent_ids if aid in available and aid in by_id] or result.agent_ids[:2]
    return [by_id[aid] for aid in routed if aid in by_id]

