#!/usr/bin/env bash
# Auto-bootstrap and launch the Universal Downloader GUI (Linux/macOS).
# Safe to run from anywhere; creates the venv if it doesn't exist.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$SCRIPT_DIR/.venv"
PY="$VENV/bin/python"

if [[ ! -x "$PY" ]]; then
  echo "[run] Creating virtual environment..."
  python3 -m venv "$VENV"
fi

if "$PY" -c "import downloader.app.main" 2>/dev/null; then
  :
else
  echo "[run] Installing dependencies (first run, this may take a while)..."
  "$PY" -m pip install --upgrade pip
  "$PY" -m pip install -e ".[dev]"
fi

exec "$PY" -m downloader.app.main "$@"
