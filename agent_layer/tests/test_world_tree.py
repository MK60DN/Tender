from pathlib import Path
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.daoql import insert_event
from app.preassessment import preassessment_items, submit_preassessment
from app.world_tree import build_world_tree


def test_world_tree_projects_roots_canopy_flowers_outcomes_and_shared_boundary():
    student_id = 'world-tree-' + uuid.uuid4().hex[:8]
    items = preassessment_items()
    responses = {item['id']: 3 for section in ['big_five', 'world_interface'] for item in items[section]['items']}
    submit_preassessment(student_id, responses, consent=True)
    insert_event({
        'event_type': 'reflection', 'student_id': student_id, 'source': 'test',
        'payload': {'text': '我发现自己一被评价就反复检查，也很难开始下一步。'},
    })
    insert_event({
        'event_type': 'answer', 'student_id': student_id, 'source': 'test',
        'payload': {'correct': False, 'node_id': 'math-functions', 'subject': '数学'},
    })
    tree = build_world_tree(student_id)
    assert tree['tree_version'] == 'world-tree-1.0'
    assert tree['roots']['event_count'] >= 3
    assert tree['trunk']['world_entry']['code'] in {'objective_first', 'subjective_first', 'bridge_first'}
    assert len(tree['canopy']['branches']) == 5
    nodes = [node for branch in tree['canopy']['branches'] for node in branch['nodes']]
    assert len(nodes) == 11
    assert any(node['local_state_axis'] == '确定 / 不确定' for node in nodes)
    assert tree['flowers']['count'] >= 1
    assert tree['outcomes']['count'] >= 1
    assert tree['shared_branches']['status'] == 'not_materialized'
    assert tree['golden_ratio_lens']['status'] == 'design_hypothesis_not_scientific_law'
    assert tree['golden_ratio_lens']['dynamic_regulator']['status'] == 'insufficient_evidence'
    assert '不是脑区诊断' in tree['boundary']


if __name__ == '__main__':
    test_world_tree_projects_roots_canopy_flowers_outcomes_and_shared_boundary()
    print('ok world tree tests')