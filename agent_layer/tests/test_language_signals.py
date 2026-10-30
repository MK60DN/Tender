import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient
from app.main import app
from app.language_signals import analyze_language
from app.tender import compute_state


def test_language_script_and_feature_spans():
    result = analyze_language('我不知道怎么做，老师是不是觉得我不行，我不想学了')
    assert result['status'] == 'ok'
    assert result['language']['label'] == 'zh'
    assert result['feature_vector']['uncertainty'] >= 0.55
    assert result['feature_vector']['mentalizing'] >= 0.55
    assert result['feature_vector']['avoidance'] >= 0.55
    assert all('start' in span and 'end' in span for feature in result['features'] for span in feature['spans'])


def test_language_risk_routes_to_protection_without_diagnosis():
    result = analyze_language('我不想活了，想伤害自己')
    assert result['hypotheses'][0]['id'] == 'safety_check_required'
    assert result['hypotheses'][0]['recommended_response_mode'] == 'protect'
    assert '不是读心、诊断或能力判决' in result['boundary']


def test_language_never_updates_mastery_by_itself():
    state = compute_state('LANGUAGE_ONLY', [{
        'event_type': 'message',
        'payload': {'text': '我明明会，这题肯定没问题，我完全不焦虑'},
    }])
    assert state['knowledge']['mastery'] == 0.5
    assert state['cognitive']['theta'] == 0.0


def test_language_api_contract():
    client = TestClient(app)
    response = client.post('/language/analyze', json={'text': '有点焦虑，不知道下一步怎么办，能帮我吗？'})
    assert response.status_code == 200
    body = response.json()
    assert body['model_version'] == 'tender-language-signals-1.0'
    assert body['hypotheses']
    schema = client.get('/language/schema').json()
    assert '语言检测是弱证据层' in schema['boundary']
    assert '仅凭语言判断知识掌握度' in schema['not_supported']


if __name__ == '__main__':
    test_language_script_and_feature_spans()
    test_language_risk_routes_to_protection_without_diagnosis()
    test_language_never_updates_mastery_by_itself()
    test_language_api_contract()
    print('language signal tests passed')
