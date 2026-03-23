# SKILLS.md

## Purpose

This package is a structured knowledge base for official n8n nodes. It is designed for AI agents that need to identify, compare, explain, and recommend n8n nodes.

The package is optimized for:
- lookup by node name or alias
- retrieval by category or capability
- node comparison
- workflow design assistance
- safe answering without inventing unsupported operations

## Scope

This package targets official n8n nodes documented in the official n8n documentation.
It is not a guarantee of full ecosystem coverage unless the package manifest explicitly says coverage is complete.

## Canonical lookup order

When answering a question:

1. Read `package-manifest.json` to understand snapshot scope.
2. Read `map.json` to resolve candidate nodes.
3. Open the target `node.json` file for canonical structured data.
4. Use `node.md` only when narrative explanation or richer prose is needed.
5. Use `taxonomy.json` for category and type reasoning.
6. Use `indexes/*` for bulk discovery tasks.
7. Use `auxiliary/*` for aliases, crosswalks, credential-only references, and edge cases.

## Node identity resolution

Resolve a node in this order:

1. exact `id`
2. exact `slug`
3. exact `display_name`
4. aliases
5. service + family match
6. capability match

If multiple nodes remain, disambiguate by:
- action vs trigger
- core vs app node
- cluster root vs cluster sub-node
- service-specific node vs `HTTP Request`

## Retrieval strategy

### If the user asks for a node by name
Search `map.json` first, then open the referenced `node.json`.

### If the user asks which node to use
Search by capability, then family, then service. Prefer specialized nodes over generic ones unless the package explicitly says a needed operation is unsupported.

### If the user asks for all nodes
Use `map.json` or `indexes/by-category.json`. Do not crawl the filesystem if an index already exists.

### If the user asks how to use a node
Prioritize these fields in `node.json`:
- `summary`
- `description`
- `why_use_it`
- `credentials`
- `operations`
- `node_parameters`
- `limitations`
- `gotchas`
- `agent_guidance`

### If the user asks about AI nodes
Check whether the node is:
- `cluster_root`
- `cluster_sub`
- an action node with optional tool behavior

Use cluster compatibility and parent requirements before answering.

## Response policy

When answering from this package:
- distinguish extracted facts from normalized summaries
- do not invent operations or parameters that are missing
- mention uncertainty when fields are empty or source coverage is partial
- prefer canonical names from `display_name`
- cite the internal file path if your environment supports it
- mention the official `doc_url` when useful

## Disambiguation policy

### Specialized node vs HTTP Request
Prefer the specialized node when it supports the requested use case.
Prefer `HTTP Request` when the package explicitly indicates that the specialized node does not expose the needed operation.

### Action vs Trigger
If the user wants to start a workflow from an event, prefer a trigger.
If the user wants to perform an operation inside an existing workflow, prefer an action.

### Cluster root vs sub-node
Root nodes orchestrate a higher-level AI flow.
Sub-nodes provide a connected capability such as tool, model, retriever, loader, or memory.

### Historical or replaced nodes
If version notes mention replacements or deprecated behavior, mention that explicitly.

## Safety and correctness

- Never claim package-wide completeness unless `coverage_status` says so.
- Never assume freshness beyond `documentation_snapshot_date`.
- Never promote a community node as official unless the package explicitly includes it.
- Never infer credential support if the source did not confirm it.

## Maintenance metadata interpretation

- `build_date` = when this package snapshot was built
- `documentation_snapshot_date` = when source docs were last collected
- `last_verified_at` = last verification of a specific node file
- `status` = active, partial, deprecated, or unknown

## Recommended answering style

For concise help:
1. identify the node
2. explain what it does
3. explain when to use it
4. mention key operations or parameters
5. mention limitations or gotchas
6. mention alternatives if relevant

For comparison:
1. compare family
2. compare trigger/action role
3. compare service scope
4. compare operations
5. compare limitations
6. recommend based on user intent
