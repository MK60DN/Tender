from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from app.main import app


def test_neuro_learning_catalog_endpoint():
    with TestClient(app) as client:
        response = client.get('/research/neuro-learning/catalog')
        assert response.status_code == 200
        data = response.json()
        assert data['summary']['dataset_count'] == 13
        assert data['summary']['runtime_neuro_inference_allowed'] is False
        assert any(item['id'] == 'abcd' for item in data['datasets'])
        assert any(item['id'] == 'assistments_data_shop' for item in data['datasets'])


def test_neuro_learning_filters_and_claim_boundaries():
    with TestClient(app) as client:
        filtered = client.get('/research/neuro-learning/datasets', params={'stage': 'university', 'modality': 'learning_interaction'})
        assert filtered.status_code == 200
        ids = {item['id'] for item in filtered.json()['datasets']}
        assert {'assistments_data_shop', 'oulad'} <= ids

        claim = client.get('/research/neuro-learning/claim/direct_brain_reading')
        assert claim.status_code == 200
        assert claim.json()['allowed'] is False


if __name__ == '__main__':
    test_neuro_learning_catalog_endpoint()
    test_neuro_learning_filters_and_claim_boundaries()
    print('ok neuro-learning API tests')
