from app.main import (
    student_status_board, update_student_status, StudentStatusUpdate,
    create_teaching_task, TeachingTaskCreate, list_teaching_tasks,
    complete_teaching_task, TeachingTaskComplete,
    write_dorm_rollcall, DormRollCallCreate, role_home,
)


def test_cross_role_ops():
    status = update_student_status("理科班", StudentStatusUpdate(student_id="S11", status="leave", note="测试：请假状态"))
    assert status["status"] == "stored"
    board = student_status_board("理科班")
    assert any(x["student_id"] == "S11" and x["status"] == "leave" for x in board["students"])

    task = create_teaching_task("理科班", TeachingTaskCreate(
        class_id="理科班", subject="英语", title="测试：语法填空复盘", student_ids=["S01"]))
    assert task["status"] == "assigned"
    listed = list_teaching_tasks("理科班")["tasks"]
    assert any(t["task_event_id"] == task["event_id"] for t in listed)
    done = complete_teaching_task("理科班", task["event_id"], TeachingTaskComplete(note="测试完成"))
    assert done["status"] == "completed"

    call = write_dorm_rollcall("理科班", DormRollCallCreate(
        class_id="理科班", expected_ids=["S01", "S02"], actual_ids=["S01"],
        exceptions=[{"student_id": "S02", "reason": "测试异常"}]))
    assert "今日宿舍巡查结束" in call["report"]

    assert "tasks" in role_home("teacher", "S01", "理科班", "institution")["data"]
    assert "status_board" in role_home("dorm_supervisor", "S01", "理科班")["data"]