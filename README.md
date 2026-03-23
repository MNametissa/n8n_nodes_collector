# n8n Nodes Collector

This repository builds and operates a structured knowledge package for official n8n built-in nodes.

It has two jobs:

1. collect and normalize official n8n node documentation into a machine-usable package
2. help an AI agent or human operator choose the right node quickly, with specialized nodes preferred over generic fallbacks

The current system is not a speculative bootstrap anymore. It contains a working Python CLI, a generated package layout, validation, audits, routing metadata, and an installable skill for Codex and Claude Code.

## What This Tool Does

The collector turns the official n8n docs into a repository-local package with:
- `package-manifest.json` for freshness, scope, and coverage
- `map.json` for canonical node lookup
- `indexes/*` for fast retrieval
- `auxiliary/aliases.json` and `auxiliary/crosswalks.json` for routing and fallback behavior
- `nodes/**/node.json` as the canonical machine-readable record
- `nodes/**/node.md` as the human-readable companion
- `SKILLS.md` as a routing and usage guide for agents

On top of that, the CLI can resolve free-form requests like:
- `odoo erp api`
- `spreadsheet append row`
- `schedule workflow every hour`
- `connect openrouter for ai classification and sorting`

The intended outcome is faster, more reliable n8n workflow design with less generic guessing and fewer bad node choices.

## Current Role

This repository is the source of truth for:
- the collector implementation under [collector/](/home/mnametissa/development/tools/N8N%20system/collector)
- the generated package under [package/](/home/mnametissa/development/tools/N8N%20system/package)
- the governing specs under [specs/](/home/mnametissa/development/tools/N8N%20system/specs)
- the research notes under [research/](/home/mnametissa/development/tools/N8N%20system/research)
- the reusable routing skill under [skills/n8n-workflow-router](/home/mnametissa/development/tools/N8N%20system/skills/n8n-workflow-router)

The upstream factual source remains the official n8n docs.

## Repository Layout

```text
collector/                     Python CLI and test suite
package/                       Rendered knowledge package
research/                      Evidence, open questions, architecture notes
scripts/                       Bootstrap installers for CLI and skill
skills/n8n-workflow-router/    Codex + Claude Code routing skill
specs/                         Schema, validation, collector, and workflow specs
n8n_nodes_package_starter/     Bootstrap evidence, not the final architecture
```

## Source Of Truth Order

1. official n8n docs for live taxonomy and page structure
2. `specs/`
3. `research/`
4. repo `AGENTS.md`
5. `n8n_nodes_package_starter/`
6. root `.docx` bootstrap briefs

## Main Capabilities

The CLI currently supports:
- `discover`
- `discover-live`
- `fetch`
- `extract`
- `normalize`
- `render`
- `validate`
- `build`
- `build-report`
- `build-live`
- `refresh`
- `audit-package`
- `resolve`
- `install-skill`
- `uninstall-skill`
- `self-uninstall`

The live pipeline supports:
- official-doc navigation discovery
- bounded concurrent fetch with default concurrency `24`
- progress bars and aggregate live progress
- progressive `map` and index updates during `build-live`
- readiness audits for package quality

The routing layer supports:
- specialized-first ranking
- service-first lookup
- tag and capability lookup
- alias expansion
- crosswalk-driven generic fallback penalties
- AI task-root and model-sub-node retrieval

## Install

### CLI bootstrap install

Install the CLI into a dedicated virtual environment and expose `collector` in `~/.local/bin`:

```bash
./scripts/install-cli.sh
```

Default paths:
- install root: `~/.local/share/n8n-nodes-collector`
- venv: `~/.local/share/n8n-nodes-collector/venv`
- executable symlink: `~/.local/bin/collector`

Uninstall it:

```bash
./scripts/uninstall-cli.sh
```

After installation, you do not need the external skill scripts anymore for day-to-day skill management because the CLI exposes native commands.

### Skill install

Install the repository-aligned routing skill into Codex and Claude Code:

```bash
collector install-skill
```

Remove it:

```bash
collector uninstall-skill
```

Installed targets:
- Codex: `~/.codex/skills/n8n-workflow-router`
- Claude shared: `~/.claude-shared/skills/n8n-workflow-router.md`
- Claude local: `~/.claude/skills/n8n-workflow-router.md`

### CLI self-uninstall

If the CLI was installed through the dedicated collector install root, remove it from the installed environment with:

```bash
collector self-uninstall
```

## Typical Workflows

### 1. Build a live package

```bash
collector build-live \
  --output-dir package \
  --reports-dir .cache/n8n-nodes/reports \
  --cache-dir .cache/n8n-nodes/raw \
  --fetch-concurrency 24
```

### 2. Validate the package

```bash
collector validate package
collector audit-package package --output /tmp/n8n-audit.json
```

### 3. Resolve nodes for workflow work

```bash
collector resolve package "odoo erp api" --limit 3
collector resolve package "spreadsheet append row" --limit 3
collector resolve package "schedule workflow every hour" --limit 3
collector resolve package "connect openrouter for ai classification and sorting" --limit 5
```

### 4. Refresh an existing package

```bash
collector refresh --mode daily --input-dir collector/tests/fixtures/discovery
collector refresh --mode monthly --package-dir package
```

## Routing Policy

The system is intentionally opinionated:
- exact service mention first
- specialized app node first
- `HTTP Request` only as fallback
- trigger vs action kept distinct
- `cluster_root` vs `cluster_sub` kept distinct
- AI requests should resolve to a task root plus a compatible model sub-node when appropriate

Examples:
- Odoo request: prefer the Odoo node before `HTTP Request`
- classification request with OpenRouter: prefer `Text Classifier` plus `OpenRouter Chat Model`
- generic API call only when no specialized node fits

## Validation And Quality Status

What is already proven in this repository:
- the collector pipeline runs end-to-end
- the package structure validates
- the live discovery path works against official docs
- the routing layer can resolve specialized nodes over generic fallbacks
- install/uninstall flows exist for the CLI and the routing skill
- the Codex/Claude skill is aligned with the actual package and resolver behavior

The latest local validation baseline before this README update included:
- `51` passing tests in `collector/tests`
- a passing live discovery test against the official n8n docs

This makes the tool usable and credible. It does not mean every possible workflow intent is perfectly benchmarked yet. The remaining quality frontier is broader routing evaluation over larger real-world intent sets.

## Documentation Map

Start here depending on what you need:
- repository rules: [AGENTS.md](/home/mnametissa/development/tools/N8N%20system/AGENTS.md)
- collector usage: [collector/README.md](/home/mnametissa/development/tools/N8N%20system/collector/README.md)
- project index: [specs/00_index.md](/home/mnametissa/development/tools/N8N%20system/specs/00_index.md)
- collector contract: [specs/collector_build_spec.md](/home/mnametissa/development/tools/N8N%20system/specs/collector_build_spec.md)
- schema contract: [specs/schema_contract.md](/home/mnametissa/development/tools/N8N%20system/specs/schema_contract.md)
- validation rules: [specs/validation_rules.md](/home/mnametissa/development/tools/N8N%20system/specs/validation_rules.md)
- routing skill: [skills/n8n-workflow-router/SKILL.md](/home/mnametissa/development/tools/N8N%20system/skills/n8n-workflow-router/SKILL.md)

## Git Workflow

Use:
- `main` as the stable line
- short-lived feature branches from `main`
- Conventional Commits

The repo conventions are recorded in [specs/git_workflow.md](/home/mnametissa/development/tools/N8N%20system/specs/git_workflow.md).
