# Tender Deployment Options

Tender has a Python FastAPI backend, SQLite event storage, MCP services and a Windows desktop overlay. GitHub Pages can host the static teaching site and browser demo, but it cannot run the backend.

## 1. GitHub Codespaces: full backend, one click

Open:

<https://codespaces.new/MK60DN/Tender?quickstart=1>

The dev container installs the backend and starts FastAPI on forwarded port `8080`. Open the forwarded URL and use `/ui/login.html`. Codespaces needs a GitHub account; usage is subject to GitHub's free quota and billing rules.

This is the best option when the goal is to let a user test the real backend without configuring hosting.

## 2. Render Blueprint: public demo URL

Open:

<https://render.com/deploy?repo=https://github.com/MK60DN/Tender>

The included `render.yaml` creates one Docker web service on Render's free plan with mock LLM mode and a generated session secret. This is suitable for a product demo.

Important limits:

- Free instances may sleep and cold-start.
- Render's filesystem is ephemeral unless a persistent disk is added.
- SQLite data can reset after redeploy or instance replacement.
- Do not use the free demo for production learner records.
- Add a paid persistent disk or managed database before storing real data.

## 3. Local Docker

```bash
docker compose up --build
```

Open <http://127.0.0.1:8080/ui/login.html>.

## 4. Static GitHub Pages demo

<https://mk60dn.github.io/Tender/app/>

This version runs entirely in the browser and stores only local demo data in `localStorage`. It demonstrates login, world coordinates, assessment, account controls and the danmaku preview, but does not run FastAPI, DAOQL or server-side Agents.

## Production checklist

- Replace demo authentication with OIDC.
- Use a managed database with backups.
- Set a strong `TENDER_SESSION_SECRET`.
- Put the service behind HTTPS and a restricted CORS policy.
- Add retention, deletion and audit review procedures.
- Keep raw screenshots, media and full window text out of DAOQL.
