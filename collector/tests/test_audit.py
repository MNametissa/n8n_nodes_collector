from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from n8n_nodes_collector.audit import audit_package
from n8n_nodes_collector.cli import app
from n8n_nodes_collector.discovery import discover_from_directory
from n8n_nodes_collector.extract import extract_records
from n8n_nodes_collector.normalize import normalize_records
from n8n_nodes_collector.render import render_package

from test_build import DISCOVERY_FIXTURE_DIR
from test_extract import build_fetch_report


def test_audit_package_flags_partial_sample_as_prototype(tmp_path: Path) -> None:
    package_dir = render_package(
        normalize_records(extract_records(build_fetch_report()), verified_at="2026-03-23"),
        output_dir=tmp_path / "package",
    )
    discovery_report = discover_from_directory(DISCOVERY_FIXTURE_DIR)

    report = audit_package(package_dir, discovery_report=discovery_report)

    assert report.readiness_status == "prototype"
    assert report.package_nodes_total == 3
    assert report.discovered_nodes_total == 3
    assert report.coverage_ratio == 1.0
    assert report.summary_coverage_ratio == 1.0
    assert report.families_missing == ["cluster_sub", "core"]


def test_audit_package_command_writes_json_report(tmp_path: Path) -> None:
    package_dir = render_package(
        normalize_records(extract_records(build_fetch_report()), verified_at="2026-03-23"),
        output_dir=tmp_path / "package",
    )
    discovery_report = discover_from_directory(DISCOVERY_FIXTURE_DIR)
    discovery_path = tmp_path / "discovery-report.json"
    discovery_path.write_text(json.dumps(discovery_report.as_sorted_payload(), indent=2) + "\n", encoding="utf-8")

    runner = CliRunner()
    output_path = tmp_path / "audit-report.json"
    result = runner.invoke(
        app,
        [
            "audit-package",
            str(package_dir),
            "--output",
            str(output_path),
            "--discovery-report",
            str(discovery_path),
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["readiness_status"] == "prototype"
    assert payload["package_nodes_total"] == 3
    assert "summary_coverage_ratio" in payload
