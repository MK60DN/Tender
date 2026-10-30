from __future__ import annotations

import json
import urllib.request


def get(path: str):
    with urllib.request.urlopen(f"http://127.0.0.1:8080{path}", timeout=10) as response:
        return response.status, json.load(response)


def post(path: str, payload: dict):
    request = urllib.request.Request(
        f"http://127.0.0.1:8080{path}",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        return response.status, json.load(response)


if __name__ == "__main__":
    print("health", get("/health"))
    language_status, language = post(
        "/language/analyze",
        {"text": "我明明会，考试又错，老师是不是觉得我不行？我不想学了。"},
    )
    print("language", language_status, [item["id"] for item in language["hypotheses"]])
    forest_status, forest = get("/knowledge/forest")
    print("forest", forest_status, forest["totals"])
