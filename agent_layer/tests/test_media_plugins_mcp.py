"""Live MCP stdio integration test for local media plugins."""
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


@pytest.mark.skipif(sys.platform != "win32", reason="SAPI and Windows media stack")
def test_media_plugins_mcp_exposes_and_runs_local_ocr():
    asyncio.run(_run_media_mcp_integration())


async def _run_media_mcp_integration():
    overlay = Path(__file__).resolve().parents[1] / "desktop_overlay"
    server = overlay / "media_plugins_mcp.py"
    with tempfile.TemporaryDirectory() as directory:
        from PIL import Image, ImageDraw, ImageFont

        image_path = Path(directory) / "ocr.png"
        image = Image.new("RGB", (700, 180), "white")
        ImageDraw.Draw(image).text(
            (20, 55),
            "Tender local plugin 2026",
            font=ImageFont.truetype(str(Path("C:/Windows/Fonts/arial.ttf")), 34),
            fill="black",
        )
        image.save(image_path)
        env = os.environ.copy()
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
                assert {"list_media_plugins", "analyze_image", "transcribe_audio", "analyze_video", "speak_text"} <= names

                catalog = await session.call_tool("list_media_plugins", {})
                catalog_payload = json.loads(catalog.content[0].text)
                assert catalog_payload["ok"] is True
                assert catalog_payload["total_count"] >= 5

                refused = await session.call_tool(
                    "analyze_image",
                    {"file_path": str(image_path), "acknowledge_local_processing": False},
                )
                refused_payload = json.loads(refused.content[0].text)
                assert refused_payload["error"] == "file_access_not_acknowledged"

                analyzed = await session.call_tool(
                    "analyze_image",
                    {"file_path": str(image_path), "acknowledge_local_processing": True},
                )
                analyzed_payload = json.loads(analyzed.content[0].text)
                assert analyzed_payload["ok"] is True
                assert "Tender" in analyzed_payload["text"]
                assert analyzed_payload["privacy"]["persisted"] is False
