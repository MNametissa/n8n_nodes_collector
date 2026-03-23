#!/usr/bin/env bash
set -euo pipefail

INSTALL_ROOT="${N8N_COLLECTOR_HOME:-$HOME/.local/share/n8n-nodes-collector}"
BIN_DIR="${N8N_COLLECTOR_BIN_DIR:-$HOME/.local/bin}"
BIN_PATH="${N8N_COLLECTOR_BIN_PATH:-$BIN_DIR/collector}"
VENV_COLLECTOR="$INSTALL_ROOT/venv/bin/collector"

if [[ -L "$BIN_PATH" ]] && [[ "$(readlink -f "$BIN_PATH")" == "$(readlink -f "$VENV_COLLECTOR" 2>/dev/null || true)" ]]; then
  rm -f "$BIN_PATH"
fi

if [[ -d "$INSTALL_ROOT" ]]; then
  rm -rf "$INSTALL_ROOT"
fi

echo "Uninstalled collector CLI"
echo "  removed root: $INSTALL_ROOT"
echo "  removed bin link if present: $BIN_PATH"
