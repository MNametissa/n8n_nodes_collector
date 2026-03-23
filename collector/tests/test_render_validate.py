from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from n8n_nodes_collector.cli import app
from n8n_nodes_collector.extract import extract_records
from n8n_nodes_collector.normalize import normalize_records
from n8n_nodes_collector.render import render_package
from n8n_nodes_collector.validate import PackageValidationError, validate_package

from test_extract import build_fetch_report


def build_normalize_report():
    return normalize_records(extract_records(build_fetch_report()), verified_at="2026-03-23")


def test_render_package_writes_required_artifacts(tmp_path: Path) -> None:
    package_dir = render_package(build_normalize_report(), output_dir=tmp_path / "package")

    assert (package_dir / "README.md").exists()
    assert (package_dir / "SKILLS.md").exists()
    assert (package_dir / "package-manifest.json").exists()
    assert (package_dir / "map.json").exists()
    assert (package_dir / "map.md").exists()
    assert (package_dir / "sources.json").exists()
    assert (package_dir / "stats.json").exists()
    assert (package_dir / "indexes" / "by-name.json").exists()
    assert (package_dir / "auxiliary" / "aliases.json").exists()
    assert (package_dir / "nodes" / "actions" / "google-sheets" / "node.json").exists()
    assert (package_dir / "nodes" / "cluster" / "root" / "ai-agent" / "node.md").exists()

    stats = json.loads((package_dir / "stats.json").read_text(encoding="utf-8"))
    manifest = json.loads((package_dir / "package-manifest.json").read_text(encoding="utf-8"))
    assert stats["nodes_total"] == 3
    assert manifest["node_count"] == 3


def test_validate_package_accepts_rendered_output(tmp_path: Path) -> None:
    package_dir = render_package(build_normalize_report(), output_dir=tmp_path / "package")

    validate_package(package_dir)


def test_validate_package_rejects_stats_mismatch(tmp_path: Path) -> None:
    package_dir = render_package(build_normalize_report(), output_dir=tmp_path / "package")
    stats_path = package_dir / "stats.json"
    stats = json.loads(stats_path.read_text(encoding="utf-8"))
    stats["nodes_total"] = 99
    stats_path.write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")

    try:
        validate_package(package_dir)
    except PackageValidationError as exc:
        assert "nodes_total mismatch" in str(exc)
    else:
        raise AssertionError("Expected PackageValidationError")


def test_render_and_validate_commands_work(tmp_path: Path) -> None:
    normalize_report = build_normalize_report()
    normalize_path = tmp_path / "normalize-report.json"
    normalize_path.write_text(
        json.dumps(normalize_report.as_sorted_payload(), indent=2) + "\n",
        encoding="utf-8",
    )

    runner = CliRunner()
    package_dir = tmp_path / "package"
    render_result = runner.invoke(
        app,
        ["render", str(normalize_path), "--output-dir", str(package_dir)],
    )
    assert render_result.exit_code == 0

    validate_result = runner.invoke(app, ["validate", str(package_dir)])
    assert validate_result.exit_code == 0
