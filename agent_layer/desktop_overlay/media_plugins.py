"""Local multimedia plugins for Tender.

Each plugin has a narrow job and an explicit availability state. Heavy models are
loaded lazily. The module never starts a camera or microphone, never uploads a
file by itself, and never writes media content into DAOQL.
"""
from __future__ import annotations

import base64
import contextlib
import io
import json
import os
import shutil
import subprocess
import tempfile
import threading
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}
AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg", ".opus", ".wma"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v", ".flv"}
MAX_IMAGE_BYTES = 40 * 1024 * 1024
MAX_AUDIO_BYTES = 300 * 1024 * 1024
MAX_VIDEO_BYTES = 1024 * 1024 * 1024

_ocr_lock = threading.Lock()
_ocr_engine: Any = None
_asr_lock = threading.Lock()
_asr_models: dict[tuple[str, str, str], Any] = {}
_tts_lock = threading.Lock()


class MediaPluginError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _available(module: str) -> bool:
    import importlib.util
    return importlib.util.find_spec(module) is not None


def _version(module: str) -> str | None:
    try:
        import importlib.metadata
        return importlib.metadata.version(module)
    except Exception:
        return None


def _ffmpeg_exe() -> str | None:
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return shutil.which("ffmpeg")


def plugin_catalog() -> dict[str, Any]:
    vision_ready = bool(os.environ.get("TENDER_VISION_BASE_URL") and os.environ.get("TENDER_VISION_MODEL"))
    plugins = [
        {
            "id": "local_ocr", "kind": "image", "name": "本地图片文字识别",
            "available": _available("rapidocr") and _available("onnxruntime"),
            "version": _version("rapidocr"), "engine": "RapidOCR / ONNX Runtime",
            "source": "https://github.com/RapidAI/RapidOCR", "license": "Apache-2.0",
            "capabilities": ["中文 OCR", "英文 OCR", "截图文字", "讲义/试卷文字"],
        },
        {
            "id": "vision_provider", "kind": "image", "name": "视觉理解模型适配器",
            "available": vision_ready, "version": None,
            "engine": os.environ.get("TENDER_VISION_MODEL") or "未配置",
            "source": "https://github.com/QwenLM/Qwen3-VL", "license": "Apache-2.0",
            "capabilities": ["图像问答", "图表与界面理解", "视觉描述"],
            "setup": "设置 TENDER_VISION_BASE_URL、TENDER_VISION_MODEL；可选 TENDER_VISION_API_KEY",
        },
        {
            "id": "local_asr", "kind": "audio", "name": "本地语音转写",
            "available": _available("faster_whisper"), "version": _version("faster-whisper"),
            "engine": "faster-whisper / CTranslate2",
            "source": "https://github.com/SYSTRAN/faster-whisper", "license": "MIT",
            "capabilities": ["中文语音转写", "英文语音转写", "时间段字幕", "语言检测"],
        },
        {
            "id": "local_video", "kind": "video", "name": "本地视频理解",
            "available": _available("cv2") and bool(_ffmpeg_exe()),
            "version": _version("opencv-python-headless"),
            "engine": "OpenCV frames + ffmpeg audio + OCR/ASR",
            "source": "https://github.com/opencv/opencv", "license": "Apache-2.0",
            "capabilities": ["关键帧 OCR", "视频字幕转写", "时长与分辨率", "画面文字变化"],
        },
        {
            "id": "local_tts", "kind": "audio", "name": "本地语音播报",
            "available": _available("pyttsx3"), "version": _version("pyttsx3"),
            "engine": "Windows SAPI5 via pyttsx3",
            "source": "https://github.com/nateshmbhat/pyttsx3", "license": "MPL-2.0",
            "capabilities": ["短句播报", "WAV 生成", "语速与声音选择"],
        },
        {
            "id": "ffmpeg", "kind": "video/audio", "name": "媒体解码与转码",
            "available": bool(_ffmpeg_exe()), "version": None, "engine": _ffmpeg_exe() or "未找到",
            "source": "https://github.com/FFmpeg/FFmpeg", "license": "LGPL-2.1-or-later (build dependent)",
            "capabilities": ["音频提取", "格式解码", "视频信息"],
        },
    ]
    return {
        "plugins": plugins,
        "available_count": sum(1 for item in plugins if item["available"]),
        "total_count": len(plugins),
        "privacy": "本地文件处理；不自动上传；不写 DAOQL；不启动摄像头或麦克风。",
    }


def _validate_file(path: str | Path, allowed: set[str], max_bytes: int) -> Path:
    candidate = Path(path).expanduser()
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as exc:
        raise MediaPluginError("file_not_found", "找不到这个媒体文件。") from exc
    if not resolved.is_file():
        raise MediaPluginError("not_a_file", "选择的路径不是一个文件。")
    if resolved.suffix.lower() not in allowed:
        raise MediaPluginError("unsupported_media_type", "不支持这种媒体格式。")
    size = resolved.stat().st_size
    if size <= 0:
        raise MediaPluginError("empty_file", "这个媒体文件是空的。")
    if size > max_bytes:
        raise MediaPluginError("file_too_large", f"媒体文件超过 {max_bytes // (1024 * 1024)} MB 限制。")
    return resolved


def _ocr():
    global _ocr_engine
    if _ocr_engine is None:
        try:
            from rapidocr import RapidOCR
        except ImportError as exc:
            raise MediaPluginError("ocr_unavailable", "本地 OCR 插件未安装。") from exc
        with _ocr_lock:
            if _ocr_engine is None:
                _ocr_engine = RapidOCR()
    return _ocr_engine


def _ocr_path(path: str | Path, *, max_chars: int = 8000) -> dict[str, Any]:
    image_path = _validate_file(path, IMAGE_EXTENSIONS, MAX_IMAGE_BYTES)
    try:
        output = _ocr()(str(image_path))
    except MediaPluginError:
        raise
    except Exception as exc:
        raise MediaPluginError("ocr_failed", "图片文字识别没有完成。") from exc
    texts = list(getattr(output, "txts", None) or [])
    scores = list(getattr(output, "scores", None) or [])
    full_text = "\n".join(str(item).strip() for item in texts if str(item).strip())
    text = full_text[:max_chars] + ("…" if len(full_text) > max_chars else "")
    return {
        "type": "image_ocr",
        "path": str(image_path),
        "text": text,
        "line_count": len(texts),
        "mean_confidence": round(sum(float(x) for x in scores) / len(scores), 4) if scores else None,
        "truncated": len(full_text) > max_chars,
        "privacy": {"local_only": True, "persisted": False, "uploaded": False},
    }


def analyze_image(path: str | Path, *, mode: str = "ocr", question: str = "", max_chars: int = 8000) -> dict[str, Any]:
    """Analyze a user-selected image with local OCR or a configured vision provider."""
    if mode == "ocr":
        return _ocr_path(path, max_chars=max(100, min(int(max_chars), 20000)))
    if mode != "vision":
        raise MediaPluginError("invalid_mode", "mode 只能是 ocr 或 vision。")
    image_path = _validate_file(path, IMAGE_EXTENSIONS, MAX_IMAGE_BYTES)
    return _vision_query(image_path, question=question)


def _vision_query(path: Path, *, question: str) -> dict[str, Any]:
    base = os.environ.get("TENDER_VISION_BASE_URL", "").rstrip("/")
    model = os.environ.get("TENDER_VISION_MODEL", "")
    if not base or not model:
        raise MediaPluginError(
            "vision_not_configured",
            "视觉模型尚未配置。设置 TENDER_VISION_BASE_URL 与 TENDER_VISION_MODEL 后可用。",
        )
    media_type = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    prompt = question.strip() or "请描述图片中的学习任务、界面状态、文字和可能的下一步。不要猜取个人信息。"
    payload = {
        "model": model,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{encoded}"}},
            ],
        }],
        "temperature": 0.2,
    }
    headers = {"Content-Type": "application/json"}
    api_key = os.environ.get("TENDER_VISION_API_KEY", "")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    request = Request(base + "/chat/completions", data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    try:
        with urlopen(request, timeout=90) as response:
            result = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise MediaPluginError("vision_request_failed", "视觉模型没有返回结果。") from exc
    choices = result.get("choices") or []
    content = ((choices[0] if choices else {}).get("message") or {}).get("content", "")
    return {
        "type": "image_vision",
        "path": str(path),
        "model": model,
        "answer": str(content),
        "privacy": {"local_only": False, "uploaded_to_configured_provider": True, "persisted": False},
    }


def _asr_model(model_size: str, device: str, compute_type: str):
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise MediaPluginError("asr_unavailable", "本地语音转写插件未安装。") from exc
    key = (model_size, device, compute_type)
    with _asr_lock:
        if key not in _asr_models:
            _asr_models[key] = WhisperModel(model_size, device=device, compute_type=compute_type)
        return _asr_models[key]


def transcribe_audio(
    path: str | Path,
    *,
    model_size: str | None = None,
    language: str | None = None,
    device: str = "cpu",
    compute_type: str = "int8",
) -> dict[str, Any]:
    """Transcribe a user-selected audio file locally."""
    audio_path = _validate_file(path, AUDIO_EXTENSIONS, MAX_AUDIO_BYTES)
    model_name = model_size or os.environ.get("TENDER_WHISPER_MODEL", "tiny")
    if model_name not in {"tiny", "base", "small", "medium", "large-v3", "distil-large-v3"}:
        raise MediaPluginError("invalid_whisper_model", "不支持这个 Whisper 模型大小。")
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            model = _asr_model(model_name, device, compute_type)
            segments, info = model.transcribe(str(audio_path), language=language or None, vad_filter=True)
            rows = [{
                "start": round(float(segment.start), 2),
                "end": round(float(segment.end), 2),
                "text": str(segment.text).strip(),
            } for segment in segments]
    except Exception as exc:
        raise MediaPluginError("transcription_failed", "语音转写没有完成。") from exc
    text = " ".join(row["text"] for row in rows if row["text"]).strip()
    return {
        "type": "audio_transcript",
        "path": str(audio_path),
        "text": text,
        "segments": rows,
        "language": getattr(info, "language", language),
        "language_probability": round(float(getattr(info, "language_probability", 0.0)), 4),
        "duration_seconds": round(float(getattr(info, "duration", 0.0)), 2),
        "model": model_name,
        "privacy": {"local_only": True, "persisted": False, "uploaded": False},
    }


def _extract_audio(video_path: Path, output_path: Path) -> Path:
    ffmpeg = _ffmpeg_exe()
    if not ffmpeg:
        raise MediaPluginError("ffmpeg_unavailable", "找不到 ffmpeg，无法提取视频音轨。")
    command = [ffmpeg, "-y", "-i", str(video_path), "-vn", "-ac", "1", "-ar", "16000", str(output_path)]
    result = subprocess.run(command, capture_output=True, text=True, timeout=180, check=False)
    if result.returncode != 0 or not output_path.exists():
        raise MediaPluginError("audio_extract_failed", "视频音轨提取没有完成。")
    return output_path


def analyze_video(
    path: str | Path,
    *,
    max_frames: int = 6,
    include_audio: bool = True,
    model_size: str | None = None,
    language: str | None = None,
) -> dict[str, Any]:
    """Sample video frames for local OCR and optionally transcribe its audio."""
    video_path = _validate_file(path, VIDEO_EXTENSIONS, MAX_VIDEO_BYTES)
    try:
        import cv2
    except ImportError as exc:
        raise MediaPluginError("video_unavailable", "视频解码插件未安装。") from exc
    max_frames = max(1, min(int(max_frames), 12))
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise MediaPluginError("video_open_failed", "无法打开这个视频。")
    fps = float(capture.get(cv2.CAP_PROP_FPS) or 0)
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    duration = frame_count / fps if fps > 0 and frame_count > 0 else 0.0
    sample_times = [duration * index / (max_frames + 1) for index in range(1, max_frames + 1)] if duration else [0.0]
    frame_results: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="tender-video-") as directory:
        temp = Path(directory)
        for index, timestamp in enumerate(sample_times):
            capture.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
            ok, frame = capture.read()
            if not ok or frame is None:
                continue
            frame_path = temp / f"frame-{index}.png"
            cv2.imwrite(str(frame_path), frame)
            try:
                ocr = _ocr_path(frame_path, max_chars=3000)
                frame_results.append({"timestamp": round(timestamp, 2), "text": ocr["text"], "confidence": ocr["mean_confidence"]})
            except MediaPluginError as exc:
                frame_results.append({"timestamp": round(timestamp, 2), "text": "", "error": exc.code})
        capture.release()
        transcript = None
        if include_audio and _available("faster_whisper"):
            try:
                audio_path = _extract_audio(video_path, temp / "audio.wav")
                transcript = transcribe_audio(audio_path, model_size=model_size, language=language)
                transcript["path"] = str(video_path)
            except MediaPluginError as exc:
                transcript = {"error": exc.code, "message": str(exc)}
    deduped_lines: list[str] = []
    for frame in frame_results:
        for line in str(frame.get("text", "")).splitlines():
            normalized = line.strip()
            if normalized and normalized not in deduped_lines:
                deduped_lines.append(normalized)
    return {
        "type": "video_analysis",
        "path": str(video_path),
        "duration_seconds": round(duration, 2),
        "resolution": {"width": width, "height": height},
        "sample_frames": frame_results,
        "ocr_text": "\n".join(deduped_lines),
        "transcript": transcript,
        "privacy": {"local_only": True, "persisted": False, "uploaded": False},
    }


def synthesize_speech(text: str, *, rate: int = 170, voice_id: str | None = None) -> bytes:
    """Create a local WAV from text using Windows SAPI5."""
    content = str(text or "").strip()
    if not content:
        raise MediaPluginError("empty_text", "没有可播报的文字。")
    if len(content) > 3000:
        raise MediaPluginError("text_too_long", "单次语音播报最多 3000 字。")
    try:
        import pyttsx3
    except ImportError as exc:
        raise MediaPluginError("tts_unavailable", "本地语音播报插件未安装。") from exc
    with _tts_lock, tempfile.TemporaryDirectory(prefix="tender-tts-") as directory:
        output = Path(directory) / "speech.wav"
        try:
            engine = pyttsx3.init()
            engine.setProperty("rate", max(80, min(int(rate), 320)))
            if voice_id:
                engine.setProperty("voice", voice_id)
            engine.save_to_file(content, str(output))
            engine.runAndWait()
        except Exception as exc:
            raise MediaPluginError("tts_failed", "语音生成没有完成。") from exc
        if not output.exists():
            raise MediaPluginError("tts_failed", "语音文件没有生成。")
        return output.read_bytes()


def list_tts_voices() -> list[dict[str, str]]:
    try:
        import pyttsx3
    except ImportError:
        return []
    with _tts_lock:
        try:
            engine = pyttsx3.init()
            return [{"id": str(voice.id), "name": str(voice.name), "languages": str(voice.languages)} for voice in engine.getProperty("voices")]
        except Exception:
            return []


def summarize_for_danmaku(result: dict[str, Any], limit: int = 260) -> str:
    """Reduce media results to a short local message without writing to DAOQL."""
    kind = result.get("type")
    if kind == "image_ocr":
        text = str(result.get("text") or "").strip()
    elif kind == "image_vision":
        text = str(result.get("answer") or "").strip()
    elif kind == "audio_transcript":
        text = str(result.get("text") or "").strip()
    elif kind == "video_analysis":
        transcript = result.get("transcript") or {}
        text = str(transcript.get("text") or result.get("ocr_text") or "").strip()
    else:
        text = "媒体已经处理完成。"
    return (text[:limit] + "…") if len(text) > limit else text

