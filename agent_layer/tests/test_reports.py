from app.reports import student_report, teacher_report, parent_report

def test_reports():
    state = {"student_id":"T_REPORT","knowledge":{"mastery":0.4},
             "metacognition":{"jol_bias":0.2,"hesitation":0.6},
             "baseline":{"arrangement_fit":0.4,"habit_change":0.2},"group":{}}
    assert student_report(state)["student_id"] == "T_REPORT"
    assert teacher_report([state])["n_students"] == 1
    assert "privacy_note" in parent_report(state)
