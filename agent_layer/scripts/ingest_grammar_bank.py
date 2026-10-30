"""把 D:\\Tender\\data 下的语法填空 CSV 导入 DAOQL。"""
from __future__ import annotations
import sys, pathlib, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from app.daoql import insert_event

DATA = pathlib.Path(r"D:\Tender\data")


def main():
    n = 0
    for p in DATA.glob("*.csv"):
        try:
            df = pd.read_csv(p, encoding="utf-8-sig")
        except Exception:
            continue
        for _, row in df.iterrows():
            payload = {str(k): (None if pd.isna(v) else str(v)) for k, v in row.items()}
            insert_event({"event_type":"content_row","student_id":"CORPUS",
                          "payload":{"file":p.name,**payload},"source":"grammar_bank"})
            n += 1
    print("ingested rows", n)


if __name__ == "__main__":
    main()
