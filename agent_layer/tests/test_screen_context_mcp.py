"""Live MCP stdio integration test for the local screen-context server."""
from __future__ import annotations

import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path

import pytest
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


@pytest.mark.skipif(sys.platform != "win32", reason="Windows UI Automation only")
def test_screen_context_mcp_lists_and_reads_under_consent():
    asyncio.run(_run_mcp_integration())


async def _run_mcp_integration():
    overlay = Path(__file__).resolve().parents[1] / "desktop_overlay"
    server = overlay / "screen_context_mcp.py"
    with tempfile.TemporaryDirectory() as directory:
        env = os.environ.copy()
        env["TENDER_SCREEN_CONTEXT_STATE"] = directory
        env["PYTHONIOENCODING"] = "utf-8"
        params = StdioServerParameters(
            command=sys.executable,
            args=[str(server)],
            env=env,
            cwd=str(overlay),
        )
        async with stdio_client(params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                tools = await session.list_tools()
                names = {tool.name for tool in tools.tools}
                assert {
                    "grant_screen_context",
                    "screen_context_status",
                    "read_screen_context",
                    "capture_screen_context",
                    "revoke_screen_context",
                } <= names

                refused = await session.call_tool(
                    "grant_screen_context",
                    {"student_id": "S01", "scopes": ["windows"], "acknowledge": False},
                )
                refused_payload = json.loads(refused.content[0].text)
                assert refused_payload["ok"] is False
                assert refused_payload["error"] == "consent_required"

                granted = await session.call_tool(
                    "grant_screen_context",
                    {
                        "student_id": "S01",
                        "scopes": ["windows", "accessible"],
                        "duration_minutes": 5,
                        "acknowledge": True,
                        "confirmation_text": "我同意读取当前界面",
                    },
                )
                granted_payload = json.loads(granted.content[0].text)
                assert granted_payload["ok"] is True
                token = granted_payload["consent_token"]

                context = await session.call_tool(
                    "read_screen_context",
                    {"consent_token": token, "student_id": "S01", "max_windows": 3, "max_text_chars": 1200},
                )
                context_payload = json.loads(context.content[0].text)
                assert context_payload["ok"] is True
                assert context_payload["privacy"]["raw_content_persisted"] is False
                assert isinstance(context_payload["windows"], list)

                revoked = await session.call_tool("revoke_screen_context", {"consent_token": token})
                revoked_payload = json.loads(revoked.content[0].text)
                assert revoked_payload["ok"] is True
                assert revoked_payload["revoked"] is True

