import sys
import tempfile
from pathlib import Path

import pytest

OVERLAY = Path(__file__).resolve().parents[1] / "desktop_overlay"
sys.path.insert(0, str(OVERLAY))

from media_plugins import (  # noqa: E402
    MediaPluginError,
    analyze_image,
    analyze_video,
    plugin_catalog,
    synthesize_speech,
    summarize_for_danmaku,
    transcribe_audio,
)


def test_media_plugin_catalog_has_sources_and_licenses():
    catalog = plugin_catalog()
    assert catalog["total_count"] >= 5
    ids = {item["id"] for item in catalog["plugins"]}
    assert {"local_ocr", "local_asr", "local_video", "local_tts", "ffmpeg"} <= ids
    for item in catalog["plugins"]:
        assert item["source"].startswith("https://github.com/")
        assert item["license"]
        assert "persisted" not in item


def test_local_ocr_extracts_text_and_remains_local():
    pytest.importorskip("rapidocr")
    from PIL import Image, ImageDraw, ImageFont

    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "ocr.png"
        image = Image.new("RGB", (800, 220), "white")
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype(str(Path("C:/Windows/Fonts/arial.ttf")), 38)
        draw.text((28, 70), "Tender Media OCR 2026", font=font, fill="black")
        image.save(path)
        result = analyze_image(path)
        assert result["type"] == "image_ocr"
        assert "Tender" in result["text"]
        assert result["privacy"]["local_only"] is True
        assert result["privacy"]["persisted"] is False


def test_local_tts_returns_wav_bytes():
    pytest.importorskip("pyttsx3")
    if sys.platform != "win32":
        pytest.skip("Windows SAPI5 only")
    wav = synthesize_speech("Tender 今天先做一个小步骤。")
    assert wav[:4] == b"RIFF"
    assert len(wav) > 1000


def test_video_samples_frames_for_ocr():
    pytest.importorskip("cv2")
    pytest.importorskip("imageio_ffmpeg")
    pytest.importorskip("rapidocr")
    import cv2
    import numpy as np

    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "sample.mp4"
        writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), 2.0, (640, 360))
        assert writer.isOpened()
        for index in range(8):
            frame = np.full((360, 640, 3), 245, dtype=np.uint8)
            cv2.putText(frame, "Tender focus step", (40, 120), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (10, 10, 10), 3)
            cv2.putText(frame, f"frame {index + 1}", (40, 200), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (40, 40, 40), 2)
            writer.write(frame)
        writer.release()
        result = analyze_video(path, max_frames=3, include_audio=False)
        assert result["type"] == "video_analysis"
        assert result["resolution"] == {"width": 640, "height": 360}
        assert len(result["sample_frames"]) == 3
        assert "Tender" in result["ocr_text"]
        assert result["privacy"]["persisted"] is False


def test_heavy_asr_smoke_is_opt_in():
    if sys.platform != "win32" or __import__("os").environ.get("TENDER_RUN_HEAVY_MEDIA_TESTS") != "1":
        pytest.skip("set TENDER_RUN_HEAVY_MEDIA_TESTS=1 to run local ASR")
    pytest.importorskip("faster_whisper")
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "speech.wav"
        path.write_bytes(synthesize_speech("Tender 学习助手。"))
        result = transcribe_audio(path, model_size="tiny", language="zh")
        assert result["language"] == "zh"
        assert isinstance(result["text"], str)


def test_summary_does_not_add_new_content():
    result = {"type": "image_ocr", "text": "第一行\n第二行"}
    assert summarize_for_danmaku(result) == "第一行\n第二行"
    with pytest.raises(MediaPluginError):
        analyze_image("missing.png")
