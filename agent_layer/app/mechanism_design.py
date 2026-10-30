"""Mechanism-design primitives for Tender governance narratives."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from itertools import combinations
from math import factorial
from typing import Callable, Iterable


@dataclass
class Contribution:
    player_id: str
    shapley_value: float
    share: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class Attestation:
    """One independently attributable confirmation for the same claim/event.

    `valid_signature` means that a caller has already verified the signature.
    It does not prove that the signer observed reality correctly.
    """

    signer_id: str
    signer_role: str
    source_group: str
    source_type: str
    valid_signature: bool = True


def shapley_values(
    players: Iterable[str],
    value_fn: Callable[[frozenset[str]], float],
) -> list[Contribution]:
    player_list = list(players)
    n = len(player_list)
    if n == 0:
        return []
    if n > 10:
        raise ValueError("exact_shapley_supports_at_most_10_players")
    values = []
    total = 0.0
    for player in player_list:
        others = [p for p in player_list if p != player]
        score = 0.0
        for k in range(n):
            for subset_tuple in combinations(others, k):
                subset = frozenset(subset_tuple)
                weight = factorial(k) * factorial(n - k - 1) / factorial(n)
                score += weight * (
                    float(value_fn(subset | {player})) - float(value_fn(subset))
                )
        values.append(Contribution(player, round(score, 8), 0.0))
        total += max(0.0, score)
    for item in values:
        item.share = round(item.shapley_value / total, 6) if total > 0 else 0.0
    return values


def contribution_report(
    players: Iterable[str],
    value_fn: Callable[[frozenset[str]], float],
    baseline: float = 0.0,
) -> dict:
    cs = shapley_values(players, value_fn)
    total = float(value_fn(frozenset(players)))
    gap = max((c.shapley_value for c in cs), default=0.0) - min(
        (c.shapley_value for c in cs), default=0.0
    )
    return {
        "contributions": [c.to_dict() for c in cs],
        "coalition_value": total,
        "incremental_value": round(total - baseline, 6),
        "fairness_gap": round(gap, 6),
        "interpretation": (
            "贡献值只在给定的 coalition-value 函数下有意义；"
            "该函数必须来自清楚的实验、审计规则或可复核模型。"
        ),
    }


def expected_reporting_payoff(
    *,
    truthful_value: float,
    misreport_private_gain: float,
    detection_probability: float,
    penalty_if_detected: float,
    shared_value_share: float,
    shared_value: float,
) -> dict:
    p = max(0.0, min(1.0, float(detection_probability)))
    truthful = truthful_value + shared_value_share * shared_value
    misreport = (
        (1 - p)
        * (
            truthful_value
            + misreport_private_gain
            + shared_value_share * shared_value
        )
        - p * penalty_if_detected
    )
    return {
        "truthful_expected_payoff": round(truthful, 6),
        "misreport_expected_payoff": round(misreport, 6),
        "truth_telling_advantage": round(truthful - misreport, 6),
        "incentive_compatible": truthful >= misreport,
        "params": {
            "detection_probability": p,
            "misreport_private_gain": misreport_private_gain,
            "penalty_if_detected": penalty_if_detected,
            "shared_value_share": shared_value_share,
            "shared_value": shared_value,
        },
    }


def bft_threshold(fault_tolerance: int) -> dict:
    """Return classic Byzantine fault-tolerant node and quorum thresholds.

    Assumption: at most f of n validators are faulty and the validator set is
    fixed for the evaluated round. Thresholds alone do not establish BFT; the
    protocol, key custody, membership, view change and recovery must also hold.
    """

    f = int(fault_tolerance)
    if f < 0:
        raise ValueError("fault_tolerance_must_be_non_negative")
    minimum_nodes = 3 * f + 1
    quorum = 2 * f + 1
    return {
        "fault_tolerance": f,
        "minimum_nodes": minimum_nodes,
        "quorum": quorum,
        "honest_majority_required": quorum,
        "formula": "n >= 3f + 1; quorum = 2f + 1",
    }


def _valid_attestations(attestations: Iterable[Attestation]) -> list[Attestation]:
    return [a for a in attestations if a.valid_signature]


def _signer_source_map(attestations: Iterable[Attestation]) -> dict[str, set[tuple[str, str]]]:
    by_signer: dict[str, set[tuple[str, str]]] = {}
    for attestation in attestations:
        by_signer.setdefault(attestation.signer_id, set()).add(
            (attestation.source_group, attestation.source_type)
        )
    return by_signer


def collusion_concentration(attestations: Iterable[Attestation]) -> dict:
    """Measure whether valid confirmations cluster in one evidence source.

    Each signer contributes at most one source. A signer claiming multiple
    source pairs is flagged as a source conflict instead of increasing source
    diversity. High concentration only raises review priority; it is not
    evidence of collusion and must never be an automatic finding of wrongdoing.
    """

    valid = _valid_attestations(attestations)
    by_signer = _signer_source_map(valid)
    conflicting_signers = sorted(
        signer_id for signer_id, pairs in by_signer.items() if len(pairs) > 1
    )
    group_counts: dict[str, int] = {}
    for signer_id, pairs in by_signer.items():
        if len(pairs) > 1:
            source_group = "__conflicting_source__"
        else:
            source_group = next(iter(pairs))[0]
        group_counts[source_group] = group_counts.get(source_group, 0) + 1

    total = len(by_signer)
    if total == 0:
        return {
            "source_distribution": [],
            "distinct_source_groups": 0,
            "dominant_source_group": None,
            "dominant_share": 0.0,
            "herfindahl_index": 0.0,
            "risk_level": "insufficient_evidence",
            "signer_source_conflicts": [],
            "interpretation": "没有有效签名，无法评估来源集中度。",
        }

    distribution = sorted(
        (
            {
                "source_group": group,
                "signer_count": count,
                "share": round(count / total, 6),
            }
            for group, count in group_counts.items()
        ),
        key=lambda item: (-item["signer_count"], item["source_group"]),
    )
    dominant = distribution[0]
    hhi = sum((item["signer_count"] / total) ** 2 for item in distribution)
    if (
        len(distribution) == 1
        or dominant["share"] >= 0.8
        or conflicting_signers
    ):
        risk_level = "high"
    elif dominant["share"] >= 0.6:
        risk_level = "medium"
    else:
        risk_level = "low"
    return {
        "source_distribution": distribution,
        "distinct_source_groups": len(
            [group for group in group_counts if group != "__conflicting_source__"]
        ),
        "dominant_source_group": dominant["source_group"],
        "dominant_share": dominant["share"],
        "herfindahl_index": round(hhi, 6),
        "risk_level": risk_level,
        "signer_source_conflicts": conflicting_signers,
        "interpretation": (
            "来源越集中，越容易形成同源重复确认；同一签署人申报多个来源会形成冲突。"
            "该指标只用于安排复核优先级，不自动判定合谋或责任。"
        ),
    }


def evaluate_attestation_quorum(
    attestations: Iterable[Attestation],
    *,
    fault_tolerance: int,
    eligible_signer_ids: Iterable[str] | None = None,
    required_source_groups: int = 2,
    required_source_types: int = 2,
) -> dict:
    """Evaluate signed confirmations for a policy review gate.

    The gate requires a sufficiently large eligible validator roster, a
    BFT-sized signer quorum, and independent source diversity. Reaching the
    gate means the event is eligible for the next review step; it is not an
    automatic verdict or punishment.
    """

    if required_source_groups < 1 or required_source_types < 1:
        raise ValueError("source_diversity_requirements_must_be_positive")
    thresholds = bft_threshold(fault_tolerance)
    valid = _valid_attestations(attestations)
    valid_signer_ids = {a.signer_id for a in valid}
    eligible = (
        set(eligible_signer_ids)
        if eligible_signer_ids is not None
        else set(valid_signer_ids)
    )
    eligible_valid = [a for a in valid if a.signer_id in eligible]
    ineligible_signer_ids = sorted(valid_signer_ids - eligible)
    eligible_signer_count = len({a.signer_id for a in eligible_valid})
    by_signer = _signer_source_map(eligible_valid)
    conflicting_signers = sorted(
        signer_id for signer_id, pairs in by_signer.items() if len(pairs) > 1
    )
    canonical_pairs = {
        next(iter(pairs))
        for signer_id, pairs in by_signer.items()
        if len(pairs) == 1
    }
    signer_roles = {
        a.signer_role for a in eligible_valid if a.signer_id not in conflicting_signers
    }
    source_groups = {pair[0] for pair in canonical_pairs}
    source_types = {pair[1] for pair in canonical_pairs}
    roster_ok = len(eligible) >= thresholds["minimum_nodes"]
    quorum_reached = roster_ok and eligible_signer_count >= thresholds["quorum"]
    group_diversity_ok = len(source_groups) >= required_source_groups
    type_diversity_ok = len(source_types) >= required_source_types
    source_diversity_ok = (
        group_diversity_ok
        and type_diversity_ok
        and not conflicting_signers
    )
    concentration = collusion_concentration(eligible_valid)
    eligible_for_review = quorum_reached and source_diversity_ok

    if eligible_for_review:
        action = "proceed_to_human_policy_review"
    elif not roster_ok:
        action = "expand_eligible_validator_roster"
    elif conflicting_signers:
        action = "resolve_signer_source_conflicts"
    elif not quorum_reached:
        action = "request_more_signatures"
    else:
        action = "request_more_independent_sources"

    return {
        "thresholds": thresholds,
        "eligible_node_count": len(eligible),
        "minimum_nodes_reached": roster_ok,
        "valid_signature_count": len(valid),
        "eligible_valid_signature_count": len(eligible_valid),
        "valid_signer_count": eligible_signer_count,
        "ineligible_signers": ineligible_signer_ids,
        "signer_source_conflicts": conflicting_signers,
        "distinct_signer_roles": len(signer_roles),
        "distinct_source_groups": len(source_groups),
        "distinct_source_types": len(source_types),
        "required_source_groups": required_source_groups,
        "required_source_types": required_source_types,
        "quorum_reached": quorum_reached,
        "source_diversity_ok": source_diversity_ok,
        "eligible_for_policy_review": eligible_for_review,
        "recommended_action": action,
        "high_priority_review": (
            concentration["risk_level"] == "high" or bool(conflicting_signers)
        ),
        "concentration": concentration,
        "interpretation": (
            "该结果只判断证据是否达到进入人工复核的门槛；"
            "签名真实不保证陈述真实，共识也不能替代申诉、调查与责任认定。"
        ),
    }
