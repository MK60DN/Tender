from pathlib import Path
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.daoql import list_events
from app.preassessment import (
    big_five_change_state, big_five_pulse_items, latest_big_five_pulse,
    latest_preassessment, preassessment_items, score_big_five_pulse,
    score_preassessment, submit_big_five_pulse, submit_preassessment,
)


def neutral_responses():
    items = preassessment_items()
    responses = {item['id']: 3 for item in items['big_five']['items']}
    responses.update({item['id']: 3 for item in items['world_interface']['items']})
    return responses


def test_item_inventory_and_estimated_time():
    items = preassessment_items()
    assert len(items['big_five']['items']) == 20
    assert len(items['world_interface']['items']) == 24
    assert items['estimated_minutes'] == '7-9'
    assert 'mbti' not in items
    assert 'jungian' not in items


def test_neutral_profile_is_balanced_and_has_no_type_label():
    profile = score_preassessment(neutral_responses())
    assert all(value['score'] == 0.5 for value in profile['big_five'].values())
    assert all(value['score'] == 0.5 for value in profile['world_interface']['functions'].values())
    assert profile['world_interface']['world_entry']['code'] == 'bridge_first'
    assert 'mbti_preference' not in profile
    assert 'jungian_functions' not in profile


def test_reverse_scored_conscientiousness():
    responses = neutral_responses()
    responses.update({'c1': 5, 'c2': 5, 'c3': 1, 'c4': 5})
    profile = score_preassessment(responses)
    assert profile['big_five']['conscientiousness']['score'] == 1.0
    assert profile['big_five']['conscientiousness']['band'] == 'higher'


def test_world_entry_uses_strict_two_attitudes_by_four_functions():
    responses = neutral_responses()
    extraverted = {'se1', 'se2', 'se3', 'ne1', 'ne2', 'ne3', 'te1', 'te2', 'te3', 'fe1', 'fe2', 'fe3'}
    introverted = {'si1', 'si2', 'si3', 'ni1', 'ni2', 'ni3', 'ti1', 'ti2', 'ti3', 'fi1', 'fi2', 'fi3'}
    responses.update({key: 5 for key in extraverted})
    responses.update({key: 1 for key in introverted})
    objective = score_preassessment(responses)['world_interface']
    assert objective['matrix']['extraverted'] == {'sensation': 'Se', 'intuition': 'Ne', 'thinking': 'Te', 'feeling': 'Fe'}
    assert objective['matrix']['introverted'] == {'sensation': 'Si', 'intuition': 'Ni', 'thinking': 'Ti', 'feeling': 'Fi'}
    assert objective['world_entry']['code'] == 'objective_first'
    responses.update({key: 1 for key in extraverted})
    responses.update({key: 5 for key in introverted})
    subjective = score_preassessment(responses)['world_interface']
    assert subjective['world_entry']['code'] == 'subjective_first'


def test_function_consistency_is_tracked():
    responses = neutral_responses()
    responses.update({'te1': 5, 'te2': 5, 'te3': 5})
    responses.update({'fi1': 1, 'fi2': 5, 'fi3': 3})
    functions = score_preassessment(responses)['world_interface']['functions']
    assert functions['Te']['confidence'] == 'moderate'
    assert functions['Fi']['confidence'] in {'low', 'very_low'}
    assert functions['Te']['consistency'] > functions['Fi']['consistency']


def test_attention_profile_and_correction_use_world_interface():
    responses = neutral_responses()
    responses.update({'ne1': 5, 'ne2': 5, 'ne3': 5, 'ti1': 5, 'ti2': 5, 'ti3': 5})
    responses.update({'c1': 1, 'c2': 1, 'c3': 5, 'c4': 1})
    profile = score_preassessment(responses)
    attention = profile['attention_profile']
    assert any('新颖' in item for item in attention['capture_hypotheses'])
    assert any('切换' in item for item in attention['leakage_hypotheses'])
    ids = {item['id'] for item in profile['cognitive_correction_plan']['items']}
    assert 'idea_sprawl' in ids or 'analysis_paralysis' in ids
    assert '不是注意力测评' in attention['boundary']


def test_correction_plan_has_practice_evidence_and_boundary():
    responses = neutral_responses()
    responses.update({'n1': 5, 'n2': 5, 'n3': 1, 'n4': 1})
    plan = score_preassessment(responses)['cognitive_correction_plan']
    assert plan['items']
    item = plan['items'][0]
    assert item['correction_practice']
    assert item['success_evidence']
    assert item['fade_rule']
    assert item['boundary']
    assert '不是人的缺陷' in plan['principle']
    assert '专业支持' in plan['safe_exit']


def test_profile_uses_support_hypotheses_not_defects():
    profile = score_preassessment(neutral_responses())
    assert profile['friction_hypotheses']
    assert profile['strength_hypotheses']
    assert profile['diagnosis'] is False
    assert profile['user_review_required'] is True
    assert '缺陷' not in profile['notice']


def test_explicit_consent_and_profile_persistence_without_raw_responses():
    student_id = 'preassessment-test-' + uuid.uuid4().hex[:8]
    responses = neutral_responses()
    try:
        submit_preassessment(student_id, responses, consent=False)
    except ValueError as exc:
        assert str(exc) == 'explicit_consent_required'
    else:
        raise AssertionError('consent was not enforced')
    result = submit_preassessment(student_id, responses, consent=True)
    latest = latest_preassessment(student_id)
    assert latest['event_id'] == result['event_id']
    stored = [e for e in list_events(student_id) if e['event_type'] == 'preassessment_profile'][-1]
    assert stored['provenance']['raw_responses_stored'] is False
    assert 'responses' not in stored['payload']


def test_big_five_pulse_tracks_change_from_baseline():
    student_id = 'pulse-test-' + uuid.uuid4().hex[:8]
    submit_preassessment(student_id, neutral_responses(), consent=True)
    pulse = {item['id']: 3 for item in big_five_pulse_items()['items']}
    pulse.update({'pe1': 1, 'pe2': 5, 'pn1': 5, 'pn2': 1})
    scored = score_big_five_pulse(pulse)
    assert set(scored['big_five']) == {'openness', 'conscientiousness', 'extraversion', 'agreeableness', 'emotional_stability'}
    submitted = submit_big_five_pulse(student_id, pulse, consent=True, context={'relationship': 'cooperation', 'role': 'peer'})
    latest = latest_big_five_pulse(student_id)
    assert latest['event_id'] == submitted['event_id']
    change = big_five_change_state(student_id)
    assert change['available'] is True
    assert change['dimensions']['extraversion']['direction'] == 'lower_than_baseline'
    assert any('社交电量' in item for item in change['relationship_support'])
    assert any('评价和冲突' in item for item in change['relationship_support'])


if __name__ == '__main__':
    test_item_inventory_and_estimated_time()
    test_neutral_profile_is_balanced_and_has_no_type_label()
    test_reverse_scored_conscientiousness()
    test_world_entry_uses_strict_two_attitudes_by_four_functions()
    test_function_consistency_is_tracked()
    test_attention_profile_and_correction_use_world_interface()
    test_correction_plan_has_practice_evidence_and_boundary()
    test_profile_uses_support_hypotheses_not_defects()
    test_explicit_consent_and_profile_persistence_without_raw_responses()
    test_big_five_pulse_tracks_change_from_baseline()
    print('ok preassessment tests')