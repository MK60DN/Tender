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


def test_education_site_publishes_reproducible_evidence_and_failure_boundaries():
    root = Path(__file__).resolve().parents[2]
    index = (root / "site" / "index.html").read_text(encoding="utf-8")
    app = (root / "site" / "assets" / "app.js").read_text(encoding="utf-8")

    for value in ("+6.3 pp", "95.3%", "0.9919", "273,364", "95% CI"):
        assert value in index
    for value in ("WHAT DID NOT WIN", "Tender did not beat logistic", "尚无真人随机对照实验"):
        assert value in index
    for value in ("No randomized human trial yet", "universal superiority", "help humanity evolve"):
        assert value in app
    assert "帮助人类演化" in index


def test_living_whitepaper_has_publication_and_edit_paths():
    root = Path(__file__).resolve().parents[2]
    page = (root / "site" / "whitepaper.html").read_text(encoding="utf-8")
    markdown = root / "docs" / "whitepaper" / "Tender-DAOQL-Data-Water-Whitepaper-v1.0.md"
    collab = root / "docs" / "COLLABORATION.md"
    issue = root / ".github" / "ISSUE_TEMPLATE" / "whitepaper_feedback.yml"

    assert markdown.exists()
    assert collab.exists()
    assert issue.exists()
    assert (root / "site" / "assets" / "docs" / "Tender-DAOQL-Data-Water-Whitepaper-v1.0.pdf").exists()
    assert "在 GitHub 编辑" in page
    assert "/edit/main/docs/whitepaper/Tender-DAOQL-Data-Water-Whitepaper-v1.0.md" in page
    assert "whitepaper_feedback.yml" in page


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
