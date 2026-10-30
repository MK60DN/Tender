from pathlib import Path
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.daoql import list_events
from app.preassessment import latest_preassessment, preassessment_items, score_preassessment, submit_preassessment


def neutral_responses():
    items = preassessment_items()
    responses = {item['id']: 3 for item in items['big_five']['items']}
    responses.update({item['id']: 3 for item in items['mbti']['items']})
    responses.update({item['id']: 3 for item in items['jungian']['items']})
    return responses


def test_item_inventory_and_estimated_time():
    items = preassessment_items()
    assert len(items['big_five']['items']) == 20
    assert len(items['mbti']['items']) == 8
    assert len(items['jungian']['items']) == 8
    assert items['estimated_minutes'] == '5-7'


def test_neutral_profile_is_balanced():
    profile = score_preassessment(neutral_responses())
    assert all(value['score'] == 0.5 for value in profile['big_five'].values())
    assert profile['mbti_preference']['type_hint'] == 'XXXX'
    assert profile['jungian_functions']['confidence'] == 'exploratory_low'


def test_reverse_scored_conscientiousness():
    responses = neutral_responses()
    responses.update({'c1': 5, 'c2': 5, 'c3': 1, 'c4': 5})
    profile = score_preassessment(responses)
    assert profile['big_five']['conscientiousness']['score'] == 1.0
    assert profile['big_five']['conscientiousness']['band'] == 'higher'


def test_mbti_type_is_a_communication_hint_only():
    responses = neutral_responses()
    for item_id in ['ei1', 'ei2', 'sn1', 'sn2', 'tf1', 'tf2', 'jp1', 'jp2']:
        responses[item_id] = 5
    profile = score_preassessment(responses)
    assert profile['mbti_preference']['type_hint'] == 'ENFJ'
    assert '不输出命运或能力结论' in profile['mbti_preference']['notice']


def test_jungian_profile_is_exploratory_not_rank():
    responses = neutral_responses()
    responses.update({item_id: 1 for item_id in ['ne1', 'ni1', 'se1', 'si1', 'te1', 'ti1', 'fe1', 'fi1']})
    responses['ni1'] = 5
    profile = score_preassessment(responses)
    assert profile['jungian_functions']['top_functions'][0] == 'Ni'
    assert '不是神经测量' in profile['jungian_functions']['notice']


def test_attention_profile_links_strengths_to_attention_cost():
    responses = neutral_responses()
    responses.update({"c1": 1, "c2": 1, "c3": 5, "c4": 1})
    responses.update({"o1": 5, "o2": 5, "o3": 1, "o4": 5})
    responses.update({"jp1": 1, "jp2": 1})
    responses["ti1"] = 5
    profile = score_preassessment(responses)
    attention = profile["attention_profile"]
    assert any("新颖" in item for item in attention["capture_hypotheses"])
    assert any("切换" in item for item in attention["leakage_hypotheses"])
    ids = {item["id"] for item in profile["cognitive_correction_plan"]["items"]}
    assert "novelty_switching" in ids
    assert "open_loops" in ids
    assert "不是注意力测评" in attention["boundary"]


def test_cognitive_correction_plan_has_practice_evidence_and_boundary():
    responses = neutral_responses()
    responses.update({"n1": 5, "n2": 5, "n3": 1, "n4": 1})
    profile = score_preassessment(responses)
    plan = profile["cognitive_correction_plan"]
    assert plan["items"]
    item = plan["items"][0]
    assert item["correction_practice"]
    assert item["success_evidence"]
    assert item["fade_rule"]
    assert item["boundary"]
    assert "不是人的缺陷" in plan["principle"]
    assert "专业支持" in plan["safe_exit"]


def test_profile_uses_support_hypotheses_not_defects():
    profile = score_preassessment(neutral_responses())
    assert 'friction_hypotheses' in profile
    assert 'strength_hypotheses' in profile
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


if __name__ == '__main__':
    test_item_inventory_and_estimated_time()
    test_neutral_profile_is_balanced()
    test_reverse_scored_conscientiousness()
    test_mbti_type_is_a_communication_hint_only()
    test_jungian_profile_is_exploratory_not_rank()
    test_profile_uses_support_hypotheses_not_defects()
    test_attention_profile_links_strengths_to_attention_cost()
    test_cognitive_correction_plan_has_practice_evidence_and_boundary()
    test_explicit_consent_and_profile_persistence_without_raw_responses()
    print('ok preassessment tests')
