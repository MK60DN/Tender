import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from app.main import app


def test_knowledge_database_api():
    client = TestClient(app)
    assert client.get('/knowledge/subjects').json()['count'] == 13
    assert client.get('/knowledge/tree/k12:math?limit=5').json()['count'] == 5
    assert client.get('/knowledge/search?q=集合&limit=5').json()['count'] > 0
    major = client.get('/knowledge/majors/080901').json()
    assert major['major']['code'] == '080901'
    assert major['course_seed_available'] is True
    assert len(major['courses']) >= 10
    assert client.get('/knowledge/university/categories').json()['count'] == 13
    forest = client.get('/knowledge/forest').json()
    assert forest['totals']['k12_subjects'] == 13
    assert forest['totals']['k12_nodes'] == 1075
    assert forest['totals']['majors'] == 875
    assert forest['totals']['courses'] == 319
    assert forest['totals']['occupations'] == 1016
    assert forest['totals']['crosswalk_links'] > 0
    assert len(forest['subjects']) == 13
    assert len(forest['disciplines']) == 13
    assert forest['totals']['course_seed_majors'] == 26
    assert client.get('/knowledge/majors?category_code=08&limit=500').json()['count'] == 293


def test_knowledge_forest_snapshot():
    client = TestClient(app)
    forest = client.get('/knowledge/forest').json()
    assert forest['status'] == 'live_database_snapshot'
    assert forest['layers'][0]['id'] == 'subjects'
    assert forest['layers'][-1]['id'] == 'links'
    assert forest['coverage']['course_seed_gap_majors'] == 849
    subject_ids = {item['subject_id'] for item in forest['subjects']}
    assert 'k12:math' in subject_ids
    assert all(link['source'] in subject_ids for link in forest['links'])
    assert all(link['target'] for link in forest['links'])


if __name__ == '__main__':
    test_knowledge_database_api()
    test_knowledge_forest_snapshot()
    print('ok test_knowledge_database_api')

