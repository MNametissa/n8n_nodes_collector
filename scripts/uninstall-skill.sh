#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SKILL_NAME="n8n-workflow-router"
SKILL_DIR="$REPO_ROOT/skills/$SKILL_NAME"
CLAUDE_SOURCE="$SKILL_DIR/claude.md"

CODEX_SKILLS_DIR="${CODEX_SKILLS_DIR:-$HOME/.codex/skills}"
CLAUDE_SHARED_SKILLS_DIR="${CLAUDE_SHARED_SKILLS_DIR:-$HOME/.claude-shared/skills}"
CLAUDE_SKILLS_DIR="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"

CODEX_TARGET="$CODEX_SKILLS_DIR/$SKILL_NAME"
CLAUDE_SHARED_TARGET="$CLAUDE_SHARED_SKILLS_DIR/$SKILL_NAME.md"
CLAUDE_TARGET="$CLAUDE_SKILLS_DIR/$SKILL_NAME.md"

remove_if_linked_to() {
  local target="$1"
  local expected="$2"
  if [[ -L "$target" ]] && [[ "$(readlink -f "$target")" == "$(readlink -f "$expected")" ]]; then
    rm -f "$target"
  fi
}

remove_if_linked_to "$CLAUDE_TARGET" "$CLAUDE_SHARED_TARGET"
remove_if_linked_to "$CLAUDE_SHARED_TARGET" "$CLAUDE_SOURCE"
remove_if_linked_to "$CODEX_TARGET" "$SKILL_DIR"

echo "Uninstalled skill '$SKILL_NAME' from Codex/Claude targets when linked to this repository"
