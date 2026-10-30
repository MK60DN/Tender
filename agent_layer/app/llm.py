"""LLM 适配层：支持 OpenAI-compatible API、Codex 实验 API，默认 mock。"""
from __future__ import annotations
import os, json, re, urllib.request, pathlib

CODEX_CONFIG = pathlib.Path.home() / ".codex" / "config.toml"


def _codex_experimental():
    """自动读取 Codex 的本地实验 API 配置，不打印也不复制 Key。"""
    if not CODEX_CONFIG.exists():
        return None
    try:
        s = CODEX_CONFIG.read_text(encoding="utf-8")
        tok = re.search(r'experimental_bearer_token\s*=\s*"([^"]+)"', s)
        base = re.search(r'base_url\s*=\s*"([^"]+)"', s)
        model = re.search(r'^model\s*=\s*"([^"]+)"', s, re.M)
        if tok and base:
            return {"api_key": tok.group(1), "base_url": base.group(1).rstrip("/"),
                    "model": model.group(1) if model else "deepseek-v4-flash"}
    except Exception:
        return None
    return None


def config():
    codex = _codex_experimental()
    env_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY") or ""
    env_base = os.getenv("LLM_BASE_URL") or os.getenv("OPENAI_BASE_URL") or ""
    env_model = os.getenv("LLM_MODEL") or os.getenv("OPENAI_MODEL") or ""
    if codex and not env_key:
        provider = os.getenv("LLM_PROVIDER", "codex-experimental")
        api_key, base_url, model = codex["api_key"], codex["base_url"], codex["model"]
    else:
        provider = os.getenv("LLM_PROVIDER", "openai-compatible" if env_key else "mock")
        api_key = env_key
        base_url = (env_base or "https://api.openai.com/v1").rstrip("/")
        model = env_model or "gpt-4o-mini"
    return {
        "provider": provider,
        "api_key": api_key,
        "base_url": base_url.rstrip("/"),
        "model": model,
        "temperature": float(os.getenv("LLM_TEMPERATURE", "0.3")),
        "max_tokens": int(os.getenv("LLM_MAX_TOKENS", "2048")),
    }


def _mock_reply(messages):
    user = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            user = m.get("content", "")
            break
    return ("（mock 模式）我收到了你的问题。当前没有配置真实 LLM Key。\n"
            "建议：先说说你卡在哪一步，或者你觉得自己是不确定，还是只是需要更多时间？\n"
            "问题摘要：" + user[:120])


def _extract(data):
    try:
        msg = data["choices"][0]["message"]
        content = (msg.get("content") or "").strip()
        if content:
            return content, ""
        reasoning = (msg.get("reasoning_content") or "").strip()
        return "", reasoning
    except Exception:
        return "", ""


def chat(messages, temperature=None, max_tokens=None):
    c = config()
    if c["provider"] == "mock" or not c["api_key"]:
        return {"provider": "mock", "model": "mock", "text": _mock_reply(messages)}
    body = {
        "model": c["model"],
        "messages": messages,
        "temperature": c["temperature"] if temperature is None else temperature,
        "max_tokens": c["max_tokens"] if max_tokens is None else max_tokens,
    }
    req = urllib.request.Request(
        c["base_url"] + "/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + c["api_key"]},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            data = json.load(r)
        content, reasoning = _extract(data)
        if content:
            return {"provider": c["provider"], "model": c["model"], "text": content}
        if reasoning:
            return {"provider": c["provider"], "model": c["model"],
                    "text": "（模型只返回了推理内容，未返回最终答案；请提高 max_tokens）\n" + reasoning[:800],
                    "reasoning_only": True}
        return {"provider": c["provider"], "model": c["model"], "text": _mock_reply(messages),
                "error": "empty content"}
    except Exception as e:
        return {"provider": "fallback", "model": c["model"], "text": _mock_reply(messages), "error": repr(e)}
