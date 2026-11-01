"""Local multimedia MCP server for Tender.

Tools process files explicitly selected by the user. Heavy models run in a child
worker so third-party runtime output cannot corrupt the MCP stdio protocol.
Media content is not persisted to DAOQL.
"""
from __future__ import annotations

import base64
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import Audio, FastMCP

from media_plugins import list_tts_voices, plugin_catalog

MCP_INSTRUCTIONS = """
Tender Media Tools only processes files the user explicitly selected. Ask before
analyzing a file and say whether it stays local. OCR, speech-to-text, video frame
analysis and speech synthesis run locally by default. A configured vision model
adapter may upload a user-selected image to that configured provider; disclose
that before using vision mode. Never start a camera or microphone, never scan a
folder automatically, and never write media content into DAOQL.
""".strip()

mcp = FastMCP("Tender Media Tools", instructions=MCP_INSTRUCTIONS)
WORKER = Path(__file__).with_name("media_plugin_worker.py")


def _worker(operation: str, arguments: dict[str, Any], timeout: int = 600) -> dict[str, Any]:
    payload = json.dumps({"operation": operation, "arguments": arguments}, ensure_ascii=False)
    try:
        completed = subprocess.run(
            [sys.executable, str(WORKER)],
            input=payload,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=timeout,
            check=False,
        )
    except Exception:
        return {"ok": False, "error": "media_worker_failed", "message": "媒体处理进程没有启动。"}
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return {"ok": False, "error": "media_worker_failed", "message": "媒体处理没有返回有效结果。"}
    if completed.returncode != 0 and result.get("ok"):
        return {"ok": False, "error": "media_worker_failed", "message": "媒体处理进程异常退出。"}
    return result


@mcp.tool(
    title="查看媒体插件",
    description="List local image OCR, vision, audio transcription, video analysis, TTS and ffmpeg plugin availability.",
)
def list_media_plugins() -> dict[str, Any]:
    return {"ok": True, **plugin_catalog()}


@mcp.tool(
    title="读取用户选择的图片",
    description=(
        "Analyze one user-selected image. mode=ocr uses local RapidOCR; mode=vision uses the configured "
        "OpenAI-compatible vision provider. Set acknowledge_local_processing=true only after the user selected "
        "the file and approved this operation."
    ),
)
def analyze_image(
    file_path: str,
    mode: str = "ocr",
    question: str = "",
    max_chars: int = 8000,
    acknowledge_local_processing: bool = False,
) -> dict[str, Any]:
    if not acknowledge_local_processing:
        return {"ok": False, "error": "file_access_not_acknowledged", "message": "需要用户先选择并确认处理这个文件。"}
    return _worker("analyze_image", {"file_path": file_path, "mode": mode, "question": question, "max_chars": max_chars})


@mcp.tool(
    title="本地转写语音",
    description=(
        "Transcribe one user-selected audio file locally with faster-whisper. The tiny model is used by default; "
        "set model_size to base/small/large-v3 for better accuracy. No audio is uploaded or persisted."
    ),
)
def transcribe_audio(
    file_path: str,
    model_size: str = "tiny",
    language: str | None = None,
    acknowledge_local_processing: bool = False,
) -> dict[str, Any]:
    if not acknowledge_local_processing:
        return {"ok": False, "error": "file_access_not_acknowledged", "message": "需要用户先选择并确认处理这个音频。"}
    return _worker("transcribe_audio", {"file_path": file_path, "model_size": model_size, "language": language})


@mcp.tool(
    title="本地分析视频",
    description=(
        "Analyze one user-selected video by sampling frames for OCR and optionally transcribing its audio. "
        "All processing stays local. Never call this on a folder or an unselected file."
    ),
)
def analyze_video(
    file_path: str,
    max_frames: int = 6,
    include_audio: bool = True,
    model_size: str = "tiny",
    language: str | None = None,
    acknowledge_local_processing: bool = False,
) -> dict[str, Any]:
    if not acknowledge_local_processing:
        return {"ok": False, "error": "file_access_not_acknowledged", "message": "需要用户先选择并确认处理这个视频。"}
    return _worker("analyze_video", {
        "file_path": file_path,
        "max_frames": max_frames,
        "include_audio": include_audio,
        "model_size": model_size,
        "language": language,
    })


@mcp.tool(
    title="本地生成语音",
    description="Synthesize short text into an in-memory WAV using local Windows SAPI5. Does not play automatically.",
)
def speak_text(text: str, rate: int = 170, voice_id: str = ""):
    result = _worker("synthesize_speech", {"text": text, "rate": rate, "voice_id": voice_id})
    if not result.get("ok"):
        return result
    try:
        wav = base64.b64decode(result["wav_base64"])
        return [Audio(data=wav, format="wav")]
    except Exception:
        return {"ok": False, "error": "tts_failed", "message": "语音生成结果无效。"}


@mcp.tool(
    title="查看可用语音",
    description="List locally installed Windows SAPI5 voices for speak_text.",
)
def list_voices() -> dict[str, Any]:
    return {"ok": True, "voices": list_tts_voices()}


if __name__ == "__main__":
    mcp.run(transport="stdio")
