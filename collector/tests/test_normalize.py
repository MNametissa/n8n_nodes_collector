from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from n8n_nodes_collector.cli import app
from n8n_nodes_collector.extract import extract_records
from n8n_nodes_collector.models import Family
from n8n_nodes_collector.normalize import normalize_records

from test_extract import build_fetch_report


def test_normalize_records_builds_canonical_node_and_map_entries() -> None:
    extraction_report = extract_records(build_fetch_report())
    normalize_report = normalize_records(extraction_report, verified_at="2026-03-23")

    assert len(normalize_report.node_records) == 3
    assert len(normalize_report.map_entries) == 3

    nodes_by_id = {record.id: record for record in normalize_report.node_records}
    maps_by_id = {entry.id: entry for entry in normalize_report.map_entries}

    google = nodes_by_id["n8n.action.google-sheets"]
    assert google.slug == "google-sheets"
    assert google.family == Family.ACTION
    assert google.service == "Google Sheets"
    assert google.credentials.required is True
    assert google.operations == ["Append row", "Read rows", "Update row"]
    assert google.category_path == ["actions", "google-sheets"]
    assert google.last_verified_at == "2026-03-23"

    agent = nodes_by_id["n8n.cluster-root.ai-agent"]
    assert agent.family == Family.CLUSTER_ROOT
    assert agent.service == "n8n AI"
    assert agent.credentials.required is False
    assert agent.cluster.root_or_sub == "root"
    assert agent.cluster.requires_subnodes is True
    assert agent.cluster.tool_connector is True

    schedule = nodes_by_id["n8n.trigger.schedule-trigger"]
    assert schedule.family == Family.TRIGGER
    assert schedule.service is None
    assert schedule.execution_role.is_trigger is True
    assert schedule.node_parameters == ["Trigger interval", "Cron expression"]

    google_map = maps_by_id["n8n.action.google-sheets"]
    assert google_map.file_json == "nodes/actions/google-sheets/node.json"
    assert google_map.requires_credentials is True
    assert google_map.has_common_issues_page is True


def test_normalize_command_writes_json_report(tmp_path: Path) -> None:
    extraction_report = extract_records(build_fetch_report())
    extraction_path = tmp_path / "extract-report.json"
    extraction_path.write_text(
        json.dumps(extraction_report.as_sorted_payload(), indent=2) + "\n",
        encoding="utf-8",
    )

    runner = CliRunner()
    output_path = tmp_path / "normalize-report.json"
    result = runner.invoke(app, ["normalize", str(extraction_path), "--output", str(output_path)])

    assert result.exit_code == 0
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert len(payload["map_entries"]) == 3
    assert len(payload["node_records"]) == 3
    node = next(item for item in payload["node_records"] if item["id"] == "n8n.cluster-root.ai-agent")
    assert node["cluster"]["requires_subnodes"] is True
    assert node["service"] == "n8n AI"
