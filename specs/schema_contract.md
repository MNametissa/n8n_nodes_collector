# Canonical Schema Contract

## Decisions

1. `package-manifest.json` is the only package-metadata file.
2. `map.json` is a pure JSON array of node-entry objects. It does not repeat package metadata.
3. The canonical generated package lives under `package/`.
4. Canonical generated narrative content is English-only.
5. The collector is deterministic and LLM-free in v1. If source evidence is insufficient, fields stay empty rather than guessed.

## Canonical Package Layout

```
package/
  README.md
  SKILLS.md
  package-manifest.json
  map.json
  map.md
  taxonomy.json
  sources.json
  stats.json
  indexes/
    by-name.json
    by-category.json
    by-type.json
    by-service.json
    by-tag.json
    by-capability.json
    by-doc-url.json
  nodes/
    core/
    actions/
    triggers/
    cluster/
      root/
      sub/
  auxiliary/
    aliases.json
    crosswalks.json
    credential-only-nodes.json
    deprecated-or-versioned-notes.json
```

## Package Manifest

`package/package-manifest.json`

```json
{
  "package_name": "n8n-nodes-knowledge",
  "package_version": "0.1.0",
  "schema_version": "1.0.0",
  "source_vendor": "n8n",
  "source_base": "https://docs.n8n.io/",
  "build_date": "YYYY-MM-DD",
  "documentation_snapshot_date": "YYYY-MM-DD",
  "coverage_status": "partial",
  "language": "en",
  "default_formats": ["markdown", "json"],
  "taxonomy_version": "1.0.0",
  "node_count": 0,
  "included_families": ["core", "action", "trigger", "cluster_root", "cluster_sub"],
  "notes": ""
}
```

Rules:

- `package_version` uses SemVer.
- `coverage_status` enum: `starter_partial`, `partial`, `complete`, `stale_pending_review`.
- `documentation_snapshot_date` is the newest upstream-doc collection date represented by the build.

## Map Index

`package/map.json`

Top-level type: `MapEntry[]`

```json
{
  "id": "n8n.action.google-sheets",
  "slug": "google-sheets",
  "display_name": "Google Sheets",
  "family": "action",
  "category_path": ["actions", "google-sheets"],
  "service": "Google Sheets",
  "doc_url": "https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googlesheets/",
  "file_md": "nodes/actions/google-sheets/node.md",
  "file_json": "nodes/actions/google-sheets/node.json",
  "tags": ["google", "spreadsheet", "rows"],
  "capabilities": ["read sheet", "append row", "update row"],
  "related_nodes": ["n8n.core.http-request"],
  "requires_credentials": true,
  "supports_tools_connector": false,
  "has_common_issues_page": true,
  "has_templates_section": true,
  "status": "active"
}
```

Rules:

- `family` enum: `core`, `action`, `trigger`, `cluster_root`, `cluster_sub`.
- `service` is `null` only for generic non-service nodes.
- `status` enum: `active`, `deprecated`, `unknown`, `stale_pending_review`.
- `requires_credentials` must match `node.json.credentials.required`.
- `file_md` and `file_json` are always package-relative paths.

## Node Record

`package/nodes/.../node.json`

```json
{
  "id": "n8n.action.google-sheets",
  "slug": "google-sheets",
  "display_name": "Google Sheets",
  "display_name_short": "Google Sheets",
  "doc_title": "Google Sheets node",
  "family": "action",
  "service": "Google Sheets",
  "category_path": ["actions", "google-sheets"],
  "doc_url": "https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googlesheets/",
  "source_type": "official_docs",
  "summary": "",
  "description": "",
  "why_use_it": "",
  "when_to_use": [],
  "when_not_to_use": [],
  "credentials": {
    "required": true,
    "credential_refs": [],
    "notes": ""
  },
  "operations": [],
  "resource_groups": [],
  "node_parameters": [],
  "inputs": [],
  "outputs": [],
  "execution_role": {
    "is_trigger": false,
    "is_action": true,
    "is_core": false,
    "is_cluster_root": false,
    "is_cluster_sub": false
  },
  "cluster": {
    "root_or_sub": null,
    "compatible_with": [],
    "compatible_parents": [],
    "requires_parent": false,
    "requires_subnodes": false,
    "tool_connector": false,
    "functional_group": null
  },
  "templates_examples": [],
  "related_resources": [],
  "common_issues": [],
  "unsupported_ops_guidance": "",
  "version_notes": [],
  "tags": [],
  "capabilities": [],
  "limitations": [],
  "gotchas": [],
  "agent_guidance": {
    "selection_rules": [],
    "disambiguation": [],
    "prompt_hints": [],
    "retrieval_keywords": []
  },
  "related_nodes": [],
  "source_sections_present": [],
  "last_verified_at": "YYYY-MM-DD",
  "status": "active"
}
```

Rules:

- Use empty arrays for collection fields and `null` only for scalar absence.
- `source_type` is `official_docs` in v1.
- `last_verified_at` is required for generated node records.
- `status` enum matches `map.json`.
- `credentials.required` means the node surface itself requires credentials. It does not mean connected downstream nodes may require credentials.
- `AI Agent` root nodes therefore use `credentials.required = false` unless official docs change.

## Required Fields By Family

### Action

- `operations`
- `resource_groups`
- `credentials`

### Trigger

- `node_parameters`
- trigger-specific execution role

### Core

- `node_parameters`
- a generic or null `service`

### Cluster Root

- `cluster.root_or_sub = "root"`
- `cluster.requires_subnodes`
- `cluster.compatible_with`

### Cluster Sub

- `cluster.root_or_sub = "sub"`
- `cluster.requires_parent = true`
- `cluster.compatible_parents`
- `cluster.functional_group`

## Slug And ID Rules

- `slug` default: lowercase kebab-case slugified from `display_name`.
- `id` format:
  - `n8n.action.<slug>`
  - `n8n.trigger.<slug>`
  - `n8n.core.<slug>`
  - `n8n.cluster-root.<slug>`
  - `n8n.cluster-sub.<slug>`
- If a display name changes, keep the canonical slug stable through `auxiliary/crosswalks.json` rather than rewriting historical IDs blindly.

## Node Markdown Contract

Each `node.md` must follow this section order:

1. Identity
2. Summary
3. When To Use
4. When Not To Use
5. Credentials
6. Operations Or Parameters
7. Inputs And Outputs
8. Common Issues
9. Limitations And Gotchas
10. Related Nodes
11. AI Guidance
12. Source

`node.md` may clarify wording, but it must not add facts not present in source evidence or `node.json`.

## Sources Ledger

`package/sources.json`

Top-level type: `SourceRecord[]`

```json
{
  "url": "https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googlesheets/",
  "node_id": "n8n.action.google-sheets",
  "title": "Google Sheets node",
  "type": "node_page",
  "family_hint": "action",
  "collected_at": "YYYY-MM-DD",
  "http_status": 200,
  "content_hash": "sha256:...",
  "status": "parsed",
  "notes": ""
}
```

Rules:

- `type` enum: `index`, `node_page`, `supporting_page`, `concept_page`.
- `status` enum: `discovered`, `fetched`, `parsed`, `parse_failed`, `stale_pending_review`.
- Every `node.json.doc_url` must have a matching `node_page` record here.

## Stats Contract

`package/stats.json`

```json
{
  "nodes_total": 0,
  "by_family": {},
  "with_credentials_required": 0,
  "with_operations_listed": 0,
  "with_agent_guidance": 0,
  "coverage_status": "partial"
}
```

Rules:

- all counts are derived from canonical node records, never handwritten
- `coverage_status` must match `package-manifest.json.coverage_status`

## Index Contracts

All files under `package/indexes/` are JSON objects whose values are sorted arrays of node IDs, except `by-doc-url.json`, whose values are single node IDs.

- `by-name.json`: normalized display name -> node IDs
- `by-category.json`: family or category bucket -> node IDs
- `by-type.json`: execution type bucket -> node IDs
- `by-service.json`: service name -> node IDs
- `by-tag.json`: tag -> node IDs
- `by-capability.json`: capability phrase -> node IDs
- `by-doc-url.json`: doc URL -> node ID
