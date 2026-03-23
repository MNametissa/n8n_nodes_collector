# Architecture Candidates

## Decision Context

The workspace currently contains evidence and a partial starter package, but no implementation tree, no collector code, and no repo-local source-of-truth docs. The bootstrap must choose the smallest justified architecture that preserves evidence without freezing the wrong implementation shape.

## Candidate A: Promote The Starter Package To Repository Root

### Shape

- Treat `n8n_nodes_package_starter/` as the initial project root shape.
- Add only missing docs around it.

### Advantages

- Fastest path to a visible package layout.
- Minimizes translation work from current evidence.

### Risks

- Bakes current starter inconsistencies into the canonical repo.
- Blurs evidence and source of truth.
- Leaves no clean place for future collector, validator, or refresh tooling.

### Verdict

Rejected for bootstrap governance. It is too easy to mistake sample data for the canonical architecture.

## Candidate B: Tooling-First Monorepo

### Shape

- `tools/collector/`
- `tools/normalizer/`
- `tools/validator/`
- `packages/knowledge/`
- `specs/`
- `research/`

### Advantages

- Clean long-term separation of tooling and generated output.
- Supports an eventual full rebuild pipeline.

### Risks

- Over-specifies implementation before collector requirements are stable.
- Adds empty directories with no evidence-backed contracts yet.

### Verdict

Too heavy for the current evidence set. Appropriate later, after the collector plan is settled.

## Candidate C: Spec-First Bootstrap With Evidence Preserved

### Shape

- keep `n8n_nodes_package_starter/` unchanged as evidence
- create `research/` for evidence interpretation
- create `specs/` for approved decisions and execution plan
- defer collector and generated-package root layout until after the first implementation spec is accepted

### Advantages

- Preserves the original starter intact.
- Makes contradictions explicit before code or schema churn begins.
- Creates a safe planning surface for choosing the real tooling and output layout.
- Minimizes premature structure.

### Risks

- The repo remains planning-heavy until the next implementation step.
- Consumers cannot yet treat the workspace root as a finished package.

### Verdict

Recommended. This is the smallest justified architecture that keeps the project honest.

## Recommended Direction

Adopt Candidate C now, then decide between these two implementation paths during the first execution phase:

1. Package-first implementation:
   - produce a canonical package snapshot at root
   - add lightweight validator scripts later

2. Tooling-plus-snapshot implementation:
   - keep specs and research at root
   - add collector/normalizer/validator tooling plus a generated package target

Choose between those two only after the schema contract and refresh workflow are stabilized.

## Selected Direction On 2026-03-23

The repository is now moving from bootstrap to implementation planning with a hybrid of Candidate C and Candidate B:

- keep `research/` and `specs/` at repo root as the planning source of truth
- preserve `n8n_nodes_package_starter/` as historical bootstrap evidence
- implement the collector as a Python CLI under `collector/`
- commit the latest canonical generated package under `package/`

This choice is justified because the schema contract is now being frozen and the user explicitly requested the exact collector build path before implementation starts.
