from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.governance_phases import (
    GovernancePhase,
    TRANSITION_REQUIREMENTS,
    evaluate_governance_transition,
    governance_phase_policy,
    summarize_chain_boundary,
    validate_chain_write,
)


def test_current_phase_is_offchain_expert_council():
    policy = governance_phase_policy()
    assert policy['phase'] == 'expert_council'
    assert policy['chain_mode'] == 'off_chain'
    assert policy['bft_consensus_enabled'] is False
    assert policy['human_signature_required'] is True
    assert policy['agent_role'] == '只提供建议，不参与最终表决'
    assert policy['council_standards']['rotating_membership'] == '成员与主席按任期轮换'
    assert policy['council_standards']['published_minutes'] == '发布决议理由、证据范围和少数意见'


def test_expert_council_rejects_any_chain_write():
    result = validate_chain_write('commitment', phase=GovernancePhase.EXPERT_COUNCIL)
    assert result['allowed'] is False
    assert result['reason'] == 'expert_council_phase_is_off_chain'


def test_cannot_skip_from_expert_council_to_public_autonomy():
    result = evaluate_governance_transition(
        GovernancePhase.EXPERT_COUNCIL,
        GovernancePhase.PUBLIC_AUTONOMY,
        {},
    )
    assert result['allowed'] is False
    assert result['result'] == 'phase_skip_rejected'


def test_federation_requires_tanka_agreement_and_operational_gates():
    result = evaluate_governance_transition(
        GovernancePhase.EXPERT_COUNCIL,
        GovernancePhase.FEDERATED_BFT,
        {'tanka_partnership_signed': True},
    )
    assert result['allowed'] is False
    assert 'tanka_partnership_signed' not in result['missing_requirements']
    assert 'validator_registry' in result['missing_requirements']
    assert 'data_boundary_approved' in result['missing_requirements']


def test_federation_opens_only_after_all_gates_pass():
    evidence = {key: True for key in TRANSITION_REQUIREMENTS[GovernancePhase.FEDERATED_BFT]}
    result = evaluate_governance_transition(
        GovernancePhase.EXPERT_COUNCIL,
        GovernancePhase.FEDERATED_BFT,
        evidence,
    )
    assert result['allowed'] is True
    assert result['result'] == 'eligible_for_governance_approval'
    assert result['target_policy']['bft_consensus_enabled'] is True
    assert result['target_policy']['chain_mode'] == 'permissioned_federated_chain'


def test_chain_accepts_only_commitments_after_federation():
    assert validate_chain_write(
        'commitment', phase=GovernancePhase.FEDERATED_BFT
    )['allowed'] is True
    assert validate_chain_write(
        'audit_root', phase=GovernancePhase.FEDERATED_BFT
    )['allowed'] is True
    assert validate_chain_write(
        'unlisted_marketing_profile', phase=GovernancePhase.FEDERATED_BFT
    )['allowed'] is False


def test_raw_mental_and_health_data_never_go_on_chain():
    for record_type in ['raw_dialogue', 'mental_state', 'health_signal', 'minor_identity']:
        result = validate_chain_write(record_type, phase=GovernancePhase.PUBLIC_AUTONOMY)
        assert result['allowed'] is False
        assert result['reason'] == 'record_type_is_permanently_off_chain'
    sensitive = validate_chain_write(
        'attestation',
        phase=GovernancePhase.PUBLIC_AUTONOMY,
        contains_sensitive_personal_data=True,
    )
    assert sensitive['allowed'] is False
    assert sensitive['reason'] == 'sensitive_personal_data_must_remain_off_chain'


def test_public_autonomy_requires_federated_phase_and_protections():
    evidence = {key: True for key in TRANSITION_REQUIREMENTS[GovernancePhase.PUBLIC_AUTONOMY]}
    result = evaluate_governance_transition(
        GovernancePhase.FEDERATED_BFT,
        GovernancePhase.PUBLIC_AUTONOMY,
        evidence,
    )
    assert result['allowed'] is True
    assert result['target_policy']['open_validator_set'] is True
    assert 'raw_dialogue' in summarize_chain_boundary(['commitment', 'raw_dialogue'])['observed_blocked_records']


if __name__ == '__main__':
    test_current_phase_is_offchain_expert_council()
    test_expert_council_rejects_any_chain_write()
    test_cannot_skip_from_expert_council_to_public_autonomy()
    test_federation_requires_tanka_agreement_and_operational_gates()
    test_federation_opens_only_after_all_gates_pass()
    test_chain_accepts_only_commitments_after_federation()
    test_raw_mental_and_health_data_never_go_on_chain()
    test_public_autonomy_requires_federated_phase_and_protections()
    print('ok governance phase tests')
