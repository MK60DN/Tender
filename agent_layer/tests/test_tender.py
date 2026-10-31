from app.daoql import insert_event, list_events
from app.tender import compute_state

def test_tender_state():
    insert_event({"event_type":"answer","student_id":"T_TENDER","payload":{"correct":True},"source":"test"})
    insert_event({"event_type":"metacognition_jol","student_id":"T_TENDER","payload":{"predicted_correct":8,"actual_correct":5,"n_items":10},"source":"test"})
    insert_event({"event_type":"response","student_id":"T_TENDER","payload":{"response_time_ms":60000},"source":"test"})
    s = compute_state("T_TENDER", list_events("T_TENDER"))
    assert 0 <= s["knowledge"]["mastery"] <= 1
    assert "jol_bias" in s["metacognition"]
