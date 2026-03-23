from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from n8n_nodes_collector.cli import app
from n8n_nodes_collector.models import FetchRecord, FetchReport, Family, SourceType
from n8n_nodes_collector.workflows import run_build

from test_extract import FIXTURE_DIR as EXTRACT_FIXTURE_DIR

DISCOVERY_FIXTURE_DIR = Path(__file__).parent / "fixtures" / "discovery"


def build_fake_fetch_report() -> FetchReport:
    return FetchReport(
        records=[
            FetchRecord(
                url="https://docs.n8n.io/integrations/builtin/app-nodes/",
                source_type=SourceType.INDEX,
                http_status=200,
                content_hash="sha256:index-app",
                cache_path=str(EXTRACT_FIXTURE_DIR / "google_sheets_node.html"),
                changed=True,
            ),
            FetchRecord(
                url="https://docs.n8n.io/integrations/builtin/cluster-nodes/root-nodes/",
                source_type=SourceType.INDEX,
                http_status=200,
                content_hash="sha256:index-root",
                cache_path=str(EXTRACT_FIXTURE_DIR / "ai_agent_node.html"),
                changed=True,
            ),
            FetchRecord(
                url="https://docs.n8n.io/integrations/builtin/trigger-nodes/",
                source_type=SourceType.INDEX,
                http_status=200,
                content_hash="sha256:index-trigger",
                cache_path=str(EXTRACT_FIXTURE_DIR / "schedule_trigger_node.html"),
                changed=True,
            ),
            FetchRecord(
                url="https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googlesheets/",
                source_type=SourceType.NODE_PAGE,
                family=Family.ACTION,
                source_url="https://docs.n8n.io/integrations/builtin/app-nodes/",
                http_status=200,
                content_hash="sha256:google",
                cache_path=str(EXTRACT_FIXTURE_DIR / "google_sheets_node.html"),
                changed=True,
            ),
            FetchRecord(
                url="https://docs.n8n.io/integrations/builtin/cluster-nodes/root-nodes/n8n-nodes-langchain.agent/",
                source_type=SourceType.NODE_PAGE,
                family=Family.CLUSTER_ROOT,
                source_url="https://docs.n8n.io/integrations/builtin/cluster-nodes/root-nodes/",
                http_status=200,
                content_hash="sha256:agent",
                cache_path=str(EXTRACT_FIXTURE_DIR / "ai_agent_node.html"),
                changed=True,
            ),
            FetchRecord(
                url="https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.scheduletrigger/",
                source_type=SourceType.NODE_PAGE,
                family=Family.TRIGGER,
                source_url="https://docs.n8n.io/integrations/builtin/trigger-nodes/",
                http_status=200,
                content_hash="sha256:schedule",
                cache_path=str(EXTRACT_FIXTURE_DIR / "schedule_trigger_node.html"),
                changed=True,
            ),
        ]
    )


def test_run_build_writes_reports_and_package(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("n8n_nodes_collector.workflows.fetch_sources", lambda discovery_report, cache_dir=None: build_fake_fetch_report())

    reports_dir = tmp_path / "reports"
    package_dir = tmp_path / "package"
    cache_dir = tmp_path / "raw"
    rendered_dir = run_build(
        DISCOVERY_FIXTURE_DIR,
        package_dir=package_dir,
        reports_dir=reports_dir,
        cache_dir=cache_dir,
    )

    assert rendered_dir == package_dir
    assert (reports_dir / "discovery-report.json").exists()
    assert (reports_dir / "fetch-report.json").exists()
    assert (reports_dir / "extract-report.json").exists()
    assert (reports_dir / "normalize-report.json").exists()
    assert (package_dir / "map.json").exists()
    assert (package_dir / "nodes" / "actions" / "google-sheets" / "node.json").exists()

    stats = json.loads((package_dir / "stats.json").read_text(encoding="utf-8"))
    assert stats["nodes_total"] == 3


def test_build_command_runs_full_pipeline(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("n8n_nodes_collector.workflows.fetch_sources", lambda discovery_report, cache_dir=None: build_fake_fetch_report())

    runner = CliRunner()
    package_dir = tmp_path / "package"
    reports_dir = tmp_path / "reports"
    cache_dir = tmp_path / "raw"
    result = runner.invoke(
        app,
        [
            "build",
            str(DISCOVERY_FIXTURE_DIR),
            "--output-dir",
            str(package_dir),
            "--reports-dir",
            str(reports_dir),
            "--cache-dir",
            str(cache_dir),
        ],
    )

    assert result.exit_code == 0
    assert "Built" in result.stdout
    assert (package_dir / "package-manifest.json").exists()
    assert (reports_dir / "normalize-report.json").exists()
