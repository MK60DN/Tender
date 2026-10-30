import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.triage_agent import triage
from app.tender_context import build_tender_context
from app.functional_agents import build_reply, DEFAULT_AGENTS


def test_triage_routes_anxiety_to_psychology_not_subject():
    result = triage('我很焦虑', {})
    assert result.problem_type == 'anxiety_emotion'
    assert result.agent_ids[0] == 'psychologist'
    assert 'subject_expert' not in result.agent_ids
    reply = build_reply('dialogue_ack', '我很焦虑', DEFAULT_AGENTS, 'score_improvement')
    assert reply['routed_agent_ids'][0] == 'psychologist'
    assert 'subject_expert' not in reply['routed_agent_ids']
    assert all(len(m['text']) >= 50 for m in reply['ensemble_messages'])


def test_triage_routes_subject_question_to_subject_expert():
    result = triage('这道数学题不会，公式看不懂', {})
    assert result.problem_type == 'knowledge_gap'
    assert result.agent_ids[0] == 'subject_expert'


def test_triage_routes_high_risk_to_safety():
    result = triage('我不想活了', {})
    assert result.problem_type == 'acute_safety'
    assert result.risk_level == 'high'
    assert result.agent_ids[0] == 'safety_officer'



def test_triage_routes_reflective_learning_turn_to_state_review():
    result = triage('我按计划做了，但临时又改计划，这算元认知偏差吗？', {
        'tender_context': build_tender_context('triage-reflective-empty')
    })
    assert result.problem_type == 'state_review'
    assert 'metacognition_coach' in result.agent_ids

if __name__ == '__main__':
    test_triage_routes_anxiety_to_psychology_not_subject()
    test_triage_routes_subject_question_to_subject_expert()
    test_triage_routes_high_risk_to_safety()
    test_triage_routes_reflective_learning_turn_to_state_review()
    print('ok triage routing tests')
