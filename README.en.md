# Tender

**A research-grade system connecting self, world, other minds and collaborative outcomes**

[English home](README.md) · [中文](README.zh-CN.md)

## Start here

- [Teaching website](https://mk60dn.github.io/Tender/) · [Local course](http://127.0.0.1:8080/guide/) · [Source](site/)
- [Whitepaper local PDF](http://127.0.0.1:8080/guide/assets/docs/Tender-Whitepaper-v2.1.pdf) · [Repo PDF](docs/whitepaper/Tender-Whitepaper-v2.1.pdf) · [Word](docs/whitepaper/Tender-Whitepaper-v2.1.docx) · [TeX](docs/whitepaper/Tender-Whitepaper-v2.1.tex)
- [Product manual local](http://127.0.0.1:8080/guide/assets/docs/Tender-Product-Manual-v7.1.pdf) · [User guide local](http://127.0.0.1:8080/guide/assets/docs/Tender-User-Guide-v7.1.pdf) · [Teaching manual local](http://127.0.0.1:8080/guide/assets/docs/Tender-Teaching-Manual-v6.1.pdf)


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
- **Agent system**: fixed helpers, advisors, orchestration and an expert-Agent marketplace MVP.

## Dual-chain group chat

Each member keeps a private self-model. Peer models belong to the observer and use only public interactions plus authorized summaries. Shared branches require every participant to approve, and Agents never auto-send to a group.

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

Open <http://127.0.0.1:8080/ui/>.

## Tests

```bash
python agent_layer/tests/run_all.py
```

Expected baseline: `passed 114 tests`.

## Documentation

- [Whitepaper V2.1](docs/whitepaper/Tender-Whitepaper-v2.1.pdf)
- [Rhythm phase and periodicity experiment V1.0](docs/research/Tender-Rhythm-Phase-Experiment-v1.0.pdf)
- [Product manual](docs/product/Tender-Product-Manual-v7.1.pdf)
- [User guide](docs/product/Tender-User-Guide-v7.1.pdf)
- [Research boundaries](docs/RESEARCH_CLAIMS.md)

## License

PolyForm Noncommercial License 1.0.0. Commercial use is prohibited without separate written permission. This is source-available, not an OSI-approved open-source license.



