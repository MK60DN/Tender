from pathlib import Path
import json
import os
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ['TENDER_ALLOW_HEADER_IDENTITY'] = '1'

from app.daoql import insert_event
from app.group_chat import (
    approve_shared_branch,
    build_group_model,
    build_peer_model,
    create_group_draft,
    create_group_session,
    create_peer_view_grant,
    create_shared_branch,
    get_group_session,
    ingest_group_event,
    join_group_session,
    record_group_outcome,
    revoke_peer_view_grant,
)
from app.main import app


def _sid(prefix):
    return prefix + '-' + uuid.uuid4().hex[:8]


def _group():
    a = _sid('member-a')
    b = _sid('member-b')
    session = create_group_session('test-chat', 'group project', a)
    group_id = session['group_id']
    join_group_session(group_id, b)
    return group_id, a, b


def test_group_session_membership_and_public_event():
    group_id, a, b = _group()
    event = ingest_group_event(group_id, b, 'message', 'I will send the draft tomorrow.', payload={'topic': 'draft'})
    session = get_group_session(group_id, a)
    assert event['visibility'] == 'group_public'
    assert session['member_count'] == 2
    assert session['boundary'].startswith('Group membership does not grant')
    assert 'group_public.read' in session['your_consent_scopes']
    assert all('consent_scopes' not in member for member in session['members'] if member['actor_id'] != a)


def test_group_model_excludes_private_member_data():
    group_id, a, b = _group()
    insert_event({'event_type': 'private_note', 'student_id': b, 'payload': {'content': 'TOP_SECRET_PRIVATE_STATE'}, 'source': 'unit_test'})
    ingest_group_event(group_id, b, 'question', 'Which decision are we making?')
    model = build_group_model(group_id, a)
    encoded = json.dumps(model, ensure_ascii=False)
    assert model['private_member_models_accessed'] is False
    assert model['open_questions'] == 1
    assert 'TOP_SECRET_PRIVATE_STATE' not in encoded


def test_peer_model_without_grant_is_provisional_relationship_hypothesis():
    group_id, a, b = _group()
    ingest_group_event(group_id, b, 'message', 'I can take the first task.')
    model = build_peer_model(a, b, group_id)
    assert model['status'] == 'provisional'
    assert model['authorization']['status'] == 'none'
    assert model['subject_self_model_accessed'] is False
    assert 'not the subject' in model['boundary'].lower()


def test_peer_model_uses_only_authorized_shared_view_scopes():
    group_id, a, b = _group()
    for index in range(3):
        ingest_group_event(group_id, b, 'message', f'public message {index}')
    grant = create_peer_view_grant(b, a, group_id, 'project coordination', ['role_task', 'commitment'], valid_hours=2)
    model = build_peer_model(a, b, group_id)
    assert grant['status'] == 'active'
    assert model['status'] == 'corroborated'
    assert model['authorization']['authorized_scopes'] == ['commitment', 'role_task']
    assert model['subject_self_model_accessed'] is False


def test_peer_view_revocation_expires_derived_model():
    group_id, a, b = _group()
    for index in range(3):
        ingest_group_event(group_id, b, 'message', f'public message {index}')
    grant = create_peer_view_grant(b, a, group_id, 'project coordination', ['role_task'], valid_hours=2)
    build_peer_model(a, b, group_id)
    revoked = revoke_peer_view_grant(grant['grant_id'], b)
    assert revoked['status'] == 'revoked'
    rebuilt = build_peer_model(a, b, group_id)
    assert rebuilt['authorization']['status'] == 'none'
    assert rebuilt['status'] == 'provisional'


def test_shared_branch_requires_participant_approval():
    group_id, a, b = _group()
    c = _sid('member-c')
    join_group_session(group_id, c)
    bilateral = create_shared_branch(group_id, a, 'task', {'task': 'draft the agenda'}, [a, b])
    assert bilateral['status'] == 'proposed'
    assert bilateral['visibility'] == 'bilateral'
    approved = approve_shared_branch(bilateral['branch_id'], b)
    assert approved['status'] == 'active'
    model_c = build_group_model(group_id, c)
    assert bilateral['branch_id'] not in {branch['branch_id'] for branch in model_c['shared_branches']}
    group_branch = create_shared_branch(group_id, a, 'task', {'task': 'shared deadline'}, [a, b, c], visibility='group')
    approve_shared_branch(group_branch['branch_id'], b)
    approve_shared_branch(group_branch['branch_id'], c)
    model_c = build_group_model(group_id, c)
    assert group_branch['branch_id'] in {branch['branch_id'] for branch in model_c['shared_branches']}


def test_group_draft_never_auto_sends():
    group_id, a, _ = _group()
    draft = create_group_draft(group_id, a, 'clarify')
    assert draft['status'] == 'draft_only'
    assert draft['auto_send'] is False
    assert draft['requires_user_confirmation'] is True


def test_group_outcome_requires_shared_branch_approval():
    group_id, a, b = _group()
    outcome = record_group_outcome(group_id, a, 'Ship the shared draft on Friday.', [{'owner': a, 'task': 'draft'}], ['review'])
    assert outcome['status'] == 'pending_shared_approval'
    assert outcome['shared_branch']['status'] == 'proposed'
    assert set(outcome['shared_branch']['participants']) == {a, b}


def test_group_chat_api_and_observer_identity():
    from fastapi.testclient import TestClient
    group_id, a, b = _group()
    with TestClient(app) as client:
        headers_a = {'X-Tender-Actor': a, 'X-Tender-Role': 'learner', 'X-Tender-Learner': a}
        headers_b = {'X-Tender-Actor': b, 'X-Tender-Role': 'learner', 'X-Tender-Learner': b}
        client.post(f'/group-sessions/{group_id}/events', headers=headers_b, json={'event_type': 'message', 'content': 'hello group'})
        detail = client.get(f'/group-sessions/{group_id}', headers=headers_a)
        assert detail.status_code == 200
        model = client.get(f'/peer-models/{a}/{b}', headers=headers_a, params={'group_id': group_id})
        assert model.status_code == 200
        denied = client.get(f'/peer-models/{a}/{b}', headers=headers_b, params={'group_id': group_id})
        assert denied.status_code == 403


if __name__ == '__main__':
    for name, fn in list(globals().items()):
        if name.startswith('test_') and callable(fn):
            fn()
    print('ok group chat tests')
