from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from n8n_nodes_collector.cli import app
from n8n_nodes_collector.discovery import discover_from_directory
from n8n_nodes_collector.models import Family

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "discovery"


def test_discovery_classifies_known_fixture_nodes() -> None:
    report = discover_from_directory(FIXTURE_DIR)

    by_url = {candidate.url: candidate for candidate in report.candidates}
    assert len(by_url) == 3

    assert by_url[
        "https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googlesheets/"
    ].family == Family.ACTION
    assert by_url[
        "https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.scheduletrigger/"
    ].family == Family.TRIGGER
    assert by_url[
        "https://docs.n8n.io/integrations/builtin/cluster-nodes/root-nodes/n8n-nodes-langchain.agent/"
    ].family == Family.CLUSTER_ROOT


def test_discovery_uses_context_instead_of_url_path_for_schedule_trigger() -> None:
    report = discover_from_directory(FIXTURE_DIR)
    schedule = next(
        candidate
        for candidate in report.candidates
        if candidate.url.endswith("n8n-nodes-base.scheduletrigger/")
    )

    assert schedule.family == Family.TRIGGER
    assert "Trigger nodes" in schedule.context


def test_discover_command_writes_json_report(tmp_path: Path) -> None:
    runner = CliRunner()
    output_path = tmp_path / "discovery-report.json"

    result = runner.invoke(app, ["discover", str(FIXTURE_DIR), "--output", str(output_path)])

    assert result.exit_code == 0
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["source_urls"] == sorted(
        [
            "https://docs.n8n.io/integrations/builtin/app-nodes/",
            "https://docs.n8n.io/integrations/builtin/cluster-nodes/root-nodes/",
            "https://docs.n8n.io/integrations/builtin/trigger-nodes/",
        ]
    )
    assert [candidate["family"] for candidate in payload["candidates"]] == [
        "action",
        "cluster_root",
        "trigger",
    ]
