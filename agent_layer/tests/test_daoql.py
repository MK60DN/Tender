from app.daoql import insert_event, insert_edge, causal_path, event_graph

def test_causal_graph():
    a = insert_event({"event_type":"test_a","student_id":"T_DAOQL","payload":{},"source":"test"})
    b = insert_event({"event_type":"test_b","student_id":"T_DAOQL","payload":{},"source":"test"})
    insert_edge(a,b,"causes",0.9,{"why":"unit test"})
    p = causal_path(a,b)
    assert p["found"] is True
    g = event_graph("T_DAOQL")
    assert len(g["nodes"]) >= 2
