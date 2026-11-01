# Tender Media Plugins

Tender 把图片、音频和视频能力做成独立插件。它们默认只处理用户亲手选择的文件，不上传、不扫描目录、不启动摄像头或麦克风，也不把原文写入 DAOQL。

## 已接入

| 插件 | 能力 | 实现 | 来源 | 许可证 |
| --- | --- | --- | --- | --- |
| 本地 OCR | 中文/英文图片文字、截图、讲义、试卷 | RapidOCR + ONNX Runtime | [RapidAI/RapidOCR](https://github.com/RapidAI/RapidOCR) | Apache-2.0 |
| 视觉模型适配器 | 图像问答、图表和界面理解 | OpenAI-compatible Vision API | [QwenLM/Qwen3-VL](https://github.com/QwenLM/Qwen3-VL) | Apache-2.0 |
| 本地语音转写 | 音频文字、时间段字幕、语言检测 | faster-whisper + CTranslate2 | [SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper) | MIT |
| 本地视频理解 | 关键帧 OCR、音轨转写、时长与分辨率 | OpenCV + ffmpeg | [opencv/opencv](https://github.com/opencv/opencv) | Apache-2.0 |
| 媒体解码 | 音轨提取与格式转换 | imageio-ffmpeg / FFmpeg | [imageio/imageio-ffmpeg](https://github.com/imageio/imageio-ffmpeg) | BSD-2-Clause |
| 本地语音播报 | 短句 WAV 生成 | Windows SAPI5 / pyttsx3 | [nateshmbhat/pyttsx3](https://github.com/nateshmbhat/pyttsx3) | MPL-2.0 |

`opencv/opencv` 的完整发行许可 `Apache-2.0`。FFmpeg 的实际分发义务取决于构建选项，本仓库使用 `imageio-ffmpeg` 提供的二进制，不修改其源码。

## 在弹幕里使用

桌面弹幕底部新增 `媒体`：

1. 点击后选择一个图片、音频或视频。
2. 图片进入本地 OCR。
3. 音频进入本地 Whisper 转写。
4. 视频抽取最多 6 个关键帧做 OCR，并默认转写音轨。
5. 结果显示在弹幕和本机对话面板中。
6. 原始文件与识别文本不写入 DAOQL。

视频中的音轨转写默认使用 `tiny` 模型，启动快但中文准确率有限。需要更高质量时设置：

```powershell
$env:TENDER_WHISPER_MODEL = "small"
```

第一次使用某个模型会从 Hugging Face 下载模型文件。

## MCP 工具

`.mcp.json` 已增加 `tender-media-tools`：

- `list_media_plugins`
- `analyze_image`
- `transcribe_audio`
- `analyze_video`
- `speak_text`
- `list_voices`

所有文件工具都要求 `acknowledge_local_processing=true`，调用方必须先确认用户选择了这个文件。

## 视觉模型配置

视觉理解不绑定模型厂商，使用 OpenAI-compatible 接口：

```powershell
$env:TENDER_VISION_BASE_URL = "http://127.0.0.1:11434/v1"
$env:TENDER_VISION_MODEL = "qwen3-vl:8b"
$env:TENDER_VISION_API_KEY = ""
```

`image` 模式为本地 OCR，不上传；`vision` 模式会把用户选择的图片发送到上述已配置提供方。调用前必须明确告知用户。

## 隐私边界

- 不自动打开文件选择器。
- 不扫描整个磁盘或目录。
- 不读取未选择文件。
- 不自动播放语音。
- 不自动上传媒体。
- 不将媒体原文写入 DAOQL。
- 视觉模式可能上传用户选择的一张图片，因此必须单独告知并确认。

## 测试

```powershell
python -m pytest agent_layer/tests/test_media_plugins.py agent_layer/tests/test_media_plugins_mcp.py -q
```

# Optional heavier ASR smoke test
$env:TENDER_RUN_HEAVY_MEDIA_TESTS = "1"
python -m pytest agent_layer/tests/test_media_plugins.py -q
