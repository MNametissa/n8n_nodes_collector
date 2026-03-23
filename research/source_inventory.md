# Source Inventory

## Current State

The workspace is a bootstrap repository, not an established codebase. There is no local git repository yet and no existing local source-of-truth documentation tree. The main evidence consists of three briefing `.docx` files plus a partial starter package under `n8n_nodes_package_starter/`.

## Artifact Ranking

| Rank | Artifact | Type | Authority | Relevance | Notes |
| --- | --- | --- | --- | --- | --- |
| 1 | Official n8n docs on `docs.n8n.io` | External live source | High | High | Current taxonomy and page structure must be verified here before locking schemas or collector behavior. |
| 2 | `03_Complete_Specification_n8n_nodes_package.docx` | Product/spec brief | High | High | Most complete statement of project purpose, scope, taxonomy, required files, and acceptance criteria. |
| 3 | `02_Schemas_map_json_node_json_examples.docx` | Schema brief | High | High | Defines detailed `map.json` and `node.json` models plus worked examples, but some details conflict with the starter package. |
| 4 | `01_SKILLS_md_content.docx` | Usage contract brief | Medium-high | High | Useful for defining AI usage behavior and lookup order for the eventual package. |
| 5 | `n8n_nodes_package_starter/docs/SPECS.md` | Starter summary | Medium | High | Concise package summary aligned with the briefs. |
| 6 | `n8n_nodes_package_starter/docs/SCHEMAS.md` | Starter schema summary | Medium | High | Useful quick reference, but less complete than `02_...docx`. |
| 7 | `n8n_nodes_package_starter/SKILLS.md` | Starter operating guide | Medium | High | Better bounded than the enriched skills brief and closer to the package itself. |
| 8 | `n8n_nodes_package_starter/scripts/README.md` | Maintenance process | Medium | Medium-high | Strong evidence for future collector/update workflow. |
| 9 | `n8n_nodes_package_starter/scripts/update_playbook.md` | Maintenance process | Medium | Medium | Useful operational cadence and failure handling. |
| 10 | `updated_SKILLS_md_content.docx` | Expanded usage brief | Low-medium | Medium | Contains useful enterprise workflow ideas, but it blends package contract with general automation advice and includes noisy citation fragments. |
| 11 | Sample node files in `n8n_nodes_package_starter/nodes/` | Example implementation | Medium | Medium-high | Helpful examples, but not fully internally consistent with the higher-authority schema brief or official docs. |

## Extracted Evidence

### Confirmed project intent

- The project is a local, versionable knowledge package for official n8n built-in nodes.
- The package is intended for both human readers and AI agents.
- The package must support discovery, explanation, comparison, recommendation, and workflow-design assistance.
- Official n8n documentation is the authoritative upstream source.
- Community nodes are excluded by default.

### Confirmed package shape from local artifacts

- Root metadata files are expected: `README.md`, `SKILLS.md`, `package-manifest.json`, `map.json`, `map.md`, `taxonomy.json`, `sources.json`, `stats.json`.
- Derived indexes are expected under `indexes/`.
- Each node gets a stable directory with `node.json` and `node.md`.
- Auxiliary lookup files are expected under `auxiliary/`.

### Confirmed maintenance expectations

- The package is intended to support full refreshes and lighter incremental updates.
- Provenance and freshness metadata matter.
- Parsing failures should not silently delete previous node snapshots.

## Contradictions And Quality Issues

### Schema-level contradictions

- `02_Schemas_map_json_node_json_examples.docx` proposes `map.json` as a top-level object containing package metadata and an `entries` array.
- `n8n_nodes_package_starter/map.json` is only an array of entries.
- The starter `package-manifest.json` holds package metadata separately, which suggests the local starter currently uses split metadata rather than the proposed bundled `map.json` object.

### Sample-data contradictions

- `stats.json` says `with_credentials_required = 3`, but the schema brief's AI Agent example shows credentials are not inherently required at the root node level and depend on connected sub-nodes.
- The starter `AI Agent` sample sets `credentials.required` to `true`, which is at least questionable relative to the official docs and the schema brief.
- The starter samples do not fully implement all fields proposed in the richer schema brief, such as some cluster compatibility details.

### Scope drift

- `updated_SKILLS_md_content.docx` introduces enterprise automation advice, scale guidance, and workflow design principles that are useful as optional guidance but do not belong at the same authority level as the package contract itself.

## Official Doc Verification

The following live docs were checked on March 23, 2026:

- `https://docs.n8n.io/integrations/`
- `https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googlesheets/`
- `https://docs.n8n.io/integrations/builtin/cluster-nodes/root-nodes/n8n-nodes-langchain.agent/`
- `https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.scheduletrigger/`

Verified observations:

- The integrations index currently distinguishes built-in nodes and lists core nodes, actions, triggers, and cluster-node surfaces.
- The Google Sheets page exposes operation-specific sections and a common issues section.
- The AI Agent page explicitly identifies itself as a root node and states that at least one tool sub-node must be connected.
- The Schedule Trigger page exposes node-parameter sections, templates/examples, and common issues.

## Recommended Local Source Of Truth

Until implementation starts, use:

1. `specs/` for accepted project direction
2. `research/` for evidence, contradictions, and open questions
3. `n8n_nodes_package_starter/` as bootstrap evidence only
