# Collector Build Specification

## Decision

Build a deterministic Python collector that discovers official n8n built-in node pages, fetches raw HTML, extracts structured sections, normalizes them into the canonical schema, renders the package under `package/`, and validates the result.

This collector is the first implementation target.

## Why Python

- The only existing executable artifact in the repository is Python.
- The work is document collection, HTML parsing, normalization, rendering, and validation, which fits Python well.
- A Python CLI minimizes setup overhead and supports deterministic fixture-based tests.

## Implementation Boundary

The collector is responsible for:

- discovering official built-in node pages
- fetching and caching raw source HTML
- extracting normalized sections from primary and supporting pages
- building `package/`
- validating the generated package

The collector is not responsible for:

- community-node ingestion
- browser automation
- LLM summarization
- a UI

## Chosen Repository Shape

```
collector/
  pyproject.toml
  src/
    n8n_nodes_collector/
      cli.py
      config.py
      models.py
      discovery.py
      fetch.py
      extract.py
      normalize.py
      render.py
      validate.py
      workflows.py
  tests/
package/
research/
specs/
n8n_nodes_package_starter/
```

## Runtime And Tooling

- Python `>=3.11`
- `httpx` for HTTP
- `beautifulsoup4` plus `lxml` for HTML parsing
- `pydantic` v2 for schema models
- `typer` for CLI
- `pytest` for tests
- `ruff` for lint and format

The collector should remain dependency-light. Do not add headless-browser tooling unless official docs become client-rendered in a way that blocks server-side parsing.

## Output Paths

- committed latest generated package: `package/`
- collector-local raw cache: `.cache/n8n-nodes/raw/`
- collector-local normalized intermediate cache: `.cache/n8n-nodes/intermediate/`

The `.cache/` tree is not committed.

## CLI Commands

### `collector discover`

Build a canonical URL inventory from official docs and write/update intermediate discovery records.

### `collector fetch`

Fetch discovered URLs, compute hashes, and refresh cached raw HTML.

### `collector extract`

Parse raw HTML into intermediate structured records.

### `collector build`

Run discovery, fetch, extract, normalize, render, and validate in one command.

### `collector validate`

Validate an existing `package/` tree without fetching.

### `collector refresh --mode daily|weekly|monthly`

Run the corresponding workflow policy from the update playbook.

## Discovery Algorithm

### Sources

Start from official built-in node discovery pages under `docs.n8n.io`:

- `https://docs.n8n.io/integrations/`
- built-in actions library pages
- built-in core-node library pages
- built-in trigger-node library pages
- built-in cluster root-node library pages
- built-in cluster sub-node library pages

### Rules

1. Only accept URLs under `https://docs.n8n.io/integrations/builtin/`.
2. Treat root node overview pages as primary `node_page` sources.
3. Treat operation pages, common-issues pages, and related supporting pages under a node section as `supporting_page` sources tied to the same node.
4. Deduplicate by canonical URL after redirects.
5. Family classification must come from library-page context, breadcrumbs, or page-section ancestry. Do not classify by URL path alone.

### Important Constraint

The collector must not infer `trigger` versus `core` from URL patterns alone. For example, the Schedule Trigger page lives under a `core-nodes` URL path even though its package family is `trigger`.

## Fetch Algorithm

For each discovered URL:

1. GET the page with a fixed user agent and timeout.
2. Record `http_status`.
3. Compute `sha256` of the normalized response body.
4. Write raw HTML to `.cache/n8n-nodes/raw/`.
5. Skip downstream rebuild work in daily mode if the hash is unchanged.

Retries:

- retry network failures and 5xx responses with bounded exponential backoff
- do not retry 4xx except 429

## Extraction Strategy

The collector is deterministic and heading-driven.

### Primary extraction targets

- page title
- description and summary paragraphs
- credentials
- operations
- resource groups
- node parameters
- inputs and outputs when stated
- templates and examples
- related resources
- common issues
- version notes
- cluster compatibility statements

### Extraction rules

1. Parse the main article content, not site chrome.
2. Identify sections by normalized heading text rather than CSS class names whenever possible.
3. Merge information from the primary node page plus same-node supporting pages.
4. Preserve extracted phrases before normalization in intermediate records.
5. Leave fields empty when source evidence is absent.

### Intermediate model

The extractor should write an internal intermediate record per node containing:

- `node_url`
- `display_name`
- `family_hint`
- `section_text` keyed by normalized section name
- `supporting_pages`
- `content_hashes`

This intermediate record is not a public package artifact, but it is required for validation and debugging.

## Normalization Rules

### Narrative language

- generated narrative fields are English-only
- official names remain exactly as published
- free-text summaries are templated or minimally normalized from extracted source

### Slugs and IDs

- derive `slug` from `display_name` using lowercase kebab-case
- derive `id` from the family-specific format in the schema contract
- keep slug stability via curated crosswalks if upstream titles change later

### Operations

- normalize operation labels to lowercase human-readable phrases
- preserve source ordering where possible
- do not invent unsupported operations

### Related nodes

- derive from explicit source links first
- use curated crosswalks second
- do not infer service-neighbor nodes as related without evidence

### Credentials

- `credentials.required` reflects the node itself, not optional connected children
- cluster root nodes such as AI Agent are not automatically credential-required

## Rendering Rules

The renderer writes:

- `package/nodes/.../node.json`
- `package/nodes/.../node.md`
- `package/map.json`
- `package/map.md`
- `package/package-manifest.json`
- `package/sources.json`
- `package/stats.json`
- `package/indexes/*`
- `package/auxiliary/*`

JSON files are pretty-printed with deterministic key ordering and a trailing newline.

## Validation Gate

`collector build` is not successful unless `collector validate` passes.

Validation must run:

1. schema validation
2. structural validation
3. semantic validation
4. coverage and stats validation
5. editorial validation

## Test Plan

### Unit tests

- slug and ID generation
- family classification
- heading normalization
- stats derivation
- index generation

### Fixture tests

Use frozen HTML fixtures for at least:

- Google Sheets
- AI Agent
- Schedule Trigger

Each fixture test asserts expected `node.json` output and key `map.json` fields.

### End-to-end test

Build a tiny fixture package from cached HTML and assert:

- package tree exists
- all JSON parses
- validator passes

## Daily, Weekly, Monthly Workflows

### Daily

- fetch known URLs
- compare hashes
- rebuild only changed nodes
- regenerate package summaries

### Weekly

- rediscover URLs from official library pages
- detect added and removed nodes
- rebuild the whole package

### Monthly

- run validator
- run manual audit sample
- review cluster-node taxonomy drift

## First Implementation Slices

1. Create Python package scaffolding and CLI entrypoint.
2. Implement discovery with fixture tests.
3. Implement fetch/cache layer.
4. Implement extraction for the three known fixture nodes.
5. Implement normalization and rendering.
6. Implement validator.
7. Promote the first generated snapshot into `package/`.
