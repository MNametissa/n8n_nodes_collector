# n8n Workflow Router

Use this skill when choosing or comparing n8n built-in nodes from this repository's generated package.

## Fast path

If the repository package already exists, start here:

```bash
collector resolve package "<query>" --limit 5 --expand-concurrency 8
```

If freshness is doubtful:

```bash
collector validate package
collector audit-package package --output /tmp/n8n-audit.json
collector build-live --output-dir package --reports-dir .cache/n8n-nodes/reports --cache-dir .cache/n8n-nodes/raw --fetch-concurrency 24
```

## Lookup order

1. `package/package-manifest.json`
2. `collector resolve`
3. `package/map.json`
4. `package/indexes/*`
5. `package/auxiliary/aliases.json` and `package/auxiliary/crosswalks.json`
6. selected `node.json`
7. `node.md` only for narrative explanation

Do not scan every node file when indexes or the resolver can answer first.

## Routing rules

- Exact service mention wins first.
- Specialized app nodes beat generic nodes when they cover the need.
- `HTTP Request` is fallback-only.
- Trigger nodes start workflows.
- Action nodes execute inside workflows.
- `cluster_root` nodes are AI task roots.
- `cluster_sub` nodes are supporting AI components and are not standalone roots.

## AI composition rules

For AI requests, return the right composition, not just a flat single node:

- task root first: `Text Classifier`, `Basic LLM Chain`, `AI Agent`, `Information Extractor`
- model second: `OpenRouter Chat Model`, `OpenAI Chat Model`, or another compatible model
- supporting nodes only when clearly required

Examples:
- `connect OpenRouter for AI classification`
  - prefer `Text Classifier`
  - pair it with `OpenRouter Chat Model`
- `use AI instructions to transform text`
  - prefer `Basic LLM Chain`
  - pair it with a model node
- `tool-using agent`
  - prefer `AI Agent`
  - pair it with a model node and tools

## Answer shape

Return:
- best-fit node or node pair
- why it fits
- second-best alternative
- fallback guidance only if the specialized route is insufficient

## Hard rules

- Do not invent operations, credentials, or compatibility.
- If a fact is missing, say which field is missing.
- Stay specialized-first and provenance-aware.
