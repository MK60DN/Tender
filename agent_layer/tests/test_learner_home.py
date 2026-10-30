from app.main import learner_home, export_learner_data


def test_learner_home():
    x = learner_home("S01")
    assert x["learner_id"] == "S01"
    assert x["tender_id"] == "TENDER-S01"
    assert x["data_ownership"] == "学习者拥有"
    assert "next_actions" in x["plan"]
    assert "evidence" in x["passport"]
    assert 0.0 <= x["portability"]["score"] <= 1.0
    assert x["privacy"]["guardian_required"] is True
    assert x["marketplace"]["status"] == "planned"
    assert x["mentalization"]["summary"]
    assert x["mentalization"]["boundary"].startswith("这是用于学习支持")
    assert x["support_network"] and x["support_network"][0]["name"] == "学习科学顾问"
    exported = export_learner_data("S01")
    assert exported.status_code == 200
    assert "attachment" in exported.headers["content-disposition"]