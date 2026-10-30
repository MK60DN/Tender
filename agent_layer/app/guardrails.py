"""安全与护栏。"""
from __future__ import annotations
import re

PII_PATTERNS = {
    "phone": re.compile(r"1[3-9]\d{9}"),
    "id_card": re.compile(r"\d{17}[\dXx]"),
    "email": re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"),
}
BANNED = ["自杀", "自残", "暴力", "色情", "毒品"]
HIGH_RISK_ACTIONS = {"notify_parent", "change_group", "formal_comment", "referral"}


def check_text(text: str) -> dict:
    text = text or ""
    hits = [w for w in BANNED if w in text]
    pii = [k for k, p in PII_PATTERNS.items() if p.search(text)]
    return {"allowed": not hits, "banned_hits": hits, "pii_hits": pii,
            "escalate_to_human": bool(hits or pii)}


def requires_human_approval(agent_id: str, action_type: str) -> bool:
    return action_type in HIGH_RISK_ACTIONS or agent_id in {"parent_communication", "sales_ops", "assessment"}


def filter_parent_report(report: dict) -> dict:
    out = {"student_id": report.get("student_id"), "week": report.get("week"),
           "progress_summary": report.get("progress_summary", ""),
           "one_home_action": report.get("one_home_action", ""),
           "privacy_note": "仅展示聚合趋势，不展示原始分数、排名或诊断标签。"}
    return out
