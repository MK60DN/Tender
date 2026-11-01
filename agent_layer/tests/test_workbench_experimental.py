import json

from app.workbench_experimental import safe_payload, status


def test_experimental_api_is_redacted_and_status_is_secret_free():
    current = status()
    assert current["mode"] == "experimental_redacted_summary"
    assert "api_key" not in current
    payload = safe_payload(
        {
            "task_type": "mentalization_support",
            "objective": "联系张三 13800138000 zhang@example.com https://example.com/private",
            "audience_role": "parent",
        },
        {
            "student_name": "张三",
            "mastery": 0.5,
            "jol_bias": 0.1,
            "hesitation": 0.2,
            "event_count": 94,
        },
    )
    blob = json.dumps(payload, ensure_ascii=False)
    assert "张三" not in blob
    assert "13800138000" not in blob
    assert "zhang@example.com" not in blob
    assert "example.com/private" not in blob
    assert payload["objective_length"] > 0
    assert payload["state_summary"]["event_count_bucket"] == 90
    assert "不发送姓名、原始对话和健康信息" in payload["policy"]


if __name__ == "__main__":
    test_experimental_api_is_redacted_and_status_is_secret_free()
    print("ok experimental workbench tests")
