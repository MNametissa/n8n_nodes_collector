"""Installer helpers for the collector CLI and agent skills."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

SKILL_NAME = "n8n-workflow-router"


def default_codex_skills_dir() -> Path:
    return Path(os.environ.get("CODEX_SKILLS_DIR", Path.home() / ".codex" / "skills"))


def default_claude_shared_skills_dir() -> Path:
    return Path(os.environ.get("CLAUDE_SHARED_SKILLS_DIR", Path.home() / ".claude-shared" / "skills"))


def default_claude_skills_dir() -> Path:
    return Path(os.environ.get("CLAUDE_SKILLS_DIR", Path.home() / ".claude" / "skills"))


def default_install_root() -> Path | None:
    explicit = os.environ.get("N8N_COLLECTOR_HOME")
    if explicit:
        return Path(explicit)
    executable = Path(sys.executable).resolve()
    if executable.parent.name == "bin" and executable.parent.parent.name == "venv":
        return executable.parent.parent.parent
    return None


def default_bin_path() -> Path:
    explicit = os.environ.get("N8N_COLLECTOR_BIN_PATH")
    if explicit:
        return Path(explicit)
    bin_dir = Path(os.environ.get("N8N_COLLECTOR_BIN_DIR", Path.home() / ".local" / "bin"))
    return bin_dir / "collector"


def repo_root_from_module() -> Path:
    return Path(__file__).resolve().parents[3]


def install_skill(
    *,
    codex_skills_dir: Path | None = None,
    claude_shared_skills_dir: Path | None = None,
    claude_skills_dir: Path | None = None,
) -> dict[str, Path]:
    repo_root = repo_root_from_module()
    skill_dir = repo_root / "skills" / SKILL_NAME
    claude_source = skill_dir / "claude.md"

    codex_dir = codex_skills_dir or default_codex_skills_dir()
    claude_shared_dir = claude_shared_skills_dir or default_claude_shared_skills_dir()
    claude_dir = claude_skills_dir or default_claude_skills_dir()

    codex_target = codex_dir / SKILL_NAME
    claude_shared_target = claude_shared_dir / f"{SKILL_NAME}.md"
    claude_target = claude_dir / f"{SKILL_NAME}.md"

    codex_dir.mkdir(parents=True, exist_ok=True)
    claude_shared_dir.mkdir(parents=True, exist_ok=True)
    claude_dir.mkdir(parents=True, exist_ok=True)

    ensure_safe_symlink_target(codex_target, skill_dir)
    ensure_safe_symlink_target(claude_shared_target, claude_source)
    ensure_safe_symlink_target(claude_target, claude_shared_target)

    recreate_symlink(codex_target, skill_dir)
    recreate_symlink(claude_shared_target, claude_source)
    recreate_symlink(claude_target, claude_shared_target)

    return {
        "codex": codex_target,
        "claude_shared": claude_shared_target,
        "claude_local": claude_target,
    }


def uninstall_skill(
    *,
    codex_skills_dir: Path | None = None,
    claude_shared_skills_dir: Path | None = None,
    claude_skills_dir: Path | None = None,
) -> dict[str, Path]:
    repo_root = repo_root_from_module()
    skill_dir = repo_root / "skills" / SKILL_NAME
    claude_source = skill_dir / "claude.md"

    codex_dir = codex_skills_dir or default_codex_skills_dir()
    claude_shared_dir = claude_shared_skills_dir or default_claude_shared_skills_dir()
    claude_dir = claude_skills_dir or default_claude_skills_dir()

    codex_target = codex_dir / SKILL_NAME
    claude_shared_target = claude_shared_dir / f"{SKILL_NAME}.md"
    claude_target = claude_dir / f"{SKILL_NAME}.md"

    remove_symlink_if_target_matches(claude_target, claude_shared_target)
    remove_symlink_if_target_matches(claude_shared_target, claude_source)
    remove_symlink_if_target_matches(codex_target, skill_dir)

    return {
        "codex": codex_target,
        "claude_shared": claude_shared_target,
        "claude_local": claude_target,
    }


def uninstall_cli(
    *,
    install_root: Path | None = None,
    bin_path: Path | None = None,
) -> dict[str, Path | None]:
    resolved_install_root = install_root or default_install_root()
    resolved_bin_path = bin_path or default_bin_path()

    if resolved_install_root is None:
        raise ValueError("Could not determine collector install root. Pass --install-root explicitly.")

    expected_binary = resolved_install_root / "venv" / "bin" / "collector"
    if not expected_binary.exists():
        raise ValueError(f"Refusing to uninstall from unexpected install root: {resolved_install_root}")

    remove_symlink_if_target_matches(resolved_bin_path, expected_binary)
    shutil.rmtree(resolved_install_root)
    return {
        "install_root": resolved_install_root,
        "bin_path": resolved_bin_path,
    }


def ensure_safe_symlink_target(target: Path, expected_source: Path) -> None:
    if target.exists() and not target.is_symlink():
        raise ValueError(f"Refusing to replace non-symlink target: {target}")
    if target.is_symlink() and target.resolve() != expected_source.resolve():
        raise ValueError(f"Refusing to replace symlink with different target: {target}")


def recreate_symlink(target: Path, source: Path) -> None:
    if target.is_symlink() or target.exists():
        target.unlink()
    target.symlink_to(source)


def remove_symlink_if_target_matches(target: Path, expected_source: Path) -> None:
    if target.is_symlink() and target.resolve() == expected_source.resolve():
        target.unlink()
