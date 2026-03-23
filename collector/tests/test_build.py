from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from n8n_nodes_collector.cli import app
from n8n_nodes_collector.models import DiscoveryReport, FetchRecord, FetchReport, Family, SourceType
from n8n_nodes_collector.workflows import run_build, run_build_from_report, run_build_live

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
    monkeypatch.setattr(
        "n8n_nodes_collector.workflows.fetch_sources",
        lambda discovery_report, cache_dir=None, progress=None: build_fake_fetch_report(),
    )

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
    monkeypatch.setattr(
        "n8n_nodes_collector.workflows.fetch_sources",
        lambda discovery_report, cache_dir=None, progress=None: build_fake_fetch_report(),
    )

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


def test_run_build_from_report_writes_reports_and_package(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "n8n_nodes_collector.workflows.fetch_sources",
        lambda discovery_report, cache_dir=None, progress=None: build_fake_fetch_report(),
    )

    discovery_report = DiscoveryReport.model_validate(
        {
            "source_urls": ["https://docs.n8n.io/integrations/builtin/app-nodes/"],
            "candidates": [
                {
                    "url": "https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googlesheets/",
                    "title": "Google Sheets",
                    "family": "action",
                    "source_url": "https://docs.n8n.io/integrations/builtin/app-nodes/",
                    "source_type": "node_page",
                    "context": ["App nodes"],
                }
            ],
        }
    )

    rendered_dir = run_build_from_report(
        discovery_report,
        package_dir=tmp_path / "package",
        reports_dir=tmp_path / "reports",
        cache_dir=tmp_path / "raw",
    )

    assert rendered_dir == tmp_path / "package"
    assert (tmp_path / "reports" / "discovery-report.json").exists()
    assert (tmp_path / "package" / "map.json").exists()


def test_build_report_command_runs_pipeline(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("n8n_nodes_collector.cli.run_build_from_report", lambda discovery_report, package_dir=None, reports_dir=None, cache_dir=None: tmp_path / "package")

    discovery_report = {
        "source_urls": ["https://docs.n8n.io/integrations/builtin/app-nodes/"],
        "candidates": [
            {
                "url": "https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googlesheets/",
                "title": "Google Sheets",
                "family": "action",
                "source_url": "https://docs.n8n.io/integrations/builtin/app-nodes/",
                "source_type": "node_page",
                "context": ["App nodes"],
            }
        ],
    }
    discovery_path = tmp_path / "discovery-report.json"
    discovery_path.write_text(json.dumps(discovery_report, indent=2) + "\n", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "build-report",
            str(discovery_path),
            "--output-dir",
            str(tmp_path / "package"),
            "--reports-dir",
            str(tmp_path / "reports"),
            "--cache-dir",
            str(tmp_path / "raw"),
        ],
    )

    assert result.exit_code == 0
    assert "Built" in result.stdout


def test_run_build_live_runs_discovery_build_and_audit(monkeypatch, tmp_path: Path) -> None:
    discovery_report = DiscoveryReport.model_validate(
        {
            "source_urls": ["https://docs.n8n.io/integrations/builtin/app-nodes/"],
            "candidates": [
                {
                    "url": "https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googlesheets/",
                    "title": "Google Sheets",
                    "family": "action",
                    "source_url": "https://docs.n8n.io/integrations/builtin/app-nodes/",
                    "source_type": "node_page",
                    "context": ["Integrations", "Actions"],
                }
            ],
        }
    )
    expected_package = tmp_path / "package"

    monkeypatch.setattr(
        "n8n_nodes_collector.workflows.discover_from_live_sources",
        lambda progress=None: discovery_report,
    )
    monkeypatch.setattr(
        "n8n_nodes_collector.workflows.run_build_from_report",
        lambda report, package_dir=None, reports_dir=None, cache_dir=None, progress=None: expected_package,
    )
    monkeypatch.setattr(
        "n8n_nodes_collector.workflows.audit_package",
        lambda package_dir, discovery_report=None: {
            "generated_at": "2026-03-23",
            "package_dir": str(package_dir),
            "readiness_status": "prototype",
            "package_nodes_total": 1,
        },
    )
    monkeypatch.setattr(
        "n8n_nodes_collector.workflows.write_audit_report",
        lambda report, output_path: output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8"),
    )

    rendered_dir, audit_path = run_build_live(
        package_dir=expected_package,
        reports_dir=tmp_path / "reports",
        cache_dir=tmp_path / "raw",
        audit_output=tmp_path / "audit.json",
        progress=None,
    )

    assert rendered_dir == expected_package
    assert audit_path == tmp_path / "audit.json"
    assert audit_path.exists()
