from datetime import datetime, timedelta, timezone
from pathlib import Path
import os
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ['TENDER_ALLOW_HEADER_IDENTITY'] = '1'
from app.daoql import insert_event
from app.golden_bias import build_golden_bias
from app.main import app


def _sid(prefix):
    return prefix + '-' + uuid.uuid4().hex[:8]


def _event(student_id, event_type, when, payload=None):
    insert_event({'event_type': event_type, 'student_id': student_id, 'timestamp': when.isoformat(), 'payload': payload or {}, 'source': 'test'})


def test_golden_bias_insufficient_evidence():
    now = datetime(2026, 11, 1, tzinfo=timezone.utc)
    result = build_golden_bias(_sid('gb-empty'), now=now)
    assert result['available'] is False
    assert result['status'] == 'insufficient_evidence'
    assert result['band']['minor_floor'] == 0.382


def test_golden_bias_inside_band_collects_quality_metrics():
    now = datetime(2026, 11, 1, tzinfo=timezone.utc)
    sid = _sid('gb-balanced')
    base = now - timedelta(days=3)
    for i in range(6):
        _event(sid, 'response', base + timedelta(minutes=10*i), {'novel_branch': True})
    for i in range(6):
        _event(sid, 'study_session', base + timedelta(minutes=5*i), {'duration_minutes': 1})
        _event(sid, 'answer', base + timedelta(hours=1, minutes=i), {'correct': True})
    for i in range(6):
        _event(sid, 'response', base + timedelta(hours=2, minutes=10*i), {'novel_branch': True})
    result = build_golden_bias(sid, now=now)
    assert result['available'] is True
    assert result['long_band_status'] == 'inside_band'
    assert result['learning_share'] == 0.5
    assert result['creation_share'] == 0.5
    assert result['novelty_ratio'] == 1.0
    assert result['post_creation_calibration'] == 0.5
    assert result['hysteresis_state'] == 'normal'


def test_learning_overweight_returns_output_probe():
    now = datetime(2026, 11, 1, tzinfo=timezone.utc)
    sid = _sid('gb-learn')
    base = now - timedelta(days=8)
    for i in range(20):
        _event(sid, 'study_session', base + timedelta(minutes=i), {'duration_minutes': 1})
    for i in range(4):
        _event(sid, 'response', base + timedelta(hours=2, minutes=i), {'novel_branch': False})
    result = build_golden_bias(sid, now=now)
    assert result['long_band_status'] == 'learning_overweight'
    assert result['phase'] == 'learning_dominant'
    assert result['next_probe']['type'] == 'output_probe'


def test_creation_overweight_with_low_calibration_returns_calibration_probe():
    now = datetime(2026, 11, 1, tzinfo=timezone.utc)
    sid = _sid('gb-create')
    base = now - timedelta(days=8)
    for i in range(20):
        _event(sid, 'response', base + timedelta(minutes=i), {'novel_branch': i % 2 == 0})
    for i in range(2):
        _event(sid, 'answer', base + timedelta(minutes=1, seconds=i), {'correct': False})
    result = build_golden_bias(sid, now=now)
    assert result['long_band_status'] == 'creation_overweight'
    assert result['novelty_ratio'] == 0.5
    assert result['post_creation_calibration'] < 0.382
    assert result['next_probe']['type'] == 'calibration_probe'


def test_golden_bias_api_exists():
    from fastapi.testclient import TestClient
    sid = _sid('gb-api')
    with TestClient(app) as client:
        headers = {'X-Tender-Actor': sid, 'X-Tender-Role': 'learner', 'X-Tender-Learner': sid}
        response = client.get(f'/golden-bias/{sid}', headers=headers)
        assert response.status_code == 200
        assert response.json()['status'] == 'insufficient_evidence'


if __name__ == '__main__':
    test_golden_bias_insufficient_evidence()
    test_golden_bias_inside_band_collects_quality_metrics()
    test_learning_overweight_returns_output_probe()
    test_creation_overweight_with_low_calibration_returns_calibration_probe()
    test_golden_bias_api_exists()
    print('ok golden bias tests')