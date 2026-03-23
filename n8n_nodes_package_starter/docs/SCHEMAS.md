# Schémas exacts

## map.json

Chaque entrée suit ce schéma minimal :

```json
{
  "id": "n8n.action.google-sheets",
  "slug": "google-sheets",
  "display_name": "Google Sheets",
  "family": "action",
  "category_path": ["actions", "google-sheets"],
  "service": "Google Sheets",
  "doc_url": "https://docs.n8n.io/...",
  "file_md": "nodes/actions/google-sheets/node.md",
  "file_json": "nodes/actions/google-sheets/node.json",
  "capabilities": ["read spreadsheet", "append rows"],
  "related_nodes": ["n8n.action.openai"],
  "requires_credentials": true,
  "supports_tools_connector": false,
  "has_common_issues_page": true,
  "has_templates_section": true,
  "status": "active"
}
```

## node.json

```json
{
  "id": "n8n.action.google-sheets",
  "slug": "google-sheets",
  "display_name": "Google Sheets",
  "doc_title": "Google Sheets",
  "family": "action",
  "service": "Google Sheets",
  "category_path": ["actions", "google-sheets"],
  "doc_url": "https://docs.n8n.io/...",
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
    "requires_parent": false,
    "tool_connector": false
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
  "confidence": {
    "extraction": "high",
    "normalization": "medium"
  },
  "last_verified_at": "",
  "status": "active"
}
```

## Nodes d'exemple inclus

- `nodes/actions/google-sheets/`
- `nodes/actions/openai/`
- `nodes/cluster/root/ai-agent/`
