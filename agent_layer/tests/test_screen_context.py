import json
import sys
import tempfile
from pathlib import Path

import pytest

OVERLAY = Path(__file__).resolve().parents[1] / "desktop_overlay"
sys.path.insert(0, str(OVERLAY))

from screen_context import (  # noqa: E402
    CONSENT_PHRASE,
    ConsentExpired,
    ConsentRequired,
    ConsentStore,
    ScopeNotGranted,
    capture_authorized_screen,
    derive_safe_signals,
    read_screen_context,
    redact_sensitive_text,
)


def test_consent_requires_explicit_phrase_and_is_not_persisted_raw():
    with tempfile.TemporaryDirectory() as directory:
        store = ConsentStore(directory)
        with pytest.raises(ConsentRequired):
            store.grant("S01", ["windows"], acknowledge=False, confirmation_text=CONSENT_PHRASE)
        with pytest.raises(ConsentRequired):
            store.grant("S01", ["windows"], acknowledge=True, confirmation_text="同意")
        granted = store.grant(
            "S01",
            ["accessible"],
            duration_minutes=5,
            acknowledge=True,
            confirmation_text=CONSENT_PHRASE,
        )
        assert granted["scopes"] == ["accessible", "windows"]
        assert granted["consent_token"]
        persisted = store.path.read_text(encoding="utf-8")
        assert granted["consent_token"] not in persisted
        assert "token_hash" in persisted
        assert store.status(granted["consent_token"], student_id="S01")["active"] is True
        assert store.revoke(granted["consent_token"])["revoked"] is True
        with pytest.raises(ConsentRequired):
            store.status(granted["consent_token"])


def test_consent_expiry_and_student_binding():
    with tempfile.TemporaryDirectory() as directory:
        store = ConsentStore(directory)
        granted = store.grant(
            "S01",
            ["windows"],
            acknowledge=True,
            confirmation_text=CONSENT_PHRASE,
        )
        with pytest.raises(ConsentRequired):
            store.status(granted["consent_token"], student_id="S02")
        payload = json.loads(store.path.read_text(encoding="utf-8"))
        payload["sessions"][0]["expires_at"] = "2000-01-01T00:00:00+00:00"
        store.path.write_text(json.dumps(payload), encoding="utf-8")
        with pytest.raises(ConsentExpired):
            store.status(granted["consent_token"])


def test_sensitive_identifiers_are_redacted_before_use():
    raw = (
        "密码: abc12345 token=sk-secret-value email student@example.com phone 13812345678 "
        "id 11010519491231002X card 6222 0212 3456 7890 "
        "https://example.com/path?private=value"
    )
    redacted = redact_sensitive_text(raw)
    assert "abc12345" not in redacted
    assert "sk-secret-value" not in redacted
    assert "student@example.com" not in redacted
    assert "13812345678" not in redacted
    assert "11010519491231002X" not in redacted
    assert "6222 0212 3456 7890" not in redacted
    assert "private=value" not in redacted
    assert "[已隐去]" in redacted


def test_derived_signals_never_include_raw_window_text_or_title():
    context = {
        "windows": [{
            "title": "高考报名 私密材料 张三",
            "accessible_text": "这是很长的一段私人原文 password: abc12345",
            "app_category": "study",
            "task_hint": "高考报名",
            "is_active": True,
            "text_available": True,
        }]
    }
    derived = derive_safe_signals(context)
    serialized = json.dumps(derived, ensure_ascii=False)
    assert derived["screen_task_hint"] == "高考报名"
    assert derived["screen_active_category"] == "study"
    assert "私密材料" not in serialized
    assert "abc12345" not in serialized
    assert derived["privacy_mode"] == "consented_visible_ui_derived_local"


def test_screenshot_scope_is_separate():
    with tempfile.TemporaryDirectory() as directory:
        store = ConsentStore(directory)
        granted = store.grant(
            "S01",
            ["windows", "accessible"],
            acknowledge=True,
            confirmation_text=CONSENT_PHRASE,
        )
        with pytest.raises(ScopeNotGranted):
            capture_authorized_screen(store, granted["consent_token"])


@pytest.mark.skipif(sys.platform != "win32", reason="Windows UI Automation only")
def test_read_screen_context_returns_safe_ephemeral_shape():
    with tempfile.TemporaryDirectory() as directory:
        store = ConsentStore(directory)
        granted = store.grant(
            "S01",
            ["windows", "accessible"],
            acknowledge=True,
            confirmation_text=CONSENT_PHRASE,
        )
        result = read_screen_context(
            store,
            granted["consent_token"],
            student_id="S01",
            max_windows=3,
            max_text_chars=1200,
        )
        assert result["privacy"]["raw_content_persisted"] is False
        assert result["privacy"]["raw_content_sent_to_daoql"] is False
        assert result["coverage"]["visible_top_level_windows"] == len(result["windows"])
        for window in result["windows"]:
            assert "hwnd" not in window
            assert "area" not in window
            assert isinstance(window["accessible_text"], str)
            assert "password" not in window["accessible_text"].lower()
        persisted = store.path.read_text(encoding="utf-8")
        assert "accessible_text" not in persisted
        assert "screenshots" not in persisted
