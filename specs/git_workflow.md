# Git Workflow

## Branching Model

This repository uses trunk-based development.

- default branch: `main`
- short-lived work branches only
- release branches are created only when release stabilization becomes necessary

## Branch Naming

- `feature/<scope>-<short-name>`
- `fix/<scope>-<short-name>`
- `chore/<scope>-<short-name>`
- `docs/<scope>-<short-name>`
- `release/<version>`

Examples:

- `docs/schema-contract`
- `feature/collector-discovery`
- `fix/cluster-family-classifier`

## Commit Convention

Use Conventional Commits.

Allowed prefixes:

- `feat:`
- `fix:`
- `docs:`
- `chore:`
- `refactor:`
- `test:`

Examples:

- `docs: freeze canonical schema contract`
- `feat: add collector discovery command`
- `test: add schedule trigger fixture coverage`

## Pull Request Checklist

Every PR must include:

- summary of change
- testing notes
- risk assessment
- linked issue or explicit note that no issue exists

Default merge strategy:

- squash merge for short-lived branches
- merge commit only for long-lived release branches

## Versioning

- use SemVer for `package/package-manifest.json.package_version`
- maintain a root `CHANGELOG.md`
- release tags use `v<version>`

## Pre-Merge Validation

Before merge:

1. run collector or validator commands relevant to the change
2. update specs if schema or workflow changed
3. update `CHANGELOG.md` when behavior or delivered output changed

## Initial Repository State

This repository was initialized on `main` on 2026-03-23 during the bootstrap-to-spec-freeze phase.
