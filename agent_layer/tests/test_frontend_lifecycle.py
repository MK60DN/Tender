from pathlib import Path


STATIC = Path(__file__).resolve().parents[1] / "app" / "static"


def test_account_menu_exposes_logout_delete_and_shutdown():
    source = (STATIC / "account-menu.js").read_text(encoding="utf-8")
    assert "退出账号" in source
    assert "删除此学习者数据" in source
    assert "关闭 Tender 服务" in source
    assert "/learner/data/" in source
    assert "/system/shutdown" in source


def test_login_does_not_import_demo_roster():
    source = (STATIC / "login.js").read_text(encoding="utf-8")
    assert "/students" not in source
    assert "tender.accounts" in source
    assert "/ui/world-setup.html" in source


def test_world_setup_precedes_preassessment_and_is_visible_in_data_page():
    setup = (STATIC / "world-setup.html").read_text(encoding="utf-8")
    login = (STATIC / "login.js").read_text(encoding="utf-8")
    single = (STATIC / "single.js").read_text(encoding="utf-8")
    assessment = (STATIC / "preassessment.html").read_text(encoding="utf-8")
    assert "主要学习科目或能力领域" in setup
    assert "/ui/world-setup.html" in login
    assert "worldMapView" in single
    assert "你的客观世界坐标" in assessment
    assert "world_context" in assessment


def test_public_role_workspace_was_removed():
    assert not (STATIC / "index.html").exists()
    assert not (STATIC / "app.js").exists()
    single = (STATIC / "single.html").read_text(encoding="utf-8")
    assert 'href="/ui/"' not in single
    assert "完整工作台" not in single


def test_github_pages_app_and_one_click_backend_links_exist():
    root = Path(__file__).resolve().parents[2]
    site = root / "site"
    assert (site / "app" / "index.html").exists()
    assert (site / "app" / "app.js").exists()
    index = (site / "index.html").read_text(encoding="utf-8")
    demo = (site / "app" / "index.html").read_text(encoding="utf-8")
    assert 'href="app/"' in index
    assert "codespaces.new/MK60DN/Tender" in index
    assert "render.com/deploy?repo=https://github.com/MK60DN/Tender" in index
    assert "codespaces.new/MK60DN/Tender" in demo
    assert (root / "render.yaml").exists()
    assert (root / ".devcontainer" / "devcontainer.json").exists()
    assert (root / ".devcontainer" / "start-tender.sh").exists()
    dockerfile = (root / "Dockerfile").read_text(encoding="utf-8")
    assert "${PORT:-8080}" in dockerfile
