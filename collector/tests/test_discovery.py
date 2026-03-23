from __future__ import annotations

import json
from pathlib import Path

import httpx
from typer.testing import CliRunner

from n8n_nodes_collector.cli import app
from n8n_nodes_collector.discovery import discover_from_directory, discover_from_live_sources, infer_family
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


def test_discover_from_live_sources_uses_active_navigation_branch_only() -> None:
    html_map = {
        "https://docs.n8n.io/integrations/builtin/app-nodes/": """
        <html><body>
          <nav>
            <ul>
              <li class="md-nav__item md-nav__item--active md-nav__item--nested">
                <a class="md-nav__link" href="../../">Integrations</a>
                <nav>
                  <ul>
                    <li class="md-nav__item md-nav__item--active md-nav__item--nested">
                      <a class="md-nav__link" href="../node-types/">Node types</a>
                      <nav>
                        <ul>
                          <li class="md-nav__item md-nav__item--active md-nav__item--nested">
                            <a class="md-nav__link" href="./">Actions</a>
                            <nav>
                              <ul>
                                <li class="md-nav__item md-nav__item--nested">
                                  <div class="md-nav__container">
                                    <a class="md-nav__link" href="n8n-nodes-base.googlesheets/">Google Sheets</a>
                                  </div>
                                  <nav>
                                    <ul>
                                      <li class="md-nav__item"><a class="md-nav__link" href="n8n-nodes-base.googlesheets/common-issues/">Common issues</a></li>
                                    </ul>
                                  </nav>
                                </li>
                                <li class="md-nav__item">
                                  <a class="md-nav__link" href="n8n-nodes-base.gmail/">Gmail</a>
                                </li>
                              </ul>
                            </nav>
                          </li>
                        </ul>
                      </nav>
                    </li>
                  </ul>
                </nav>
              </li>
            </ul>
          </nav>
        </body></html>
        """
    }

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=200, request=request, text=html_map[str(request.url)])

    client = httpx.Client(transport=httpx.MockTransport(handler))
    report = discover_from_live_sources(
        source_urls=["https://docs.n8n.io/integrations/builtin/app-nodes/"],
        client=client,
    )

    assert report.source_urls == ["https://docs.n8n.io/integrations/builtin/app-nodes/"]
    assert [candidate.url for candidate in report.candidates] == [
        "https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.gmail/",
        "https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googlesheets/",
    ]
    assert all(candidate.family == Family.ACTION for candidate in report.candidates)
    assert all("Actions" in candidate.context for candidate in report.candidates)


def test_discover_live_command_writes_json_report(monkeypatch: object, tmp_path: Path) -> None:
    expected = discover_from_directory(FIXTURE_DIR)
    monkeypatch.setattr("n8n_nodes_collector.cli.discover_from_live_sources", lambda: expected)

    runner = CliRunner()
    output_path = tmp_path / "discovery-live-report.json"
    result = runner.invoke(app, ["discover-live", "--output", str(output_path)])

    assert result.exit_code == 0
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["source_urls"] == expected.as_sorted_payload()["source_urls"]
    assert len(payload["candidates"]) == 3


def test_infer_family_uses_trigger_title_when_context_is_core() -> None:
    family = infer_family(
        "https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.scheduletrigger/",
        ["Integrations", "Core nodes"],
        title="Schedule Trigger",
    )

    assert family == Family.TRIGGER
