# Repository Guidelines

## Mission
This repository bootstraps and maintains a structured knowledge package for official n8n built-in nodes and the tooling needed to collect, normalize, validate, and publish that package.

Agents working here must:
- treat the official n8n documentation as the external source of truth
- treat `research/`, `specs/`, and scoped `AGENTS.md` files as the local source of truth
- treat `n8n_nodes_package_starter/` and the root `.docx` files as bootstrap evidence, not as final architecture
- verify unstable n8n documentation structure and taxonomy against the live official docs before freezing schema or collector behavior
- keep working autonomously unless blocked by credentials, destructive actions, or contradictory requirements
- finish work with validation evidence, not just file creation

## Project Shape
- This is not an Odoo repository unless future source material proves otherwise.
- The current evidence supports an n8n documentation-package project with a spec-first bootstrap phase.
- Until implementation begins, the authoritative planning surface lives in `research/` and `specs/`.

## Source Of Truth Order
1. live official n8n docs for current node taxonomy and page structure
2. `specs/`
3. `research/`
4. root `AGENTS.md` and any deeper `AGENTS.md`
5. bootstrap evidence in `n8n_nodes_package_starter/`
6. root `.docx` briefs

## Default Workflow
1. map the affected area and confirm whether the work is bootstrap, spec, tooling, or generated-package work
2. identify the governing spec, research note, and local rules before editing
3. synthesize missing requirements into an implementation-ready spec when needed
4. verify unstable technical facts with official n8n docs before encoding them in code or specs
5. implement in the smallest safe slice
6. run relevant checks or record exactly what remains unverified

## Quality Bar
- no merge-ready work with unresolved placeholders in governing specs
- no schema or collector behavior based on guessed doc structure
- no generated package changes without provenance and freshness metadata
- no node facts invented when the source is silent
- no "done" status without validation evidence or a clearly stated blocker

## Repository Conventions
- preserve source evidence unless the task explicitly authorizes replacing it
- keep extracted facts separate from normalized summaries and derived guidance
- prefer stable JSON contracts for machine use and Markdown for human review
- record contradictions explicitly instead of silently picking one artifact
- add subtree `AGENTS.md` only when local rules materially differ

## Browser Validation
- use browser proof when the repository gains a real browser surface such as a collector UI, preview UI, or published package browser
- for bootstrap-only documentation work, record browser validation as not yet applicable rather than fabricating UI evidence

## Git Rules
- use Conventional Commits
- prefer branches named `feat/<scope>`, `fix/<scope>`, `chore/<scope>`, `docs/<scope>`, or `refactor/<scope>`
- keep one logical change per commit
