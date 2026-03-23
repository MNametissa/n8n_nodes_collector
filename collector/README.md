# Collector CLI

This directory contains the Python CLI that discovers, fetches, extracts, normalizes, renders, validates, audits, and resolves the n8n nodes knowledge package.

## Install

Install the CLI into a dedicated local virtual environment and expose `collector` in `~/.local/bin`:

```bash
./scripts/install-cli.sh
```

The installer defaults to:
- virtual environment: `~/.local/share/n8n-nodes-collector/venv`
- binary symlink: `~/.local/bin/collector`

For test or custom installs, override with environment variables:
- `N8N_COLLECTOR_HOME`
- `N8N_COLLECTOR_BIN_DIR`
- `N8N_COLLECTOR_BIN_PATH`
- `N8N_COLLECTOR_PYTHON`

## Uninstall

```bash
./scripts/uninstall-cli.sh
```

## Install the routing skill

Install the repository-aligned routing skill into Codex and Claude Code:

```bash
./scripts/install-skill.sh
collector install-skill
```

Uninstall it:

```bash
./scripts/uninstall-skill.sh
collector uninstall-skill
```

The skill is installed into:
- Codex: `~/.codex/skills/n8n-workflow-router`
- Claude shared: `~/.claude-shared/skills/n8n-workflow-router.md`
- Claude local: `~/.claude/skills/n8n-workflow-router.md`

## Useful commands

```bash
collector build-live --output-dir package --reports-dir .cache/n8n-nodes/reports --cache-dir .cache/n8n-nodes/raw --fetch-concurrency 24
collector validate package
collector audit-package package --output /tmp/n8n-audit.json
collector install-skill
collector uninstall-skill
collector self-uninstall
collector resolve package "odoo erp api" --limit 3
collector resolve package "connect openrouter for ai classification and sorting" --limit 5
```
