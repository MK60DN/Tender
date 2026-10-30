from app.main import roles, role_home


def test_roles():
    consumer = roles()
    consumer_ids = {r["id"] for r in consumer["roles"]}
    assert consumer["surface"] == "consumer"
    assert consumer_ids == {"learner", "parent"}
    assert all(r["surface"] == "consumer" for r in consumer["roles"])

    advisors = roles(surface="advisor_runtime")
    advisor_ids = {r["id"] for r in advisors["roles"]}
    assert {"health_advisor", "nutrition_advisor", "neurocognitive_advisor", "psychology_advisor", "learning_science_advisor", "career_advisor", "safety_advisor"} <= advisor_ids

    catalog = roles(surface="all")
    ids = {r["id"] for r in catalog["roles"]}
    assert {"learner", "parent", "teacher", "health_advisor", "nutrition_advisor", "neurocognitive_advisor", "psychology_advisor", "learning_science_advisor", "career_advisor", "safety_advisor", "head_teacher", "institution", "sales"} <= ids
    for role_id in ["learner", "parent", "teacher", "health_advisor", "nutrition_advisor", "neurocognitive_advisor", "psychology_advisor", "learning_science_advisor", "career_advisor", "safety_advisor", "head_teacher", "institution", "sales"]:
        out = role_home(role_id, "S01", "理科班")
        assert out["role"]["id"] == role_id
        assert out["rbac_status"] == "preview_only"
        assert isinstance(out["data"], dict) and out["data"]
    legacy = role_home("subject_teacher", "S01", "理科班", "institution")
    assert legacy["role"]["id"] == "teacher"
    assert legacy["data"]["teacher_mode"] == "institution"
    legacy_dorm = role_home("dorm_supervisor", "S01", "理科班")
    assert legacy_dorm["role"]["id"] == "health_advisor"
    assert "advisor" in legacy_dorm["data"]
