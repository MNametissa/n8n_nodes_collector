"""Normalize extracted records into canonical package records."""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

from .models import (
    AgentGuidance,
    CanonicalMapEntry,
    CanonicalNodeRecord,
    CanonicalSourceRecord,
    ClusterConfig,
    CredentialsConfig,
    ExecutionRole,
    ExtractionReport,
    ExtractedNodeRecord,
    Family,
    NormalizeReport,
    SourceType,
)
from .progress import NullProgressReporter


def normalize_records(
    extraction_report: ExtractionReport,
    verified_at: str | None = None,
    progress: object | None = None,
) -> NormalizeReport:
    """Normalize extracted records into canonical node and map outputs."""

    normalized_date = verified_at or date.today().isoformat()
    node_records: list[CanonicalNodeRecord] = []
    map_entries: list[CanonicalMapEntry] = []
    source_records: list[CanonicalSourceRecord] = []
    reporter = progress or NullProgressReporter()

    records = sorted(extraction_report.records, key=lambda item: (item.family_hint, item.node_url))
    reporter.stage("Normalize node records", detail=f"{len(records)} extracted nodes")
    with reporter.task("normalize", total=len(records)) as tracker:
        for extracted in records:
            node = normalize_node_record(extracted, verified_at=normalized_date)
            node_records.append(node)
            source_records.extend(normalize_source_records(extracted, node))
            map_entries.append(build_map_entry(node, extracted))
            tracker.advance(item=node.id)

    return NormalizeReport(
        map_entries=map_entries,
        node_records=node_records,
        source_records=source_records,
    )


def normalize_node_record(extracted: ExtractedNodeRecord, verified_at: str) -> CanonicalNodeRecord:
    """Normalize a single extracted record into the canonical node shape."""

    display_name = normalize_display_name(extracted.display_name)
    slug = slugify(display_name)
    node_id = build_node_id(extracted.family_hint, slug)
    service = infer_service(extracted.family_hint, display_name)
    category_path = category_path_for(extracted.family_hint, slug)
    summary = first_value(extracted.section_text, "summary")
    common_issues = extracted.section_text.get("common_issues", [])
    templates_examples = extracted.section_text.get("templates_examples", [])
    related_resources = extracted.section_text.get("related_resources", [])
    version_notes = extracted.section_text.get("version_notes", [])
    operations = extracted.section_text.get("operations", []) if extracted.family_hint == Family.ACTION else []
    node_parameters = extracted.section_text.get("node_parameters", [])
    credentials_required = infer_credentials_required(extracted)

    return CanonicalNodeRecord(
        id=node_id,
        slug=slug,
        display_name=display_name,
        display_name_short=display_name,
        doc_title=f"{display_name} node",
        family=extracted.family_hint,
        service=service,
        category_path=category_path,
        doc_url=extracted.node_url,
        summary=summary,
        description=summary,
        credentials=CredentialsConfig(
            required=credentials_required,
            notes=first_value(extracted.section_text, "credentials") if credentials_required else "",
        ),
        operations=operations,
        resource_groups=[],
        node_parameters=node_parameters,
        execution_role=execution_role_for(extracted.family_hint),
        cluster=cluster_config_for(extracted.family_hint),
        templates_examples=templates_examples,
        related_resources=related_resources,
        common_issues=common_issues,
        version_notes=version_notes,
        tags=[],
        capabilities=[],
        limitations=[],
        gotchas=[],
        agent_guidance=AgentGuidance(),
        related_nodes=[],
        source_sections_present=sorted(extracted.section_text.keys()),
        last_verified_at=verified_at,
        status="active",
    )


def normalize_source_records(
    extracted: ExtractedNodeRecord,
    node: CanonicalNodeRecord,
) -> list[CanonicalSourceRecord]:
    """Derive canonical source records from extracted provenance data."""

    return [
        CanonicalSourceRecord(
            url=url,
            node_id=node.id,
            title=node.doc_title,
            type=SourceType.NODE_PAGE if url == extracted.node_url else SourceType.SUPPORTING_PAGE,
            family_hint=node.family,
            collected_at=node.last_verified_at,
            http_status=200,
            content_hash=content_hash,
            status="parsed",
            notes="",
        )
        for url, content_hash in sorted(extracted.content_hashes.items())
    ]


def build_map_entry(
    node: CanonicalNodeRecord,
    extracted: ExtractedNodeRecord,
) -> CanonicalMapEntry:
    """Build the canonical map entry for a normalized node."""

    return CanonicalMapEntry(
        id=node.id,
        slug=node.slug,
        display_name=node.display_name,
        family=node.family,
        category_path=node.category_path,
        service=node.service,
        doc_url=node.doc_url,
        file_md=f"{node_folder(node.family, node.slug)}/node.md",
        file_json=f"{node_folder(node.family, node.slug)}/node.json",
        tags=node.tags,
        capabilities=node.capabilities,
        related_nodes=node.related_nodes,
        requires_credentials=node.credentials.required,
        supports_tools_connector=node.cluster.tool_connector,
        has_common_issues_page=has_supporting_page(extracted, "common-issues"),
        has_templates_section=bool(node.templates_examples),
        status=node.status,
    )


def infer_credentials_required(extracted: ExtractedNodeRecord) -> bool:
    """Infer whether a node itself requires credentials."""

    if extracted.family_hint == Family.ACTION:
        return bool(extracted.section_text.get("credentials"))
    return False


def has_supporting_page(extracted: ExtractedNodeRecord, suffix: str) -> bool:
    """Return whether the extracted node includes a supporting page with the given suffix."""

    return any(page.endswith(f"/{suffix}/") for page in extracted.supporting_pages)


def execution_role_for(family: Family) -> ExecutionRole:
    """Build execution-role flags from the family."""

    return ExecutionRole(
        is_trigger=family == Family.TRIGGER,
        is_action=family == Family.ACTION,
        is_core=family == Family.CORE,
        is_cluster_root=family == Family.CLUSTER_ROOT,
        is_cluster_sub=family == Family.CLUSTER_SUB,
    )


def cluster_config_for(family: Family) -> ClusterConfig:
    """Build the canonical cluster block."""

    if family == Family.CLUSTER_ROOT:
        return ClusterConfig(
            root_or_sub="root",
            compatible_with=[],
            compatible_parents=[],
            requires_parent=False,
            requires_subnodes=True,
            tool_connector=True,
            functional_group="agents",
        )
    if family == Family.CLUSTER_SUB:
        return ClusterConfig(
            root_or_sub="sub",
            compatible_with=[],
            compatible_parents=[],
            requires_parent=True,
            requires_subnodes=False,
            tool_connector=False,
            functional_group="sub_component",
        )
    return ClusterConfig()


def infer_service(family: Family, display_name: str) -> str | None:
    """Infer the service field from family and name."""

    if family == Family.ACTION:
        return display_name
    if family in {Family.CLUSTER_ROOT, Family.CLUSTER_SUB}:
        return "n8n AI"
    return None


def normalize_display_name(value: str) -> str:
    """Clean a docs heading into a stable display name."""

    cleaned = value.strip()
    cleaned = re.sub(r"\s+#\s*$", "", cleaned)
    cleaned = re.sub(r"\s+node\s*$", "", cleaned, flags=re.IGNORECASE)
    return " ".join(cleaned.split())


def category_path_for(family: Family, slug: str) -> list[str]:
    """Build the canonical category path."""

    if family == Family.ACTION:
        return ["actions", slug]
    if family == Family.TRIGGER:
        return ["triggers", slug]
    if family == Family.CORE:
        return ["core", slug]
    if family == Family.CLUSTER_ROOT:
        return ["cluster", "root", slug]
    return ["cluster", "sub", slug]


def build_node_id(family: Family, slug: str) -> str:
    """Build the canonical node ID."""

    prefix = {
        Family.ACTION: "n8n.action",
        Family.TRIGGER: "n8n.trigger",
        Family.CORE: "n8n.core",
        Family.CLUSTER_ROOT: "n8n.cluster-root",
        Family.CLUSTER_SUB: "n8n.cluster-sub",
    }[family]
    return f"{prefix}.{slug}"


def node_folder(family: Family, slug: str) -> str:
    """Build the package-relative node folder."""

    if family == Family.ACTION:
        return f"nodes/actions/{slug}"
    if family == Family.TRIGGER:
        return f"nodes/triggers/{slug}"
    if family == Family.CORE:
        return f"nodes/core/{slug}"
    if family == Family.CLUSTER_ROOT:
        return f"nodes/cluster/root/{slug}"
    return f"nodes/cluster/sub/{slug}"


def slugify(value: str) -> str:
    """Create a canonical slug."""

    lowered = value.lower()
    normalized = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    return re.sub(r"-{2,}", "-", normalized)


def first_value(section_text: dict[str, list[str]], key: str) -> str:
    """Return the first value from a section if present."""

    values = section_text.get(key, [])
    return values[0] if values else ""


def write_normalize_report(report: NormalizeReport, output_path: Path) -> None:
    """Serialize the normalization report to disk."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report.as_sorted_payload(), indent=2) + "\n", encoding="utf-8")
