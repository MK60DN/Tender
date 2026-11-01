"""Tender visible-interface MCP server.

Run as a local stdio MCP server. The user must explicitly grant a scoped,
short-lived session before any screen metadata or text is returned. Raw screen
content is never written to DAOQL by this server.
"""
from __future__ import annotations

import os
from typing import Any

from mcp.server.fastmcp import FastMCP, Image

from screen_context import (
    CONSENT_PHRASE,
    DEFAULT_DURATION_MINUTES,
    DEFAULT_MAX_TEXT_CHARS,
    DEFAULT_MAX_WINDOWS,
    ConsentStore,
    ScreenContextError,
    capture_authorized_screen,
    read_screen_context as read_authorized_screen_context,
)

MCP_INSTRUCTIONS = """
Tender Screen Context only reads a user's visible desktop after an explicit,
short-lived authorization. Before grant_screen_context, ask the user in plain
language what will be read and for how long. Never call it automatically and
never preselect screenshot access. Only read visible top-level windows; hidden
tabs, password fields, clipboard, camera, microphone, keystrokes, and protected
DRM content are outside coverage. Raw window text and screenshots stay on the
local machine and must not be copied into DAOQL. Derived task signals may be
coarse categories only. Stop immediately when the user says stop.
""".strip()

mcp = FastMCP("Tender Screen Context", instructions=MCP_INSTRUCTIONS)
_store: ConsentStore | None = None


def store() -> ConsentStore:
    global _store
    if _store is None:
        _store = ConsentStore()
    return _store


def _error(exc: Exception) -> dict[str, Any]:
    if isinstance(exc, ScreenContextError):
        return {"ok": False, "error": exc.code, "message": str(exc)}
    if isinstance(exc, ValueError):
        return {"ok": False, "error": str(exc), "message": "授权参数无效。"}
    return {"ok": False, "error": "screen_context_failed", "message": "界面读取没有完成。"}


@mcp.tool(
    title="授权读取当前界面",
    description=(
        "Create a short-lived local consent session. Call only after the user explicitly asks Tender "
        "to read visible windows. Both acknowledge=true and confirmation_text must be supplied. "
        f"Ask the user to confirm exactly: {CONSENT_PHRASE}. Screenshot scope must be requested separately."
    ),
)
def grant_screen_context(
    student_id: str,
    scopes: list[str],
    duration_minutes: int = DEFAULT_DURATION_MINUTES,
    acknowledge: bool = False,
    confirmation_text: str = "",
) -> dict[str, Any]:
    try:
        result = store().grant(
            student_id,
            scopes,
            duration_minutes=duration_minutes,
            acknowledge=acknowledge,
            confirmation_text=confirmation_text,
        )
        return {"ok": True, **result}
    except Exception as exc:
        return _error(exc)


@mcp.tool(
    title="查看界面读取授权",
    description="Check whether a consent token is active, its scopes, and its remaining seconds.",
)
def screen_context_status(consent_token: str, student_id: str | None = None) -> dict[str, Any]:
    try:
        return {"ok": True, **store().status(consent_token, student_id=student_id)}
    except Exception as exc:
        return _error(exc)


@mcp.tool(
    title="读取可见界面",
    description=(
        "Read metadata and redacted accessible text from currently visible top-level windows across the "
        "virtual desktop. Requires an active windows scope; accessible text additionally requires the "
        "accessible scope. Does not return screenshots or persist content."
    ),
)
def read_screen_context(
    consent_token: str,
    student_id: str | None = None,
    max_windows: int = DEFAULT_MAX_WINDOWS,
    max_text_chars: int = DEFAULT_MAX_TEXT_CHARS,
) -> dict[str, Any]:
    try:
        result = read_authorized_screen_context(
            store(),
            consent_token,
            student_id=student_id,
            max_windows=max_windows,
            max_text_chars=max_text_chars,
        )
        return {"ok": True, **result}
    except Exception as exc:
        return _error(exc)


@mcp.tool(
    title="截取当前所有显示器",
    description=(
        "Capture all displays as one in-memory PNG. Requires the screenshots scope explicitly granted by "
        "the user. Protected or DRM windows may be blank. Never save or transmit the image to DAOQL."
    ),
)
def capture_screen_context(
    consent_token: str,
    student_id: str | None = None,
    max_width: int = 1920,
):
    try:
        png = capture_authorized_screen(
            store(),
            consent_token,
            student_id=student_id,
            max_width=max_width,
        )
        return [Image(data=png, format="png")]
    except Exception as exc:
        return _error(exc)


@mcp.tool(
    title="停止读取界面",
    description="Revoke a consent token immediately. Call this as soon as the user asks to stop.",
)
def revoke_screen_context(consent_token: str) -> dict[str, Any]:
    try:
        return {"ok": True, **store().revoke(consent_token)}
    except Exception as exc:
        return _error(exc)


def main() -> None:
    # stdio is mandatory here: the MCP transport is local and does not expose a
    # network listener. stdout is reserved for MCP frames.
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

