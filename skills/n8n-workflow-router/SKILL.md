---
name: n8n-workflow-router
description: Resolve the best n8n built-in node quickly from this repository's generated package, prefer specialized nodes over generic fallbacks, and compose production-grade workflows with the local collector and routing metadata.
---

# n8n Workflow Router

## Purpose

Use this skill whenever the task is to choose, compare, or sequence n8n built-in nodes using this repository's generated package.

The goal is speed and correctness:
- route to the right specialized node first
- avoid generic fallbacks until they are justified
- open only the smallest number of node records needed to answer

## Default package and commands

If the current repository is this project, the default rendered package is `package/`.

Use these commands directly:

```bash
collector resolve package "<query>" --limit 5 --expand-concurrency 8
collector validate package
collector audit-package package --output /tmp/n8n-audit.json
```

If freshness or completeness is suspect, rebuild or refresh before relying on the package:

```bash
collector build-live --output-dir package --reports-dir .cache/n8n-nodes/reports --cache-dir .cache/n8n-nodes/raw --fetch-concurrency 24
```

## Canonical lookup order

1. Check `package/package-manifest.json` for freshness and coverage.
2. Resolve candidates through `collector resolve` when available.
3. If you inspect files manually, start with `package/map.json`, `package/indexes/*`, and `package/auxiliary/*`.
4. Open only the selected `node.json` files for the top candidates.
5. Use `node.md` only for narrative explanation after `node.json` is already selected.

Never scan `package/nodes/**` blindly if `collector resolve`, `map.json`, `indexes/*`, `aliases.json`, or `crosswalks.json` can answer first.

## Routing policy

- Exact service mention wins first.
  Example: if the user says `Odoo`, resolve the Odoo node before considering `HTTP Request`.
- Specialized app nodes beat generic protocol nodes when they cover the requested operation.
- `HTTP Request` is a fallback, not the default answer.
- Trigger nodes start workflows. Action nodes perform work inside a workflow.
- Core nodes express workflow logic, transport, or generic execution.
- `cluster_root` nodes define AI task orchestration.
- `cluster_sub` nodes are supporting AI components such as models, vector stores, or tools. They are not standalone workflow roots.

## AI workflow composition rules

For AI requests, do not answer with a single flat node if the real solution is a composition.

Use this pattern:
- task root first: `Text Classifier`, `Basic LLM Chain`, `AI Agent`, `Information Extractor`
- model sub-node second: `OpenRouter Chat Model`, `OpenAI Chat Model`, or another compatible model
- add supporting nodes only if the task clearly needs them

Examples:
- `connect OpenRouter for AI classification`:
  - prefer `Text Classifier`
  - pair it with `OpenRouter Chat Model`
- `use AI instructions to transform text`:
  - prefer `Basic LLM Chain`
  - add a model sub-node
- `agent with tools and multi-step reasoning`:
  - prefer `AI Agent`
  - add a model sub-node and tools as needed

## Fast decision loop

1. Run `collector resolve package "<query>"`.
2. Keep the top 3 to 5 candidates.
3. Reject generic fallbacks if a specialized candidate clearly covers the task.
4. Open only the winning `node.json` files.
5. Answer with:
   - best-fit node or composed pair
   - why it wins
   - second-best alternative
   - fallback guidance only if needed

## High-signal fields to trust

Prefer these fields from each `node.json`:
- `id`
- `display_name`
- `family`
- `service`
- `summary`
- `operations`
- `node_parameters`
- `credentials_required`
- `capabilities`
- `related_nodes`
- `agent_guidance`

Treat these files as machine routing aids:
- `package/indexes/by-service.json`
- `package/indexes/by-tag.json`
- `package/indexes/by-capability.json`
- `package/auxiliary/aliases.json`
- `package/auxiliary/crosswalks.json`

## Hard constraints

- Do not invent unsupported operations, credentials, or compatibility.
- If the package lacks a required fact, say so and name the missing field.
- If the user asks for a workflow, prefer node combinations that match n8n execution semantics instead of raw API shortcuts.
- Keep the answer specialized-first, provenance-aware, and short.
