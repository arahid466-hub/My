#!/usr/bin/env bash
set -euo pipefail
ROOT="${AETHER_ROOT:-$HOME/aether-data}"
mkdir -p "$ROOT"/{models,uploads,generated/{images,audio,videos},jobs,cache,logs,projects}
python3 -m venv .venv 2>/dev/null || true
. .venv/bin/activate
pip install -r requirements.txt
python3 -m py_compile server/main.py engine/core.py workers/worker.py
printf 'Aether initialized at %s\nStart: ./aether start\n' "$ROOT"
