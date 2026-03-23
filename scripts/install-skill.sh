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

require_safe_target() {
  local target="$1"
  local expected="$2"
  if [[ -e "$target" && ! -L "$target" ]]; then
    echo "Refusing to replace non-symlink target: $target" >&2
    exit 1
  fi
  if [[ -L "$target" ]]; then
    local resolved_target
    resolved_target="$(readlink -f "$target")"
    local resolved_expected
    resolved_expected="$(readlink -f "$expected")"
    if [[ "$resolved_target" != "$resolved_expected" ]]; then
      echo "Refusing to replace symlink with different target: $target -> $resolved_target" >&2
      exit 1
    fi
  fi
}

mkdir -p "$CODEX_SKILLS_DIR" "$CLAUDE_SHARED_SKILLS_DIR" "$CLAUDE_SKILLS_DIR"

require_safe_target "$CODEX_TARGET" "$SKILL_DIR"
require_safe_target "$CLAUDE_SHARED_TARGET" "$CLAUDE_SOURCE"
require_safe_target "$CLAUDE_TARGET" "$CLAUDE_SHARED_TARGET"

ln -sfn "$SKILL_DIR" "$CODEX_TARGET"
ln -sfn "$CLAUDE_SOURCE" "$CLAUDE_SHARED_TARGET"
ln -sfn "$CLAUDE_SHARED_TARGET" "$CLAUDE_TARGET"

echo "Installed skill '$SKILL_NAME'"
echo "  Codex: $CODEX_TARGET"
echo "  Claude shared: $CLAUDE_SHARED_TARGET"
echo "  Claude local: $CLAUDE_TARGET"
