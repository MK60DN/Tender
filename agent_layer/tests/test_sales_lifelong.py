from app.main import sales_ammunition, lifelong_passport, lifelong_transitions

def test_sales_lifelong():
    s = sales_ammunition("理科班")
    assert "actions" in s and "kpis" in s and "scripts" in s
    t = lifelong_transitions()
    assert len(t["transitions"]) == 7
    p = lifelong_passport("S01")
    assert p["learner_id"] == "S01" and "skills" in p
