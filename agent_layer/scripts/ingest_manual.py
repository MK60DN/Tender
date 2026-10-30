"""把完整版手册文本导入本地 RAG 语料。"""
from __future__ import annotations
import sys, pathlib, re
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from app.rag import ingest_text, build_index

SRC = pathlib.Path(r"D:\Tender\教学手册\Tender零基础全流程教学手册-完整版.tex")


def strip_latex(text: str) -> str:
    text = re.sub(r"\\[a-zA-Z]+\*?(\[[^\]]*\])?(\{[^{}]*\})?", " ", text)
    text = re.sub(r"[{}]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def main():
    text = strip_latex(SRC.read_text(encoding="utf-8-sig"))
    p = ingest_text("tender_handbook", text)
    print("ingested", p, "chars", len(text))
    print(build_index())


if __name__ == "__main__":
    main()
