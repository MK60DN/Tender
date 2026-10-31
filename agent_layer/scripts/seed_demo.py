"""种子演示：19 名学生 + 样例事件 + 因果关系。"""
from __future__ import annotations
import sys, pathlib, random
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from app.daoql import insert_event, insert_edge

SCI = ["张钊源","冯琦","王毅玮","陆怡婷","孙欣","顾浩喆","王萧鸣","张伦硕","张家赫","柴静轩","王昱琳"]
ART = ["霍靖瑶","马林川","屈昕旸","郭嘉冉","刘泽宇","武钰淳","孙艺轩","李陈浩然"]
ROSTER = [{"student_id": f"S{i:02d}", "class": "理科班", "name": n} for i, n in enumerate(SCI, 1)] + \
         [{"student_id": f"A{i:02d}", "class": "文科班", "name": n} for i, n in enumerate(ART, 1)]


def main():
    random.seed(20261016)
    n = 0
    for r in ROSTER:
        sid = r["student_id"]
        base = 0.5 + random.uniform(-0.2, 0.2)
        for k in range(6):
            correct = random.random() < base
            e1 = insert_event({"event_type":"answer","student_id":sid,"session_id":f"ses{k}",
                               "payload":{"correct":correct,"item_id":f"q{k}"},"source":"platform"})
            e2 = insert_event({"event_type":"metacognition_jol","student_id":sid,"session_id":f"ses{k}",
                               "payload":{"predicted_correct":random.randint(4,9),"actual_correct":6 if correct else 3,"n_items":10},
                               "source":"teacher_card"})
            e3 = insert_event({"event_type":"response","student_id":sid,"session_id":f"ses{k}",
                               "payload":{"response_time_ms":random.randint(8000,90000)},"source":"platform"})
            insert_edge(e1, e2, "precedes", 0.6, {"session":f"ses{k}"})
            n += 3
        insert_event({"event_type":"baseline","student_id":sid,"session_id":"baseline",
                      "payload":{"arrangement_fit":round(random.uniform(0.4,0.9),3),
                                 "habit_change":round(random.uniform(0,0.4),3)},"source":"scheduler"})
        insert_event({"event_type":"group_interaction","student_id":sid,"session_id":"survey",
                      "payload":{"clustering":round(random.uniform(0.2,0.8),3),
                                 "bridge_ratio":round(random.uniform(0.1,0.6),3)},"source":"survey"})
        n += 2
    print("seeded students", len(ROSTER), "events", n)


if __name__ == "__main__":
    main()
