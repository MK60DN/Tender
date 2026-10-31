from pathlib import Path
import json
import math
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app.llm_dialogue as llm_dialogue
import app.ambient as ambient
import app.tender_context as tender_context_module
from app.daoql import insert_event, list_events
from app.preassessment import preassessment_items, submit_preassessment
from app.tender_context import build_tender_context, format_tender_context
from app.triage_agent import triage


def _student() -> str:
    return 'ctx-test-' + uuid.uuid4().hex[:8]


def _responses():
    items = preassessment_items()
    responses = {item['id']: 3 for section in ['big_five', 'world_interface'] for item in items[section]['items']}
    responses.update({'c1': 1, 'c2': 1, 'c3': 5, 'c4': 1})
    responses.update({'o1': 5, 'o2': 5, 'o3': 1, 'o4': 5})
    responses.update({'ti1': 5, 'ti2': 5, 'ti3': 5, 'te1': 1, 'te2': 1, 'te3': 1})
    return responses


def _seed_context_student(student_id):
    submit_preassessment(student_id, _responses(), consent=True)
    insert_event({'event_type':'answer','student_id':student_id,'payload':{'correct':False},'source':'test'})
    insert_event({'event_type':'response','student_id':student_id,'payload':{'response_time_ms':48000},'source':'test'})
    insert_event({'event_type':'metacognition_jol','student_id':student_id,'payload':{'predicted_correct':9,'actual_correct':3,'n_items':10},'source':'test'})
    insert_event({'event_type':'ambient_card_shown','student_id':student_id,'payload':{'kind':'attention_drift','task_hint':'数学作业'},'source':'test'})


def _longitudinal_state():
    return {
        'knowledge': {'mastery': 0.72},
        'cognitive': {'theta': 0.18, 'uncertainty': 0.31},
        'metacognition': {
            'jol_bias': 0.22,
            'hesitation': 0.61,
            'profile': {'元认知敏感性AUC': 0.71, '元认知偏差': 0.12, 'd_prime': 0.84},
        },
        'baseline': {
            'arrangement_fit': 0.78,
            'baseline_model': {'deviation_mean': 0.84, 'deviation_max': 1.63},
            'rhythm': {'主导节律': '周内节律', '日内强度R24': 0.42, '周内强度R168': 0.73, '节律平衡B': 0.31},
        },
        'group': {'clustering': 0.38, 'bridge_ratio': 0.64},
        'observer': {'teacher_metameta': {'metameta_r': 0.71, 'n': 6}},
        'emotion': {'label': '紧张或高负荷'},
    }


def test_tender_context_contains_preassessment_state_and_corrections():
    student_id = _student()
    _seed_context_student(student_id)
    context = build_tender_context(student_id, user_message='这道函数题不会，怎么做？')
    assert context['digest']['preassessment_available'] is True
    assert context['knowledge']['available'] is True
    assert context['digest']['knowledge_available'] is True
    assert context['preassessment']['attention_profile']['leakage']
    assert context['preassessment']['cognitive_correction_plan']['items']
    assert context['preassessment']['world_interface']['world_entry']['code'] in {'objective_first','subjective_first','bridge_first'}
    assert context['digest']['world_entry'] in {'objective_first','subjective_first','bridge_first'}
    assert context['event_count'] >= 4
    assert context['state']['mastery'] == 0.0
    assert context['mentalization']['hypotheses']
    assert 'responses' not in context['preassessment']


def test_format_tender_context_includes_grounding_rules():
    student_id = _student()
    _seed_context_student(student_id)
    text = format_tender_context(build_tender_context(student_id, user_message='这道函数题不会，怎么做？'))
    assert 'Tender 状态上下文' in text
    assert '注意泄漏' in text
    assert '世界入口' in text
    assert '心理资源基线' in text
    assert '当前主要假设' in text
    assert '学科知识' in text
    assert '知识节点' in text
    assert '当前用户消息和真实结果优先' in text


def test_triage_routes_state_question_with_tender_context():
    student_id = _student()
    _seed_context_student(student_id)
    result = triage('我现在什么状态，怎么办', {'tender_context': build_tender_context(student_id)})
    assert result.problem_type == 'state_review'
    assert 'neuro_cognition' in result.agent_ids
    assert any('Tender当前主要假设' in item for item in result.evidence)


def test_llm_prompt_receives_tender_context():
    student_id = _student()
    _seed_context_student(student_id)
    context = build_tender_context(student_id, user_message='这道函数题不会，怎么做？')
    captured = {}
    original_chat = llm_dialogue.chat

    def fake_chat(messages, **kwargs):
        captured['messages'] = messages
        return {'text':'我看到了近期证据，先做一个最小步骤。','provider':'test','model':'test'}

    llm_dialogue.chat = fake_chat
    try:
        card = {
            'triage': {'problem_type':'state_review','label':'状态回顾与下一步','confidence':0.78,'risk_level':'low','alternative':'证据不足也可能'},
            'ensemble_messages': [{'agent_id':'metacognition_coach','name':'元认知教练','mark':'元认知','role':'复盘','text':'fallback'}],
        }
        result = llm_dialogue.enrich_reply(card, '我现在什么状态，怎么办', tender_context=context, max_agents=1)
    finally:
        llm_dialogue.chat = original_chat
    prompt = captured['messages'][-1]['content']
    assert 'Tender 状态上下文' in prompt
    assert '注意泄漏' in prompt
    assert '当前主要假设' in prompt
    assert '知识节点' in prompt
    assert result['ensemble_messages'][0]['llm_used'] is True
    assert result['tender_context_used']['attention_available'] is True


def test_ambient_reply_records_context_digest():
    student_id = _student()
    _seed_context_student(student_id)
    original_enrich = ambient.enrich_reply
    ambient.enrich_reply = lambda card, text, history=None, max_agents=2, tender_context=None: {
        **card,
        'ensemble_messages': card.get('ensemble_messages', [])[:1],
        'tender_context_used': (tender_context or {}).get('digest', {}),
    }
    try:
        result = ambient.reply_to_ambient(student_id, 'ambient_test_context', '我现在什么状态，怎么办')
    finally:
        ambient.enrich_reply = original_enrich
    stored = [event for event in list_events(student_id) if event['event_type'] == 'ambient_dialogue_reply'][-1]
    assert stored['payload']['tender_context_digest']['preassessment_available'] is True
    assert stored['payload']['tender_context_digest']['knowledge_available'] is True
    assert result['reply_card']['tender_context_used']['preassessment_available'] is True


def test_tender_context_sanitizes_non_finite_metrics():
    student_id = _student()
    original = tender_context_module.compute_state

    def fake_compute_state(_student_id, _events):
        return {
            'knowledge': {'mastery': float('nan')},
            'cognitive': {'theta': float('inf'), 'uncertainty': float('nan')},
            'metacognition': {
                'jol_bias': float('nan'), 'hesitation': float('inf'),
                'profile': {'元认知敏感性AUC': float('nan')},
            },
            'baseline': {
                'arrangement_fit': float('nan'),
                'baseline_model': {'deviation_mean': float('nan'), 'deviation_max': float('inf')},
                'rhythm': {'主导节律': '稳定', '日内强度R24': float('nan')},
            },
            'group': {'clustering': float('nan'), 'bridge_ratio': float('inf')},
            'observer': {'teacher_metameta': {'metameta_r': float('nan'), 'n': 6}},
            'emotion': {},
        }

    tender_context_module.compute_state = fake_compute_state
    try:
        context = tender_context_module.build_tender_context(student_id, user_message='请综合我的状态')
    finally:
        tender_context_module.compute_state = original
    json.dumps(context, allow_nan=False)
    assert context['state']['baseline_model']['deviation_mean'] is None
    assert context['state']['rhythm']['日内强度R24'] is None
    assert context['state']['observer']['teacher_metameta']['metameta_r'] is None


def test_tender_context_exposes_longitudinal_modules():
    student_id = _student()
    original = tender_context_module.compute_state
    tender_context_module.compute_state = lambda _student_id, _events: _longitudinal_state()
    try:
        context = tender_context_module.build_tender_context(student_id, user_message='请综合我的状态')
        text = tender_context_module.format_tender_context(context)
    finally:
        tender_context_module.compute_state = original
    assert context['state']['baseline_model']['deviation_mean'] == 0.84
    assert context['state']['rhythm']['主导节律'] == '周内节律'
    assert context['state']['metacognition_profile']['元认知敏感性AUC'] == 0.71
    assert context['state']['group']['clustering'] == 0.38
    assert context['state']['observer']['teacher_metameta']['metameta_r'] == 0.71
    assert '节律与个人基线' in text
    assert '群体结构' in text
    assert '教师元元校准' in text


def test_state_review_precedes_subject_route():
    result = triage('综合我的函数题状态，是否在改善，怎么办', {
        'tender_context': build_tender_context(_student())
    })
    assert result.problem_type == 'state_review'


def test_comprehensive_prompt_requires_consistent_module_coverage():
    student_id = _student()
    _seed_context_student(student_id)
    context = build_tender_context(student_id, user_message='请综合我的基线、周期、元认知、群体和教师预测')
    captured = {}
    original_chat = llm_dialogue.chat

    def fake_chat(messages, **kwargs):
        captured['messages'] = messages
        return {'text': '我会逐项说明当前有哪些证据。', 'provider': 'test', 'model': 'test'}

    llm_dialogue.chat = fake_chat
    try:
        card = {
            'triage': {'problem_type':'state_review','label':'状态回顾与下一步','confidence':0.78,'risk_level':'low','alternative':'证据不足也可能'},
            'ensemble_messages': [{'agent_id':'metacognition_coach','name':'元认知教练','mark':'元认知','role':'复盘','text':'fallback'}],
        }
        llm_dialogue.enrich_reply(card, '请综合我的基线、周期、元认知、群体和教师预测', tender_context=context, max_agents=1)
    finally:
        llm_dialogue.chat = original_chat
    prompt = captured['messages'][-1]['content']
    assert '逐项覆盖当前可用的基线' in prompt
    assert '同一模块只能给一个证据判断' in prompt
    assert '不要同时说‘有样本’和‘完全为空’' in prompt


def test_llm_reply_strips_internal_agent_prefix():
    student_id = _student()
    _seed_context_student(student_id)
    context = build_tender_context(student_id, user_message='我现在是什么状态')
    original_chat = llm_dialogue.chat
    llm_dialogue.chat = lambda messages, **kwargs: {
        'text': '[元认知教练] 我先把最重要的判断说清楚：现在的证据更像注意负荷偏高。',
        'provider': 'test',
        'model': 'test',
    }
    try:
        card = {
            'triage': {'problem_type':'state_review','label':'状态回顾与下一步','confidence':0.78,'risk_level':'low','alternative':'证据不足也可能'},
            'ensemble_messages': [{'agent_id':'metacognition_coach','name':'元认知教练','mark':'元认知','role':'复盘','text':'fallback'}],
        }
        result = llm_dialogue.enrich_reply(card, '我现在是什么状态', tender_context=context, max_agents=1)
    finally:
        llm_dialogue.chat = original_chat
    assert not result['ensemble_messages'][0]['text'].startswith('[')
    assert result['ensemble_messages'][0]['text'].startswith('我先把最重要')



if __name__ == '__main__':
    test_tender_context_contains_preassessment_state_and_corrections()
    test_format_tender_context_includes_grounding_rules()
    test_triage_routes_state_question_with_tender_context()
    test_llm_prompt_receives_tender_context()
    test_ambient_reply_records_context_digest()
    test_tender_context_sanitizes_non_finite_metrics()
    test_tender_context_exposes_longitudinal_modules()
    test_state_review_precedes_subject_route()
    test_comprehensive_prompt_requires_consistent_module_coverage()
    test_llm_reply_strips_internal_agent_prefix()
    print('ok tender context tests')
