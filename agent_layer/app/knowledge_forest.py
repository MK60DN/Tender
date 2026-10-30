from __future__ import annotations

import sqlite3
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / 'knowledge_data'
SUBJECT_INDEX = ROOT / 'subject_databases' / 'db_subject_index.sqlite'
K12 = ROOT / 'db_k12.sqlite'
UNIVERSITY = ROOT / 'db_university.sqlite'
COURSES = ROOT / 'db_university_courses.sqlite'
CAREER = ROOT / 'db_career.sqlite'


def _connect(path: Path):
    if not path.exists():
        raise FileNotFoundError(path)
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    return con


@lru_cache(maxsize=1)
def forest_snapshot():
    # Return the complete knowledge ecosystem used by the forest view.
    subject_con = _connect(SUBJECT_INDEX)
    subjects = [dict(row) for row in subject_con.execute(
        'SELECT subject_id,name,node_count,unit_count,coverage FROM subject_catalog ORDER BY subject_id'
    )]
    subject_con.close()

    k12_con = _connect(K12)
    type_rows = [dict(row) for row in k12_con.execute(
        'SELECT subject_id,node_type,COUNT(*) AS count FROM knowledge_nodes GROUP BY subject_id,node_type'
    )]
    type_counts = {}
    for row in type_rows:
        type_counts.setdefault(row['subject_id'], {})[row['node_type']] = row['count']
    edge_total = k12_con.execute('SELECT COUNT(*) FROM knowledge_edges').fetchone()[0]
    question_total = k12_con.execute('SELECT COUNT(*) FROM question_modes').fetchone()[0]
    for subject in subjects:
        sid = subject['subject_id']
        subject['counts'] = type_counts.get(sid, {})
        subject['edge_count'] = k12_con.execute(
            'SELECT COUNT(*) FROM knowledge_edges WHERE source_node LIKE ? OR target_node LIKE ?',
            (f'{sid}:%', f'{sid}:%'),
        ).fetchone()[0]
        subject['question_mode_count'] = k12_con.execute(
            'SELECT COUNT(*) FROM question_modes WHERE subject_id=?', (sid,)
        ).fetchone()[0]
    k12_con.close()

    university_con = _connect(UNIVERSITY)
    disciplines = [dict(row) for row in university_con.execute('''
        SELECT c.code,c.name,
               COUNT(DISTINCT m.code) AS major_count,
               COUNT(DISTINCT m.class_code) AS class_count
        FROM discipline_categories c
        LEFT JOIN majors m ON m.category_code=c.code
        GROUP BY c.code,c.name ORDER BY c.code
    ''')]
    major_total = university_con.execute('SELECT COUNT(*) FROM majors').fetchone()[0]
    class_total = university_con.execute('SELECT COUNT(*) FROM major_classes').fetchone()[0]
    graduate_total = university_con.execute('SELECT COUNT(*) FROM graduate_disciplines').fetchone()[0]
    university_con.close()

    course_con = _connect(COURSES)
    course_total = course_con.execute('SELECT COUNT(*) FROM major_courses').fetchone()[0]
    course_edge_total = course_con.execute('SELECT COUNT(*) FROM course_edges').fetchone()[0]
    course_seed_majors = course_con.execute('SELECT COUNT(DISTINCT major_code) FROM major_courses').fetchone()[0]
    course_types = [dict(row) for row in course_con.execute(
        'SELECT course_type,COUNT(*) AS count FROM major_courses GROUP BY course_type ORDER BY count DESC,course_type'
    )]
    bridge_rows = [dict(row) for row in course_con.execute('''
        SELECT r.subject_id,m.category_code,COUNT(*) AS evidence_count,AVG(r.weight) AS weight
        FROM major_subject_requirements r
        JOIN majors m ON m.code=r.major_code
        GROUP BY r.subject_id,m.category_code
        ORDER BY evidence_count DESC,weight DESC
    ''')]
    course_con.close()

    known_subjects = {item['subject_id'] for item in subjects}
    links = [{
        'source': row['subject_id'],
        'target': row['category_code'],
        'evidence_count': row['evidence_count'],
        'weight': round(float(row['weight']), 4),
        'evidence_type': 'major_subject_requirement_heuristic',
    } for row in bridge_rows if row['subject_id'] in known_subjects]

    career_con = _connect(CAREER)
    career_total = career_con.execute('SELECT COUNT(*) FROM occupations').fetchone()[0]
    interest_dimensions = [dict(row) for row in career_con.execute(
        'SELECT code,name_zh,name_en FROM interest_dimensions ORDER BY code'
    )]
    career_con.close()

    return {
        'version': 'knowledge-forest-1.0',
        'status': 'live_database_snapshot',
        'totals': {
            'k12_subjects': len(subjects),
            'k12_nodes': sum(item['node_count'] for item in subjects),
            'k12_edges': edge_total,
            'question_modes': question_total,
            'discipline_categories': len(disciplines),
            'major_classes': class_total,
            'majors': major_total,
            'graduate_disciplines': graduate_total,
            'courses': course_total,
            'course_edges': course_edge_total,
            'course_seed_majors': course_seed_majors,
            'occupations': career_total,
            'crosswalk_links': len(links),
        },
        'subjects': subjects,
        'disciplines': disciplines,
        'course_types': course_types,
        'career': {'occupations': career_total, 'riasec': interest_dimensions},
        'links': links,
        'layers': [
            {'id': 'subjects', 'name': '知识树层', 'meaning': '高中课程标准结构化后的领域、单元与概念'},
            {'id': 'disciplines', 'name': '专业林层', 'meaning': '本科门类、专业类、专业与研究生学科'},
            {'id': 'courses', 'name': '课程灌层', 'meaning': '代表专业的课程名与先修顺序种子'},
            {'id': 'careers', 'name': '职业天际层', 'meaning': '职业与 RIASEC 兴趣方向'},
            {'id': 'links', 'name': '生态廊道', 'meaning': '高中学科与本科门类之间的启发式桥接'},
        ],
        'coverage': {
            'course_seed_ratio': round(course_seed_majors / major_total, 4) if major_total else 0,
            'course_seed_gap_majors': max(0, major_total - course_seed_majors),
            'note': '26 个代表专业已有课程种子，不代表 875 个专业都拥有完整培养方案。',
        },
        'boundary': '森林展示的是现有知识与路径数据库的覆盖与连接，不是智力、能力或兴趣诊断；专业要求与选科必须以官方当年来源为准。',
    }

