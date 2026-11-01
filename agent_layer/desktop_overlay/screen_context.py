"""Local, consent-gated desktop screen context for Tender.

The module deliberately separates three things:

1. Consent state: only opaque token hashes and expiry metadata are stored.
2. Ephemeral screen context: window text and screenshots stay in memory.
3. Derived signals: only coarse, redacted task hints may leave this module.

It reads visible top-level windows. It does not read hidden tabs, password
fields, clipboard, camera, microphone, keystrokes, or protected DRM content.
"""
from __future__ import annotations

import ctypes
import hashlib
import hmac
import io
import json
import os
import re
import secrets
import tempfile
import threading
import time
from ctypes import wintypes
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

CONSENT_PHRASE = "我同意读取当前界面"
CONSENT_SCOPES = frozenset({"windows", "accessible", "screenshots"})
DEFAULT_DURATION_MINUTES = 15
MAX_DURATION_MINUTES = 60
DEFAULT_MAX_WINDOWS = 8
DEFAULT_MAX_TEXT_CHARS = 12000


class ScreenContextError(RuntimeError):
    """Base error with a stable machine-readable code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class ConsentRequired(ScreenContextError):
    def __init__(self, message: str = "需要用户明确授权后才能读取界面。") -> None:
        super().__init__("consent_required", message)


class ConsentExpired(ScreenContextError):
    def __init__(self, message: str = "这次界面读取授权已经到期。") -> None:
        super().__init__("consent_expired", message)


class ScopeNotGranted(ScreenContextError):
    def __init__(self, scope: str) -> None:
        super().__init__("scope_not_granted", f"本次授权不包含 {scope} 权限。")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.isoformat(timespec="seconds")


def _parse_iso(value: Any) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _default_state_dir() -> Path:
    configured = os.environ.get("TENDER_SCREEN_CONTEXT_STATE")
    if configured:
        return Path(configured).expanduser().resolve()
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "Tender" / "screen-context"
    return Path.home() / ".tender" / "screen-context"


def _normalize_scopes(scopes: Iterable[str]) -> list[str]:
    normalized = sorted({str(scope).strip().lower() for scope in scopes if str(scope).strip()})
    unknown = set(normalized) - CONSENT_SCOPES
    if unknown:
        raise ValueError("unknown_scope:" + ",".join(sorted(unknown)))
    if not normalized:
        raise ValueError("empty_scopes")
    if "accessible" in normalized or "screenshots" in normalized:
        if "windows" not in normalized:
            normalized.append("windows")
            normalized.sort()
    return normalized


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class ConsentStore:
    """Short-lived consent sessions stored locally as token hashes only."""

    def __init__(self, state_dir: str | Path | None = None) -> None:
        self.state_dir = Path(state_dir).expanduser().resolve() if state_dir else _default_state_dir()
        self.path = self.state_dir / "consent.json"
        self._lock = threading.RLock()

    def _load_unlocked(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        sessions = payload.get("sessions", []) if isinstance(payload, dict) else []
        return [item for item in sessions if isinstance(item, dict)]

    def _write_unlocked(self, sessions: list[dict[str, Any]]) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        payload = {"version": 1, "sessions": sessions[-8:]}
        fd, temporary = tempfile.mkstemp(prefix="consent-", suffix=".json", dir=str(self.state_dir))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2)
            try:
                os.chmod(temporary, 0o600)
            except OSError:
                pass
            os.replace(temporary, self.path)
        finally:
            if os.path.exists(temporary):
                try:
                    os.unlink(temporary)
                except OSError:
                    pass

    def _active_unlocked(self, token: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        if not token:
            raise ConsentRequired()
        digest = _token_hash(token)
        sessions = self._load_unlocked()
        now = _utcnow()
        session = next(
            (item for item in sessions if hmac.compare_digest(str(item.get("token_hash", "")), digest)),
            None,
        )
        if session is None:
            raise ConsentRequired("这次授权无效或已经停止。")
        expires = _parse_iso(session.get("expires_at"))
        if expires is None or expires <= now:
            sessions = [item for item in sessions if item is not session]
            self._write_unlocked(sessions)
            raise ConsentExpired()
        return session, sessions

    def grant(
        self,
        student_id: str,
        scopes: Iterable[str],
        *,
        duration_minutes: int = DEFAULT_DURATION_MINUTES,
        acknowledge: bool = False,
        confirmation_text: str = "",
    ) -> dict[str, Any]:
        """Create an explicit, short-lived consent session.

        The caller must have just obtained a real user confirmation. This method
        enforces both an acknowledgement flag and the exact confirmation phrase
        so an MCP client cannot silently opt a user in through a default value.
        """
        if not acknowledge or confirmation_text.strip() != CONSENT_PHRASE:
            raise ConsentRequired(f"授权时必须由用户确认：{CONSENT_PHRASE}")
        if not str(student_id).strip():
            raise ValueError("student_id_required")
        try:
            duration = int(duration_minutes)
        except (TypeError, ValueError) as exc:
            raise ValueError("invalid_duration") from exc
        if duration < 1 or duration > MAX_DURATION_MINUTES:
            raise ValueError(f"duration_must_be_1_to_{MAX_DURATION_MINUTES}")
        normalized = _normalize_scopes(scopes)
        token = secrets.token_urlsafe(36)
        now = _utcnow()
        session = {
            "token_hash": _token_hash(token),
            "student_id": str(student_id).strip(),
            "scopes": normalized,
            "created_at": _iso(now),
            "expires_at": _iso(now + timedelta(minutes=duration)),
        }
        with self._lock:
            sessions = [item for item in self._load_unlocked() if (_parse_iso(item.get("expires_at")) or now) > now]
            sessions.append(session)
            self._write_unlocked(sessions)
        return {
            "consent_token": token,
            "student_id": session["student_id"],
            "scopes": normalized,
            "expires_at": session["expires_at"],
            "duration_minutes": duration,
            "notice": "授权只在本机生效；可随时停止；界面原文与截图不会写入 DAOQL。",
        }

    def validate(
        self,
        token: str,
        *,
        student_id: str | None = None,
        required_scope: str | None = None,
    ) -> dict[str, Any]:
        with self._lock:
            session, _sessions = self._active_unlocked(token)
            if student_id and str(session.get("student_id")) != str(student_id):
                raise ConsentRequired("这次授权不属于当前学习者。")
            scopes = set(session.get("scopes") or [])
            if required_scope and required_scope not in scopes:
                raise ScopeNotGranted(required_scope)
            expires = _parse_iso(session.get("expires_at"))
            return {
                "student_id": session.get("student_id"),
                "scopes": sorted(scopes),
                "created_at": session.get("created_at"),
                "expires_at": session.get("expires_at"),
                "remaining_seconds": max(0, int((expires - _utcnow()).total_seconds())) if expires else 0,
            }

    def status(self, token: str, *, student_id: str | None = None) -> dict[str, Any]:
        status = self.validate(token, student_id=student_id)
        return {"active": True, **status}

    def revoke(self, token: str) -> dict[str, Any]:
        if not token:
            return {"revoked": False, "reason": "no_token"}
        digest = _token_hash(token)
        with self._lock:
            sessions = self._load_unlocked()
            kept = [item for item in sessions if not hmac.compare_digest(str(item.get("token_hash", "")), digest)]
            changed = len(kept) != len(sessions)
            if changed:
                self._write_unlocked(kept)
        return {"revoked": changed}


def _looks_like_secret(value: str) -> bool:
    lowered = value.lower()
    return any(marker in lowered for marker in ("password", "passwd", "密码", "口令", "验证码", "动态码", "短信码", "token", "secret", "api key", "access key"))


_SECRET_LINE = re.compile(
    r"(?im)(?P<label>\b(?:password|passwd|pin|token|secret|api\s*key|access\s*key|cvv)\b|密码|口令|验证码|动态码|短信码)"
    r"\s*[:：=]?\s*(?P<value>[^\s，。；;]{3,})"
)
_EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
_PHONE = re.compile(r"(?<!\d)(?:\+?86[-\s]?)?1[3-9]\d{9}(?!\d)")
_ID_CARD = re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)")
_BANK_CARD = re.compile(r"(?<!\d)(?:\d[ -]?){16,19}(?!\d)")
_URL_QUERY = re.compile(r"(https?://[^\s?#]+)(?:\?[^\s#]*)?", re.IGNORECASE)


def redact_sensitive_text(text: str) -> str:
    """Redact common secret and personal identifiers before text leaves a window."""
    value = str(text or "")
    value = _SECRET_LINE.sub(lambda match: f"{match.group('label')}：[已隐去]", value)
    value = _EMAIL.sub("[邮箱已隐去]", value)
    value = _PHONE.sub("[手机号已隐去]", value)
    value = _ID_CARD.sub("[证件号已隐去]", value)
    value = _BANK_CARD.sub("[卡号已隐去]", value)
    value = _URL_QUERY.sub(lambda match: match.group(1) + "?[参数已隐去]", value)
    return value


def _clean_text(value: Any, limit: int) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if not text:
        return ""
    return redact_sensitive_text(text)[: max(0, limit)]


TASK_TERMS: tuple[tuple[str, str], ...] = (
    ("高考报名", "study"), ("报名", "study"), ("准考证", "study"), ("志愿", "study"),
    ("语法填空", "study"), ("错题", "study"), ("试卷", "study"), ("复习", "study"),
    ("数学", "study"), ("物理", "study"), ("化学", "study"), ("生物", "study"),
    ("英语", "study"), ("语文", "study"), ("历史", "study"), ("地理", "study"),
    ("python", "coding"), ("javascript", "coding"), ("代码", "coding"), ("vscode", "coding"),
    ("bilibili", "video"), ("哔哩哔哩", "video"), ("youtube", "video"), ("抖音", "video"),
    ("快手", "video"), ("腾讯视频", "video"), ("爱奇艺", "video"), ("netflix", "video"),
    ("微信", "chat"), ("wechat", "chat"), ("qq", "chat"), ("飞书", "chat"), ("钉钉", "chat"),
    ("chatgpt", "chat"), ("claude", "chat"), ("codex", "chat"), ("discord", "chat"),
    ("steam", "game"), ("原神", "game"), ("英雄联盟", "game"), ("游戏", "game"),
    ("word", "document"), ("wps", "document"), ("pdf", "document"), ("notion", "document"),
    ("obsidian", "document"), ("文档", "document"), ("讲义", "document"),
)

PROCESS_CATEGORIES = {
    "chrome.exe": "browser", "msedge.exe": "browser", "firefox.exe": "browser",
    "winword.exe": "document", "wps.exe": "document", "acrobat.exe": "document",
    "code.exe": "coding", "pycharm64.exe": "coding", "cursor.exe": "coding",
    "wechat.exe": "chat", "weixin.exe": "chat", "qq.exe": "chat", "feishu.exe": "chat",
    "dingtalk.exe": "chat", "chatgpt.exe": "chat", "potplayermini64.exe": "video", "vlc.exe": "video",
}


def classify_text(text: str, process_name: str = "") -> tuple[str, str]:
    lowered = f"{text} {process_name}".lower()
    for keyword, category in TASK_TERMS:
        if keyword.lower() in lowered:
            return category, keyword[:40]
    return PROCESS_CATEGORIES.get(process_name.lower(), "unknown"), ""


class _RECT(ctypes.Structure):
    _fields_ = [("left", wintypes.LONG), ("top", wintypes.LONG), ("right", wintypes.LONG), ("bottom", wintypes.LONG)]


def _process_name(hwnd: int) -> str:
    if os.name != "nt":
        return ""
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    handle = kernel32.OpenProcess(0x1000, False, pid.value)
    if not handle:
        return ""
    try:
        size = wintypes.DWORD(512)
        buffer = ctypes.create_unicode_buffer(size.value)
        if kernel32.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)):
            return Path(buffer.value).name
    finally:
        kernel32.CloseHandle(handle)
    return ""


def _window_title(hwnd: int) -> str:
    if os.name != "nt":
        return ""
    user32 = ctypes.windll.user32
    length = user32.GetWindowTextLengthW(hwnd)
    if length <= 0 or length > 500:
        return ""
    buffer = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buffer, length + 1)
    return buffer.value


def _is_cloaked(hwnd: int) -> bool:
    if os.name != "nt":
        return True
    try:
        value = wintypes.DWORD()
        result = ctypes.windll.dwmapi.DwmGetWindowAttribute(hwnd, 14, ctypes.byref(value), ctypes.sizeof(value))
        return result == 0 and value.value != 0
    except (AttributeError, OSError):
        return False


def enumerate_visible_windows(max_windows: int = DEFAULT_MAX_WINDOWS) -> list[dict[str, Any]]:
    """Return visible top-level windows across the current virtual desktop."""
    if os.name != "nt":
        return []
    user32 = ctypes.windll.user32
    foreground = int(user32.GetForegroundWindow())
    windows: list[dict[str, Any]] = []
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def callback(hwnd: int, _lparam: int) -> bool:
        if not user32.IsWindowVisible(hwnd) or _is_cloaked(hwnd):
            return True
        exstyle = int(user32.GetWindowLongW(hwnd, -20))
        if exstyle & 0x00000080:  # tool windows are usually transient system chrome
            return True
        rect = _RECT()
        if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
            return True
        width, height = rect.right - rect.left, rect.bottom - rect.top
        if width < 180 or height < 120:
            return True
        title = _window_title(hwnd)
        process = _process_name(hwnd)
        if not title and not process:
            return True
        category, hint = classify_text(title, process)
        windows.append({
            "window_id": f"win_{int(hwnd)}",
            "hwnd": int(hwnd),
            "title": title,
            "process": process,
            "app_category": category,
            "task_hint": hint,
            "bounds": {"left": rect.left, "top": rect.top, "right": rect.right, "bottom": rect.bottom},
            "width": width,
            "height": height,
            "is_active": int(hwnd) == foreground,
            "area": width * height,
        })
        return True

    user32.EnumWindows(callback_type(callback), 0)
    windows.sort(key=lambda item: (not item["is_active"], -item["area"]))
    return windows[: max(1, min(int(max_windows), 16))]


def _control_value(control: Any) -> str:
    try:
        if bool(getattr(control, "IsPassword", False)):
            return ""
    except Exception:
        pass
    values: list[str] = []
    try:
        name = str(getattr(control, "Name", "") or "").strip()
        if name:
            values.append(name)
    except Exception:
        pass
    try:
        if hasattr(control, "GetValuePattern"):
            value = getattr(control.GetValuePattern(), "Value", "")
            if value:
                values.append(str(value))
    except Exception:
        pass
    return " ".join(values)


def extract_accessible_text(hwnd: int, max_chars: int = 4000) -> str:
    """Extract UIA text from one window without touching password fields."""
    if os.name != "nt" or max_chars <= 0:
        return ""
    try:
        import uiautomation as auto
    except ImportError:
        return ""
    try:
        root = auto.ControlFromHandle(hwnd)
    except Exception:
        return ""
    if root is None:
        return ""
    chunks: list[str] = []
    seen: set[str] = set()
    stack: list[tuple[Any, int]] = [(root, 0)]
    visited = 0
    while stack and visited < 350 and sum(len(chunk) for chunk in chunks) < max_chars:
        control, depth = stack.pop()
        visited += 1
        text = _clean_text(_control_value(control), max_chars)
        if text and text not in seen and not _looks_like_secret(text):
            seen.add(text)
            chunks.append(text)
        if depth >= 6:
            continue
        try:
            children = control.GetChildren()
        except Exception:
            continue
        for child in reversed(children[:80]):
            stack.append((child, depth + 1))
    return _clean_text(" · ".join(chunks), max_chars)


def read_screen_context(
    store: ConsentStore,
    consent_token: str,
    *,
    student_id: str | None = None,
    max_windows: int = DEFAULT_MAX_WINDOWS,
    max_text_chars: int = DEFAULT_MAX_TEXT_CHARS,
) -> dict[str, Any]:
    """Read current visible windows under an active consent session.

    Accessible text is included only when the `accessible` scope was granted.
    No result is persisted and no screenshot is included here.
    """
    session = store.validate(consent_token, student_id=student_id, required_scope="windows")
    scopes = set(session.get("scopes") or [])
    accessible = "accessible" in scopes
    windows = enumerate_visible_windows(max_windows=max_windows)
    text_budget = max(0, min(int(max_text_chars), 40000))
    per_window_budget = max(300, text_budget // max(1, len(windows))) if windows else text_budget
    for window in windows:
        title = _clean_text(window.get("title", ""), 500)
        window["title"] = title
        if accessible:
            remaining = max(0, text_budget - sum(len(item.get("accessible_text", "")) for item in windows))
            window["accessible_text"] = extract_accessible_text(window["hwnd"], min(per_window_budget, remaining))
            window["text_available"] = bool(window["accessible_text"])
        else:
            window["accessible_text"] = ""
            window["text_available"] = False
        window.pop("hwnd", None)
        window.pop("area", None)
    return {
        "captured_at": _iso(_utcnow()),
        "student_id": session.get("student_id"),
        "scopes": sorted(scopes),
        "coverage": {
            "visible_top_level_windows": len(windows),
            "includes": ["当前桌面可见的顶层窗口"],
            "excludes": ["隐藏标签页", "密码字段", "剪贴板", "摄像头", "麦克风", "键盘记录", "受保护或 DRM 内容"],
        },
        "windows": windows,
        "privacy": {
            "raw_content_persisted": False,
            "raw_content_sent_to_daoql": False,
            "screenshots_included": False,
            "local_only_until_caller_decides": True,
        },
    }


def derive_safe_signals(context: dict[str, Any]) -> dict[str, Any]:
    """Reduce screen context to coarse signals safe for the ambient planner."""
    windows = context.get("windows") or []
    categories = sorted({str(item.get("app_category") or "unknown") for item in windows})
    public_category = {item: item for item in ("study", "coding", "document", "video", "chat", "game", "browser", "unknown")}
    categories = [public_category.get(item, "unknown") for item in categories]
    found_terms: list[str] = []
    for window in windows:
        haystack = f"{window.get('title', '')} {window.get('accessible_text', '')}".lower()
        for keyword, category in TASK_TERMS:
            if keyword.lower() in haystack:
                if keyword not in found_terms:
                    found_terms.append(keyword)
                if category not in categories:
                    categories.append(category)
                break
    active = next((item for item in windows if item.get("is_active")), None)
    active_category = "unknown"
    task_hint = ""
    if active:
        active_category = str(active.get("app_category") or "unknown")
        task_hint = str(active.get("task_hint") or "")
    if not task_hint and found_terms:
        task_hint = found_terms[0]
    return {
        "screen_context_available": True,
        "screen_window_count": len(windows),
        "screen_categories": ",".join(categories[:8]),
        "screen_active_category": active_category,
        "screen_task_hint": task_hint[:40],
        "screen_evidence_windows": sum(1 for item in windows if item.get("text_available")),
        "privacy_mode": "consented_visible_ui_derived_local",
    }


def capture_authorized_screen(
    store: ConsentStore,
    consent_token: str,
    *,
    student_id: str | None = None,
    max_width: int = 1920,
) -> bytes:
    """Capture all displays as PNG bytes under the screenshots scope.

    The image stays in memory. Protected windows may appear black depending on
    the operating system and the application.
    """
    store.validate(consent_token, student_id=student_id, required_scope="screenshots")
    try:
        from PIL import ImageGrab
    except ImportError as exc:
        raise ScreenContextError("screenshot_unavailable", "截图组件未安装。") from exc
    image = ImageGrab.grab(all_screens=True)
    maximum = max(640, min(int(max_width), 2560))
    if image.width > maximum:
        ratio = maximum / image.width
        image = image.resize((maximum, max(1, int(image.height * ratio))))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()
