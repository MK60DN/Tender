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
        assert len(data['mbti']['items']) == 8
        assert len(data['jungian']['items']) == 8
        assert data['estimated_minutes'] == '5-7'


def test_preassessment_submit_requires_identity_and_explicit_consent():
    with TestClient(app) as client:
        student_id = 'preassess-api-' + uuid.uuid4().hex[:8]
        responses = {}
        catalog = client.get('/preassessment/items').json()
        for section in ['big_five', 'mbti', 'jungian']:
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
        fetched = client.get(f'/preassessment/profile/{student_id}', headers=headers)
        assert fetched.status_code == 200
        assert fetched.json()['event_id'] == submitted.json()['event_id']


if __name__ == '__main__':
    test_preassessment_items_are_public()
    test_preassessment_submit_requires_identity_and_explicit_consent()
    print('ok preassessment API tests')
