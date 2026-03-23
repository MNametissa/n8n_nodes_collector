from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from n8n_nodes_collector.cli import app
from n8n_nodes_collector.extract import extract_records
from n8n_nodes_collector.normalize import normalize_records
from n8n_nodes_collector.render import render_package
from n8n_nodes_collector.validate import PackageValidationError, validate_package
from n8n_nodes_collector.workflows import refresh_package

from test_build import DISCOVERY_FIXTURE_DIR
from test_extract import build_fetch_report


def test_refresh_package_daily_dispatches_to_build(monkeypatch, tmp_path: Path) -> None:
    expected = tmp_path / "package"

    def fake_run_build(input_dir: Path, package_dir=None, reports_dir=None, cache_dir=None):
        return expected

    monkeypatch.setattr("n8n_nodes_collector.workflows.run_build", fake_run_build)
    result = refresh_package(
        "daily",
        input_dir=DISCOVERY_FIXTURE_DIR,
        package_dir=expected,
        reports_dir=tmp_path / "reports",
        cache_dir=tmp_path / "raw",
    )

    assert result == expected


def test_refresh_package_monthly_validates_existing_package(tmp_path: Path) -> None:
    package_dir = render_package(
        normalize_records(extract_records(build_fetch_report()), verified_at="2026-03-23"),
        output_dir=tmp_path / "package",
    )

    result = refresh_package("monthly", package_dir=package_dir)
    assert result == package_dir


def test_validate_package_rejects_unknown_source_hash(tmp_path: Path) -> None:
    package_dir = render_package(
        normalize_records(extract_records(build_fetch_report()), verified_at="2026-03-23"),
        output_dir=tmp_path / "package",
    )
    sources_path = package_dir / "sources.json"
    sources = json.loads(sources_path.read_text(encoding="utf-8"))
    sources[0]["content_hash"] = "unknown"
    sources_path.write_text(json.dumps(sources, indent=2) + "\n", encoding="utf-8")

    try:
        validate_package(package_dir)
    except PackageValidationError as exc:
        assert "Unknown source content_hash" in str(exc)
    else:
        raise AssertionError("Expected PackageValidationError")


def test_refresh_command_monthly_validates_package(tmp_path: Path) -> None:
    package_dir = render_package(
        normalize_records(extract_records(build_fetch_report()), verified_at="2026-03-23"),
        output_dir=tmp_path / "package",
    )

    runner = CliRunner()
    result = runner.invoke(app, ["refresh", "--mode", "monthly", "--package-dir", str(package_dir)])

    assert result.exit_code == 0
    assert "Refreshed" in result.stdout


def test_refresh_command_daily_uses_build_path(monkeypatch, tmp_path: Path) -> None:
    expected = tmp_path / "package"

    def fake_refresh_package(mode: str, input_dir=None, package_dir=None, reports_dir=None, cache_dir=None):
        assert mode == "daily"
        return expected

    monkeypatch.setattr("n8n_nodes_collector.cli.refresh_package", fake_refresh_package)

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "refresh",
            "--mode",
            "daily",
            "--input-dir",
            str(DISCOVERY_FIXTURE_DIR),
            "--package-dir",
            str(expected),
            "--reports-dir",
            str(tmp_path / "reports"),
            "--cache-dir",
            str(tmp_path / "raw"),
        ],
    )

    assert result.exit_code == 0
    assert "Refreshed" in result.stdout
