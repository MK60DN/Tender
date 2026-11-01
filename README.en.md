# Tender

**A research-grade system connecting self, world, other minds and collaborative outcomes**

[English home](README.md) · [中文](README.zh-CN.md)

## Start here

- **One-click backend / 一键后端**：[GitHub Codespaces](https://codespaces.new/MK60DN/Tender?quickstart=1) · [Deploy to Render](https://render.com/deploy?repo=https://github.com/MK60DN/Tender) · [Deployment guide](docs/DEPLOYMENT.md)
- [Teaching website](https://mk60dn.github.io/Tender/) · [Local course](http://127.0.0.1:8080/guide/) · [Source](site/)
- [Whitepaper local PDF](http://127.0.0.1:8080/guide/assets/docs/Tender-Whitepaper-v2.2.pdf) · [Repo PDF](docs/whitepaper/Tender-Whitepaper-v2.2.pdf) · [Word](docs/whitepaper/Tender-Whitepaper-v2.2.docx) · [TeX](docs/whitepaper/Tender-Whitepaper-v2.2.tex)
- [Product manual local](http://127.0.0.1:8080/guide/assets/docs/Tender-Product-Manual-v7.2.pdf) · [Word](docs/product/Tender-Product-Manual-v7.2.docx) · [User guide local](http://127.0.0.1:8080/guide/assets/docs/Tender-User-Guide-v7.2.pdf) · [Word](docs/product/Tender-User-Guide-v7.2.docx) · [Teaching manual local](http://127.0.0.1:8080/guide/assets/docs/Tender-Teaching-Manual-v6.2.pdf)


> Tender starts by gently understanding your mind, then turns that understanding into action in the world, mentalizing in relationships, and confirmed commitments in groups. It separates objective events, language evidence, subjective experience and optional Agent support.

## Why Tender

- A single score arrives late and explains too little.
- Tender treats exams as periodic checks and behavior, language and outcomes as continuous evidence.
- The objective is not to grade a person, but to support the next viable action and preserve long-term evidence.

## Core layers

- **Three value loops**: self-understanding, action in the world, relational mentalizing and group outcomes.
- **Mentalization layer**: competing, reversible state hypotheses.
- **Language evidence layer**: source-grounded emotion, uncertainty, avoidance, help-seeking and mentalizing signals.
- **World tree**: DAOQL roots, Agent Bridge trunk, five experience branches, local state axes, flowering and outcomes; shared branches require explicit consent.
- **Knowledge forest**: 13 subjects, 1,075 K12 nodes, 875 majors, 319 course seeds and 1,016 occupations.
- **DAOQL event layer**: facts, provenance, causality, authorization and audit.
- **Three UI modes**: solo focus, multi-person group chat and ambient assistance, selected from one persistent three-part switch.
- **Agent system**: fixed helpers, advisors, orchestration, a multi-Agent command center, a redacted experimental-model API path and an expert-Agent marketplace MVP.

## Dual-chain group chat

Each member keeps a private self-model. Peer models belong to the observer and use only public interactions plus authorized summaries. Shared branches require every participant to approve, and Agents never auto-send to a group.

## Multimedia and screen context

Tender can process user-selected images, audio and video with local OCR, Whisper transcription, video-frame analysis and local speech synthesis. The desktop danmaku layer can also read currently visible windows only after scoped, revocable consent. Source repositories, licenses and privacy boundaries are documented in [Media Plugins](docs/MEDIA_PLUGINS.md) and [Screen Context MCP](docs/SCREEN_CONTEXT_MCP.md).
## Boundaries

Tender is not a diagnostic or mind-reading system. Language evidence does not determine mastery, personality or clinical state. Synthetic and benchmark results are not proof of real-world educational effect.

## Teaching site

The bilingual course is in `site/`. FastAPI serves it at `/guide/` and GitHub Pages deploys it from `.github/workflows/pages.yml`.

## Quick start

```bash
python -m venv .venv
# Windows
.venv\Scripts\Activate.ps1
# macOS / Linux
source .venv/bin/activate

pip install -r requirements-dev.txt
cd agent_layer
python -m uvicorn app.main:app --host 127.0.0.1 --port 8080
```

Open <http://127.0.0.1:8080/ui/login.html>. Complete the three steps (login, world coordinates, mentalizing assessment). The account menu can sign out, delete the current learner data or shut down Tender. After onboarding: <http://127.0.0.1:8080/ui/single.html> (solo), <http://127.0.0.1:8080/ui/multi.html> (multi-person), or <http://127.0.0.1:8080/ui/ambient.html> (ambient assistance).

## Tests

```bash
python agent_layer/tests/run_all.py
```

Expected baseline: `passed 136 tests`; full `pytest` currently has 139 passing and 1 opt-in heavy-media skip.

## Documentation

- [Whitepaper V2.2](docs/whitepaper/Tender-Whitepaper-v2.2.pdf)
- [Rhythm phase and periodicity experiment V1.0](docs/research/Tender-Rhythm-Phase-Experiment-v1.0.pdf)
- [Product manual](docs/product/Tender-Product-Manual-v7.2.pdf)
- [User guide](docs/product/Tender-User-Guide-v7.2.pdf)
- [Research boundaries](docs/RESEARCH_CLAIMS.md)

## License

PolyForm Noncommercial License 1.0.0. Commercial use is prohibited without separate written permission. This is source-available, not an OSI-approved open-source license.

