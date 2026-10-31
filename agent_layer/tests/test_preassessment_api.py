from pathlib import Path
import os
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ['TENDER_ALLOW_HEADER_IDENTITY'] = '1'
from fastapi.testclient import TestClient
from app.main import app


def test_preassessment_items_are_public():
    with TestClient(app) as client:
        response = client.get('/preassessment/items')
        assert response.status_code == 200
        data = response.json()
        assert len(data['big_five']['items']) == 20
        assert len(data['world_interface']['items']) == 24
        assert data['estimated_minutes'] == '7-9'


def test_preassessment_submit_requires_identity_and_explicit_consent():
    with TestClient(app) as client:
        student_id = 'preassess-api-' + uuid.uuid4().hex[:8]
        responses = {}
        catalog = client.get('/preassessment/items').json()
        for section in ['big_five', 'world_interface']:
            responses.update({item['id']: 3 for item in catalog[section]['items']})
        headers = {
            'X-Tender-Actor': student_id,
            'X-Tender-Role': 'learner',
            'X-Tender-Learner': student_id,
        }
        unauthenticated = client.post(
            f'/preassessment/submit/{student_id}',
            json={'responses': responses, 'consent': True},
        )
        assert unauthenticated.status_code == 401
        no_consent = client.post(
            f'/preassessment/submit/{student_id}',
            json={'responses': responses, 'consent': False},
            headers=headers,
        )
        assert no_consent.status_code == 422
        submitted = client.post(
            f'/preassessment/submit/{student_id}',
            json={'responses': responses, 'consent': True},
            headers=headers,
        )
        assert submitted.status_code == 200
        profile = submitted.json()['profile']
        assert profile['diagnosis'] is False
        assert profile['user_review_required'] is True
        assert profile['world_interface']['world_entry']['code'] in {'objective_first','subjective_first','bridge_first'}
        fetched = client.get(f'/preassessment/profile/{student_id}', headers=headers)
        assert fetched.status_code == 200
        assert fetched.json()['event_id'] == submitted.json()['event_id']

def test_big_five_pulse_api():
    with TestClient(app) as client:
        student_id = 'pulse-api-' + uuid.uuid4().hex[:8]
        catalog = client.get('/preassessment/items').json()
        responses = {}
        for section in ['big_five', 'world_interface']:
            responses.update({item['id']: 3 for item in catalog[section]['items']})
        headers = {'X-Tender-Actor': student_id, 'X-Tender-Role': 'learner', 'X-Tender-Learner': student_id}
        baseline = client.post(f'/preassessment/submit/{student_id}', json={'responses': responses, 'consent': True}, headers=headers)
        assert baseline.status_code == 200
        pulse_items = client.get('/preassessment/pulse/items')
        assert pulse_items.status_code == 200
        pulse = {item['id']: 3 for item in pulse_items.json()['items']}
        pulse.update({'pe1': 1, 'pe2': 5})
        posted = client.post(f'/preassessment/pulse/{student_id}', json={'responses': pulse, 'consent': True, 'context': {'relationship': 'peer'}}, headers=headers)
        assert posted.status_code == 200
        fetched = client.get(f'/preassessment/pulse/{student_id}', headers=headers)
        assert fetched.status_code == 200
        assert fetched.json()['latest']['event_id'] == posted.json()['event_id']
        assert fetched.json()['change']['dimensions']['extraversion']['direction'] == 'lower_than_baseline'

if __name__ == '__main__':
    test_preassessment_items_are_public()
    test_preassessment_submit_requires_identity_and_explicit_consent()
    test_big_five_pulse_api()
    print('ok preassessment API tests')
