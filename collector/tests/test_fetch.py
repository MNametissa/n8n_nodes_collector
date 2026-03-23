from __future__ import annotations

import json
from pathlib import Path

import httpx
from typer.testing import CliRunner

from n8n_nodes_collector.cli import app
from n8n_nodes_collector.fetch import cache_key, fetch_sources, sha256_text
from n8n_nodes_collector.models import DiscoveryCandidate, DiscoveryReport, Family


def build_discovery_report() -> DiscoveryReport:
    return DiscoveryReport(
        source_urls=["https://docs.n8n.io/integrations/builtin/app-nodes/"],
        candidates=[
            DiscoveryCandidate(
                url="https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googlesheets/",
                title="Google Sheets",
                family=Family.ACTION,
                source_url="https://docs.n8n.io/integrations/builtin/app-nodes/",
            )
        ],
    )


def make_client(responses: dict[str, str]) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        body = responses.get(str(request.url))
        if body is None:
            return httpx.Response(status_code=404, request=request, text="not found")
        return httpx.Response(status_code=200, request=request, text=body)

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_fetch_sources_writes_cached_html_and_report_records(tmp_path: Path) -> None:
    report = build_discovery_report()
    client = make_client(
        {
            "https://docs.n8n.io/integrations/builtin/app-nodes/": "<html><body>library</body></html>",
            "https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googlesheets/": "<html><body>node</body></html>",
        }
    )

    fetch_report = fetch_sources(report, cache_dir=tmp_path, client=client)

    assert len(fetch_report.records) == 2
    cached_files = sorted(path.name for path in tmp_path.glob("*.html"))
    assert cached_files == sorted(
        [
            f"{cache_key('https://docs.n8n.io/integrations/builtin/app-nodes/')}.html",
            f"{cache_key('https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googlesheets/')}.html",
        ]
    )
    node_record = next(
        record for record in fetch_report.records if record.url.endswith("n8n-nodes-base.googlesheets/")
    )
    assert node_record.family == Family.ACTION
    assert node_record.content_hash == f"sha256:{sha256_text('<html><body>node</body></html>')}"
    assert node_record.changed is True


def test_fetch_sources_marks_unchanged_content_on_second_fetch(tmp_path: Path) -> None:
    report = build_discovery_report()
    responses = {
        "https://docs.n8n.io/integrations/builtin/app-nodes/": "<html><body>library</body></html>",
        "https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googlesheets/": "<html><body>node</body></html>",
    }

    first = fetch_sources(report, cache_dir=tmp_path, client=make_client(responses))
    second = fetch_sources(report, cache_dir=tmp_path, client=make_client(responses))

    assert all(record.changed is True for record in first.records)
    assert all(record.changed is False for record in second.records)


def test_fetch_command_writes_fetch_report(monkeypatch: object, tmp_path: Path) -> None:
    report = build_discovery_report()
    discovery_path = tmp_path / "discovery-report.json"
    discovery_path.write_text(json.dumps(report.as_sorted_payload(), indent=2) + "\n", encoding="utf-8")

    def fake_fetch_sources(discovery_report: DiscoveryReport, cache_dir: Path | None = None, client: httpx.Client | None = None):
        return fetch_sources(
            discovery_report,
            cache_dir=cache_dir or (tmp_path / "raw"),
            client=make_client(
                {
                    "https://docs.n8n.io/integrations/builtin/app-nodes/": "<html><body>library</body></html>",
                    "https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googlesheets/": "<html><body>node</body></html>",
                }
            ),
        )

    monkeypatch.setattr("n8n_nodes_collector.cli.fetch_sources", fake_fetch_sources)

    runner = CliRunner()
    output_path = tmp_path / "fetch-report.json"
    cache_dir = tmp_path / "raw"
    result = runner.invoke(
        app,
        [
            "fetch",
            str(discovery_path),
            "--output",
            str(output_path),
            "--cache-dir",
            str(cache_dir),
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert len(payload["records"]) == 2
    assert payload["records"][0]["source_type"] == "index"
