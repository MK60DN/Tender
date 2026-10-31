"""Synthetic validation of evidence-gated rhythm periodicity and phase detection."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import math
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'agent_layer'))

from app.golden_bias import (  # noqa: E402
    PERIOD_ANALYSIS_DAYS,
    _current_rhythm_phase,
    _post_creation_calibration,
    _shares,
    detect_periodicity,
)

SEED = 20261102
DAYS = 112
END = datetime(2026, 11, 1, 23, 59, tzinfo=timezone.utc)
TRUE_PERIODS = (7, 10, 14, 21, 28)
N_PER_PERIOD = 80
N_APERIODIC = 400
N_PER_PHASE = 80
PHASES = ('absorb', 'integrate', 'express', 'calibrate', 'recover')


def event(sid: str, kind: str, when: datetime, rng: random.Random) -> dict:
    payload = {'duration_minutes': 10, 'novel_branch': bool(rng.random() < 0.6)}
    return {'event_type': kind, 'student_id': sid, 'timestamp': when.isoformat(), 'payload': payload, 'source': 'synthetic_rhythm_bench'}


def periodic_events(sid: str, period: int, phase_offset: float, rng: random.Random) -> list[dict]:
    events = []
    start = END - timedelta(days=DAYS - 1)
    for day in range(DAYS):
        if rng.random() < 0.06:
            continue
        signal = math.sin(2 * math.pi * day / period + phase_offset)
        create = signal >= 0
        if rng.random() < 0.08:
            create = not create
        when = start + timedelta(days=day, hours=10)
        if create:
            events.append(event(sid, 'response', when, rng))
            events.append(event(sid, 'ambient_feedback', when + timedelta(hours=2), rng))
        else:
            events.append(event(sid, 'study_session', when, rng))
    return events


def aperiodic_events(sid: str, rng: random.Random) -> list[dict]:
    events = []
    latent = 0.0
    start = END - timedelta(days=DAYS - 1)
    for day in range(DAYS):
        latent = 0.72 * latent + rng.gauss(0, 0.68)
        create = latent >= 0
        if rng.random() < 0.10:
            create = not create
        when = start + timedelta(days=day, hours=10)
        if create:
            events.append(event(sid, 'response', when, rng))
            if rng.random() < 0.7:
                events.append(event(sid, 'ambient_feedback', when + timedelta(hours=2), rng))
        else:
            events.append(event(sid, 'study_session', when, rng))
    return events


def baseline_events(sid: str, rng: random.Random, reserve_days: int = 7) -> list[dict]:
    events = []
    start = END - timedelta(days=DAYS - 1)
    stop = DAYS - reserve_days
    for day in range(stop):
        when = start + timedelta(days=day, hours=10)
        if day % 2 == 0:
            events.append(event(sid, 'study_session', when, rng))
        else:
            events.append(event(sid, 'response', when, rng))
            events.append(event(sid, 'ambient_feedback', when + timedelta(hours=2), rng))
    return events


def phase_events(sid: str, phase: str, rng: random.Random) -> tuple[list[dict], datetime]:
    reserve = 7
    events = baseline_events(sid, rng, reserve)
    start = END - timedelta(days=reserve - 1)
    if phase == 'recover':
        # Remove any event from the last four days; low activity remains ambiguous rather than a diagnosis.
        cutoff = END - timedelta(days=4)
        events = [item for item in events if datetime.fromisoformat(item['timestamp']) < cutoff]
        return events, END
    for day in range(reserve):
        when = start + timedelta(days=day, hours=10)
        if phase == 'absorb':
            events.append(event(sid, 'study_session', when, rng))
            events.append(event(sid, 'answer', when + timedelta(minutes=20), rng))
        elif phase == 'calibrate':
            events.append(event(sid, 'response', when, rng))
            events.append(event(sid, 'response', when + timedelta(minutes=20), rng))
        elif phase == 'express':
            events.append(event(sid, 'response', when, rng))
            events.append(event(sid, 'ambient_feedback', when + timedelta(hours=1), rng))
        else:
            events.append(event(sid, 'study_session', when, rng))
            events.append(event(sid, 'response', when + timedelta(minutes=20), rng))
            events.append(event(sid, 'ambient_feedback', when + timedelta(hours=1), rng))
    return events, END


def classify_phase(sid: str, events: list[dict], end: datetime) -> str:
    start = end - timedelta(days=28)
    learning, creation, _ = _shares(events, start, end)
    calibration, _ = _post_creation_calibration(events, start, end)
    return _current_rhythm_phase(events, end, learning, creation, calibration)['code']


def run() -> dict:
    rng = random.Random(SEED)
    periodic_rows = []
    for true_period in TRUE_PERIODS:
        detected = 0
        stable = 0
        correct = 0
        abs_errors = []
        for index in range(N_PER_PERIOD):
            sid = f'period-{true_period}-{index}'
            events = periodic_events(sid, true_period, rng.uniform(0, 2 * math.pi), rng)
            result = detect_periodicity(events, end=END, student_id=sid)
            is_detected = result['status'] in {'stable_period', 'candidate_period'}
            is_stable = result['status'] == 'stable_period'
            detected += int(is_detected)
            stable += int(is_stable)
            if is_detected and result['period_days'] is not None:
                error = abs(result['period_days'] - true_period)
                abs_errors.append(error)
                if error <= max(1.5, true_period * 0.12):
                    correct += 1
        periodic_rows.append({
            'true_period_days': true_period,
            'n': N_PER_PERIOD,
            'detected_rate': round(detected / N_PER_PERIOD, 3),
            'stable_rate': round(stable / N_PER_PERIOD, 3),
            'within_tolerance_rate': round(correct / N_PER_PERIOD, 3),
            'mae_days_among_detected': round(sum(abs_errors) / len(abs_errors), 2) if abs_errors else None,
        })
    false_positives = 0
    false_stable = 0
    false_candidate = 0
    abstentions = 0
    for index in range(N_APERIODIC):
        sid = f'aperiodic-{index}'
        result = detect_periodicity(aperiodic_events(sid, rng), end=END, student_id=sid)
        false_positives += int(result['status'] in {'stable_period', 'candidate_period'})
        false_stable += int(result['status'] == 'stable_period')
        false_candidate += int(result['status'] == 'candidate_period')
        abstentions += int(result['status'] == 'insufficient_evidence')
    confusion = {expected: {predicted: 0 for predicted in PHASES} for expected in PHASES}
    phase_correct = 0
    phase_total = 0
    for expected in PHASES:
        for index in range(N_PER_PHASE):
            sid = f'phase-{expected}-{index}'
            events, end = phase_events(sid, expected, rng)
            predicted = classify_phase(sid, events, end)
            if predicted not in confusion[expected]:
                confusion[expected][predicted] = 0
            confusion[expected][predicted] += 1
            phase_correct += int(predicted == expected)
            phase_total += 1
    period_total = len(TRUE_PERIODS) * N_PER_PERIOD
    within_total = sum(row['within_tolerance_rate'] * row['n'] for row in periodic_rows)
    detected_total = sum(row['detected_rate'] * row['n'] for row in periodic_rows)
    stable_total = sum(row['stable_rate'] * row['n'] for row in periodic_rows)
    mae_values = [row['mae_days_among_detected'] for row in periodic_rows if row['mae_days_among_detected'] is not None]
    summary = {
        'periodic_detection_rate': round(detected_total / period_total, 3),
        'periodic_stable_rate': round(stable_total / period_total, 3),
        'period_within_tolerance_rate': round(within_total / period_total, 3),
        'period_mae_days': round(sum(mae_values) / len(mae_values), 2) if mae_values else None,
        'aperiodic_false_positive_rate': round(false_positives / N_APERIODIC, 3),
        'aperiodic_stable_false_positive_rate': round(false_stable / N_APERIODIC, 3),
        'aperiodic_candidate_rate': round(false_candidate / N_APERIODIC, 3),
        'insufficient_evidence_rate_aperiodic': round(abstentions / N_APERIODIC, 3),
        'phase_accuracy': round(phase_correct / phase_total, 3),
        'phase_n': phase_total,
    }
    return {
        'version': 'rhythm-phase-detection-1.0',
        'design': 'synthetic_periodic_and_aperiodic_validation',
        'seed': SEED,
        'days': DAYS,
        'analysis_days': PERIOD_ANALYSIS_DAYS,
        'end': END.isoformat(),
        'n_per_period': N_PER_PERIOD,
        'n_aperiodic': N_APERIODIC,
        'n_per_phase': N_PER_PHASE,
        'true_periods': list(TRUE_PERIODS),
        'periodic_results': periodic_rows,
        'summary': summary,
        'phase_confusion': confusion,
        'fixed_7_baseline': {
            'periodic_accuracy': round(N_PER_PERIOD / period_total, 3),
            'aperiodic_false_positive_rate': 1.0,
            'note': 'A fixed seven-day rule labels every learner as seven-day periodic and cannot abstain.',
        },
        'boundary': 'This is a synthetic detector validation, not evidence that human learning or emotion is periodic, nor a clinical or educational efficacy study.',
    }


def markdown(data: dict) -> str:
    s = data['summary']
    lines = [
        '# 节律相位与周期证据 — 合成实验',
        '',
        f"- 随机种子：{data['seed']}",
        f"- 合成时间跨度：{data['days']} 天；周期分析窗口：{data['analysis_days']} 天",
        f"- 周期类别：{', '.join(str(x) for x in data['true_periods'])} 天；每类 {data['n_per_period']} 条",
        f"- 非周期对照：{data['n_aperiodic']} 条；相位分类：每类 {data['n_per_phase']} 条",
        '',
        '## 主要结果',
        '',
        '| 指标 | 结果 |',
        '|---|---:|',
        f"| 周期检出率 | {s['periodic_detection_rate']:.3f} |",
        f"| 稳定周期率 | {s['periodic_stable_rate']:.3f} |",
        f"| 周期误差在容忍范围内 | {s['period_within_tolerance_rate']:.3f} |",
        f"| 平均绝对周期误差 | {s['period_mae_days']:.2f} 天 |",
        f"| 非周期序列稳定周期误报率 | {s['aperiodic_stable_false_positive_rate']:.3f} |",
        f"| 非周期序列候选周期率 | {s['aperiodic_candidate_rate']:.3f} |",
        f"| 相位分类准确率 | {s['phase_accuracy']:.3f} |",
        '',
        '## 各周期结果',
        '',
        '| 真实周期 | 检出率 | 稳定率 | 容忍范围内 | 平均绝对误差 |',
        '|---:|---:|---:|---:|---:|',
    ]
    for row in data['periodic_results']:
        mae = '—' if row['mae_days_among_detected'] is None else f"{row['mae_days_among_detected']:.2f}"
        lines.append(f"| {row['true_period_days']} 天 | {row['detected_rate']:.3f} | {row['stable_rate']:.3f} | {row['within_tolerance_rate']:.3f} | {mae} |")
    lines += [
        '',
        '## 与固定 7 天假设比较',
        '',
        "固定 7 天会强制给所有序列一个周周期，不能表达“没有稳定周期”。本实验因此同时比较检出、估计误差和弃判。",
        '',
        f"- 固定 7 天在五类真实周期中的理论准确率：{data['fixed_7_baseline']['periodic_accuracy']:.3f}",
        f"- 固定 7 天对非周期序列的误报率：{data['fixed_7_baseline']['aperiodic_false_positive_rate']:.3f}",
        f"- 当前检测器的稳定周期误报率：{s['aperiodic_stable_false_positive_rate']:.3f}",
        f"- 当前检测器的候选周期率：{s['aperiodic_candidate_rate']:.3f}",
        '',
        '## 相位混淆矩阵',
        '',
        '| 期望相位 | ' + ' | '.join(PHASES) + ' |',
        '|---|' + '---:|' * len(PHASES),
    ]
    for expected in PHASES:
        row = data['phase_confusion'][expected]
        lines.append('| ' + expected + ' | ' + ' | '.join(str(row.get(p, 0)) for p in PHASES) + ' |')
    lines += [
        '',
        '## 解释与限制',
        '',
        '- 该实验检验的是检测器在已知合成结构中的数据行为，不是对人的周期诊断。',
        '- 7 天和 28 天在系统中只承担短期提示与阶段控制；真实周期必须从事件序列中估计并与随机基线比较。',
        '- 相位分类依赖近期学习、创造和校准证据；恢复与低活动只能作为待确认假设。',
        '- 下一步应在获得授权、可撤回的真实纵向数据上预注册测试，并保留无周期假设、固定 7 天和开放搜索三类基线。',
        '',
        '## 研究边界',
        '',
        data['boundary'],
    ]
    return '\n'.join(lines) + '\n'


def main() -> None:
    data=run()
    (Path(__file__).parent/'results.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (Path(__file__).parent/'REPORT.md').write_text(markdown(data),encoding='utf-8')
    print(json.dumps(data['summary'],ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
