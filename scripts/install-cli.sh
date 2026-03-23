#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
COLLECTOR_DIR="$REPO_ROOT/collector"

INSTALL_ROOT="${N8N_COLLECTOR_HOME:-$HOME/.local/share/n8n-nodes-collector}"
BIN_DIR="${N8N_COLLECTOR_BIN_DIR:-$HOME/.local/bin}"
BIN_PATH="${N8N_COLLECTOR_BIN_PATH:-$BIN_DIR/collector}"
PYTHON_BIN="${N8N_COLLECTOR_PYTHON:-python3}"
VENV_DIR="$INSTALL_ROOT/venv"

mkdir -p "$INSTALL_ROOT" "$BIN_DIR"

if [[ ! -x "$PYTHON_BIN" ]] && ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Python interpreter not found: $PYTHON_BIN" >&2
  exit 1
fi

if [[ ! -d "$VENV_DIR" ]]; then
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

"$VENV_DIR/bin/python" -m pip install --upgrade pip >/dev/null
"$VENV_DIR/bin/python" -m pip install -e "$COLLECTOR_DIR"
ln -sfn "$VENV_DIR/bin/collector" "$BIN_PATH"

echo "Installed collector CLI"
echo "  package: $COLLECTOR_DIR"
echo "  venv: $VENV_DIR"
echo "  bin: $BIN_PATH"
