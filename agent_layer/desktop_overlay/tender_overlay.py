"""Tender 真桌面弹幕层（Windows）。

特点：
- 始终置顶、无边框、不抢焦点、鼠标穿透；
- 用户可以在浏览器、Word、PDF、网课或其他软件上方继续工作；
- 默认每 8 秒读取一次 Tender 的单卡计划；
- 实时读取前台应用类型和任务关键词，在本地归一化后交给 Tender；
- 原始窗口标题不离开本机，也不写入 DAOQL；
- Ctrl+Alt+Space 手动触发；Ctrl+Alt+R 打开回复框；1/2/3/0 记录反馈；Q 退出。
"""
from __future__ import annotations

import argparse
import ctypes
import json
import os
import queue
import sys
import threading
import time
from ctypes import wintypes
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import tkinter as tk
from tkinter import filedialog, font as tkfont, messagebox

OVERLAY_DIR = Path(__file__).resolve().parent
if str(OVERLAY_DIR) not in sys.path:
    sys.path.insert(0, str(OVERLAY_DIR))

from media_plugins import (
    MediaPluginError,
    analyze_image,
    analyze_video,
    summarize_for_danmaku,
    transcribe_audio,
)

from screen_context import (
    CONSENT_PHRASE,
    ConsentExpired,
    ConsentRequired,
    ConsentStore,
    ScreenContextError,
    derive_safe_signals,
    read_screen_context,
)

CFG_PATH = Path(__file__).with_name("config.json")


def runtime_shutdown_marker() -> Path:
    base = Path(os.environ.get("LOCALAPPDATA") or Path.home())
    return base / "Tender" / "runtime" / "shutdown.request"
WM_HOTKEY = 0x0312
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_NOREPEAT = 0x4000
GWL_EXSTYLE = -20
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_LAYERED = 0x00080000
WS_EX_NOACTIVATE = 0x08000000

HOTKEYS = {
    1: ("useful", "已记录：这条有用", 0x31),
    2: ("wrong", "已记录：这条不合适", 0x32),
    3: ("silence", "已进入 30 分钟静默", 0x33),
    4: ("dismiss", "已收起", 0x30),
    5: ("trigger", "手动请求一张最小提示", 0x20),
    6: ("exit", "Tender 弹幕已退出", 0x51),
    7: ("reply", "回复 Tender", 0x52),
    8: ("behavior", "按当前行为触发测试", 0x42),
    9: ("persona", "选择陪伴人设", 0x50),
    10: ("screen_context", "授权读取当前界面", 0x49),
}


class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.UINT), ("dwTime", wintypes.DWORD)]


BEHAVIOR_RULES = [
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
]
PROCESS_RULES = {
    "chrome.exe": "browser", "msedge.exe": "browser", "firefox.exe": "browser",
    "winword.exe": "document", "wps.exe": "document", "acrobat.exe": "document",
    "code.exe": "coding", "pycharm64.exe": "coding", "cursor.exe": "coding",
    "wechat.exe": "chat", "weixin.exe": "chat", "qq.exe": "chat", "feishu.exe": "chat",
    "dingtalk.exe": "chat", "chatgpt.exe": "chat",
    "potplayermini64.exe": "video", "vlc.exe": "video",
}
ACTIVITY_KEYS = list(range(0x30, 0x5B)) + [0x08, 0x09, 0x0D, 0x20, 0x25, 0x26, 0x27, 0x28]
AGENT_FALLBACK = [
    {"id": "learning_strategist", "name": "学习策略师", "mark": "策略", "role": "任务拆解、优先级与复习节奏"},
    {"id": "subject_expert", "name": "学科专家", "mark": "学科", "role": "知识点、先修关系与错因定位"},
    {"id": "neuro_cognition", "name": "神经认知师", "mark": "认知", "role": "注意力、工作记忆与认知负荷"},
    {"id": "psychologist", "name": "心理调节师", "mark": "心理", "role": "焦虑、回避、动机与自我评价"},
    {"id": "nutritionist", "name": "营养健康师", "mark": "营养", "role": "睡眠、饮食、补水与身体能量"},
    {"id": "career_advisor", "name": "生涯规划师", "mark": "生涯", "role": "专业兴趣、目标路径与长期证据"},
    {"id": "safety_officer", "name": "安全保护官", "mark": "安全", "role": "隐私、身心安全与求助边界"},
    {"id": "metacognition_coach", "name": "元认知教练", "mark": "元认知", "role": "策略觉察、监控与复盘"},
]

def agent_lookup(agent_id: str | None) -> dict:
    return next((item for item in AGENT_FALLBACK if item["id"] == agent_id), AGENT_FALLBACK[0])

def classify_behavior(title: str, process_name: str) -> tuple[str, str]:
    text = f"{title} {process_name}".lower()
    for keyword, category in BEHAVIOR_RULES:
        if keyword.lower() in text:
            return category, keyword[:40]
    return PROCESS_RULES.get(process_name.lower(), "unknown"), ""


class WindowsSignals:
    def __init__(self, observe_titles: bool = True) -> None:
        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32
        self.kernel32.GetTickCount64.restype = ctypes.c_ulonglong
        self.observe_titles = observe_titles
        self.started = time.monotonic()
        self.focus_started = self.started
        self.last_idle = 0.0
        self.last_hwnd = None
        self.switches: list[float] = []
        self.activity_events: list[float] = []
        self.key_state: dict[int, bool] = {}
        self.last_cursor: tuple[int, int] | None = None
        self.current_category = "unknown"
        self.current_task_hint = ""
        self.current_process = ""

    def idle_seconds(self) -> float:
        info = LASTINPUTINFO()
        info.cbSize = ctypes.sizeof(LASTINPUTINFO)
        if not self.user32.GetLastInputInfo(ctypes.byref(info)):
            return 0.0
        tick = self.kernel32.GetTickCount64()
        return max(0.0, (tick - int(info.dwTime)) / 1000.0)

    def _process_name(self, hwnd: int) -> str:
        pid = wintypes.DWORD()
        self.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        handle = self.kernel32.OpenProcess(0x1000, False, pid.value)
        if not handle:
            return ""
        try:
            size = wintypes.DWORD(512)
            buf = ctypes.create_unicode_buffer(size.value)
            if self.kernel32.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size)):
                return Path(buf.value).name
        finally:
            self.kernel32.CloseHandle(handle)
        return ""

    def _window_title(self, hwnd: int) -> str:
        if not self.observe_titles:
            return ""
        length = self.user32.GetWindowTextLengthW(hwnd)
        if length <= 0 or length > 300:
            return ""
        buf = ctypes.create_unicode_buffer(length + 1)
        self.user32.GetWindowTextW(hwnd, buf, length + 1)
        return buf.value

    def _refresh_context(self, hwnd: int) -> None:
        process = self._process_name(hwnd)
        title = self._window_title(hwnd)
        category, hint = classify_behavior(title, process)
        self.current_process = process
        self.current_category = category
        self.current_task_hint = hint

    def activity_tick(self) -> None:
        now = time.monotonic()
        for vk in ACTIVITY_KEYS:
            down = bool(self.user32.GetAsyncKeyState(vk) & 0x8000)
            if down and not self.key_state.get(vk, False):
                self.activity_events.append(now)
            self.key_state[vk] = down
        for vk in (0x01, 0x02, 0x04):
            down = bool(self.user32.GetAsyncKeyState(vk) & 0x8000)
            if down and not self.key_state.get(vk, False):
                self.activity_events.append(now)
            self.key_state[vk] = down
        point = wintypes.POINT()
        if self.user32.GetCursorPos(ctypes.byref(point)):
            current = (point.x, point.y)
            if self.last_cursor and abs(current[0] - self.last_cursor[0]) + abs(current[1] - self.last_cursor[1]) > 4:
                self.activity_events.append(now)
            self.last_cursor = current
        cutoff = now - 60
        self.activity_events = [t for t in self.activity_events if t >= cutoff]

    def sample(self) -> None:
        now = time.monotonic()
        hwnd = self.user32.GetForegroundWindow()
        if hwnd and hwnd != self.last_hwnd:
            if self.last_hwnd is not None:
                self.switches.append(now)
            self.last_hwnd = hwnd
        if hwnd:
            self._refresh_context(hwnd)
        cutoff = now - 90
        self.switches = [t for t in self.switches if t >= cutoff]
        idle = self.idle_seconds()
        if idle > 90:
            self.focus_started = now
        elif self.last_idle > 90 and idle < 2:
            self.focus_started = now
        self.last_idle = idle

    def signals(self, scenario: str) -> dict:
        self.sample()
        now = time.monotonic()
        idle = self.idle_seconds()
        focus_minutes = max(0.0, (now - self.focus_started) / 60.0) if idle < 90 else 0.0
        return {
            "scenario": scenario,
            "idle_seconds": round(idle, 1),
            "focus_minutes": round(focus_minutes, 1),
            "visibility_switches": len(self.switches),
            "activity_events_per_min": len(self.activity_events),
            "app_category": self.current_category,
            "task_hint": self.current_task_hint,
            "explicit_need": 0,
            "privacy_mode": "local_normalized_behavior",
        }


class TenderClient:
    def __init__(self, cfg: dict) -> None:
        self.base = str(cfg["api_base"]).rstrip("/")
        self.student_id = str(cfg["student_id"])
        self.role = str(cfg.get("role", "learner"))
        self.token: str | None = None

    def _json(self, method: str, path: str, payload: dict | None = None, auth: bool = True) -> dict:
        body = json.dumps(payload or {}, ensure_ascii=False).encode("utf-8")
        headers = {"Content-Type": "application/json; charset=utf-8"}
        if auth:
            if not self.token:
                self.login()
            headers.update({
                "Authorization": "Bearer " + (self.token or ""),
                "X-Tender-Actor": self.student_id,
                "X-Tender-Role": self.role,
                "X-Tender-Learner": self.student_id,
            })
        req = Request(self.base + path, data=body, headers=headers, method=method)
        try:
            with urlopen(req, timeout=6) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except HTTPError as exc:
            if auth and exc.code == 401:
                self.token = None
                self.login()
                return self._json(method, path, payload, auth=True)
            raise

    def login(self) -> None:
        data = self._json(
            "POST",
            "/auth/demo-session",
            {"actor_id": self.student_id, "role": self.role, "learner_id": self.student_id},
            auth=False,
        )
        self.token = data["token"]

    def plan(self, signals: dict, force: bool = False) -> dict:
        return self._json("POST", f"/ambient/plan/{self.student_id}", {"signals": signals, "force": force})

    def feedback(self, card_id: str, feedback: str) -> dict:
        return self._json("POST", f"/ambient/feedback/{self.student_id}", {"card_id": card_id, "feedback": feedback})

    def reply(self, card_id: str, message: str, scenario: str = "score_improvement", agent_id: str | None = None, agent_ids: list[str] | None = None) -> dict:
        return self._json("POST", f"/ambient/reply/{self.student_id}", {"card_id": card_id, "message": message, "scenario": scenario, "agent_id": agent_id, "agent_ids": agent_ids})

    def shutdown(self) -> dict:
        return self._json("POST", "/system/shutdown", {})

    def list_personas(self) -> dict:
        return self._json("GET", "/ambient/personas", {})

    def set_persona(self, persona_id: str) -> dict:
        return self._json("POST", f"/ambient/persona/{self.student_id}", {"persona_id": persona_id})

    def set_ensemble(self, persona_ids: list[str]) -> dict:
        return self._json("POST", f"/ambient/ensemble/{self.student_id}", {"persona_ids": persona_ids})


class HotkeyThread(threading.Thread):
    def __init__(self, callbacks: queue.Queue) -> None:
        super().__init__(daemon=True)
        self.callbacks = callbacks
        self.user32 = ctypes.windll.user32
        self.registered: list[int] = []

    def run(self) -> None:
        modifiers = MOD_CONTROL | MOD_ALT | MOD_NOREPEAT
        for ident, (_, _, vk) in HOTKEYS.items():
            if self.user32.RegisterHotKey(None, ident, modifiers, vk):
                self.registered.append(ident)
        msg = wintypes.MSG()
        while self.user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            if msg.message == WM_HOTKEY:
                self.callbacks.put(int(msg.wParam))
        for ident in self.registered:
            self.user32.UnregisterHotKey(None, ident)


class Overlay:
    def __init__(self, cfg: dict, demo: bool = False, demo_once: bool = False) -> None:
        self.cfg = cfg
        self.demo = demo
        self.demo_once = demo_once
        self.root = tk.Tk()
        self.root.title("Tender Ambient Overlay")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", float(cfg.get("alpha", 0.82)))
        self.root.configure(bg="#c9cbcd")
        self.root.withdraw()
        try:
            runtime_shutdown_marker().unlink(missing_ok=True)
        except OSError:
            pass

        self.card_id: str | None = None
        self.hide_job = None
        self.reply_window = None
        self.persona_window = None
        self.conversation_window = None
        self.conversation_panel = None
        self.conversation_text = None
        self.conversation_entry = None
        self.conversation_status = None
        self.conversation_placeholder = "和 Tender 说点什么…"
        self.danmaku_window = None
        self.danmaku_canvas = None
        self.danmaku_job = None
        self.danmaku_items: dict[str, int] = {}
        self.danmaku_pending: list[dict] = []
        self.danmaku_spawn_job = None
        self.danmaku_lane = 0
        self.current_persona = str(cfg.get("agent_id", "learning_strategist"))
        self.current_ensemble = list(cfg.get("agent_ids") or ["learning_strategist", "subject_expert", "neuro_cognition", "psychologist", "nutritionist", "career_advisor", "safety_officer", "metacognition_coach"])
        self.last_signals = WindowsSignals(bool(cfg.get("observe_window_title", True)))
        self.screen_store = ConsentStore()
        self.screen_token: str | None = None
        self.screen_context_cache: dict = {}
        self.screen_context_cached_at = 0.0
        self.screen_context_reading = False
        self.screen_context_button = None
        self.screen_consent_window = None
        self.media_button = None
        self.media_running = False
        self.client = TenderClient(cfg)
        self.hotkey_queue: queue.Queue[int] = queue.Queue()
        self.hotkeys = HotkeyThread(self.hotkey_queue)
        self.hotkeys.start()

        self.width = 520
        self.height = 104
        self.frame = tk.Frame(self.root, bg="#c9cbcd", highlightbackground="#777b7f", highlightthickness=1)
        self.frame.pack(fill="both", expand=True)
        self.scene = tk.Label(self.frame, text="", fg="#202326", bg="#c9cbcd", anchor="w", font=("Microsoft YaHei UI", 9, "bold"))
        self.scene.pack(fill="x", padx=18, pady=(12, 0))
        self.message = tk.Label(self.frame, text="", fg="#080808", bg="#c9cbcd", anchor="w", justify="left", wraplength=480, font=("Microsoft YaHei UI", 12, "bold"))
        self.message.pack(fill="x", padx=18, pady=(3, 0))
        self.room = tk.Label(self.frame, text="", fg="#303438", bg="#c9cbcd", anchor="w", font=("Microsoft YaHei UI", 8))
        self.room.pack(fill="x", padx=18, pady=(3, 0))
        self.hint = tk.Label(self.frame, text="Ctrl+Alt+R 回复  ·  1 有用  ·  2 不准  ·  3 静默  ·  0 收起", fg="#3b3f43", bg="#c9cbcd", anchor="w", font=("Microsoft YaHei UI", 8))
        self.hint.pack(fill="x", padx=18, pady=(4, 10))
        self.root.update_idletasks()
        self._make_click_through()
        self._create_conversation_dock()

        self.root.after(200, self.poll)
        self.root.after(120, self.process_hotkeys)
        self.root.after(500, self.monitor_tick)
        if self.demo:
            self.root.after(350, lambda: self.show_card({
                "card_id": "ambient_demo_overlay",
                "kind": "desktop_overlay_ready",
                "text": "桌面弹幕已启动。我会在你使用其他软件时只出现一条最小提示。",
                "action": "Ctrl+Alt+Space 可以手动触发",
                "scenario": self.cfg.get("scenario", "gaokao_registration"),
            }))
        if self.demo_once:
            self.root.after(12000, self.exit)

    def _create_conversation_dock(self) -> None:
        win = tk.Toplevel(self.root)
        self.conversation_window = win
        win.title("Tender 对话")
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.configure(bg="#c9cbcd")
        width = int(self.cfg.get("dock_width", 780))
        height = int(self.cfg.get("dock_height", 54))
        rect = wintypes.RECT()
        if not ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0):
            rect.left, rect.top, rect.right, rect.bottom = 0, 0, win.winfo_screenwidth(), win.winfo_screenheight()
        x = rect.left + max(0, (rect.right - rect.left - width) // 2)
        y = rect.bottom - height - 4
        win.geometry(f"{width}x{height}+{x}+{y}")
        win.configure(bg="#c9cbcd", highlightbackground="#777b7f", highlightthickness=1)
        self._create_conversation_panel(width, x, y)

        tk.Label(win, text="● Tender", fg="#111111", bg="#c9cbcd", font=("Microsoft YaHei UI", 10, "bold")).pack(side="left", padx=(14, 10))
        self.conversation_status = tk.Label(win, text=f"{len(self.current_ensemble)} Agent", fg="#3b3f43", bg="#c9cbcd", font=("Microsoft YaHei UI", 8))
        self.conversation_status.pack(side="left", padx=(0, 10))
        send_btn = tk.Button(win, text="发送", bg="#bfc2c5", fg="#111111", activebackground="#aeb2b5", activeforeground="#000000", relief="flat", bd=0, padx=14, cursor="hand2", font=("Microsoft YaHei UI", 9, "bold"), command=self.send_conversation)
        send_btn.pack(side="right", padx=(8, 12), pady=9)
        self.media_button = tk.Button(win, text="媒体", bg="#bfc2c5", fg="#111111", activebackground="#aeb2b5", activeforeground="#000000", relief="flat", bd=0, padx=10, cursor="hand2", font=("Microsoft YaHei UI", 8), command=self.choose_media_file)
        self.media_button.pack(side="right", padx=(0, 4), pady=9)
        tk.Button(win, text="关闭", bg="#bfc2c5", fg="#7d2929", activebackground="#e2bcbc", activeforeground="#5d1717", relief="flat", bd=0, padx=10, cursor="hand2", font=("Microsoft YaHei UI", 8), command=self.shutdown_tender).pack(side="right", padx=(0, 4), pady=9)
        self.screen_context_button = tk.Button(win, text="读界面 · 关", bg="#bfc2c5", fg="#111111", activebackground="#aeb2b5", activeforeground="#000000", relief="flat", bd=0, padx=10, cursor="hand2", font=("Microsoft YaHei UI", 8), command=self.toggle_screen_context)
        self.screen_context_button.pack(side="right", padx=(0, 4), pady=9)
        self.conversation_entry = tk.Entry(win, bg="#f3f3f3", fg="#777777", insertbackground="#111111", relief="flat", font=("Microsoft YaHei UI", 10))
        self.conversation_entry.pack(side="left", fill="both", expand=True, pady=9)
        self.conversation_entry.insert(0, self.conversation_placeholder)
        self.conversation_entry.bind("<FocusIn>", self._conversation_focus_in)
        self.conversation_entry.bind("<FocusOut>", self._conversation_focus_out)
        self.conversation_entry.bind("<Return>", self.send_conversation)
        win.bind("<Escape>", lambda _e: self.root.focus_force())
        win.lift()

    def _create_conversation_panel(self, width: int, x: int, bar_y: int) -> None:
        panel = tk.Toplevel(self.root)
        self.conversation_panel = panel
        panel.title("Tender 对话记录")
        panel.overrideredirect(True)
        panel.attributes("-topmost", True)
        panel.configure(bg="#c9cbcd", highlightbackground="#777b7f", highlightthickness=1)
        panel_height = min(320, max(190, bar_y - 160))
        panel_y = max(20, bar_y - panel_height - 6)
        panel.geometry(f"{width}x{panel_height}+{x}+{panel_y}")
        scrollbar = tk.Scrollbar(panel)
        scrollbar.pack(side="right", fill="y")
        text = tk.Text(panel, bg="#f3f3f3", fg="#111111", wrap="word", relief="flat", bd=0, padx=12, pady=10, font=("Microsoft YaHei UI", 10), yscrollcommand=scrollbar.set)
        text.pack(side="left", fill="both", expand=True)
        scrollbar.configure(command=text.yview)
        text.tag_configure("user", foreground="#1f4d6a", font=("Microsoft YaHei UI", 10, "bold"))
        text.tag_configure("agent", foreground="#111111", font=("Microsoft YaHei UI", 10, "bold"))
        text.tag_configure("body", foreground="#222222", font=("Microsoft YaHei UI", 10))
        text.tag_configure("triage", foreground="#555555", font=("Microsoft YaHei UI", 9, "italic"))
        text.configure(state="disabled")
        self.conversation_text = text
        panel.withdraw()
        panel.bind("<Escape>", lambda _e: panel.withdraw())

    def show_conversation_panel(self) -> None:
        if self.conversation_panel is not None:
            self.conversation_panel.deiconify()
            self.conversation_panel.lift()

    def append_conversation(self, speaker: str, message: str, kind: str = "body") -> None:
        if self.conversation_text is None:
            return
        self.conversation_text.configure(state="normal")
        self.conversation_text.insert(tk.END, speaker + chr(10), "user" if kind == "user" else ("agent" if kind == "agent" else "triage"))
        self.conversation_text.insert(tk.END, message.strip() + chr(10) + chr(10), "body")
        self.conversation_text.configure(state="disabled")
        self.conversation_text.see(tk.END)

    def _conversation_focus_in(self, _event=None) -> None:
        if self.conversation_entry and self.conversation_entry.get() == self.conversation_placeholder:
            self.conversation_entry.delete(0, tk.END)
            self.conversation_entry.configure(fg="#111111")

    def _conversation_focus_out(self, _event=None) -> None:
        if self.conversation_entry and not self.conversation_entry.get().strip():
            self.conversation_entry.insert(0, self.conversation_placeholder)
            self.conversation_entry.configure(fg="#777777")

    def focus_conversation_bar(self) -> None:
        if self.conversation_window is not None:
            self.show_conversation_panel()
            self.conversation_window.deiconify()
            self.conversation_window.lift()
            self.conversation_entry.focus_force()

    def send_conversation(self, _event=None) -> str:
        if self.conversation_entry is None:
            return "break"
        message = self.conversation_entry.get().strip()
        if not message or message == self.conversation_placeholder:
            return "break"
        source_card = self.card_id or "ambient_manual_dialogue"
        scenario = str(self.cfg.get("scenario", "score_improvement"))
        agents = list(self.current_ensemble)
        self.append_conversation("你", message, "user")
        self.show_conversation_panel()
        self.conversation_entry.delete(0, tk.END)
        self.conversation_entry.insert(0, self.conversation_placeholder)
        self.conversation_entry.configure(fg="#777777")
        self.conversation_status.configure(text="思考中…")

        def worker():
            try:
                result = self.client.reply(source_card, message, scenario, self.current_persona, agents)
                self.root.after(0, lambda: self._handle_conversation_result(result))
            except Exception:
                self.root.after(0, self._handle_conversation_error)

        threading.Thread(target=worker, daemon=True).start()
        return "break"

    def _handle_conversation_result(self, result: dict) -> None:
        self.conversation_status.configure(text="已回复")
        card = result.get("reply_card")
        if card:
            triage = card.get("triage") or {}
            if triage:
                self.append_conversation("分诊", f"{triage.get('label','')} · 置信度 {triage.get('confidence','')}", "triage")
            for item in card.get("ensemble_messages") or []:
                self.append_conversation(f"[{item.get('mark','Agent')}] {item.get('name','')}", item.get("text", ""), "agent")
            self.show_card(card)
        elif result.get("silence_until"):
            self.show_card({"card_id": "ambient_silence_ack", "text": "收到。我会安静 30 分钟。", "scenario": "score_improvement"})

    def _handle_conversation_error(self) -> None:
        self.conversation_status.configure(text="连接稍后重试")
        self.show_card({"card_id": "ambient_reply_offline", "text": "这条消息稍后可以再试一次。", "scenario": self.cfg.get("scenario", "score_improvement")})

    def _make_click_through(self) -> None:
        hwnd = self.root.winfo_id()
        parent = ctypes.windll.user32.GetParent(hwnd)
        hwnd = parent or hwnd
        style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        style |= WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW | WS_EX_LAYERED | WS_EX_NOACTIVATE
        ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)

    def monitor_tick(self) -> None:
        marker = runtime_shutdown_marker()
        if marker.exists():
            try:
                marker.unlink(missing_ok=True)
            except OSError:
                pass
            self.exit()
            return
        self.last_signals.sample()
        self.last_signals.activity_tick()
        self._update_screen_context_label()
        self.root.after(1000, self.monitor_tick)

    def _apply_click_through(self, win: tk.Misc) -> None:
        hwnd = win.winfo_id()
        parent = ctypes.windll.user32.GetParent(hwnd)
        hwnd = parent or hwnd
        style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        style |= WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW | WS_EX_LAYERED | WS_EX_NOACTIVATE
        ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)

    def _ensure_danmaku_window(self) -> None:
        if self.danmaku_window is not None:
            try:
                self.danmaku_window.deiconify()
                return
            except tk.TclError:
                self.danmaku_window = None
        win = tk.Toplevel(self.root)
        self.danmaku_window = win
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        try:
            win.attributes("-transparentcolor", "#010203")
            bg = "#010203"
        except tk.TclError:
            win.attributes("-alpha", 0.94)
            bg = "#101418"
        sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
        win.geometry(f"{sw}x{sh}+0+0")
        canvas = tk.Canvas(win, bg=bg, highlightthickness=0, bd=0)
        canvas.pack(fill="both", expand=True)
        self.danmaku_canvas = canvas
        win.update_idletasks()
        self._apply_click_through(win)

    def clear_danmaku(self) -> None:
        for attr in ("danmaku_job", "danmaku_spawn_job"):
            job = getattr(self, attr)
            if job:
                try:
                    self.root.after_cancel(job)
                except tk.TclError:
                    pass
                setattr(self, attr, None)
        self.danmaku_items.clear()
        self.danmaku_pending.clear()
        self.danmaku_lane = 0
        if self.danmaku_canvas is not None:
            try:
                self.danmaku_canvas.delete("danmaku")
                self.danmaku_canvas.delete("roomstrip")
            except tk.TclError:
                pass
        if self.danmaku_window is not None:
            try:
                self.danmaku_window.withdraw()
            except tk.TclError:
                pass

    def show_danmaku(self, card: dict) -> None:
        messages = list(card.get("ensemble_messages") or [])
        if len(messages) <= 1:
            return
        self.card_id = card.get("card_id")
        self.root.withdraw()
        self.clear_danmaku()
        self._ensure_danmaku_window()
        canvas = self.danmaku_canvas
        if canvas is None:
            return
        width = self.danmaku_window.winfo_screenwidth()
        room_text = "Agent 圆桌：" + " ".join(f"[{m.get('mark','Agent')}]" for m in messages)
        room_font = tkfont.Font(family="Microsoft YaHei UI", size=10, weight="bold")
        room_width = room_font.measure(room_text) + 34
        room_x = max(20, (width - room_width) // 2)
        canvas.create_rectangle(room_x, 58, room_x + room_width, 94, fill="#d0d2d4", outline="#73777b", width=1, stipple="gray25", tags=("roomstrip",))
        canvas.create_text(room_x + 17, 76, text=room_text, fill="#111111", font=room_font, anchor="w", tags=("roomstrip",))
        self.danmaku_pending = messages
        spawn_ms = max(500, int(self.cfg.get("danmaku_spawn_ms", 1200)))
        if self.hide_job:
            self.root.after_cancel(self.hide_job)
        self.hide_job = self.root.after(max(15000, len(messages) * spawn_ms + 13000), self.hide_card)
        self.animate_danmaku()
        self.spawn_next_danmaku()

    def spawn_next_danmaku(self) -> None:
        if self.danmaku_canvas is None or not self.danmaku_pending:
            self.danmaku_spawn_job = None
            return
        max_concurrent = max(1, min(2, int(self.cfg.get("danmaku_max_concurrent", 2))))
        if len(self.danmaku_items) >= max_concurrent:
            self.danmaku_spawn_job = self.root.after(300, self.spawn_next_danmaku)
            return
        message = self.danmaku_pending.pop(0)
        text = str(message.get("text", "")).strip().replace("\n", " ")
        if len(text) > 58:
            text = text[:56] + "…"
        label = f"[{message.get('mark','Agent')}] {message.get('name','')}：{text}"
        font = tkfont.Font(family="Microsoft YaHei UI", size=11, weight="bold")
        text_width = font.measure(label)
        box_width = text_width + 34
        y = 126 + (self.danmaku_lane % 2) * 66
        self.danmaku_lane += 1
        screen_width = self.danmaku_window.winfo_screenwidth()
        start_x = screen_width + 20
        tag = f"danmaku_{int(time.time() * 1000)}_{self.danmaku_lane}"
        self.danmaku_canvas.create_rectangle(start_x, y, start_x + box_width, y + 44, fill="#d0d2d4", outline="#73777b", width=1, stipple="gray25", tags=("danmaku", tag))
        self.danmaku_canvas.create_text(start_x + 16, y + 22, text=label, fill="#080808", font=font, anchor="w", tags=("danmaku", tag))
        self.danmaku_items[tag] = max(2, int(self.cfg.get("danmaku_speed", 5)))
        spawn_ms = max(500, int(self.cfg.get("danmaku_spawn_ms", 1200)))
        self.danmaku_spawn_job = self.root.after(spawn_ms, self.spawn_next_danmaku)

    def animate_danmaku(self) -> None:
        if self.danmaku_canvas is None:
            return
        finished = []
        for tag, speed in list(self.danmaku_items.items()):
            try:
                self.danmaku_canvas.move(tag, -speed, 0)
                bbox = self.danmaku_canvas.bbox(tag)
                if bbox and bbox[2] < -20:
                    self.danmaku_canvas.delete(tag)
                    finished.append(tag)
            except tk.TclError:
                finished.append(tag)
        for tag in finished:
            self.danmaku_items.pop(tag, None)
        if self.danmaku_items or self.danmaku_pending:
            self.danmaku_job = self.root.after(33, self.animate_danmaku)
        else:
            self.clear_danmaku()

    def _position(self) -> None:
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        right = int(self.cfg.get("right_margin", 28))
        top = int(self.cfg.get("top_margin", 110))
        pos = self.cfg.get("position", "top_right")
        if pos == "bottom_right":
            y = self.root.winfo_screenheight() - self.height - top
        elif pos == "top_left":
            x, y = right, top
        elif pos == "top_center":
            x, y = (sw - self.width) // 2, top
        else:
            x, y = sw - self.width - right, top
        self.root.geometry(f"{self.width}x{self.height}+{max(0, x)}+{max(0, y)}")

    def show_card(self, card: dict) -> None:
        if len(card.get("ensemble_messages") or []) > 1:
            self.show_danmaku(card)
            return
        self.clear_danmaku()
        self.card_id = card.get("card_id")
        scenario = card.get("scenario") or self.cfg.get("scenario", "")
        scene = "高考报名" if scenario == "gaokao_registration" else "提分陪伴"
        agent_label = " ".join(x for x in (card.get("agent_mark"), card.get("agent_name")) if x)
        self.scene.configure(text=f"TENDER · {agent_label + ' · ' if agent_label else ''}{scene}")
        self.message.configure(text=str(card.get("text", "")).strip())
        action = str(card.get("action", "")).strip()
        hint = "Ctrl+Alt+R 回复  ·  Ctrl+Alt+I 读界面  ·  P 换人设  ·  1 有用  ·  2 不准  ·  3 静默  ·  0 收起"
        if action:
            hint = action + "  ·  " + hint
        self.hint.configure(text=hint if self.cfg.get("show_hotkey_hint", True) else "")
        room = card.get("room") or []
        if room:
            icons = " ".join(f"[{member.get('mark','')}]" for member in room)
            speaker = next((member for member in room if member.get("speaking")), {})
            self.room.configure(text=f"Agent 圆桌 {icons} · 首位发言 {speaker.get('name','')}")
        else:
            self.room.configure(text="")
        self.height = 132 if action else 120
        self._position()
        self.root.deiconify()
        self.root.lift()
        self.root.attributes("-topmost", True)
        self.root.update_idletasks()
        hwnd = self.root.winfo_id()
        parent = ctypes.windll.user32.GetParent(hwnd)
        hwnd = parent or hwnd
        SWP_NOSIZE, SWP_NOMOVE, SWP_NOACTIVATE, SWP_SHOWWINDOW = 0x0001, 0x0002, 0x0010, 0x0040
        ctypes.windll.user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE | SWP_SHOWWINDOW)
        self._make_click_through()
        if self.hide_job:
            self.root.after_cancel(self.hide_job)
        self.hide_job = self.root.after(int(float(self.cfg.get("card_seconds", 9)) * 1000), self.hide_card)

    def hide_card(self) -> None:
        self.clear_danmaku()
        self.root.withdraw()
        self.hide_job = None

    def feedback(self, feedback: str) -> None:
        if not self.card_id:
            return
        try:
            self.client.feedback(self.card_id, feedback)
        except Exception:
            pass
        self.hide_card()

    def process_hotkeys(self) -> None:
        try:
            while True:
                ident = self.hotkey_queue.get_nowait()
                action = HOTKEYS.get(ident, (None, "", 0))[0]
                if action in {"useful", "wrong", "silence", "dismiss"}:
                    self.feedback(action)
                elif action == "trigger":
                    self.request_manual_card()
                elif action == "reply":
                    self.open_reply_window()
                elif action == "behavior":
                    self.request_behavior_card()
                elif action == "persona":
                    self.open_persona_picker()
                elif action == "screen_context":
                    self.toggle_screen_context()
                elif action == "exit":
                    self.exit()
                    return
        except queue.Empty:
            pass
        self.root.after(120, self.process_hotkeys)

    def shutdown_tender(self) -> None:
        if not messagebox.askyesno("关闭 Tender", "关闭桌面弹幕和后台服务？"):
            return
        try:
            self.client.shutdown()
        except Exception:
            pass
        self.exit()

    def choose_media_file(self) -> None:
        if self.media_running:
            self.show_card({
                "card_id": "ambient_media_busy",
                "text": "上一个媒体还在本地处理中。先等它完成，不需要重复选择。",
                "scenario": self.cfg.get("scenario", "score_improvement"),
            })
            return
        path = filedialog.askopenfilename(
            title="选择要给 Tender 读取的图片、音频或视频",
            filetypes=[
                ("图片、音频与视频", "*.png *.jpg *.jpeg *.webp *.bmp *.tif *.tiff *.wav *.mp3 *.m4a *.aac *.flac *.ogg *.opus *.wma *.mp4 *.mov *.mkv *.avi *.webm *.m4v *.flv"),
                ("图片", "*.png *.jpg *.jpeg *.webp *.bmp *.tif *.tiff"),
                ("音频", "*.wav *.mp3 *.m4a *.aac *.flac *.ogg *.opus *.wma"),
                ("视频", "*.mp4 *.mov *.mkv *.avi *.webm *.m4v *.flv"),
                ("所有文件", "*.*"),
            ],
        )
        if not path:
            return
        self.media_running = True
        self.show_card({
            "card_id": "ambient_media_local_processing",
            "text": "正在本机读取你选择的媒体。图片做文字识别，音频做转写，视频取关键帧并转写。不会自动上传。",
            "action": "处理期间可以继续手上的事",
            "scenario": self.cfg.get("scenario", "score_improvement"),
        })

        def worker() -> None:
            suffix = Path(path).suffix.lower()
            try:
                if suffix in {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}:
                    result = analyze_image(path)
                elif suffix in {".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg", ".opus", ".wma"}:
                    result = transcribe_audio(path)
                elif suffix in {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v", ".flv"}:
                    result = analyze_video(path, max_frames=6, include_audio=True)
                else:
                    raise MediaPluginError("unsupported_media_type", "这个文件不是支持图片、音频或视频类型。")
                self.root.after(0, lambda value=result: self._handle_media_result(path, value))
            except Exception as exc:
                self.root.after(0, lambda error=exc: self._handle_media_error(error))

        threading.Thread(target=worker, daemon=True).start()

    def _handle_media_result(self, path: str, result: dict) -> None:
        self.media_running = False
        summary = summarize_for_danmaku(result, limit=320) or "处理完成，但没有识别到清晰的文字。"
        kind = result.get("type", "media")
        self.append_conversation("本地媒体 · " + Path(path).name, summary, "agent")
        self.show_conversation_panel()
        self.show_card({
            "card_id": "ambient_media_result",
            "kind": kind,
            "text": summary,
            "action": "原文只在本机显示，未写入 DAOQL",
            "scenario": self.cfg.get("scenario", "score_improvement"),
        })

    def _handle_media_error(self, error: Exception) -> None:
        self.media_running = False
        message = str(error) if isinstance(error, MediaPluginError) else "媒体插件没有完成处理。"
        self.show_card({
            "card_id": "ambient_media_error",
            "text": message,
            "action": "可以换一个文件，或先在设置中安装对应插件",
            "scenario": self.cfg.get("scenario", "score_improvement"),
        })

    def _update_screen_context_label(self) -> None:
        if self.screen_context_button is None:
            return
        if not self.screen_token:
            self.screen_context_button.configure(text="读界面 · 关")
            return
        try:
            status = self.screen_store.status(self.screen_token)
            remaining = int(status.get("remaining_seconds", 0))
            minutes, seconds = divmod(max(0, remaining), 60)
            self.screen_context_button.configure(text=f"读界面 · {minutes}:{seconds:02d}")
        except ConsentExpired:
            self.screen_token = None
            self.screen_context_cache = {}
            self.screen_context_cached_at = 0.0
            self.screen_context_button.configure(text="读界面 · 已到期")
        except ConsentRequired:
            self.screen_token = None
            self.screen_context_cache = {}
            self.screen_context_cached_at = 0.0
            self.screen_context_button.configure(text="读界面 · 关")

    def toggle_screen_context(self) -> None:
        if self.screen_token:
            self.stop_screen_context()
        else:
            self.open_screen_consent()

    def open_screen_consent(self) -> None:
        if self.screen_consent_window is not None:
            try:
                self.screen_consent_window.deiconify()
                self.screen_consent_window.lift()
                return
            except tk.TclError:
                self.screen_consent_window = None
        win = tk.Toplevel(self.root)
        self.screen_consent_window = win
        win.title("Tender 界面读取授权")
        win.attributes("-topmost", True)
        win.configure(bg="#d0d2d4")
        width, height = 600, 390
        sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
        win.geometry(f"{width}x{height}+{max(0,(sw-width)//2)}+{max(0,(sh-height)//2)}")
        tk.Label(win, text="允许 Tender 读取当前界面 15 分钟", fg="#111111", bg="#d0d2d4", font=("Microsoft YaHei UI", 17, "bold"), anchor="w").pack(fill="x", padx=24, pady=(20, 6))
        copy = (
            "Tender 会读取当前桌面所有可见顶层窗口的标题和可见文字，用来判断你正在做什么、需要哪种帮助。"
            "密码、验证码、证件号、手机号、邮箱等会先在本机隐去；原文和截图不写入 DAOQL。"
            "隐藏标签页、剪贴板和键盘输入不会被读取。授权到期或点击停止后立即失效。"
        )
        tk.Label(win, text=copy, fg="#303438", bg="#d0d2d4", font=("Microsoft YaHei UI", 10), anchor="w", justify="left", wraplength=548).pack(fill="x", padx=24, pady=(0, 12))
        choose = tk.Frame(win, bg="#d0d2d4")
        choose.pack(fill="x", padx=24, pady=4)
        text_var = tk.BooleanVar(value=True)
        confirm_var = tk.BooleanVar(value=False)
        tk.Checkbutton(choose, text="读取可见文字（推荐）", variable=text_var, bg="#d0d2d4", fg="#111111", activebackground="#d0d2d4", selectcolor="#e1e2e3", font=("Microsoft YaHei UI", 10)).pack(anchor="w", pady=4)
        tk.Checkbutton(choose, text="我确认现在允许读取，并知道界面中可能包含私人内容", variable=confirm_var, bg="#d0d2d4", fg="#111111", activebackground="#d0d2d4", selectcolor="#e1e2e3", font=("Microsoft YaHei UI", 10, "bold")).pack(anchor="w", pady=4)
        status = tk.Label(win, text="本次不包含屏幕截图权限。", fg="#555b60", bg="#d0d2d4", font=("Microsoft YaHei UI", 9), anchor="w")
        status.pack(fill="x", padx=24, pady=(8, 0))
        actions = tk.Frame(win, bg="#d0d2d4")
        actions.pack(side="bottom", fill="x", padx=24, pady=18)
        def close() -> None:
            if self.screen_consent_window is not None:
                try:
                    self.screen_consent_window.destroy()
                except tk.TclError:
                    pass
            self.screen_consent_window = None
        def allow() -> None:
            if not confirm_var.get():
                status.configure(text="请先勾选确认，再开始读取。", fg="#9b342f")
                return
            scopes = ["windows", "accessible"] if text_var.get() else ["windows"]
            try:
                granted = self.screen_store.grant(
                    str(self.cfg.get("student_id", "S01")),
                    scopes,
                    duration_minutes=15,
                    acknowledge=True,
                    confirmation_text=CONSENT_PHRASE,
                )
            except Exception as exc:
                status.configure(text=f"授权没有完成：{exc}", fg="#9b342f")
                return
            self.screen_token = str(granted["consent_token"])
            self.screen_context_cache = {}
            self.screen_context_cached_at = 0.0
            self._update_screen_context_label()
            close()
            self.show_card({
                "card_id": "ambient_screen_context_started",
                "text": "界面读取已授权 15 分钟。我会只在需要帮助时使用窗口中的线索，原文不会写进 DAOQL。",
                "action": "点击底部“读界面”可随时停止",
                "scenario": self.cfg.get("scenario", "score_improvement"),
            })
            self._refresh_screen_context()
        tk.Button(actions, text="取消", command=close, bg="#bfc2c5", fg="#111111", relief="flat", bd=0, padx=16, pady=9, cursor="hand2").pack(side="right")
        tk.Button(actions, text="允许 15 分钟", command=allow, bg="#d95d39", fg="#ffffff", activebackground="#bf4e2d", activeforeground="#ffffff", relief="flat", bd=0, padx=18, pady=9, cursor="hand2", font=("Microsoft YaHei UI", 10, "bold")).pack(side="right", padx=(0, 8))
        win.protocol("WM_DELETE_WINDOW", close)
        win.focus_force()

    def stop_screen_context(self) -> None:
        token = self.screen_token
        self.screen_token = None
        self.screen_context_cache = {}
        self.screen_context_cached_at = 0.0
        if token:
            try:
                self.screen_store.revoke(token)
            except Exception:
                pass
        self._update_screen_context_label()
        self.show_card({
            "card_id": "ambient_screen_context_stopped",
            "text": "界面读取已经停止。",
            "scenario": self.cfg.get("scenario", "score_improvement"),
        })

    def _refresh_screen_context(self) -> None:
        if not self.screen_token or self.screen_context_reading:
            return
        token = self.screen_token
        self.screen_context_reading = True
        def worker() -> None:
            try:
                context = read_screen_context(
                    self.screen_store,
                    token,
                    student_id=str(self.cfg.get("student_id", "S01")),
                    max_windows=6,
                    max_text_chars=6000,
                )
                signals = derive_safe_signals(context)
                self.root.after(0, lambda value=signals: self._store_screen_context(value))
            except Exception:
                self.root.after(0, self._expire_screen_context)
        threading.Thread(target=worker, daemon=True).start()

    def _store_screen_context(self, signals: dict) -> None:
        self.screen_context_reading = False
        self.screen_context_cache = dict(signals)
        self.screen_context_cached_at = time.monotonic()

    def _expire_screen_context(self) -> None:
        self.screen_context_reading = False
        self.screen_token = None
        self.screen_context_cache = {}
        self.screen_context_cached_at = 0.0
        self._update_screen_context_label()

    def _signals_with_screen_context(self, scenario: str, *, explicit_need: bool = False) -> dict:
        signals = self.last_signals.signals(scenario)
        if explicit_need:
            signals["explicit_need"] = 1
        if self.screen_token and self.screen_context_cache:
            signals.update(self.screen_context_cache)
            active_category = str(self.screen_context_cache.get("screen_active_category") or "")
            if active_category and active_category != "unknown":
                signals["app_category"] = active_category
            task_hint = str(self.screen_context_cache.get("screen_task_hint") or "")
            if task_hint:
                signals["task_hint"] = task_hint
            if time.monotonic() - self.screen_context_cached_at > 20:
                self._refresh_screen_context()
        return signals

    def open_persona_picker(self) -> None:
        if self.persona_window is not None:
            try:
                self.persona_window.deiconify()
                self.persona_window.lift()
                return
            except tk.TclError:
                self.persona_window = None
        try:
            personas = self.client.list_personas().get("personas", [])
        except Exception:
            personas = AGENT_FALLBACK
        if not personas:
            personas = AGENT_FALLBACK
        selected = set(self.current_ensemble)
        if not selected:
            selected = {"learning_strategist", "subject_expert", "neuro_cognition", "psychologist", "nutritionist", "career_advisor", "safety_officer", "metacognition_coach"}
        win = tk.Toplevel(self.root)
        self.persona_window = win
        win.title("组建 Tender Agent 圆桌")
        win.attributes("-topmost", True)
        win.configure(bg="#d0d2d4")
        w, h = 820, 620
        sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
        win.geometry(f"{w}x{h}+{max(0,(sw-w)//2)}+{max(0,(sh-h)//2)}")
        tk.Label(win, text="组建你的 Agent 圆桌", fg="#111111", bg="#d0d2d4", font=("Microsoft YaHei UI", 18, "bold"), anchor="w").pack(fill="x", padx=24, pady=(20, 2))
        tk.Label(win, text="选择不同的功能型 Agent。它们会针对同一情境给出不同专业视角，并像弹幕一样同时出现。", fg="#303438", bg="#d0d2d4", font=("Microsoft YaHei UI", 9), anchor="w", wraplength=760, justify="left").pack(fill="x", padx=24, pady=(0, 12))
        grid = tk.Frame(win, bg="#d0d2d4")
        grid.pack(fill="both", expand=True, padx=18, pady=(0, 8))
        buttons = {}
        save_btn = tk.Button(win, text="", bg="#d95d39", fg="#ffffff", activebackground="#bf4e2d", activeforeground="#ffffff", relief="flat", bd=0, padx=18, pady=10, cursor="hand2", font=("Microsoft YaHei UI", 10, "bold"))
        save_btn.pack(side="bottom", pady=(0, 18))

        def render_button(persona_id: str) -> None:
            persona = next((x for x in personas if x.get("id") == persona_id), None)
            if not persona or persona_id not in buttons:
                return
            active = persona_id in selected
            buttons[persona_id].configure(
                text=f"[{persona.get('mark','Agent')}] {persona.get('name','')}" + ("  ✓" if active else "") + f"\n{persona.get('role','')}",
                bg="#b5b8bb" if active else "#e1e2e3",
                highlightbackground="#5e6266" if active else "#8d9195",
            )
            save_btn.configure(text=f"保存圆桌 · 已选 {len(selected)} 位 Agent")

        def toggle(persona_id: str) -> None:
            if persona_id in selected:
                if len(selected) == 1:
                    return
                selected.remove(persona_id)
            else:
                selected.add(persona_id)
            render_button(persona_id)

        for index, persona in enumerate(personas):
            pid = persona.get("id")
            if not pid:
                continue
            button = tk.Button(
                grid, justify="left", anchor="w", wraplength=350,
                fg="#111111", activebackground="#b5b8bb", activeforeground="#000000", relief="flat", bd=0,
                highlightthickness=2, padx=14, pady=10, cursor="hand2",
                font=("Microsoft YaHei UI", 10), command=lambda value=pid: toggle(value),
            )
            button.grid(row=index // 2, column=index % 2, sticky="nsew", padx=7, pady=7)
            buttons[pid] = button
        grid.grid_columnconfigure(0, weight=1); grid.grid_columnconfigure(1, weight=1)
        for row in range(3): grid.grid_rowconfigure(row, weight=1)

        def save_selection() -> None:
            self.select_ensemble(list(selected))

        def select_all() -> None:
            selected.clear(); selected.update(pid for pid in buttons)
            for pid in buttons: render_button(pid)

        controls = tk.Frame(win, bg="#d0d2d4")
        controls.pack(side="bottom", fill="x", padx=24, pady=(0, 6))
        tk.Button(controls, text="全选 8 位", command=select_all, bg="#bfc2c5", fg="#111111", relief="flat", bd=0, padx=12, pady=7, cursor="hand2").pack(side="left")
        tk.Button(controls, text="取消", command=self.close_persona_picker, bg="#bfc2c5", fg="#111111", relief="flat", bd=0, padx=12, pady=7, cursor="hand2").pack(side="right")
        save_btn.configure(command=save_selection)
        for pid in buttons: render_button(pid)
        win.protocol("WM_DELETE_WINDOW", self.close_persona_picker)
        win.focus_force()

    def close_persona_picker(self) -> None:
        if self.persona_window is not None:
            try:
                self.persona_window.destroy()
            except tk.TclError:
                pass
        self.persona_window = None

    def save_persona_choice(self, persona_id: str) -> None:
        try:
            config = load_config()
            config["persona_id"] = persona_id
            CFG_PATH.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError:
            pass

    def save_ensemble_choice(self, persona_ids: list[str]) -> None:
        try:
            config = load_config()
            config["ensemble_ids"] = list(persona_ids)
            config["persona_id"] = self.current_persona
            CFG_PATH.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError:
            pass

    def select_ensemble(self, persona_ids: list[str]) -> None:
        if not persona_ids:
            return
        try:
            result = self.client.set_ensemble(persona_ids)
            self.current_ensemble = list(result.get("persona_ids") or persona_ids)
            preview = result.get("preview") or {}
            if preview.get("persona_id"):
                self.current_persona = str(preview["persona_id"])
            self.save_ensemble_choice(self.current_ensemble)
            if self.conversation_status is not None:
                self.conversation_status.configure(text=f"{len(self.current_ensemble)} Agent")
            self.close_persona_picker()
            if preview:
                self.show_card(preview)
            else:
                self.show_card({"card_id": "ambient_ensemble_changed", "text": "Agent 圆桌已经更新。", "scenario": self.cfg.get("scenario", "score_improvement")})
        except Exception:
            self.show_card({"card_id": "ambient_ensemble_offline", "text": "圆桌暂时没有保存成功，我先保留原来的 Agent。", "scenario": self.cfg.get("scenario", "score_improvement")})

    def select_persona(self, persona_id: str | None) -> None:
        if not persona_id:
            return
        try:
            result = self.client.set_persona(persona_id)
            self.current_persona = persona_id
            self.save_persona_choice(persona_id)
            self.close_persona_picker()
            preview = result.get("preview")
            if preview:
                self.show_card(preview)
            else:
                self.show_card({"card_id": "ambient_persona_changed", "text": "人设已切换。", "scenario": self.cfg.get("scenario", "score_improvement"), "persona_name": result.get("persona", {}).get("name", "")})
        except Exception:
            self.show_card({"card_id": "ambient_persona_offline", "text": "人设暂时没有保存成功，我先保留原来的说话方式。", "scenario": self.cfg.get("scenario", "score_improvement")})

    def open_reply_window(self) -> None:
        self.focus_conversation_bar()

    def close_reply_window(self) -> None:
        if self.reply_window is not None:
            try:
                self.reply_window.destroy()
            except tk.TclError:
                pass
        self.reply_window = None

    def submit_reply(self, _event=None) -> str:
        message = self.reply_entry.get().strip()
        if not message:
            return "break"
        source_card = self.card_id or "ambient_manual_dialogue"
        self.close_reply_window()
        try:
            result = self.client.reply(source_card, message, str(self.cfg.get("scenario", "score_improvement")), self.current_persona, self.current_ensemble)
            card = result.get("reply_card")
            if card:
                triage = card.get("triage") or {}
                if triage:
                    self.append_conversation("分诊", f"{triage.get('label','')} · 置信度 {triage.get('confidence','')}", "triage")
                for item in card.get("ensemble_messages") or []:
                    self.append_conversation(f"[{item.get('mark','Agent')}] {item.get('name','')}", item.get("text", ""), "agent")
                self.show_card(card)
            elif result.get("silence_until"):
                self.show_card({"card_id": "ambient_silence_ack", "text": "收到。我会安静 30 分钟。", "scenario": "score_improvement"})
        except Exception:
            self.show_card({"card_id": "ambient_reply_offline", "text": "这次回复没有送达。我先把弹幕收起，不继续打扰。", "scenario": "score_improvement"})
        return "break"

    def request_behavior_card(self) -> None:
        signals = self._signals_with_screen_context(str(self.cfg.get("scenario", "score_improvement")))
        signals["agent_id"] = self.current_persona
        signals["agent_ids"] = self.current_ensemble
        try:
            result = self.client.plan(signals, force=True)
            card = result.get("card")
            if card:
                self.show_card(card)
            else:
                self.show_card({"card_id": "ambient_behavior_quiet", "text": "当前行为还不足以触发提醒。我会继续安静观察。", "scenario": signals["scenario"]})
        except Exception:
            self.show_card({"card_id": "ambient_behavior_offline", "text": "行为上下文暂时没有送达 Tender。我不会继续打扰。", "scenario": signals["scenario"]})

    def request_manual_card(self) -> None:
        signals = self._signals_with_screen_context(str(self.cfg.get("scenario", "score_improvement")), explicit_need=True)
        signals["agent_id"] = self.current_persona
        signals["agent_ids"] = self.current_ensemble
        try:
            result = self.client.plan(signals, force=True)
            if result.get("card"):
                self.show_card(result["card"])
            else:
                self.show_card({"card_id": "ambient_manual_quiet", "text": "我现在没有合适的提醒。你可以继续手上的事。", "scenario": signals["scenario"]})
        except Exception:
            self.show_card({"card_id": "ambient_offline", "text": "Tender 服务暂时没有连上；我不会打扰你。", "scenario": signals["scenario"]})

    def poll(self) -> None:
        if self.demo_once:
            self.root.after(1000, self.poll)
            return
        signals = self._signals_with_screen_context(str(self.cfg.get("scenario", "gaokao_registration")))
        signals["agent_id"] = self.current_persona
        signals["agent_ids"] = self.current_ensemble
        try:
            result = self.client.plan(signals, force=False)
            if result.get("status") == "shown" and result.get("card"):
                self.show_card(result["card"])
        except (URLError, TimeoutError, OSError, KeyError, json.JSONDecodeError):
            pass
        self.root.after(max(2, int(self.cfg.get("poll_seconds", 8))) * 1000, self.poll)

    def exit(self) -> None:
        try:
            self.root.destroy()
        except tk.TclError:
            pass

    def run(self) -> None:
        self.root.mainloop()


def load_config() -> dict:
    defaults = {
        "api_base": "http://127.0.0.1:8080",
        "student_id": "S01",
        "role": "learner",
        "scenario": "gaokao_registration",
        "poll_seconds": 8,
        "card_seconds": 9,
        "position": "top_right",
        "top_margin": 110,
        "right_margin": 28,
        "alpha": 0.94,
        "show_hotkey_hint": True,
        "observe_window_title": True,
        "agent_id": "learning_strategist",
        "agent_ids": ["learning_strategist", "subject_expert", "neuro_cognition", "psychologist", "nutritionist", "career_advisor", "safety_officer", "metacognition_coach"],
        "danmaku_max_concurrent": 2,
        "danmaku_spawn_ms": 1200,
        "danmaku_speed": 5,
        "dock_width": 780,
        "dock_height": 54,
    }
    if CFG_PATH.exists():
        defaults.update(json.loads(CFG_PATH.read_text(encoding="utf-8")))
    return defaults


def main() -> None:
    ap = argparse.ArgumentParser(description="Tender true desktop overlay")
    ap.add_argument("--demo", action="store_true", help="立即显示一条启动提示")
    ap.add_argument("--demo-once", action="store_true", help="演示并在 12 秒后退出")
    ap.add_argument("--student", help="学生 ID，例如 S01 或 A01")
    ap.add_argument("--scenario", choices=["gaokao_registration", "score_improvement"], help="场景")
    ap.add_argument("--api-base", help="Tender API 地址")
    ap.add_argument("--card-seconds", type=float, help="弹幕显示时长，演示可设为 30")
    ap.add_argument("--position", choices=["top_right", "top_left", "top_center", "bottom_right"], help="弹幕位置")
    args = ap.parse_args()
    cfg = load_config()
    if args.student:
        cfg["student_id"] = args.student
    if args.scenario:
        cfg["scenario"] = args.scenario
    if args.api_base:
        cfg["api_base"] = args.api_base
    if args.card_seconds:
        cfg["card_seconds"] = args.card_seconds
    if args.position:
        cfg["position"] = args.position
    Overlay(cfg, demo=args.demo or args.demo_once, demo_once=args.demo_once).run()


if __name__ == "__main__":
    main()
