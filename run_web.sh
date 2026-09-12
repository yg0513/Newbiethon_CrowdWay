#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
  echo '먼저 python3 -m venv .venv && .venv/bin/pip install -r requirements.txt 를 실행하세요.' >&2
  exit 1
fi
if [ ! -f frontend/dist/index.html ]; then
  echo '먼저 npm --prefix frontend ci && npm --prefix frontend run build 를 실행하세요.' >&2
  exit 1
fi
# .env and shell settings remain authoritative; empty path downloads regional OSM graphs.
exec .venv/bin/python - <<'PY'
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv('.env')
import uvicorn
uvicorn.run('app.main:app', host='127.0.0.1', port=int(os.environ.get('PORT', '8000')))
PY
