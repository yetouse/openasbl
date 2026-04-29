#!/usr/bin/env bash
set -euo pipefail

export OPENASBL_RUNTIME_MODE="${OPENASBL_RUNTIME_MODE:-desktop}"
export OPENASBL_DATA_DIR="${OPENASBL_DATA_DIR:-$HOME/.openasbl}"
OPENASBL_PORT="${OPENASBL_PORT:-8765}"

if [ -f "$(dirname "$0")/../venv/bin/python" ]; then
    PYTHON="$(dirname "$0")/../venv/bin/python"
else
    PYTHON="python3"
fi

cd "$(dirname "$0")/.."

"$PYTHON" manage.py migrate --noinput
exec "$PYTHON" manage.py runserver "127.0.0.1:${OPENASBL_PORT}"
