# Tender Screen Context MCP

Tender 的弹幕日常入口可以读取“用户此刻正在使用的其他软件”，但必须先得到用户明确授权。这个能力由本地 stdio MCP server 提供，不是网页后台偷读。

## 用户会看到什么

- 底部对话条新增 `读界面 · 关`。
- 点击后弹出授权框，说明读取范围与时长。
- 用户必须亲手勾选“我确认现在允许读取”，再点“允许 15 分钟”。
- 授权期间按钮显示剩余时间；再次点击立即停止。
- 快捷键 `Ctrl+Alt+I` 只负责打开授权框，不会自动授权。

## MCP 工具

启动命令由仓库根目录的 `.mcp.json` 配置。工具如下：

| Tool | 作用 | 权限 |
| --- | --- | --- |
| `grant_screen_context` | 建立短时授权 | 用户必须确认“我同意读取当前界面” |
| `screen_context_status` | 查看剩余时间与范围 | 已授权 token |
| `read_screen_context` | 返回可见窗口元数据与脱敏文字 | `windows`；文字另需 `accessible` |
| `capture_screen_context` | 返回当前所有显示器的内存截图 | 另需 `screenshots` |
| `revoke_screen_context` | 立即停止 | 已授权 token |

调用示例（MCP client 参数，不是网页 API）：

```json
{
  "student_id": "S01",
  "scopes": ["windows", "accessible"],
  "duration_minutes": 15,
  "acknowledge": true,
  "confirmation_text": "我同意读取当前界面"
}
```

截图必须单独授权：

```json
{
  "student_id": "S01",
  "scopes": ["windows", "screenshots"],
  "duration_minutes": 5,
  "acknowledge": true,
  "confirmation_text": "我同意读取当前界面"
}
```

## 读取边界

会读取：当前桌面所有可见顶层窗口、应用名、窗口标题、位置；授权 `accessible` 时读取 UI Automation 暴露的可见文字；单独授权 `screenshots` 时捕获所有显示器的合成截图。

不会读取：浏览器隐藏标签页、密码字段、剪贴板、摄像头、麦克风、键盘记录、受保护或 DRM 内容，以及其他用户账户的桌面。

受应用自身限制，部分 Electron、浏览器或 DRM 窗口能提供的无障碍文字很少；此时窗口元数据仍然可用，截图可能有效，也可能为空白。产品不会声称“任何界面都一定读得到”。

## 隐私设计

1. 授权状态只存随机 token 的 SHA-256 哈希、权限范围和到期时间。
2. 原始 token 只保存在调用方内存中；到期或撤销后失效。
3. 截图以内存 bytes 返回，不落盘。
4. 窗口原文与截图不会写入 DAOQL。
5. 密码、验证码、证件号、手机号、邮箱、卡号和 URL 参数会先在本机脱敏。
6. 弹幕规划只接收粗粒度信号：窗口数量、应用类别、任务关键词数量；不接收整段原文。
7. 用户点击停止后，下一次读取立即失败。

## 安装与运行

```powershell
pip install -r requirements-desktop.txt
```

桌面弹幕：

```powershell
powershell -ExecutionPolicy Bypass -File agent_layer/desktop_overlay/start_overlay.ps1
```

MCP 通过仓库根目录 `.mcp.json` 启动。启动器会优先使用 Codex 自带 Python，也可设置：

```powershell
$env:TENDER_PYTHON = "C:\path\to\python.exe"
```

直接诊断 MCP：

```powershell
python agent_layer/tests/run_all.py
python -m pytest agent_layer/tests/test_screen_context.py agent_layer/tests/test_screen_context_mcp.py -q
```
