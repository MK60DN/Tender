"""Resolve a learner message to bounded K12 knowledge-graph context."""
from __future__ import annotations

import sqlite3
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2] / 'knowledge_data'
K12 = ROOT / 'db_k12.sqlite'
SUBJECT_INDEX = ROOT / 'subject_databases' / 'db_subject_index.sqlite'
UNIVERSITY = ROOT / 'db_university.sqlite'
COURSES = ROOT / 'db_university_courses.sqlite'
CAREER = ROOT / 'db_career.sqlite'

SUBJECT_ALIASES = {
    '数学': 'k12:math',
    '物理': 'k12:physics',
    '化学': 'k12:chemistry',
    '生物': 'k12:biology',
    '生物学': 'k12:biology',
    '英语': 'k12:english',
    '语文': 'k12:chinese',
    '历史': 'k12:history',
    '地理': 'k12:geography',
    '政治': 'k12:politics',
    '思想政治': 'k12:politics',
    '信息技术': 'k12:it',
    '通用技术': 'k12:general_technology',
    '艺术': 'k12:arts',
    '美术': 'k12:arts',
    '体育': 'k12:pe_health',
}


def _connect(path: Path):
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    return con


@lru_cache(maxsize=1)
def _nodes() -> tuple[dict, ...]:
    if not K12.exists():
        return ()
    with _connect(K12) as con:
        return tuple(dict(row) for row in con.execute(
            'SELECT node_id,subject_id,parent_id,name,node_type,module_scope,difficulty,estimated_minutes,sort_order FROM knowledge_nodes'
        ))


@lru_cache(maxsize=1)
def _edges() -> tuple[dict, ...]:
    if not K12.exists():
        return ()
    with _connect(K12) as con:
        return tuple(dict(row) for row in con.execute('SELECT * FROM knowledge_edges'))


@lru_cache(maxsize=1)
def _subject_catalog() -> dict[str, dict]:
    if not SUBJECT_INDEX.exists():
        return {}
    with _connect(SUBJECT_INDEX) as con:
        return {row['subject_id']: dict(row) for row in con.execute('SELECT * FROM subject_catalog')}


@lru_cache(maxsize=1)
def _majors() -> tuple[dict, ...]:
    if not COURSES.exists():
        return ()
    with _connect(COURSES) as con:
        return tuple(dict(row) for row in con.execute('SELECT code,name,category_code,class_code,degree_note FROM majors'))


@lru_cache(maxsize=1)
def _occupations() -> tuple[dict, ...]:
    if not CAREER.exists():
        return ()
    with _connect(CAREER) as con:
        return tuple(dict(row) for row in con.execute('SELECT code,title,description FROM occupations'))


def _major_context(topic_text: str, full_text: str) -> dict:
    intent_words = ('专业', '大学', '转行', '职业', '就业', '志愿', '培养方案', '课程')
    intent = any(word in full_text for word in intent_words)
    scored = []
    for major in _majors():
        score = _lcs_len(topic_text, major['name'])
        if score >= 3:
            scored.append((score + (4 if major['name'] in topic_text else 0), major))
    scored.sort(key=lambda pair: -pair[0])
    matches = []
    for _, major in scored[:3]:
        courses, competencies, bridges, coverage = [], [], [], None
        with _connect(COURSES) as con:
            courses = [dict(row) for row in con.execute(
                'SELECT sequence_no,course_name,course_type,knowledge_domain,evidence_type,confidence FROM major_courses WHERE major_code=? ORDER BY sequence_no LIMIT 12',
                (major['code'],),
            )]
            competencies = [row[0] for row in con.execute('SELECT competency FROM major_competencies WHERE major_code=? ORDER BY weight DESC LIMIT 8', (major['code'],))]
            bridges = [dict(row) for row in con.execute('SELECT subject_id,weight,evidence_type,confidence,note FROM major_highschool_bridges WHERE major_code=? ORDER BY weight DESC LIMIT 6', (major['code'],))]
            row = con.execute('SELECT coverage_status,course_count,evidence_note FROM program_coverage WHERE major_code=?', (major['code'],)).fetchone()
            coverage = dict(row) if row else None
        matches.append({**major, 'courses': courses, 'competencies': competencies, 'highschool_bridges': bridges, 'coverage': coverage})
    return {
        'intent_detected': intent,
        'matches': matches,
        'available': bool(matches),
        'boundary': '专业课程为种子和探索路径，正式选科、培养方案与招生要求必须以官方来源为准。',
    }


def _career_context(full_text: str) -> dict:
    intent = any(word in full_text for word in ('职业', '就业', '转行', '工作', '岗位', '行业'))
    lower = full_text.lower()
    tokens = [token for token in lower.replace('，', ' ').replace('。', ' ').split() if len(token) >= 4]
    matches = []
    for occupation in _occupations():
        title = occupation['title'].lower()
        if any(token in title for token in tokens):
            matches.append(dict(occupation))
    dimensions = []
    if CAREER.exists():
        with _connect(CAREER) as con:
            dimensions = [dict(row) for row in con.execute('SELECT code,name_zh,name_en,description FROM interest_dimensions ORDER BY code')]
    return {
        'intent_detected': intent,
        'matches': matches[:5],
        'riasec_dimensions': dimensions,
        'match_method': 'occupation_title' if matches else ('riasec_fallback' if intent else 'none'),
        'available': bool(matches or intent),
        'boundary': '职业数据用于探索兴趣与能力方向，不用于命定式职业选择或招聘决策。',
    }


def _subject_id(text: str) -> str | None:
    for alias, subject_id in SUBJECT_ALIASES.items():
        if alias in text:
            return subject_id
    return None


def _lcs_len(left: str, right: str) -> int:
    if not left or not right:
        return 0
    best = 0
    previous = [0] * (len(right) + 1)
    for char in left:
        current = [0]
        for index, other in enumerate(right, start=1):
            value = previous[index - 1] + 1 if char == other else 0
            current.append(value)
            best = max(best, value)
        previous = current
    return best


def _node_by_id() -> dict[str, dict]:
    return {node['node_id']: node for node in _nodes()}


def _path(node: dict, by_id: dict[str, dict]) -> list[dict]:
    path = []
    current = node
    while current and current.get('node_id') not in {item.get('node_id') for item in path}:
        path.append(current)
        current = by_id.get(current.get('parent_id'))
    return list(reversed(path))


def _mastery(events: list[dict], node_id: str) -> dict:
    outcomes = []
    for event in events:
        if event.get('event_type') != 'answer':
            continue
        payload = event.get('payload') or {}
        if payload.get('node_id') != node_id and payload.get('knowledge_node_id') != node_id:
            continue
        outcomes.append(1.0 if payload.get('correct') else 0.0)
    return {
        'value': round(sum(outcomes) / len(outcomes), 4) if outcomes else None,
        'observations': len(outcomes),
        'source': 'DAOQL answer events' if outcomes else 'no node-level observations',
    }


def _related_nodes(node_id: str, by_id: dict[str, dict]) -> tuple[list[dict], list[dict]]:
    prerequisites, next_nodes = [], []
    for edge in _edges():
        if edge.get('target_node') == node_id and edge.get('relation') in {'recommended_before', 'recommended_sequence'}:
            source = by_id.get(edge.get('source_node'))
            if source:
                prerequisites.append({'node_id': source['node_id'], 'name': source['name'], 'strength': edge.get('confidence', edge.get('strength'))})
        if edge.get('source_node') == node_id and edge.get('relation') in {'recommended_before', 'recommended_sequence'}:
            target = by_id.get(edge.get('target_node'))
            if target:
                next_nodes.append({'node_id': target['node_id'], 'name': target['name'], 'strength': edge.get('confidence', edge.get('strength'))})
    return prerequisites[:4], next_nodes[:4]


def _subject_details(subject_id: str, path: list[dict], node_id: str) -> dict:
    catalog = _subject_catalog().get(subject_id)
    if not catalog:
        return {'question_modes': [], 'competencies': []}
    db_path = ROOT / 'subject_databases' / catalog['db_file']
    if not db_path.exists():
        return {'question_modes': [], 'competencies': []}
    unit_ids = [item['node_id'] for item in path if item.get('node_type') == 'unit']
    question_modes, competencies = [], []
    with _connect(db_path) as con:
        if unit_ids:
            placeholders = ','.join('?' for _ in unit_ids)
            rows = con.execute(f'''SELECT DISTINCT q.name,q.description,u.importance FROM unit_question_modes u
                JOIN question_modes q ON q.question_mode_id=u.question_mode_id
                WHERE u.node_id IN ({placeholders}) ORDER BY u.importance DESC,q.name LIMIT 6''', tuple(unit_ids)).fetchall()
            question_modes = [dict(row) for row in rows]
        rows = con.execute('''SELECT c.name,c.description,nc.weight FROM node_competencies nc
            JOIN competencies c ON c.competency_id=nc.competency_id
            WHERE nc.node_id=? ORDER BY nc.weight DESC LIMIT 5''', (node_id,)).fetchall()
        competencies = [dict(row) for row in rows]
    return {'question_modes': question_modes, 'competencies': competencies}


def build_knowledge_context(user_message: str = '', task_hint: str | None = None, events: list[dict] | None = None) -> dict:
    text = ' '.join(str(part or '') for part in (user_message, task_hint)).strip()
    if not text or not _nodes():
        return {'available': False, 'query': text, 'matches': [], 'reason': 'no_query_or_database', 'boundary': '知识体系未命中时不要假设具体知识点。'}
    subject_id = _subject_id(text)
    topic_text = text
    for alias in sorted(SUBJECT_ALIASES, key=len, reverse=True):
        topic_text = topic_text.replace(alias, " ")
    by_id = _node_by_id()
    major = _major_context(topic_text, text)
    career = _career_context(text)
    scored = []
    for node in _nodes():
        if node['node_type'] not in {'concept', 'unit', 'domain'}:
            continue
        if subject_id and node['subject_id'] != subject_id:
            continue
        score = _lcs_len(topic_text, node['name'])
        minimum_match = 2 if subject_id else 3
        if score < minimum_match and node['name'] not in topic_text:
            continue
        if node['name'] in topic_text:
            score += 8
        if node['node_type'] == 'concept':
            score += 2
        scored.append((score, node))
    scored.sort(key=lambda pair: (-pair[0], pair[1]['node_type'] != 'concept', pair[1].get('sort_order', 0)))
    concept_matches = [node for _, node in scored if node['node_type'] == 'concept']
    selected = concept_matches[:3] if concept_matches else [node for _, node in scored[:3]]
    method = 'topic_match'
    if not selected and subject_id:
        selected = [node for node in _nodes() if node['subject_id'] == subject_id and node['node_type'] == 'unit'][:3]
        method = 'subject_fallback'
    if not selected:
        available = bool(major.get('available') or career.get('available'))
        return {
            'available': available,
            'query': text,
            'subject_id': subject_id,
            'matches': [],
            'major': major,
            'career': career,
            'reason': 'major_or_career_only' if available else 'no_knowledge_match',
            'boundary': '知识体系未命中时不要假设具体知识点；专业和职业信息只作为探索依据。',
        }
    matches = []
    for node in selected:
        path = _path(node, by_id)
        prerequisites, next_nodes = _related_nodes(node['node_id'], by_id)
        matches.append({
            'specific': method == 'topic_match',
            'node_id': node['node_id'],
            'name': node['name'],
            'node_type': node['node_type'],
            'subject_id': node['subject_id'],
            'module_scope': node.get('module_scope'),
            'difficulty': node.get('difficulty'),
            'estimated_minutes': node.get('estimated_minutes'),
            'path': [{'node_id': item['node_id'], 'name': item['name'], 'node_type': item['node_type']} for item in path],
            'prerequisites': prerequisites,
            'next_nodes': next_nodes,
            'learner_mastery': _mastery(events or [], node['node_id']),
            **_subject_details(node['subject_id'], path, node['node_id']),
        })
    subject_ids = {node['subject_id'] for node in selected}
    subject_ambiguous = subject_id is None and len(subject_ids) > 1
    subject_names = [_subject_catalog().get(item, {}).get('name', item) for item in sorted(subject_ids)]
    return {
        'available': True,
        'query': text,
        'subject_id': selected[0]['subject_id'],
        'subject_name': _subject_catalog().get(selected[0]['subject_id'], {}).get('name'),
        'subject_ambiguous': subject_ambiguous,
        'subject_names': subject_names,
        'match_method': method,
        'confidence': 'topic_match' if method == 'topic_match' else 'subject_fallback',
        'matches': matches,
        'major': major,
        'career': career,
        'boundary': '知识节点用于组织下一步学习与练习；正式课程、选科和考试要求仍需核对官方来源。',
    }
