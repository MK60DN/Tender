"""本地 RAG：TF-IDF + 可选 RAGFlow。"""
from __future__ import annotations
import os, pathlib, json, urllib.request
import numpy as np

CORPUS = pathlib.Path(__file__).resolve().parent.parent / "data" / "rag_corpus"
CORPUS.mkdir(parents=True, exist_ok=True)
_INDEX = {"vectorizer": None, "matrix": None, "chunks": []}


def ingest_text(name: str, text: str):
    p = CORPUS / (name if name.endswith(".txt") else name + ".txt")
    p.write_text(text, encoding="utf-8")
    return str(p)


def _load_chunks(max_chars=800):
    chunks = []
    for p in CORPUS.glob("*.txt"):
        text = p.read_text(encoding="utf-8", errors="ignore")
        for i in range(0, len(text), max_chars):
            chunk = text[i:i+max_chars].strip()
            if chunk:
                chunks.append({"source": p.name, "text": chunk})
    return chunks


def build_index():
    chunks = _load_chunks()
    _INDEX["chunks"] = chunks
    if not chunks:
        return {"n_chunks": 0, "mode": "empty"}
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        vec = TfidfVectorizer(max_features=30000, analyzer="char_wb", ngram_range=(2,4))
        mat = vec.fit_transform([c["text"] for c in chunks])
        _INDEX["vectorizer"] = vec
        _INDEX["matrix"] = mat
        return {"n_chunks": len(chunks), "mode": "tfidf"}
    except Exception as e:
        return {"n_chunks": len(chunks), "mode": "keyword", "error": repr(e)}


def search(query: str, top_k: int = 5):
    if not _INDEX["chunks"]:
        build_index()
    if not _INDEX["chunks"]:
        return []
    try:
        from sklearn.metrics.pairwise import cosine_similarity
        q = _INDEX["vectorizer"].transform([query])
        scores = cosine_similarity(q, _INDEX["matrix"])[0]
        idx = np.argsort(scores)[::-1][:top_k]
        return [{**_INDEX["chunks"][i], "score": float(scores[i])} for i in idx if scores[i] > 0]
    except Exception:
        q = set(query.lower().split())
        scored = []
        for c in _INDEX["chunks"]:
            s = len(q & set(c["text"].lower().split())) / max(len(q), 1)
            scored.append({**c, "score": s})
        return sorted(scored, key=lambda x: x["score"], reverse=True)[:top_k]


def ragflow_search(query: str, top_k: int = 5):
    url = os.getenv("RAGFLOW_API_URL", "")
    if not url:
        return None
    try:
        req = urllib.request.Request(url.rstrip("/") + "/v1/retrieval",
                                     data=json.dumps({"question": query, "top_k": top_k}).encode(),
                                     headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except Exception as e:
        return {"error": repr(e)}
