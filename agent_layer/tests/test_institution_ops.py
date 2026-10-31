from uuid import uuid4
from fastapi import HTTPException
from app.main import (
    institution_performance, create_schedule, institution_schedule,
    teacher_availability, role_home, TeacherScheduleCreate, finance_rules,
    estimate_finance, FinanceEstimateInput,
)


def test_institution_ops():
    perf = institution_performance("理科班")
    assert perf["class_id"] == "理科班"
    assert "metrics" in perf and "excluded_dimensions" in perf
    assert perf["decision_rule"].startswith("仅用于")

    teacher_id = "teacher_test_" + uuid4().hex[:8]
    item = TeacherScheduleCreate(
        teacher_id=teacher_id, teacher_name="测试教师", class_id="理科班",
        weekday=1, start_time="09:00", end_time="10:00", course="英语", room="A1",
    )
    created = create_schedule(item)
    assert created["status"] == "stored"
    listed = institution_schedule("all")["items"]
    assert any(x["teacher_id"] == teacher_id for x in listed)
    availability = teacher_availability(teacher_id)
    assert availability["items"]
    try:
        create_schedule(TeacherScheduleCreate(
            teacher_id=teacher_id, class_id="理科班", weekday=1,
            start_time="09:30", end_time="10:30", course="英语", room="A2",
        ))
        assert False, "overlap should fail"
    except HTTPException as exc:
        assert exc.status_code == 409
    data = role_home("institution")["data"]
    assert "performance" in data and "schedule" in data