from pathlib import Path
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.daoql import insert_event
from app.knowledge_context import build_knowledge_context
from app.preassessment import preassessment_items, submit_preassessment
from app.tender_context import build_tender_context, format_tender_context


def _student():
    return 'know-ctx-' + uuid.uuid4().hex[:8]


def test_function_question_resolves_to_math_knowledge_node():
    result = build_knowledge_context('这道函数题不会，怎么做？', '数学作业')
    assert result['available'] is True
    assert result['subject_id'] == 'k12:math'
    assert result['match_method'] == 'topic_match'
    first = result['matches'][0]
    assert '函数' in first['name']
    assert any(item['node_type'] == 'subject' for item in first['path'])
    assert first['question_modes']
    assert first['competencies']


def test_subject_fallback_uses_units_when_topic_is_vague():
    result = build_knowledge_context('我现在状态不好，不知道怎么办', '数学作业')
    assert result['available'] is True
    assert result['match_method'] == 'subject_fallback'
    assert result['subject_id'] == 'k12:math'
    assert all(item['subject_id'] == 'k12:math' for item in result['matches'])
    assert all(item['specific'] is False for item in result['matches'])


def test_no_match_does_not_invent_knowledge_node():
    result = build_knowledge_context('今天天气不错，想出去走走', None)
    assert result['available'] is False
    assert result['matches'] == []
    assert '不要假设具体知识点' in result['boundary']


def test_major_query_loads_courses_and_competencies():
    result = build_knowledge_context('计算机科学与技术专业需要学什么课程？', '大学志愿')
    assert result['available'] is True
    assert result['major']['available'] is True
    major = result['major']['matches'][0]
    assert major['code'] == '080901'
    assert major['name'] == '计算机科学与技术'
    assert len(major['courses']) >= 5
    assert major['competencies']


def test_career_intent_returns_riasec_exploration_context():
    result = build_knowledge_context('我想转行做产品经理，需要什么能力？', '就业')
    assert result['career']['intent_detected'] is True
    assert result['career']['match_method'] == 'riasec_fallback'
    assert len(result['career']['riasec_dimensions']) == 6
    assert '命定式职业选择' in result['career']['boundary']


def test_tender_context_includes_knowledge_and_node_mastery():
    student_id = _student()
    items = preassessment_items()
    responses = {item['id']: 3 for section in ['big_five', 'mbti', 'jungian'] for item in items[section]['items']}
    submit_preassessment(student_id, responses, consent=True)
    initial = build_knowledge_context('这道函数题不会，怎么做？', '数学作业')
    node = initial['matches'][0]
    insert_event({
        'event_type': 'answer',
        'student_id': student_id,
        'payload': {'correct': False, 'node_id': node['node_id'], 'subject': '数学'},
        'source': 'test',
    })
    insert_event({
        'event_type': 'ambient_card_shown',
        'student_id': student_id,
        'payload': {'kind': 'stuck', 'task_hint': '数学作业'},
        'source': 'test',
    })
    context = build_tender_context(student_id, user_message='这道函数题不会，怎么做？')
    assert context['knowledge']['available'] is True
    assert context['digest']['knowledge_available'] is True
    assert context['digest']['knowledge_node'] == node['name']
    match = context['knowledge']['matches'][0]
    assert match['learner_mastery']['value'] == 0.0
    assert match['learner_mastery']['observations'] == 1
    text = format_tender_context(context)
    assert '学科知识' in text
    assert '知识节点' in text
    assert '先修=' in text
    assert '节点掌握度=0.0' in text


if __name__ == '__main__':
    test_function_question_resolves_to_math_knowledge_node()
    test_subject_fallback_uses_units_when_topic_is_vague()
    test_no_match_does_not_invent_knowledge_node()
    test_major_query_loads_courses_and_competencies()
    test_career_intent_returns_riasec_exploration_context()
    test_tender_context_includes_knowledge_and_node_mastery()
    print('ok knowledge context tests')
