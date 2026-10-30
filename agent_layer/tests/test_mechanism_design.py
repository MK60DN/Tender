from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.mechanism_design import (
    Attestation,
    bft_threshold,
    collusion_concentration,
    contribution_report,
    evaluate_attestation_quorum,
    expected_reporting_payoff,
    shapley_values,
)


def test_shapley_additive_game():
    value = {'A': 3.0, 'B': 5.0, 'C': 2.0}
    result = {
        c.player_id: c.shapley_value
        for c in shapley_values(['A', 'B', 'C'], lambda S: sum(value[p] for p in S))
    }
    assert result == {'A': 3.0, 'B': 5.0, 'C': 2.0}
    report = contribution_report(['A', 'B', 'C'], lambda S: sum(value[p] for p in S))
    assert report['coalition_value'] == 10.0
    assert abs(sum(c['share'] for c in report['contributions']) - 1.0) < 0.001


def test_reporting_incentive_diagnostic():
    weak = expected_reporting_payoff(
        truthful_value=10,
        misreport_private_gain=8,
        detection_probability=.1,
        penalty_if_detected=2,
        shared_value_share=.1,
        shared_value=20,
    )
    strong = expected_reporting_payoff(
        truthful_value=10,
        misreport_private_gain=8,
        detection_probability=.9,
        penalty_if_detected=30,
        shared_value_share=.1,
        shared_value=20,
    )
    assert weak['incentive_compatible'] is False
    assert strong['incentive_compatible'] is True


def test_bft_threshold_for_one_fault():
    result = bft_threshold(1)
    assert result['minimum_nodes'] == 4
    assert result['quorum'] == 3


def test_bft_rejects_two_signatures_for_one_fault():
    attestations = [
        Attestation('student-1', 'student', 'student', 'interaction'),
        Attestation('parent-1', 'parent', 'family', 'feedback'),
    ]
    result = evaluate_attestation_quorum(
        attestations,
        fault_tolerance=1,
        eligible_signer_ids=['student-1', 'parent-1', 'teacher-1', 'auditor-1'],
    )
    assert result['quorum_reached'] is False
    assert result['eligible_for_policy_review'] is False
    assert result['recommended_action'] == 'request_more_signatures'


def test_bft_rejects_three_signatures_from_one_source_group():
    attestations = [
        Attestation('teacher-1', 'teacher', 'school', 'delivery'),
        Attestation('manager-1', 'manager', 'school', 'approval'),
        Attestation('assistant-1', 'assistant', 'school', 'delivery'),
    ]
    result = evaluate_attestation_quorum(
        attestations,
        fault_tolerance=1,
        eligible_signer_ids=['teacher-1', 'manager-1', 'assistant-1', 'auditor-1'],
    )
    assert result['quorum_reached'] is True
    assert result['source_diversity_ok'] is False
    assert result['eligible_for_policy_review'] is False
    assert result['high_priority_review'] is True


def test_bft_diverse_quorum_enters_human_review():
    attestations = [
        Attestation('student-1', 'student', 'student', 'interaction'),
        Attestation('parent-1', 'parent', 'family', 'feedback'),
        Attestation('teacher-1', 'teacher', 'school', 'delivery'),
    ]
    result = evaluate_attestation_quorum(
        attestations,
        fault_tolerance=1,
        eligible_signer_ids=['student-1', 'parent-1', 'teacher-1', 'auditor-1'],
    )
    assert result['minimum_nodes_reached'] is True
    assert result['quorum_reached'] is True
    assert result['source_diversity_ok'] is True
    assert result['eligible_for_policy_review'] is True
    assert result['recommended_action'] == 'proceed_to_human_policy_review'
    assert '只判断证据是否达到进入人工复核的门槛' in result['interpretation']


def test_source_concentration_raises_review_priority_not_guilt():
    attestations = [
        Attestation('teacher-1', 'teacher', 'school', 'delivery'),
        Attestation('manager-1', 'manager', 'school', 'approval'),
        Attestation('assistant-1', 'assistant', 'school', 'delivery'),
    ]
    result = collusion_concentration(attestations)
    assert result['dominant_share'] == 1.0
    assert result['risk_level'] == 'high'
    assert '不自动判定合谋或责任' in result['interpretation']


def test_bft_requires_minimum_validator_roster():
    attestations = [
        Attestation('student-1', 'student', 'student', 'interaction'),
        Attestation('parent-1', 'parent', 'family', 'feedback'),
        Attestation('teacher-1', 'teacher', 'school', 'delivery'),
    ]
    result = evaluate_attestation_quorum(
        attestations,
        fault_tolerance=1,
        eligible_signer_ids=['student-1', 'parent-1', 'teacher-1'],
    )
    assert result['minimum_nodes_reached'] is False
    assert result['quorum_reached'] is False
    assert result['recommended_action'] == 'expand_eligible_validator_roster'


def test_bft_rejects_signer_claiming_multiple_sources():
    attestations = [
        Attestation('student-1', 'student', 'student', 'interaction'),
        Attestation('student-1', 'student', 'device', 'sensor'),
        Attestation('parent-1', 'parent', 'family', 'feedback'),
        Attestation('teacher-1', 'teacher', 'school', 'delivery'),
    ]
    result = evaluate_attestation_quorum(
        attestations,
        fault_tolerance=1,
        eligible_signer_ids=['student-1', 'parent-1', 'teacher-1', 'auditor-1'],
    )
    assert result['quorum_reached'] is True
    assert result['source_diversity_ok'] is False
    assert result['signer_source_conflicts'] == ['student-1']
    assert result['recommended_action'] == 'resolve_signer_source_conflicts'


if __name__ == '__main__':
    test_shapley_additive_game()
    test_reporting_incentive_diagnostic()
    test_bft_threshold_for_one_fault()
    test_bft_rejects_two_signatures_for_one_fault()
    test_bft_rejects_three_signatures_from_one_source_group()
    test_bft_diverse_quorum_enters_human_review()
    test_source_concentration_raises_review_priority_not_guilt()
    test_bft_requires_minimum_validator_roster()
    test_bft_rejects_signer_claiming_multiple_sources()
    print('ok mechanism design tests')
