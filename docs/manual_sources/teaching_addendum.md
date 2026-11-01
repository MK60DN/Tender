# 教学手册 V6.2 增补章：界面上下文、多媒体插件与本地 MCP

## 组件关系

```text
Windows 桌面
  ├─ tender_overlay.py
  │    ├─ 读界面按钮 -> screen_context.py -> screen_context_mcp.py
  │    └─ 媒体按钮   -> media_plugins.py  -> media_plugins_mcp.py
  ├─ %LOCALAPPDATA%\Tender\screen-context\consent.json
  │    └─ 仅保存 token 哈希、scope、过期时间
  └─ 本机内存
       ├─ 可见窗口元数据与脱敏文字
       ├─ 截图 bytes
       └─ OCR / ASR / 视频关键帧结果
```

## 界面读取链路

1. `ConsentStore.grant()` 要求 `acknowledge=True` 和用户确认短语“我同意读取当前界面”；
2. token 使用随机值，磁盘只保存 SHA-256 哈希；
3. `enumerate_visible_windows()` 枚举当前桌面可见顶层窗口；
4. `extract_accessible_text()` 通过 Windows UI Automation 读取可见文字；
5. `redact_sensitive_text()` 在本机隐去密码、验证码、证件号、手机号、邮箱、卡号和 URL 参数；
6. `derive_safe_signals()` 只输出应用类别、窗口数量、任务关键词等派生信号；
7. `capture_authorized_screen()` 只有在单独授予 `screenshots` 时才截图。

## 媒体插件链路

| 层 | 文件 | 职责 |
|---|---|---|
| 核心 | `media_plugins.py` | OCR、ASR、视频抽帧、TTS、文件校验与插件目录 |
| 子进程 | `media_plugin_worker.py` | 隔离第三方运行时输出 |
| MCP | `media_plugins_mcp.py` | 对外提供图片、音频、视频、语音工具 |
| 桌面 UI | `tender_overlay.py` | 媒体按钮、文件选择、结果弹幕与本机对话面板 |

为什么使用子进程：RapidOCR、ONNX Runtime 和 faster-whisper 可能输出库级日志。如果这些日志混进 MCP 的 stdio 帧，会破坏协议。工作进程只返回 JSON 或 base64 音频。

## 安装与配置

```powershell
pip install -r requirements-desktop.txt
```

仓库根目录的 `.mcp.json` 同时启动两个本地 stdio 服务：

- `tender-screen-context`：界面授权、可见窗口与文字读取；
- `tender-media-tools`：本地 OCR、Whisper 转写、视频分析、视觉适配器和 TTS。

视觉适配器使用 OpenAI-compatible 接口。本地 OCR 不上传；只有配置视觉提供方并选择 `vision` 模式时，单张图片才可能发送到该提供方。

## 安全不变量

- 没有用户确认短语，授权必须失败；
- 过期 token 和撤销 token 必须失败；
- `windows` 权限不能自动获得 `accessible` 或 `screenshots`；
- 密码字段必须跳过，敏感字段必须脱敏；
- 截图不得写入磁盘或 DAOQL；
- 媒体工具必须要求 `acknowledge_local_processing=true`；
- 不支持的文件类型、空文件和超大文件必须拒绝；
- OCR 或转写结果不直接更新掌握度；
- 授权拒绝不得被解释成隐瞒、懒惰或心理问题。

## 验收

工程验收包括界面授权、过期、撤销、scope 分离、可见窗口枚举、媒体文件校验、MCP stdio 集成、图片 OCR、语音生成、视频关键帧 OCR 和项目全量回归。

已知限制：浏览器和 Electron 应用暴露的无障碍文字数量不一致；DRM 窗口截图可能为空；`tiny` Whisper 模型中文准确率有限；视觉理解依赖用户配置的模型提供方；本机速度取决于 CPU、内存和模型大小。

正确表述：Tender 在授权范围内读取有限界面与用户选择的媒体，不读取隐藏内容，不把原文写进长期事件库，也不把识别结果当成人的全部。
