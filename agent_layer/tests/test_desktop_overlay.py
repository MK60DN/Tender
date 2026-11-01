import importlib.util
from pathlib import Path


def test_desktop_overlay_config_and_signals():
    path = Path(__file__).resolve().parents[1] / 'desktop_overlay' / 'tender_overlay.py'
    spec = importlib.util.spec_from_file_location('tender_overlay_test', path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    cfg = mod.load_config()
    assert cfg['api_base'].startswith('http://')
    assert cfg['student_id']
    assert cfg['agent_id'] in {item['id'] for item in mod.AGENT_FALLBACK}
    assert len(cfg['agent_ids']) >= 1
    assert cfg['danmaku_max_concurrent'] == 2
    assert len(mod.AGENT_FALLBACK) >= 8
    sig = mod.WindowsSignals().signals('gaokao_registration')
    assert sig['scenario'] == 'gaokao_registration'
    assert sig['idle_seconds'] >= 0
    assert sig['visibility_switches'] >= 0
    assert sig['privacy_mode'] == 'local_normalized_behavior'
    assert sig['app_category'] in {'study','coding','document','video','chat','game','browser','unknown'}
    category, hint = mod.classify_behavior('高考报名 - 省教育考试院', 'chrome.exe')
    assert category == 'study' and hint == '高考报名'
    category, hint = mod.classify_behavior('语法填空讲义.pdf', 'Acrobat.exe')
    assert category == 'study' and hint == '语法填空'
    category, hint = mod.classify_behavior('哔哩哔哩 - 视频', 'chrome.exe')
    assert category == 'video'
    source = path.read_text(encoding='utf-8')
    assert 'WS_EX_TRANSPARENT' in source
    assert 'WS_EX_NOACTIVATE' in source
    assert 'clipboard' not in source.lower()
    assert 'def show_danmaku' in source
    assert 'def spawn_next_danmaku' in source
    assert 'conversation_panel' in source
    assert 'def append_conversation' in source
    assert 'from media_plugins import' in source
    assert 'def choose_media_file' in source
    assert '读界面 · 关' in source
    assert '-transparentcolor' in source


if __name__ == '__main__':
    test_desktop_overlay_config_and_signals()
    print('ok test_desktop_overlay_config_and_signals')
