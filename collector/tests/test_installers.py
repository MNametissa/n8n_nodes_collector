from __future__ import annotations

import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def run_script(script_name: str, tmp_path: Path) -> subprocess.CompletedProcess[str]:
    home = tmp_path / "home"
    env = os.environ.copy()
    env.update(
        {
            "HOME": str(home),
            "N8N_COLLECTOR_HOME": str(home / ".local" / "share" / "n8n-nodes-collector"),
            "N8N_COLLECTOR_BIN_DIR": str(home / ".local" / "bin"),
            "N8N_COLLECTOR_BIN_PATH": str(home / ".local" / "bin" / "collector"),
            "CODEX_SKILLS_DIR": str(home / ".codex" / "skills"),
            "CLAUDE_SHARED_SKILLS_DIR": str(home / ".claude-shared" / "skills"),
            "CLAUDE_SKILLS_DIR": str(home / ".claude" / "skills"),
        }
    )
    return subprocess.run(
        [str(REPO_ROOT / "scripts" / script_name)],
        check=True,
        capture_output=True,
        text=True,
        env=env,
        cwd=REPO_ROOT,
    )


def test_install_and_uninstall_cli_scripts(tmp_path: Path) -> None:
    install = run_script("install-cli.sh", tmp_path)
    assert "Installed collector CLI" in install.stdout

    binary = tmp_path / "home" / ".local" / "bin" / "collector"
    assert binary.exists()

    help_result = subprocess.run(
        [str(binary), "--help"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "Collector for the n8n nodes knowledge package." in help_result.stdout

    uninstall = run_script("uninstall-cli.sh", tmp_path)
    assert "Uninstalled collector CLI" in uninstall.stdout
    assert not binary.exists()


def test_install_and_uninstall_skill_scripts(tmp_path: Path) -> None:
    install = run_script("install-skill.sh", tmp_path)
    assert "Installed skill 'n8n-workflow-router'" in install.stdout

    codex_skill = tmp_path / "home" / ".codex" / "skills" / "n8n-workflow-router"
    claude_shared_skill = tmp_path / "home" / ".claude-shared" / "skills" / "n8n-workflow-router.md"
    claude_skill = tmp_path / "home" / ".claude" / "skills" / "n8n-workflow-router.md"

    assert codex_skill.is_symlink()
    assert (codex_skill / "SKILL.md").exists()
    assert claude_shared_skill.is_symlink()
    assert claude_skill.is_symlink()

    uninstall = run_script("uninstall-skill.sh", tmp_path)
    assert "Uninstalled skill 'n8n-workflow-router'" in uninstall.stdout
    assert not codex_skill.exists()
    assert not claude_shared_skill.exists()
    assert not claude_skill.exists()
