from pathlib import Path
import json
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from app.agent_runtime import list_agents
from app.daoql import insert_event, list_edges, list_events
from app.main import app
from app.metameta_cartographer import (
    NODE_EVENT_TYPE,
    SUMMARY_EVENT_TYPE,
    annotate_input,
    build_metameta_annotation_map,
    decompose_and_store,
)
from app.tender_context import build_tender_context, format_tender_context


def _student():
    return 'metameta-' + uuid.uuid4().hex[:8]


def _headers(client, learner):
    response = client.post('/auth/demo-session', json={'actor_id': learner, 'role': 'learner', 'learner_id': learner})
    assert response.status_code == 200, response.text
    return {'Authorization': 'Bearer ' + response.json()['token']}


def test_life_tree_experience_mapper_labels_multiple_regions():
    text = '我一看到函数图就慌，刚才的步骤也记不住，也不知道怎么表达。'
    result = annotate_input(text, 'ambient_dialogue_reply')
    region_ids = {item['id'] for item in result['regions']}
    assert {'working_memory', 'visual_cortex', 'language_expression', 'limbic_emotion'} <= region_ids
    assert result['agent_id'] == 'metameta_cartographer'
    assert result['annotation_version'] == 'fishbowl-experience-1.0'
    assert result['primary_region']['confidence'] > 0
    assert result['life_tree']['stage'] in {'roots', 'trunk', 'branches', 'flower', 'fruit'}
    assert text not in json.dumps(result, ensure_ascii=False)


def test_life_tree_experience_mapper_uses_event_priors_without_text():
    result = annotate_input('', 'metacognition_jol', {'predicted_correct': 8, 'actual_correct': 3})
    assert result['primary_region']['id'] == 'introspection_feedback'
    assert result['memory_type']['kind'] == 'reflection'


def test_objective_event_is_decomposed_into_subjective_nodes_without_mutation():
    learner = _student()
    source_id = insert_event({
        'event_type': 'reflection',
        'student_id': learner,
        'payload': {'reflection': '我担心自己其实没有真正理解这个公式。'},
        'source': 'unit_test',
    })
    events = list_events(learner)
    source = next(event for event in events if event['event_id'] == source_id)
    assert source['event_type'] == 'reflection'
    assert 'epistemic_status' not in source['payload']
    summaries = [event for event in events if event['event_type'] == SUMMARY_EVENT_TYPE]
    nodes = [event for event in events if event['event_type'] == NODE_EVENT_TYPE]
    assert len(summaries) == 1
    assert len(nodes) >= 1
    assert all(node['payload']['epistemic_status'] == 'subjective_experience' for node in nodes)
    assert all(node['payload']['source_event_id'] == source_id for node in nodes)
    again = decompose_and_store(learner, '我担心自己其实没有真正理解这个公式。', source_event_id=source_id, source_event_type='reflection')
    assert again['status'] == 'already_decomposed'
    edges = list_edges()
    assert any(edge['relation'] == 'experienced_as' and edge['source_event_id'] == source_id for edge in edges)
    assert any(edge['relation'] == 'yields_subjective_experience' and edge['source_event_id'] == source_id for edge in edges)


def test_subjective_experience_map_enters_tender_context():
    learner = _student()
    insert_event({
        'event_type': 'reflection',
        'student_id': learner,
        'payload': {'reflection': '我昨晚没睡好，今天一看到图就慌，也不知道该怎么开始。'},
        'source': 'unit_test',
    })
    context = build_tender_context(learner, user_message='综合我的状态')
    experience_map = context['state']['observer']['input_map']
    assert experience_map['epistemic_status'] == 'subjective_experience'
    assert experience_map['total'] >= 1
    assert experience_map['decomposition_count'] == 1
    assert context['digest']['subjective_experience_nodes'] == experience_map['total']
    text = format_tender_context(context)
    assert '生命树主观体验图谱' in text
    assert '体验节点=' in text
    assert '客观事件' not in text or '主观体验' in text


def test_metameta_api_exposes_objective_to_subjective_decomposition():
    client = TestClient(app)
    learner = _student()
    headers = _headers(client, learner)
    response = client.post('/daoql/events', headers=headers, json={
        'event_type': 'reflection',
        'student_id': learner,
        'payload': {'reflection': '我读这段材料时很焦虑，也记不住刚才的步骤。'},
        'source': 'unit_test',
    })
    assert response.status_code == 200, response.text
    body = response.json()
    assert body['metameta_decomposition']['event_id']
    mapping = client.get(f'/metameta/map/{learner}', headers=headers)
    assert mapping.status_code == 200, mapping.text
    experience_map = mapping.json()['map']
    assert experience_map['epistemic_status'] == 'subjective_experience'
    assert experience_map['total'] >= 1
    assert experience_map['objective_source_event_count'] == 1
    manual = client.post(f'/metameta/decompose/{learner}', headers=headers, json={
        'message': '我现在很焦虑，也不知道下一步怎么选。',
        'event_type': 'user_input',
    })
    assert manual.status_code == 200, manual.text
    assert manual.json()['status'] == 'stored'
    assert manual.json()['region_node_event_ids']
    assert 'metameta_cartographer' in {item['id'] for item in list_agents()}


if __name__ == '__main__':
    test_life_tree_experience_mapper_labels_multiple_regions()
    test_life_tree_experience_mapper_uses_event_priors_without_text()
    test_objective_event_is_decomposed_into_subjective_nodes_without_mutation()
    test_subjective_experience_map_enters_tender_context()
    test_metameta_api_exposes_objective_to_subjective_decomposition()
    print('ok metameta cartographer tests')
