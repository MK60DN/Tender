"""Agent 配置加载与最小决策逻辑。"""
from __future__ import annotations
import pathlib, yaml

AGENTS_DIR = pathlib.Path(__file__).resolve().parent.parent / "agents"


def list_agents():
    out = []
    for p in sorted(AGENTS_DIR.glob("*.yaml")):
        cfg = yaml.safe_load(p.read_text(encoding="utf-8"))
        out.append(cfg)
    return out


def get_agent(agent_id: str):
    p = AGENTS_DIR / (agent_id + ".yaml")
    if not p.exists():
        return None
    return yaml.safe_load(p.read_text(encoding="utf-8"))


def _message(agent_id, student_id, intent, action, evidence, policy):
    return {
        "message_id": "msg_" + agent_id + "_" + str(student_id),
        "from_agent": agent_id,
        "to_agent": "user",
        "student_id": student_id,
        "intent": intent,
        "action": action,
        "evidence": evidence,
        "policy": policy,
        "status": "proposed",
    }


def invoke(agent_id: str, student_id: str, message: str, state: dict):
    cfg = get_agent(agent_id)
    if cfg is None:
        return {"error": "unknown_agent", "agent_id": agent_id}
    mastery = float(state.get("knowledge", {}).get("mastery", 0.5))
    bias = float(state.get("metacognition", {}).get("jol_bias", 0.0))
    hesitation = float(state.get("metacognition", {}).get("hesitation", 0.0))
    evidence = {"n_events": state.get("n_events", 0), "state_version": state.get("timestamp")}

    if agent_id == "student_tutor":
        level = "minimal_hint" if mastery >= 0.6 else "worked_step"
        return _message(agent_id, student_id, "tutor", {"hint_level": level,
                         "text": "先说说你卡在哪一步，我再给最小提示。"}, evidence, cfg["policy"])

    if agent_id == "metacognition_coach":
        if hesitation >= 0.5 and mastery < 0.5:
            quadrant = "high_hesitation_wrong"
        elif hesitation >= 0.5:
            quadrant = "high_hesitation_right"
        elif mastery < 0.5:
            quadrant = "low_hesitation_wrong"
        else:
            quadrant = "low_hesitation_right"
        return _message(agent_id, student_id, "metacognition", {
            "quadrant": quadrant,
            "prompt": "你刚才在这里停了一下：你觉得自己是不确定，还是只是需要更多时间？",
            "jol_bias": bias, "hesitation": hesitation}, evidence, cfg["policy"])

    if agent_id == "teacher_copilot":
        return _message(agent_id, student_id, "teacher_support", {
            "summary": {"mastery": mastery, "jol_bias": bias, "hesitation": hesitation},
            "suggestion": "优先确认该生是知识缺口还是信心偏差；把证据链接到 DAOQL。"},
            evidence, cfg["policy"])

    if agent_id == "group_facilitator":
        return _message(agent_id, student_id, "group_rotation", {
            "clique_warning": state.get("group", {}).get("clustering", 0) > 0.6,
            "bridge_suggestion": "本轮安排一个跨组桥接角色。",
            "group_state": state.get("group", {})}, evidence, cfg["policy"])

    if agent_id == "safety_guardrail":
        banned = ["自杀", "自残", "暴力"]
        hit = [w for w in banned if w in (message or "")]
        return _message(agent_id, student_id, "safety_check", {
            "allowed": len(hit) == 0, "hits": hit,
            "escalate_to_human": len(hit) > 0}, evidence, cfg["policy"])

    if agent_id == "data_steward":
        return _message(agent_id, student_id, "data_quality", {
            "n_events": state.get("n_events", 0),
            "has_consent": True,
            "retention_days": 365}, evidence, cfg["policy"])

    # 其余 Agent 返回最小可执行建议
    return _message(agent_id, student_id, cfg["role"], {
        "text": "Agent 骨架已就绪；接入对应工具后返回真实动作。",
        "role": cfg["role"]}, evidence, cfg["policy"])
