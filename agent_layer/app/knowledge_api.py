from pathlib import Path
import sqlite3
from fastapi import APIRouter, HTTPException, Query

from .knowledge_forest import forest_snapshot

router = APIRouter(prefix='/knowledge', tags=['knowledge'])
ROOT = Path(__file__).resolve().parents[2] / 'knowledge_data'
SUBJECT_INDEX = ROOT / 'subject_databases' / 'db_subject_index.sqlite'
K12 = ROOT / 'db_k12.sqlite'
UNIVERSITY = ROOT / 'db_university.sqlite'
COURSES = ROOT / 'db_university_courses.sqlite'


def _connect(path: Path):
    if not path.exists():
        raise HTTPException(status_code=503, detail=f'knowledge_database_missing:{path.name}')
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    return con


@router.get('/subjects')
def list_subjects():
    con = _connect(SUBJECT_INDEX)
    rows = [dict(r) for r in con.execute('SELECT * FROM subject_catalog ORDER BY subject_id')]
    con.close()
    return {'count': len(rows), 'subjects': rows}


@router.get('/tree/{subject_id}')
def subject_tree(subject_id: str, limit: int = Query(200, ge=1, le=2000)):
    con = _connect(SUBJECT_INDEX)
    catalog = con.execute('SELECT * FROM subject_catalog WHERE subject_id=?', (subject_id,)).fetchone()
    if not catalog:
        con.close()
        raise HTTPException(status_code=404, detail='subject_not_found')
    db_path = ROOT / 'subject_databases' / catalog['db_file']
    con.close()
    con = _connect(db_path)
    rows = [dict(r) for r in con.execute('''SELECT node_id,parent_id,name,node_type,module_scope,official_ref,evidence_type,difficulty,estimated_minutes FROM knowledge_nodes WHERE subject_id=? ORDER BY node_type,sort_order,node_id LIMIT ?''', (subject_id, limit))]
    con.close()
    return {'subject': dict(catalog), 'count': len(rows), 'nodes': rows}


@router.get('/search')
def search_knowledge(q: str = Query(..., min_length=1), limit: int = Query(20, ge=1, le=100)):
    con = _connect(K12)
    rows = [dict(r) for r in con.execute('''SELECT node_id,subject_id,name,node_type,module_scope,official_ref FROM knowledge_nodes WHERE name LIKE ? ORDER BY CASE WHEN name=? THEN 0 WHEN name LIKE ? THEN 1 ELSE 2 END,node_type LIMIT ?''', (f'%{q}%', q, f'{q}%', limit))]
    con.close()
    return {'query': q, 'count': len(rows), 'results': rows}


@router.get('/majors')
def search_majors(q: str = Query('', max_length=80), category_code: str | None = Query(None, max_length=4),
                  limit: int = Query(20, ge=1, le=500)):
    con = _connect(UNIVERSITY)
    where, params = [], []
    if category_code:
        where.append('m.category_code=?')
        params.append(category_code)
    if q.strip():
        pattern = f'%{q.strip()}%'
        where.append('(m.name LIKE ? OR m.code LIKE ?)')
        params.extend([pattern, pattern])
    clause = (' WHERE ' + ' AND '.join(where)) if where else ''
    order = " ORDER BY CASE WHEN m.name=? THEN 0 WHEN m.name LIKE ? THEN 1 ELSE 2 END,m.code" if q.strip() else ' ORDER BY m.code'
    sql = f'''SELECT m.code,m.name,cat.name category,cl.name class_name,m.category_code
            FROM majors m JOIN discipline_categories cat ON cat.code=m.category_code
            JOIN major_classes cl ON cl.code=m.class_code{clause}{order} LIMIT ?'''
    if q.strip():
        params.extend([q.strip(), f'{q.strip()}%'])
    params.append(limit)
    rows = [dict(r) for r in con.execute(sql, tuple(params))]
    con.close()
    return {'query': q, 'category_code': category_code, 'count': len(rows), 'majors': rows}


@router.get('/majors/{major_code}')
def major_detail(major_code: str):
    con = _connect(UNIVERSITY)
    major = con.execute('''SELECT m.code,m.name,m.degree_note,c.name category,cl.name class_name FROM majors m JOIN discipline_categories c ON c.code=m.category_code JOIN major_classes cl ON cl.code=m.class_code WHERE m.code=?''', (major_code,)).fetchone()
    con.close()
    if not major:
        raise HTTPException(status_code=404, detail='major_not_found')
    con = _connect(COURSES)
    courses = [dict(r) for r in con.execute('SELECT sequence_no,course_name,course_type,knowledge_domain,evidence_type,confidence FROM major_courses WHERE major_code=? ORDER BY sequence_no', (major_code,))]
    bridges = [dict(r) for r in con.execute('SELECT subject_id,weight,evidence_type,confidence,note FROM major_highschool_bridges WHERE major_code=? ORDER BY weight DESC', (major_code,))]
    competencies = [r['competency'] for r in con.execute('SELECT competency FROM major_competencies WHERE major_code=? ORDER BY weight DESC', (major_code,))]
    con.close()
    return {'major': dict(major), 'competencies': competencies, 'high_school_bridges': bridges, 'courses': courses, 'course_seed_available': bool(courses), 'boundary': '课程层为种子，正式选科与培养方案须核对官方来源'}


@router.get('/university/categories')
def university_categories():
    path = ROOT / 'subject_databases' / 'university' / 'db_university_index.sqlite'
    con = _connect(path)
    rows = [dict(r) for r in con.execute('SELECT * FROM category_catalog ORDER BY category_code')]
    con.close()
    return {'count': len(rows), 'categories': rows}



@router.get('/forest')
def knowledge_forest():
    return forest_snapshot()
