# Tender Application

The application source is intentionally kept under `agent_layer/` so DAOQL,
Tender state models, language evidence, knowledge retrieval and Agent tests can
be inspected as separate layers.

## Run

```bash
pip install -r ../requirements-dev.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8080
```

From the repository root on Windows:

```powershell
.\agent_layer\run.ps1
```

## Test

```bash
python tests/run_all.py
```

See the repository root [README](../README.md), `ARCHITECTURE.md` and `API.md`.
