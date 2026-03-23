# Open Questions

## Critical Questions

1. Is the first deliverable only the documentation package, or does v1 also include a collector/normalizer toolchain that can rebuild the package from live docs?
2. Should the eventual canonical package live at repository root, or should the repo contain both tooling and generated snapshots in separate top-level areas?
3. Should `map.json` remain split from package metadata, or should it be promoted to the richer top-level object proposed in `02_Schemas_map_json_node_json_examples.docx`?
4. What is the intended canonical language mix for generated content: English only, French plus English, or source-faithful mixed output?
5. Are templates and examples stored only as references, or will the project later snapshot template metadata as first-class structured records?

## Important Questions

1. Should `updated_SKILLS_md_content.docx` be treated as an optional extended guide, or should its enterprise workflow guidance be folded into the final `SKILLS.md`?
2. Should cluster-node compatibility be modeled minimally at first, or should v1 require explicit parent/sub-node compatibility matrices?
3. Will the project eventually ingest only official docs HTML, or also related official supporting pages such as common-issues pages and advanced AI concept pages?
4. Should `node.md` follow a strict section template checked by automation, or only a recommended narrative structure?
5. Should aliases and deprecated-node crosswalks be curated manually, generated, or both?

## Bootstrap Assumptions Used Now

These assumptions are used for the current bootstrap so work can proceed safely:

- The repository is being set up for a documentation package project, not an Odoo project.
- The starter package is evidence and example material, not the final repo shape.
- The local source of truth should be spec-first and separate from generated artifacts.
- The collector/tooling shape is not frozen yet, so the bootstrap should create planning surfaces rather than implementation folders.
- Browser-proof validation is not yet applicable because there is no local browser surface in the workspace.

## Resolved Enough For Bootstrap

- Upstream authority: official n8n docs.
- Core scope: official built-in nodes only.
- Primary artifact model: stable machine-readable JSON plus human-readable Markdown.
- Minimum planning surfaces required now: research inventory, open questions, architecture comparison, spec index, implementation plan.

## Resolved On 2026-03-23

1. The repository will contain both the collector toolchain and a committed latest generated package snapshot.
2. The canonical generated package will live under `package/`, while planning docs remain under `research/` and `specs/`.
3. `package-manifest.json` remains the sole package-metadata file. `map.json` is a pure node-entry index and will not duplicate manifest metadata.
4. Canonical generated narrative content will be English-only. French remains acceptable for repo planning docs and evidence notes.
5. Templates and examples stay as referenced metadata in v1. They are not first-class template records yet.
