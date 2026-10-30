"""19 名学生名单。"""

SCI = ["张钊源","冯琦","王毅玮","陆怡婷","孙欣","顾浩喆","王萧鸣","张伦硕","张家赫","柴静轩","王昱琳"]
ART = ["霍靖瑶","马林川","屈昕旸","郭嘉冉","刘泽宇","武钰淳","孙艺轩","李陈浩然"]

ROSTER = [{"student_id": f"S{i:02d}", "class": "理科班", "name": n} for i, n in enumerate(SCI, 1)] + \
         [{"student_id": f"A{i:02d}", "class": "文科班", "name": n} for i, n in enumerate(ART, 1)]


def students_in_class(class_id: str):
    if class_id in ("all", "全部", ""):
        return [r["student_id"] for r in ROSTER]
    ids = [r["student_id"] for r in ROSTER if r["class"] == class_id]
    return ids or [r["student_id"] for r in ROSTER]
