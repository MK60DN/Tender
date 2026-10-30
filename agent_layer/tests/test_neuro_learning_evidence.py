from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.neuro_learning_evidence import (
    catalog_summary,
    get_claim_boundary,
    get_integration_layers,
    list_datasets,
    list_research,
    runtime_neuro_inference_allowed,
)


def test_catalog_contains_behavior_and_brain_resources():
    summary = catalog_summary()
    assert summary['dataset_count'] == 13
    assert summary['behavioral_dataset_count'] == 5
    assert summary['brain_dataset_count'] == 8


def test_high_school_stage_has_behavior_and_development_data():
    datasets = list_datasets(stage='high')
    ids = {item['id'] for item in datasets}
    assert {'assistments_data_shop', 'ednet', 'healthy_brain_network', 'abcd'} <= ids


def test_university_stage_supports_adult_learning_analytics():
    datasets = list_datasets(stage='university', modality='learning_interaction')
    ids = {item['id'] for item in datasets}
    assert 'assistments_data_shop' in ids
    assert 'oulad' in ids


def test_working_memory_research_is_traceable():
    items = list_research('working_memory')
    ids = {item['id'] for item in items}
    assert {'working_memory_cowan', 'executive_functions_diamond'} <= ids
    assert all(item['doi'].startswith('https://doi.org/') for item in items)


def test_direct_brain_reading_is_blocked():
    claim = get_claim_boundary('direct_brain_reading')
    assert claim['allowed'] is False
    assert '没有运行时神经解码能力' in claim['reason']


def test_behavioral_proxy_requires_uncertainty_language():
    claim = get_claim_boundary('behavioral_proxy')
    assert claim['allowed'] is True
    assert '弱信号' in claim['required_language']


def test_neural_inference_is_not_enabled_at_runtime():
    assert runtime_neuro_inference_allowed() is False
    layers = {item['id']: item for item in get_integration_layers()}
    assert layers['neural_runtime_inference']['status'] == 'not_implemented_and_not_claimed'


if __name__ == '__main__':
    test_catalog_contains_behavior_and_brain_resources()
    test_high_school_stage_has_behavior_and_development_data()
    test_university_stage_supports_adult_learning_analytics()
    test_working_memory_research_is_traceable()
    test_direct_brain_reading_is_blocked()
    test_behavioral_proxy_requires_uncertainty_language()
    test_neural_inference_is_not_enabled_at_runtime()
    print('ok neuro-learning evidence tests')
