"""Tender governance phases and chain-write guardrails.

The product starts off-chain with a named expert council. A federated BFT
deployment is only eligible after the Tanka partnership and operational gates
are evidenced. Public autonomy is the final phase and cannot be entered by
skipping the federation phase.
"""
from __future__ import annotations

from enum import Enum
from typing import Iterable, Mapping


class GovernancePhase(str, Enum):
    EXPERT_COUNCIL = "expert_council"
    FEDERATED_BFT = "federated_bft"
    PUBLIC_AUTONOMY = "public_autonomy"


PHASE_ORDER = (
    GovernancePhase.EXPERT_COUNCIL,
    GovernancePhase.FEDERATED_BFT,
    GovernancePhase.PUBLIC_AUTONOMY,
)

CURRENT_PHASE = GovernancePhase.EXPERT_COUNCIL

CHAIN_SAFE_RECORDS = frozenset(
    {
        "commitment",
        "attestation",
        "audit_root",
        "rule_version",
        "credential_hash",
        "governance_vote",
        "contribution_report_hash",
    }
)

NEVER_CHAIN_RECORDS = frozenset(
    {
        "raw_dialogue",
        "mental_state",
        "health_signal",
        "biometric_timeseries",
        "minor_identity",
        "raw_learning_event",
        "raw_device_signal",
    }
)

EXPERT_COUNCIL_STANDARDS = {
    "named_members": "专家实名、履历和任期公开",
    "agents_non_voting": "Agent 只提供建议，不参与最终表决",
    "conflict_disclosure": "每次议题前披露利益冲突并回避",
    "rotating_membership": "成员与主席按任期轮换",
    "published_minutes": "发布决议理由、证据范围和少数意见",
    "independent_appeal": "重大争议可提交独立复核",
    "external_audit": "定期接受外部工程、隐私与安全审计",
}

PHASE_POLICIES = {
    GovernancePhase.EXPERT_COUNCIL: {
        "phase": "expert_council",
        "label_zh": "链下专家议会",
        "chain_mode": "off_chain",
        "bft_consensus_enabled": False,
        "external_anchor_enabled": False,
        "open_validator_set": False,
        "decision_body": "实名专家议会",
        "agent_role": "只提供建议，不参与最终表决",
        "human_signature_required": True,
        "allowed_chain_records": [],
        "release_status": "current",
        "purpose": "先验证教育效果、责任边界、申诉和证据规范，不引入链上治理复杂度",
        "council_standards": EXPERT_COUNCIL_STANDARDS,
    },
    GovernancePhase.FEDERATED_BFT: {
        "phase": "federated_bft",
        "label_zh": "多机构联盟 BFT",
        "chain_mode": "permissioned_federated_chain",
        "bft_consensus_enabled": True,
        "external_anchor_enabled": True,
        "open_validator_set": False,
        "decision_body": "Tender、Tanka 与联盟伙伴共同治理",
        "agent_role": "提供证据摘要和审计建议",
        "human_signature_required": True,
        "allowed_chain_records": sorted(CHAIN_SAFE_RECORDS),
        "release_status": "conditional_next",
        "purpose": "只对承诺、签名、规则版本和贡献摘要形成多方共识，不把敏感心智数据上链",
    },
    GovernancePhase.PUBLIC_AUTONOMY: {
        "phase": "public_autonomy",
        "label_zh": "开放验证者与全民自治",
        "chain_mode": "public_or_open_federated_chain",
        "bft_consensus_enabled": True,
        "external_anchor_enabled": True,
        "open_validator_set": True,
        "decision_body": "开放治理与可撤回委任",
        "agent_role": "只做透明的提案、模拟与审计辅助",
        "human_signature_required": True,
        "allowed_chain_records": sorted(CHAIN_SAFE_RECORDS),
        "release_status": "long_term",
        "purpose": "在联盟治理稳定后开放验证者参与，同时保留隐私、申诉、少数保护和紧急制动",
    },
}

TRANSITION_REQUIREMENTS = {
    GovernancePhase.FEDERATED_BFT: {
        "tanka_partnership_signed": "与 Tanka 及联盟伙伴签署正式合作与治理协议",
        "multi_party_charter": "联盟章程、责任边界与退出机制获批",
        "validator_registry": "验证者名单、角色和利益冲突登记完成",
        "key_custody_reviewed": "多方密钥托管与轮换方案通过评审",
        "independent_security_audit": "独立安全审计完成且高风险项关闭",
        "dispute_and_appeal_process": "争议、申诉、撤回和人工复核流程可运行",
        "incident_response_drill": "故障、分叉、密钥泄露和节点失联演练通过",
        "testnet_cycle": "联盟测试网完成至少一个完整治理周期",
        "data_boundary_approved": "链上链下数据边界通过隐私与合规评审",
        "offchain_metrics_stable": "链下专家议会连续运行并达到预设质量门槛",
    },
    GovernancePhase.PUBLIC_AUTONOMY: {
        "federated_phase_stable": "联盟 BFT 已稳定运行并完成独立复审",
        "open_validator_rules": "开放验证者准入、质押、退出与惩罚规则生效",
        "constitution_ratified": "公开治理章程和权利保护条款获批",
        "minority_protection": "少数意见、未成年人和家庭权利保护机制可验证",
        "appeal_and_emergency_powers": "申诉机制与紧急权力日落条款明确",
        "participation_threshold": "真实参与率、代表性与决策质量达到门槛",
        "transparent_audit": "代码、规则版本、资金和治理记录可独立审计",
    },
}


def _phase(value: GovernancePhase | str) -> GovernancePhase:
    if isinstance(value, GovernancePhase):
        return value
    try:
        return GovernancePhase(value)
    except ValueError as exc:
        raise ValueError(f"unknown_governance_phase:{value}") from exc


def governance_phase_policy(phase: GovernancePhase | str = CURRENT_PHASE) -> dict:
    policy = PHASE_POLICIES[_phase(phase)]
    return {**policy, "allowed_chain_records": list(policy["allowed_chain_records"])}


def evaluate_governance_transition(
    current_phase: GovernancePhase | str,
    target_phase: GovernancePhase | str,
    evidence: Mapping[str, bool],
) -> dict:
    current = _phase(current_phase)
    target = _phase(target_phase)
    current_index = PHASE_ORDER.index(current)
    target_index = PHASE_ORDER.index(target)

    if target == current:
        return {
            "allowed": False,
            "result": "no_transition",
            "current_phase": current.value,
            "target_phase": target.value,
            "missing_requirements": [],
            "required_evidence": [],
        }
    if target_index < current_index:
        return {
            "allowed": False,
            "result": "rollback_requires_separate_governance_process",
            "current_phase": current.value,
            "target_phase": target.value,
            "missing_requirements": [],
            "required_evidence": [],
        }
    if target_index > current_index + 1:
        return {
            "allowed": False,
            "result": "phase_skip_rejected",
            "current_phase": current.value,
            "target_phase": target.value,
            "missing_requirements": [],
            "required_evidence": sorted(TRANSITION_REQUIREMENTS[target]),
        }

    requirements = TRANSITION_REQUIREMENTS[target]
    missing = sorted(key for key in requirements if evidence.get(key) is not True)
    return {
        "allowed": not missing,
        "result": "eligible_for_governance_approval" if not missing else "requirements_missing",
        "current_phase": current.value,
        "target_phase": target.value,
        "missing_requirements": missing,
        "missing_descriptions": [requirements[key] for key in missing],
        "required_evidence": sorted(requirements),
        "target_policy": governance_phase_policy(target),
    }


def validate_chain_write(
    record_type: str,
    *,
    phase: GovernancePhase | str,
    contains_sensitive_personal_data: bool = False,
) -> dict:
    policy = governance_phase_policy(phase)
    if contains_sensitive_personal_data:
        return {
            "allowed": False,
            "reason": "sensitive_personal_data_must_remain_off_chain",
            "record_type": record_type,
            "phase": policy["phase"],
        }
    if record_type in NEVER_CHAIN_RECORDS:
        return {
            "allowed": False,
            "reason": "record_type_is_permanently_off_chain",
            "record_type": record_type,
            "phase": policy["phase"],
        }
    if not policy["bft_consensus_enabled"]:
        return {
            "allowed": False,
            "reason": "expert_council_phase_is_off_chain",
            "record_type": record_type,
            "phase": policy["phase"],
        }
    if record_type not in policy["allowed_chain_records"]:
        return {
            "allowed": False,
            "reason": "record_type_not_on_phase_allowlist",
            "record_type": record_type,
            "phase": policy["phase"],
        }
    return {
        "allowed": True,
        "reason": "chain_safe_record_and_phase_policy_satisfied",
        "record_type": record_type,
        "phase": policy["phase"],
    }


def summarize_chain_boundary(records: Iterable[str]) -> dict:
    blocked = sorted({record for record in records if record in NEVER_CHAIN_RECORDS})
    return {
        "permanently_blocked_record_types": list(NEVER_CHAIN_RECORDS),
        "observed_blocked_records": blocked,
        "policy": "链上只保存承诺、签名、审计根、规则版本与治理凭证；原始心智、健康、对话和未成年人身份数据始终留在链下。",
    }
