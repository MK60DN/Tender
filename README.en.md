# Tender

**A research-grade lifelong learning and mentalization system**

[English home](README.md) · [中文](README.zh-CN.md)

> Tender learns, with explicit authorization, from behavior, language and real outcomes to form revisable hypotheses about attention, cognitive load, motivation and friction. It separates objective events, language evidence, subjective experience and optional Agent support.

## Why Tender

- A single score arrives late and explains too little.
- Tender treats exams as periodic checks and behavior, language and outcomes as continuous evidence.
- The objective is not to grade a person, but to support the next viable action and preserve long-term evidence.

## Core layers

- **Mentalization layer**: competing, reversible state hypotheses.
- **Language evidence layer**: source-grounded emotion, uncertainty, avoidance, help-seeking and mentalizing signals.
- **Knowledge forest**: 13 subjects, 1,075 K12 nodes, 875 majors, 319 course seeds and 1,016 occupations.
- **DAOQL event layer**: facts, provenance, causality, authorization and audit.
- **Agent system**: fixed helpers, advisors, orchestration and an expert-Agent marketplace MVP.

## Boundaries

Tender is not a diagnostic or mind-reading system. Language evidence does not determine mastery, personality or clinical state. Synthetic and benchmark results are not proof of real-world educational effect.

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

Expected baseline: `passed 93 tests`.

## Documentation

- [Whitepaper V1.5](docs/whitepaper/Tender-Whitepaper-v1.5.pdf)
- [Product manual](docs/product/Tender-Product-Manual-v6.19.pdf)
- [User guide](docs/product/Tender-User-Guide-v6.7.pdf)
- [Research boundaries](docs/RESEARCH_CLAIMS.md)

## License

PolyForm Noncommercial License 1.0.0. Commercial use is prohibited without separate written permission. This is source-available, not an OSI-approved open-source license.
