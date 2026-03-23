"""Validate a rendered package tree."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path


class PackageValidationError(Exception):
    """Raised when a rendered package fails validation."""


REQUIRED_ROOT_FILES = [
    "README.md",
    "SKILLS.md",
    "package-manifest.json",
    "map.json",
    "map.md",
    "taxonomy.json",
    "sources.json",
    "stats.json",
]

REQUIRED_NODE_MD_SECTIONS = [
    "## Identity",
    "## Summary",
    "## When To Use",
    "## When Not To Use",
    "## Credentials",
    "## Operations Or Parameters",
    "## Inputs And Outputs",
    "## Common Issues",
    "## Limitations And Gotchas",
    "## Related Nodes",
    "## AI Guidance",
    "## Source",
]


def validate_package(package_dir: Path) -> None:
    """Validate a rendered package tree."""

    ensure_root_files(package_dir)

    manifest = load_json(package_dir / "package-manifest.json")
    map_entries = load_json(package_dir / "map.json")
    sources = load_json(package_dir / "sources.json")
    stats = load_json(package_dir / "stats.json")

    validate_dates(manifest)
    validate_map_entries(package_dir, map_entries)
    validate_nodes(package_dir, map_entries, sources)
    validate_stats_and_manifest(map_entries, package_dir, stats, manifest)
    validate_map_markdown(package_dir / "map.md", stats)
    validate_indexes(package_dir / "indexes")


def ensure_root_files(package_dir: Path) -> None:
    for relative in REQUIRED_ROOT_FILES:
        if not (package_dir / relative).exists():
            raise PackageValidationError(f"Missing required root file: {relative}")


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise PackageValidationError(f"Invalid JSON at {path}") from exc


def validate_dates(manifest: dict) -> None:
    today = date.today()
    build_date = parse_date(manifest["build_date"], "build_date")
    snapshot_date = parse_date(manifest["documentation_snapshot_date"], "documentation_snapshot_date")
    if build_date > today:
        raise PackageValidationError("build_date is in the future")
    if snapshot_date > today:
        raise PackageValidationError("documentation_snapshot_date is in the future")
    if snapshot_date > build_date:
        raise PackageValidationError("documentation_snapshot_date is newer than build_date")


def parse_date(value: str, field_name: str) -> date:
    try:
        return date.fromisoformat(value)
    except Exception as exc:  # noqa: BLE001
        raise PackageValidationError(f"Invalid date in {field_name}: {value}") from exc


def validate_map_entries(package_dir: Path, map_entries: list[dict]) -> None:
    if [entry["id"] for entry in map_entries] != sorted(entry["id"] for entry in map_entries):
        raise PackageValidationError("map.json entries are not sorted by id")

    seen_ids: set[str] = set()
    seen_slugs: set[str] = set()
    seen_urls: set[str] = set()
    for entry in map_entries:
        if entry["id"] in seen_ids:
            raise PackageValidationError(f"Duplicate map id: {entry['id']}")
        if entry["slug"] in seen_slugs:
            raise PackageValidationError(f"Duplicate map slug: {entry['slug']}")
        if entry["doc_url"] in seen_urls:
            raise PackageValidationError(f"Duplicate map doc_url: {entry['doc_url']}")
        seen_ids.add(entry["id"])
        seen_slugs.add(entry["slug"])
        seen_urls.add(entry["doc_url"])

        for key in ("file_json", "file_md"):
            target = package_dir / entry[key]
            if not target.exists():
                raise PackageValidationError(f"Missing node file referenced by map.json: {entry[key]}")


def validate_nodes(package_dir: Path, map_entries: list[dict], sources: list[dict]) -> None:
    source_urls = {(source["url"], source["type"]) for source in sources}
    for entry in map_entries:
        node_json = load_json(package_dir / entry["file_json"])
        node_md = (package_dir / entry["file_md"]).read_text(encoding="utf-8")

        if node_json["id"] != entry["id"]:
            raise PackageValidationError(f"Node id mismatch for {entry['id']}")
        if node_json["status"] != entry["status"]:
            raise PackageValidationError(f"Node status mismatch for {entry['id']}")
        if node_json["credentials"]["required"] != entry["requires_credentials"]:
            raise PackageValidationError(f"Credential mismatch for {entry['id']}")
        if node_json["doc_url"] != entry["doc_url"]:
            raise PackageValidationError(f"doc_url mismatch for {entry['id']}")
        if not node_json["last_verified_at"]:
            raise PackageValidationError(f"Missing last_verified_at for {entry['id']}")

        validate_execution_role(node_json, entry["id"])
        validate_cluster(node_json, entry["id"])

        if entry["has_common_issues_page"] and not node_json["common_issues"]:
            raise PackageValidationError(f"Common issues mismatch for {entry['id']}")
        if node_json["operations"] and "operations" not in node_json["source_sections_present"]:
            raise PackageValidationError(f"Operations missing from source_sections_present for {entry['id']}")
        if (entry["doc_url"], "node_page") not in source_urls:
            raise PackageValidationError(f"Missing source record for {entry['id']}")

        for section in REQUIRED_NODE_MD_SECTIONS:
            if section not in node_md:
                raise PackageValidationError(f"Missing markdown section {section} for {entry['id']}")


def validate_execution_role(node_json: dict, node_id: str) -> None:
    family = node_json["family"]
    role = node_json["execution_role"]
    expected = {
        "core": {"is_core": True, "is_action": False, "is_trigger": False, "is_cluster_root": False, "is_cluster_sub": False},
        "action": {"is_core": False, "is_action": True, "is_trigger": False, "is_cluster_root": False, "is_cluster_sub": False},
        "trigger": {"is_core": False, "is_action": False, "is_trigger": True, "is_cluster_root": False, "is_cluster_sub": False},
        "cluster_root": {"is_core": False, "is_action": False, "is_trigger": False, "is_cluster_root": True, "is_cluster_sub": False},
        "cluster_sub": {"is_core": False, "is_action": False, "is_trigger": False, "is_cluster_root": False, "is_cluster_sub": True},
    }[family]
    for key, value in expected.items():
        if role[key] != value:
            raise PackageValidationError(f"Execution role mismatch for {node_id}")


def validate_cluster(node_json: dict, node_id: str) -> None:
    family = node_json["family"]
    cluster = node_json["cluster"]
    if family == "cluster_root" and cluster["root_or_sub"] != "root":
        raise PackageValidationError(f"Cluster root_or_sub mismatch for {node_id}")
    if family == "cluster_sub" and not cluster["requires_parent"]:
        raise PackageValidationError(f"cluster_sub requires_parent mismatch for {node_id}")
    if family not in {"cluster_root", "cluster_sub"} and cluster["root_or_sub"] is not None:
        raise PackageValidationError(f"Non-cluster node has cluster root_or_sub for {node_id}")


def validate_stats_and_manifest(map_entries: list[dict], package_dir: Path, stats: dict, manifest: dict) -> None:
    node_records = [load_json(package_dir / entry["file_json"]) for entry in map_entries]
    if stats["nodes_total"] != len(map_entries):
        raise PackageValidationError("stats.json nodes_total mismatch")
    if manifest["node_count"] != stats["nodes_total"]:
        raise PackageValidationError("package-manifest.json node_count mismatch")

    derived_by_family: dict[str, int] = {}
    with_credentials_required = 0
    with_operations_listed = 0
    with_agent_guidance = 0
    for record in node_records:
        derived_by_family[record["family"]] = derived_by_family.get(record["family"], 0) + 1
        if record["credentials"]["required"]:
            with_credentials_required += 1
        if record["operations"]:
            with_operations_listed += 1
        if any(record["agent_guidance"].values()):
            with_agent_guidance += 1

    if dict(sorted(derived_by_family.items())) != stats["by_family"]:
        raise PackageValidationError("stats.json by_family mismatch")
    if stats["with_credentials_required"] != with_credentials_required:
        raise PackageValidationError("stats.json with_credentials_required mismatch")
    if stats["with_operations_listed"] != with_operations_listed:
        raise PackageValidationError("stats.json with_operations_listed mismatch")
    if stats["with_agent_guidance"] != with_agent_guidance:
        raise PackageValidationError("stats.json with_agent_guidance mismatch")


def validate_map_markdown(path: Path, stats: dict) -> None:
    content = path.read_text(encoding="utf-8")
    expected = f"- Nodes included: {stats['nodes_total']}"
    if expected not in content:
        raise PackageValidationError("map.md count summary mismatch")


def validate_indexes(index_dir: Path) -> None:
    for path in sorted(index_dir.glob("*.json")):
        payload = load_json(path)
        if path.name == "by-doc-url.json":
            if list(payload.keys()) != sorted(payload.keys()):
                raise PackageValidationError(f"Unsorted index keys in {path.name}")
            continue
        for key in sorted(payload.keys()):
            values = payload[key]
            if values != sorted(values):
                raise PackageValidationError(f"Unsorted index values in {path.name}:{key}")
