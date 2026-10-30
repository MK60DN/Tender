# -*- coding: utf-8 -*-
from uuid import uuid4
import re
from fastapi.testclient import TestClient
from app.main import app
from app.ambient import plan_ambient_card, ambient_status


def _session(client, actor_id):
    r=client.post('/auth/demo-session',json={'actor_id':actor_id,'role':'learner','learner_id':actor_id})
    assert r.status_code==200,r.text
    return {'Authorization':'Bearer '+r.json()['token']}


def test_ambient_mode_planner_and_feedback():
    learner='AMB_'+uuid4().hex[:8]
    shown=plan_ambient_card(learner,{'hesitation':0.8,'repeated_errors':3},actor_id=learner)
    assert shown['status']=='shown'
    assert shown['card']['kind']=='stuck'
    cooldown=plan_ambient_card(learner,{'hesitation':0.8,'repeated_errors':3},actor_id=learner)
    assert cooldown['status']=='cooling_down'
    forced=plan_ambient_card(learner,{'explicit_need':True},actor_id=learner,force=True)
    assert forced['status']=='shown'
    silence=__import__('app.ambient',fromlist=['record_ambient_feedback']).record_ambient_feedback(learner,forced['card']['card_id'],'silence',actor_id=learner)
    assert silence['feedback']=='silence'
    silent=plan_ambient_card(learner,{'explicit_need':True},actor_id=learner)
    assert silent['status']=='silenced'
    assert ambient_status(learner)['quiet'] is True

    gaokao = plan_ambient_card('AMB_GK_' + uuid4().hex[:8], {'scenario':'gaokao_registration','deadline_hours':12,'missing_items':2,'confirmation_pending':True}, actor_id='gaokao')
    assert gaokao['status'] == 'shown'
    assert gaokao['card']['kind'] == 'registration_deadline'
    assert re.search(r'\d{6,}', gaokao['card']['text']) is None
    score = plan_ambient_card('AMB_SCORE_' + uuid4().hex[:8], {'scenario':'score_improvement','days_to_target':5,'weak_skill_count':3}, actor_id='score')
    assert score['status'] == 'shown'
    assert score['card']['kind'] == 'score_improvement_priority'

    behavior = plan_ambient_card('AMB_BEHAVIOR_' + uuid4().hex[:8], {'scenario':'score_improvement','app_category':'video','focus_minutes':3,'activity_events_per_min':8}, actor_id='behavior')
    assert behavior['status'] == 'shown'
    assert behavior['card']['kind'] == 'behavior_attention_drift'

    client=TestClient(app)
    learner2='AMB_HTTP_'+uuid4().hex[:8]
    headers=_session(client,learner2)
    other=_session(client,'AMB_OTHER_'+uuid4().hex[:8])
    payload={'signals':{'idle_seconds':100,'visibility_switches':4},'force':False}
    assert client.post(f'/ambient/plan/{learner2}',json=payload).status_code==401
    r=client.post(f'/ambient/plan/{learner2}',headers=headers,json=payload)
    assert r.status_code==200,r.text
    assert r.json()['status']=='shown'
    card_id=r.json()['card']['card_id']
    f=client.post(f'/ambient/feedback/{learner2}',headers=headers,json={'card_id':card_id,'feedback':'useful'})
    assert f.status_code==200 and f.json()['feedback']=='useful'
    assert client.get(f'/ambient/status/{learner2}',headers=headers).status_code==200
    assert client.get(f'/ambient/status/{learner2}',headers=other).status_code==403
    reply=client.post(f'/ambient/reply/{learner2}',headers=headers,json={'card_id':card_id,'message':'我不会这一步','ensemble_ids':['learning_strategist','subject_expert','neuro_cognition']})
    assert reply.status_code==200,reply.text
    assert reply.json()['reply_card']['kind']=='dialogue_scaffold'
    assert reply.json()['reply_card']['agent_id']=='subject_expert'
    reply_card=reply.json()['reply_card']; assert reply_card['ensemble_messages']; assert {m['agent_id'] for m in reply_card['ensemble_messages']}.issubset({m['id'] for m in reply_card['room']})
    assert client.post(f'/ambient/reply/{learner2}',headers=other,json={'card_id':card_id,'message':'你好'}).status_code==403
    personas=client.get('/ambient/personas')
    assert personas.status_code==200 and personas.json()['count']>=6
    selected=client.post(f'/ambient/persona/{learner2}',headers=headers,json={'persona_id':'nutritionist'})
    assert selected.status_code==200,selected.text
    assert selected.json()['preview']['agent_id']=='nutritionist'
    assert client.get(f'/ambient/persona/{learner2}',headers=headers).json()['agent_ids']==['nutritionist']
    room=client.post(f'/ambient/ensemble/{learner2}',headers=headers,json={'persona_ids':['learning_strategist','subject_expert','neuro_cognition']})
    assert room.status_code==200,room.text
    assert len(room.json()['room'])==3
    ensemble_plan=client.post(f'/ambient/plan/{learner2}',headers=headers,json={'signals':{'app_category':'video','focus_minutes':3,'agent_ids':['learning_strategist','subject_expert','neuro_cognition']},'force':True})
    assert ensemble_plan.status_code==200,ensemble_plan.text
    card=ensemble_plan.json()['card']
    assert card['kind']=='behavior_attention_drift'
    assert card['agent_id']=='neuro_cognition'
    assert len(card['room'])==3
    assert set(card['routed_agent_ids'])=={'learning_strategist','neuro_cognition'}
    assert len(card['ensemble_messages'])==2
    assert len({m['text'] for m in card['ensemble_messages']})==2
    assert card['triage']['problem_type']=='attention_focus'
    assert client.get(f'/ambient/ensemble/{learner2}',headers=headers).json()['agent_ids']==['learning_strategist','subject_expert','neuro_cognition']


