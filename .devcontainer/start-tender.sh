#!/usr/bin/env bash
set -euo pipefail
if python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health', timeout=1)" >/dev/null 2>&1; then
  echo "Tender backend is already running on port 8080."
  exit 0
fi
SECRET_FILE=/tmp/tender-session-secret
if [ ! -f "$SECRET_FILE" ]; then
  python -c "import secrets; print(secrets.token_hex(32))" > "$SECRET_FILE"
fi
cd "$(dirname "$0")/../agent_layer"
TENDER_SESSION_SECRET="$(cat "$SECRET_FILE")" \
TENDER_DEMO_MODE=1 \
TENDER_ALLOW_HEADER_IDENTITY=0 \
LLM_PROVIDER=mock \
nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 > /tmp/tender-backend.log 2>&1 &
echo "Tender backend started on forwarded port 8080. Log: /tmp/tender-backend.log"
