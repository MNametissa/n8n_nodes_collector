# Implementation Plan

## Goal

Move from mixed bootstrap evidence to an implementation-ready repository that can later produce and maintain a trustworthy n8n nodes knowledge package.

## Phase 0: Bootstrap Governance

### Outcome

Create the local source-of-truth structure and document what is known, unknown, and currently recommended.

### Tasks

1. Create root governance in `AGENTS.md`.
2. Inventory evidence in `research/source_inventory.md`.
3. Capture unresolved questions in `research/open_questions.md`.
4. Compare candidate repo shapes in `research/architecture_candidates.md`.
5. Create the spec index and this implementation plan.

### Validation

- required bootstrap files exist
- the chosen source-of-truth order is explicit
- contradictions are documented

## Phase 1: Freeze The Canonical Data Contract

### Outcome

Choose the canonical schema contract for:

- package metadata
- `map.json`
- per-node `node.json`
- per-node `node.md`
- provenance ledger
- derived indexes

### Tasks

1. Decide whether `map.json` is an array plus separate manifest or a top-level object with metadata and entries.
2. Reconcile cluster-node fields across the schema brief and the starter samples.
3. Define required versus optional fields by family.
4. Decide the canonical language policy for generated text.
5. Write schema acceptance criteria and validation rules.

### Validation

- schema decisions documented in specs
- example fixtures updated or replaced to match the accepted contract
- unresolved schema disputes listed explicitly

## Phase 2: Define The Collection And Refresh Workflow

### Outcome

Specify how the repository discovers node pages, snapshots sources, extracts structured content, and handles change detection.

### Tasks

1. Define the source inventory process for official node URLs.
2. Define what raw source material is stored locally, if any.
3. Define parsing inputs and normalized outputs.
4. Define failure handling for parse errors, removed pages, and stale nodes.
5. Define refresh cadence and release policy.

### Validation

- collection workflow written as an executable spec
- provenance fields and freshness rules tied to the workflow
- failure states and recovery paths documented

## Phase 3: Choose The First Implementation Slice

### Option A: Package-first

- build validators and static fixtures around the accepted schema
- promote a small canonical package example into the repo root or a dedicated snapshot area

### Option B: Tooling-plus-snapshot

- add a collector/normalizer/validator structure
- generate the first canonical snapshot from official docs

### Selection Rule

Choose Option A if the immediate need is package consumption and schema stability.
Choose Option B if the immediate need is reproducible refreshes.

## Phase 4: Implement Validation And QA

### Minimum validation requirements

- JSON validity checks
- path integrity checks from map to node files
- family/folder consistency checks
- cluster root/sub consistency checks
- freshness metadata checks
- editorial consistency checks between `node.json` and `node.md`

### Browser-proof status

No browser QA target exists yet. If a UI is later introduced, add browser-level validation for lookup, preview, and error states.

## Current Risks

- Schema authority is split across multiple artifacts.
- Starter examples may be mistaken for canonical truth if left undocumented.
- The repo has no git history yet, so change discipline and release flow are not established.
- The final implementation language and tooling layout are still open.

## Done Definition For The Next Execution Step

The next execution step is complete when the canonical schema contract is frozen tightly enough that an engineer can build validators and/or a collector without guessing field semantics.
