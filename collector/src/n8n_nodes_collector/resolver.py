"""Local package resolver for agent-facing node lookup and ranking."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

GENERIC_QUERY_TOKENS = {
    "ai",
    "connect",
    "connected",
    "connecter",
    "connexion",
    "instruction",
    "instructions",
    "ia",
    "n8n",
    "setup",
    "utilisation",
    "usage",
    "workflow",
    "workflows",
}
QUERY_INTENT_ALIASES = {
    "tri": ["classification", "classifier", "categorization", "sorting"],
    "sort": ["sorting", "classification", "classifier"],
    "sorting": ["sorting", "classification", "classifier"],
    "classify": ["classification", "classifier", "categorization"],
    "classification": ["classification", "classifier", "categorization"],
    "classifier": ["classification", "classifier", "categorization"],
    "instructions": ["prompting", "instructions", "prompt"],
    "instruction": ["prompting", "instructions", "prompt"],
    "openrouter": ["openrouter", "chat model", "llm provider"],
}


def resolve_package_query(
    package_dir: Path,
    query: str,
    *,
    family: str | None = None,
    limit: int = 5,
    expand_concurrency: int = 4,
) -> dict[str, Any]:
    """Resolve a free-form query against a rendered package."""

    package = load_package_indexes(package_dir)
    normalized_query = normalize_lookup_key(query)
    query_tokens = tokenize_query(normalized_query)
    expanded_tokens = expand_query_tokens(query_tokens)
    query_phrases = build_query_phrases(query_tokens)

    scores: dict[str, float] = defaultdict(float)
    reasons: dict[str, list[str]] = defaultdict(list)

    def add_matches(node_ids: list[str], score: float, reason: str) -> None:
        for node_id in node_ids:
            scores[node_id] += score
            reasons[node_id].append(reason)

    def lookup_exact_id() -> None:
        if normalized_query in package["by_id"]:
            add_matches([normalized_query], 1.0, "exact_id")

    def lookup_slug() -> None:
        for entry in package["entries"]:
            if entry["slug"] == normalized_query:
                add_matches([entry["id"]], 0.95, "exact_slug")

    def lookup_name() -> None:
        add_matches(package["by_name"].get(normalized_query, []), 0.92, "exact_display_name")

    def lookup_service() -> None:
        add_matches(package["by_service"].get(normalized_query, []), 0.94, "exact_service")

    def lookup_alias() -> None:
        add_matches(package["aliases"].get(normalized_query, []), 0.9, "alias_match")
        for token in expanded_tokens + query_phrases:
            add_matches(package["aliases"].get(token, []), 0.82, f"alias:{token}")

    def lookup_tags() -> None:
        for token in expanded_tokens + query_phrases:
            add_matches(package["by_tag"].get(token, []), 0.65, f"tag:{token}")

    def lookup_capabilities() -> None:
        for token in query_phrases:
            add_matches(package["by_capability"].get(token, []), 1.0, f"capability_phrase:{token}")
        for token in expanded_tokens:
            if len(token) < 4:
                continue
            for capability, node_ids in package["by_capability"].items():
                if re.search(rf"\b{re.escape(token)}\b", capability):
                    add_matches(node_ids, 0.2, f"capability:{token}")

    with ThreadPoolExecutor(max_workers=6) as executor:
        for lookup in (
            lookup_exact_id,
            lookup_slug,
            lookup_name,
            lookup_service,
            lookup_alias,
            lookup_tags,
            lookup_capabilities,
        ):
            executor.submit(lookup)

    for node_id, entry in package["by_id"].items():
        entry_family = entry["family"]
        if family:
            if entry_family == family:
                scores[node_id] += 0.08
                reasons[node_id].append("family_match")
            else:
                scores[node_id] -= 0.3
        if "trigger" in query_tokens and entry_family == "trigger":
            scores[node_id] += 0.08
            reasons[node_id].append("trigger_intent")
        if "action" in query_tokens and entry_family == "action":
            scores[node_id] += 0.08
            reasons[node_id].append("action_intent")
        overlap = name_token_overlap(entry, expanded_tokens)
        if overlap:
            scores[node_id] += 0.14 * overlap
            reasons[node_id].append("name_overlap")
        if entry["family"] == "core" and entry["slug"] == "http-request":
            scores[node_id] += 0.2 if {"http", "api", "rest", "endpoint"} & set(query_tokens) else 0.0

    boost_related_candidates(package["by_id"], scores, reasons, expanded_tokens)
    apply_specialized_first_penalties(package["crosswalks"], scores, reasons)

    ranked_ids = [
        node_id
        for node_id, _ in sorted(scores.items(), key=lambda item: (-item[1], item[0]))
        if scores[node_id] > 0
    ]
    ranked_ids = ranked_ids[: max(limit, 1)]
    expanded = expand_candidates(package_dir, package["by_id"], ranked_ids, expand_concurrency)

    return {
        "query": query,
        "normalized_query": normalized_query,
        "family_filter": family,
        "candidates": [
            {
                "id": node["id"],
                "display_name": node["display_name"],
                "family": node["family"],
                "service": node["service"],
                "score": round(scores[node["id"]], 4),
                "reasons": sorted(set(reasons[node["id"]])),
                "capabilities": node["capabilities"][:5],
                "tags": node["tags"][:8],
                "related_nodes": node["related_nodes"][:5],
                "doc_url": node["doc_url"],
            }
            for node in expanded
        ],
    }


def load_package_indexes(package_dir: Path) -> dict[str, Any]:
    entries = json.loads((package_dir / "map.json").read_text(encoding="utf-8"))
    return {
        "entries": entries,
        "by_id": {entry["id"]: entry for entry in entries},
        "by_name": load_json(package_dir / "indexes" / "by-name.json"),
        "by_service": {normalize_lookup_key(key): value for key, value in load_json(package_dir / "indexes" / "by-service.json").items()},
        "by_tag": load_json(package_dir / "indexes" / "by-tag.json"),
        "by_capability": {normalize_lookup_key(key): value for key, value in load_json(package_dir / "indexes" / "by-capability.json").items()},
        "aliases": load_json(package_dir / "auxiliary" / "aliases.json"),
        "crosswalks": load_json(package_dir / "auxiliary" / "crosswalks.json"),
    }


def apply_specialized_first_penalties(
    crosswalks: dict[str, Any],
    scores: dict[str, float],
    reasons: dict[str, list[str]],
) -> None:
    """Penalize generic nodes when specialized nodes are already strong candidates."""

    for relationship in crosswalks.get("specialized_vs_generic", []):
        specialized = relationship["specialized"]
        generic = relationship["generic_alternative"]
        if scores.get(specialized, 0) > 0:
            scores[specialized] += 0.1
            reasons[specialized].append("specialized_preferred")
            scores[generic] -= 0.25
            reasons[generic].append("generic_fallback_penalty")


def expand_candidates(
    package_dir: Path,
    by_id: dict[str, dict[str, Any]],
    ranked_ids: list[str],
    expand_concurrency: int,
) -> list[dict[str, Any]]:
    """Read top candidate node.json files concurrently."""

    def read_node(node_id: str) -> dict[str, Any]:
        entry = by_id[node_id]
        return json.loads((package_dir / entry["file_json"]).read_text(encoding="utf-8"))

    with ThreadPoolExecutor(max_workers=max(expand_concurrency, 1)) as executor:
        futures = [executor.submit(read_node, node_id) for node_id in ranked_ids]
        return [future.result() for future in futures]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_lookup_key(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def tokenize_query(value: str) -> list[str]:
    return re.findall(r"[a-z0-9][a-z0-9+.-]*", normalize_lookup_key(value))


def expand_query_tokens(tokens: list[str]) -> list[str]:
    expanded: list[str] = []
    for token in tokens:
        if token in GENERIC_QUERY_TOKENS:
            continue
        expanded.append(token)
        expanded.extend(QUERY_INTENT_ALIASES.get(token, []))
    return list(dict.fromkeys(expanded))


def build_query_phrases(tokens: list[str]) -> list[str]:
    phrases: list[str] = []
    for size in (2, 3):
        for index in range(len(tokens) - size + 1):
            phrase = " ".join(tokens[index : index + size])
            phrases.append(phrase)
    return phrases


def name_token_overlap(entry: dict[str, Any], query_tokens: list[str]) -> int:
    entry_tokens = set(tokenize_query(" ".join(filter(None, [entry["display_name"], entry["slug"], entry.get("service") or ""]))))
    return len(entry_tokens & set(query_tokens))


def boost_related_candidates(
    by_id: dict[str, dict[str, Any]],
    scores: dict[str, float],
    reasons: dict[str, list[str]],
    query_tokens: list[str],
) -> None:
    """Boost compatible related nodes for provider + task searches."""

    task_tokens = {"classification", "classifier", "categorization", "sorting", "tri", "prompting", "instructions", "prompt"}
    provider_tokens = {"openrouter", "openai", "anthropic", "gemini", "mistral", "groq"}
    if not (set(query_tokens) & task_tokens):
        return

    for node_id, entry in by_id.items():
        score = scores.get(node_id, 0)
        if score <= 0:
            continue
        entry_tokens = set(tokenize_query(" ".join(entry.get("tags", []) + entry.get("capabilities", []))))
        if not (entry_tokens & provider_tokens or set(query_tokens) & provider_tokens):
            continue
        for related_id in entry.get("related_nodes", []):
            related = by_id.get(related_id)
            if not related:
                continue
            related_tokens = set(tokenize_query(" ".join(related.get("tags", []) + related.get("capabilities", []))))
            if related.get("family") == "cluster_root" and related_tokens & task_tokens:
                scores[related_id] += 0.9
                reasons[related_id].append("compatible_root_for_provider")
