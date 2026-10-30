from uuid import uuid4
from fastapi.testclient import TestClient
from app.main import app
from app.identity import grant_consent, revoke_consent, get_consent, authorize_learner, Principal


def _headers(client, actor, role, learner_id):
    r = client.post('/auth/demo-session', json={'actor_id': actor, 'role': role, 'learner_id': learner_id})
    assert r.status_code == 200, r.text
    return {'Authorization': 'Bearer ' + r.json()['token']}


def test_identity_gate_and_consent():
    client = TestClient(app)
    assert client.get('/learner/home/S01').status_code == 401
    learner = _headers(client, 'S01', 'learner', 'S01')
    assert client.get('/learner/home/S01', headers=learner).status_code == 200
    other = _headers(client, 'S02', 'learner', 'S02')
    assert client.get('/learner/home/S01', headers=other).status_code == 403
    assert client.get('/audit', headers=learner).status_code == 403
    admin = _headers(client, 'admin', 'admin', None)
    assert client.get('/audit', headers=admin).status_code == 200
    assert client.get('/roles?surface=all', headers=learner).status_code == 403
    assert client.get('/roles?surface=all', headers=admin).status_code == 200
    assert client.get('/openapi.json').status_code == 404
    assert client.get('/docs').status_code == 404
    parent = _headers(client, 'P-S01', 'parent', 'S01')
    assert client.get('/learner/home/S01', headers=parent).status_code == 200
    mismatch = client.post('/agents/generate', headers=learner, json={
        'owner_id': 'S02', 'need': '给出一个支持', 'category': 'learning_support'
    })
    assert mismatch.status_code == 403
    assert client.get('/auth/me', headers=learner).json()['actor_id'] == 'S01'

    learner_id = 'CONSENT_' + uuid4().hex[:8]
    guardian_id = 'G_' + uuid4().hex[:8]
    guardian = _headers(client, guardian_id, 'parent', learner_id)
    req = client.post('/guardian/requests', headers=guardian, json={
        'learner_id': learner_id, 'guardian_id': guardian_id, 'evidence': 'demo verification'
    })
    assert req.status_code == 200
    assert req.json()['status'] == 'pending_verification'
    assert client.get('/learner/home/' + learner_id, headers=guardian).status_code == 403
    verify = client.post(f'/guardian/requests/{learner_id}/{guardian_id}/verify', headers=admin, json={
        'scopes': ['learning_support', 'family_summary']
    })
    assert verify.status_code == 200
    assert verify.json()['verification_status'] == 'verified'
    assert client.get('/learner/home/' + learner_id, headers=guardian).status_code == 200
    revoke = client.post(f'/guardian/requests/{learner_id}/{guardian_id}/revoke', headers=guardian)
    assert revoke.status_code == 200
    assert client.get('/learner/home/' + learner_id, headers=guardian).status_code == 403
    chain = client.get('/audit/verify', headers=admin)
    assert chain.status_code == 200
    assert chain.json()['valid'] is True

    revoked_actor = 'REVOKE_' + uuid4().hex[:8]
    session_headers = _headers(client, revoked_actor, 'learner', revoked_actor)
    assert client.get('/auth/me', headers=session_headers).status_code == 200
    assert client.post('/auth/logout', headers=session_headers).status_code == 200
    assert client.get('/auth/me', headers=session_headers).status_code == 401
