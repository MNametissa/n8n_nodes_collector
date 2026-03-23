# Validation Rules

## Purpose

These rules define what the validator must reject before a package build is considered valid.

## Structural Validation

The validator must fail if:

- any required root file is missing from `package/`
- any JSON file fails to parse
- any `map.json` entry points to a missing `node.json` or `node.md`
- any duplicate `id`, `slug`, or `doc_url` appears in `map.json`
- any node file path does not match the declared family folder
- any required family subtree is missing once that family exists in the package

## Schema Validation

The validator must fail if:

- a required field is absent from `package-manifest.json`, `map.json`, `node.json`, `sources.json`, or `stats.json`
- an enum field contains an unsupported value
- a scalar field uses an array or object shape incorrectly
- a collection field is represented by placeholder strings instead of arrays

## Semantic Validation

The validator must fail if:

- `map.json.requires_credentials` does not equal `node.json.credentials.required`
- `execution_role` flags are not mutually consistent with `family`
- a `cluster_sub` node does not set `cluster.requires_parent = true`
- a `cluster_root` node does not set `cluster.root_or_sub = "root"`
- a non-cluster node sets cluster-specific compatibility fields inconsistently
- an `action` node is marked as a trigger
- a `trigger` node is marked as an action
- a node with `service = null` is clearly a service-specific app node
- `status` differs between `map.json` and `node.json`

## Source Fidelity Validation

The validator must fail if:

- a node `doc_url` has no matching `node_page` record in `sources.json`
- a source record has `status = parse_failed` for a primary node page but the node is still marked `active`
- `last_verified_at` is missing from a generated node record
- a node advertises `has_common_issues_page = true` but no supporting source or source section indicates common issues
- a node has non-empty `operations` but no operation-like source section was detected during extraction

## Editorial Validation

The validator must fail if:

- `node.md` contradicts `node.json` on family, credentials, status, or related nodes
- `node.md` omits the required section structure
- `map.md` count summaries disagree with `stats.json`

## Coverage Validation

The validator must fail if:

- `stats.json.nodes_total` differs from the count of `map.json` entries
- `stats.json.by_family` differs from the actual family counts
- `with_credentials_required`, `with_operations_listed`, or `with_agent_guidance` differ from values derived from `node.json`
- `package-manifest.json.node_count` differs from `stats.json.nodes_total`

## Freshness Validation

The validator must fail if:

- `build_date`, `documentation_snapshot_date`, or `last_verified_at` are invalid dates
- a date is in the future relative to the build machine date
- `documentation_snapshot_date` is newer than `build_date`

## Sorting And Determinism

The validator must fail if:

- `map.json` entries are not sorted by `id`
- index arrays are not sorted lexicographically
- JSON output formatting differs from the repository standard

## Manual Audit Checks

The monthly audit must manually confirm at least:

- one action node
- one trigger node
- one core node
- one cluster root node
- one cluster sub-node

If a family is not yet present in the generated package, the audit records that as a coverage gap rather than passing silently.
