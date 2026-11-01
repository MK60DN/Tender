"""Subprocess worker for media MCP tools.

Keeping model runtimes in a child process protects the MCP stdio protocol from
third-party console output and C-level runtime messages.
"""
from __future__ import annotations

import base64
import json
import sys
from typing import Any

from media_plugins import (
    MediaPluginError,
    analyze_image,
    analyze_video,
    synthesize_speech,
    transcribe_audio,
)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        operation = payload.get("operation")
        arguments = payload.get("arguments") or {}
        if operation == "analyze_image":
            result: Any = analyze_image(arguments["file_path"], mode=arguments.get("mode", "ocr"), question=arguments.get("question", ""), max_chars=arguments.get("max_chars", 8000))
        elif operation == "transcribe_audio":
            result = transcribe_audio(arguments["file_path"], model_size=arguments.get("model_size", "tiny"), language=arguments.get("language"))
        elif operation == "analyze_video":
            result = analyze_video(arguments["file_path"], max_frames=arguments.get("max_frames", 6), include_audio=arguments.get("include_audio", True), model_size=arguments.get("model_size", "tiny"), language=arguments.get("language"))
        elif operation == "synthesize_speech":
            wav = synthesize_speech(arguments["text"], rate=arguments.get("rate", 170), voice_id=arguments.get("voice_id") or None)
            result = {"type": "audio_wav", "wav_base64": base64.b64encode(wav).decode("ascii")}
        else:
            raise MediaPluginError("invalid_operation", "未知的媒体操作。")
        sys.stdout.write(json.dumps({"ok": True, **result}, ensure_ascii=False))
        return 0
    except MediaPluginError as exc:
        sys.stdout.write(json.dumps({"ok": False, "error": exc.code, "message": str(exc)}, ensure_ascii=False))
        return 2
    except Exception:
        sys.stdout.write(json.dumps({"ok": False, "error": "media_plugin_failed", "message": "媒体插件没有完成处理。"}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
