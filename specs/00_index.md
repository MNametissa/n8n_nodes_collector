# n8n Nodes Knowledge Package Bootstrap Spec

## Project Summary

This repository is being bootstrapped to produce a structured, versionable knowledge package for official n8n built-in nodes. The package must support both machine consumption and human review, with explicit provenance and freshness metadata.

## Source Of Truth

### Upstream

- Official n8n docs on `docs.n8n.io`

### Local

- `specs/` for accepted project direction
- `research/` for source analysis, contradictions, and open questions
- `n8n_nodes_package_starter/` as evidence and example material

## Functional Scope

### In scope for the project

- official built-in n8n nodes
- family-aware node discovery
- per-node machine-readable records
- per-node human-readable records
- package-level metadata, provenance, indexes, and coverage reporting
- AI-safe lookup and answering guidance

### Explicitly out of scope for v1

- community nodes
- marketplace nodes
- marketing/blog content as primary node records
- non-official sources used as canonical facts
- Odoo-specific addon or module work

## Technical Scope

The repository must eventually define:

- a canonical package schema for root metadata and per-node records
- a repeatable collection and normalization workflow sourced from official docs
- validation rules for structure, semantics, freshness, and cross-file consistency
- packaging guidance for versioned snapshots

The repository does not yet implement:

- the collector code
- the validator code
- the generated canonical package under `package/`

## Resolved Decisions

- The collector will be implemented as a Python CLI under `collector/`.
- The canonical generated package will live under `package/`.
- `package-manifest.json` remains separate from `map.json`.
- Canonical generated narrative content will be English-only.

## Governing Specs

- [schema_contract.md](/home/mnametissa/development/tools/N8N%20system/specs/schema_contract.md)
- [validation_rules.md](/home/mnametissa/development/tools/N8N%20system/specs/validation_rules.md)
- [collector_build_spec.md](/home/mnametissa/development/tools/N8N%20system/specs/collector_build_spec.md)
- [git_workflow.md](/home/mnametissa/development/tools/N8N%20system/specs/git_workflow.md)

## Evidence-Based Constraints

- Node facts must not be invented when source documentation is silent.
- Cluster root and cluster sub-node behavior must remain distinct.
- Provenance and verification dates must be tracked.
- The current evidence includes contradictions, so the bootstrap must not canonize starter sample values without review.

## Current Verified Facts

- The n8n integrations docs currently expose built-in node groupings for core nodes, actions, triggers, and cluster-node surfaces.
- Google Sheets exposes operation-specific sections plus common issues.
- AI Agent is a cluster root page and requires at least one connected tool sub-node.
- Schedule Trigger exposes detailed node parameter sections and common issues.

## Required Outputs

The completed project should ultimately maintain:

- package metadata
- canonical node map
- human-readable map
- taxonomy
- source provenance ledger
- coverage statistics
- derived indexes
- per-node `node.json`
- per-node `node.md`
- AI usage guide

## Acceptance Criteria For Bootstrap Phase

- Root governance exists in `AGENTS.md`.
- Research files inventory the evidence and contradictions.
- A recommended repository direction is chosen and justified.
- An ordered implementation plan exists.
- Official-doc verification has been recorded for unstable taxonomy assumptions.
- Browser-proof status is recorded as not applicable yet rather than fabricated.

## Validation Strategy For Bootstrap Phase

- confirm required bootstrap files exist
- confirm the chosen architecture is documented
- confirm contradictions are captured explicitly
- confirm the local source-of-truth order is written down
- confirm no Odoo-specific structure was created without evidence

## Browser-Proof Status

`browser-proof-runbook` was applied as an applicability check during bootstrap. There is currently no local browser surface, preview app, or UI flow in this repository, so browser reproduction and post-fix proof are deferred until a UI exists.
