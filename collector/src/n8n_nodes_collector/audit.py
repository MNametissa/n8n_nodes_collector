"""Readiness audit for rendered packages."""

from __future__ import annotations

import json
from collections import Counter
from datetime import date
from pathlib import Path

from .models import AuditReport, DiscoveryReport, Family


def audit_package(
    package_dir: Path,
    discovery_report: DiscoveryReport | None = None,
) -> AuditReport:
    """Assess whether a rendered package is ready for professional workflow-development use."""

    map_entries = load_json(package_dir / "map.json")
    stats = load_json(package_dir / "stats.json")

    by_family = dict(stats["by_family"])
    families_present = sorted(by_family)
    expected_families = sorted(member.value for member in Family)
    families_missing = [family for family in expected_families if family not in by_family]

    nodes_with_heading_marker: list[str] = []
    nodes_missing_summary: list[str] = []
    nodes_missing_operations_or_parameters: list[str] = []
    action_nodes_missing_service: list[str] = []

    for entry in map_entries:
        node_path = package_dir / entry["file_json"]
        node = load_json(node_path)
        node_id = node["id"]
        display_name = node["display_name"]
        summary = node["summary"].strip()
        operations = node["operations"]
        node_parameters = node["node_parameters"]
        service = node["service"]

        if "#" in display_name:
            nodes_with_heading_marker.append(node_id)
        if not summary or summary == "Not present in source.":
            nodes_missing_summary.append(node_id)
        if not operations and not node_parameters:
            nodes_missing_operations_or_parameters.append(node_id)
        if node["family"] == "action" and not service:
            action_nodes_missing_service.append(node_id)

    discovered_nodes_total = None
    coverage_ratio = None
    if discovery_report is not None:
        discovered_nodes_total = len(discovery_report.candidates)
        coverage_ratio = (
            round(len(map_entries) / discovered_nodes_total, 4)
            if discovered_nodes_total
            else None
        )

    readiness_status, notes = classify_readiness(
        package_nodes_total=len(map_entries),
        discovered_nodes_total=discovered_nodes_total,
        coverage_ratio=coverage_ratio,
        families_missing=families_missing,
        nodes_with_heading_marker=nodes_with_heading_marker,
        nodes_missing_summary=nodes_missing_summary,
        nodes_missing_operations_or_parameters=nodes_missing_operations_or_parameters,
        action_nodes_missing_service=action_nodes_missing_service,
    )

    return AuditReport(
        generated_at=date.today().isoformat(),
        package_dir=str(package_dir),
        readiness_status=readiness_status,
        package_nodes_total=len(map_entries),
        discovered_nodes_total=discovered_nodes_total,
        coverage_ratio=coverage_ratio,
        by_family=by_family,
        families_present=families_present,
        families_missing=families_missing,
        nodes_with_heading_marker=sorted(nodes_with_heading_marker),
        nodes_missing_summary=sorted(nodes_missing_summary),
        nodes_missing_operations_or_parameters=sorted(nodes_missing_operations_or_parameters),
        action_nodes_missing_service=sorted(action_nodes_missing_service),
        notes=notes,
    )


def classify_readiness(
    *,
    package_nodes_total: int,
    discovered_nodes_total: int | None,
    coverage_ratio: float | None,
    families_missing: list[str],
    nodes_with_heading_marker: list[str],
    nodes_missing_summary: list[str],
    nodes_missing_operations_or_parameters: list[str],
    action_nodes_missing_service: list[str],
) -> tuple[str, list[str]]:
    """Classify package readiness from objective audit signals."""

    notes: list[str] = []
    if discovered_nodes_total is not None:
        notes.append(
            f"Coverage against discovery report: {package_nodes_total}/{discovered_nodes_total}"
        )
    if families_missing:
        notes.append(f"Missing families: {', '.join(families_missing)}")
    if nodes_with_heading_marker:
        notes.append("Some display names still include heading markers from docs HTML")
    if nodes_missing_summary:
        notes.append("Some nodes are missing summaries")
    if nodes_missing_operations_or_parameters:
        notes.append("Some nodes lack both operations and node parameters")
    if action_nodes_missing_service:
        notes.append("Some action nodes are missing service names")

    if (
        coverage_ratio is not None
        and coverage_ratio >= 0.95
        and not families_missing
        and not nodes_with_heading_marker
        and not action_nodes_missing_service
        and len(nodes_missing_summary) <= max(5, int(package_nodes_total * 0.02))
    ):
        return "professional_ready", notes

    if (
        coverage_ratio is not None
        and coverage_ratio >= 0.5
        and not families_missing
        and not nodes_with_heading_marker
    ):
        return "usable_with_gaps", notes

    return "prototype", notes


def load_json(path: Path) -> dict | list:
    return json.loads(path.read_text(encoding="utf-8"))


def write_audit_report(report: AuditReport, output_path: Path) -> None:
    """Serialize the audit report to disk."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report.as_sorted_payload(), indent=2) + "\n", encoding="utf-8")
