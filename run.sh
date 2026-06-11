#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$SCRIPT_DIR/.venv"

if [[ ! -d "$VENV" ]]; then
  echo "Virtual environment not found. Run 'make install' first." >&2
  exit 1
fi

export SIMRACING_DEVICE_IP="${SIMRACING_DEVICE_IP:-${1:-}}"

exec "$VENV/bin/python" -m simracing.main # --debug
