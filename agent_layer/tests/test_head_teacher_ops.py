from app.main import report_head_teacher, write_head_teacher_note, HeadTeacherNote


def test_head_teacher_ops():
    r = report_head_teacher("理科班")
    assert len(r["shift"]["schedule"]) == 8
    assert r["shift"]["current_block"]
    assert r["collaboration"]["tickets"]
    assert r["collaboration"]["responsibility_matrix"]
    assert r["care_board"]
    assert r["handoff_templates"]
    note = HeadTeacherNote(student_id="S01", category="learning", text="19:10 完成语法填空复盘，记录供后续核对。")
    out = write_head_teacher_note("理科班", note)
    assert out["status"] == "stored"
    assert out["event_id"].startswith("evt_")