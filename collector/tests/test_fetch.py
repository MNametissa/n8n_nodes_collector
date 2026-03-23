from __future__ import annotations

import json
import asyncio
from pathlib import Path

import httpx
from typer.testing import CliRunner

from n8n_nodes_collector.cli import app
from n8n_nodes_collector.fetch import cache_key, fetch_sources, sha256_text
from n8n_nodes_collector.models import DiscoveryCandidate, DiscoveryReport, Family, SourceType


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


def make_client(responses: dict[str, str]) -> httpx.AsyncClient:
    async def handler(request: httpx.Request) -> httpx.Response:
        body = responses.get(str(request.url))
        if body is None:
            return httpx.Response(status_code=404, request=request, text="not found")
        return httpx.Response(status_code=200, request=request, text=body)

    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


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

    def fake_fetch_sources(
        discovery_report: DiscoveryReport,
        cache_dir: Path | None = None,
        client: httpx.AsyncClient | None = None,
        progress=None,
        concurrency: int = 24,
    ):
        return fetch_sources(
            discovery_report,
            cache_dir=cache_dir or (tmp_path / "raw"),
            client=make_client(
                {
                    "https://docs.n8n.io/integrations/builtin/app-nodes/": "<html><body>library</body></html>",
                    "https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googlesheets/": "<html><body>node</body></html>",
                }
            ),
            progress=progress,
            concurrency=concurrency,
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


def test_fetch_sources_discovers_same_node_supporting_pages(tmp_path: Path) -> None:
    report = build_discovery_report()
    client = make_client(
        {
            "https://docs.n8n.io/integrations/builtin/app-nodes/": "<html><body>library</body></html>",
            "https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googlesheets/": (
                "<html><body><article>"
                "<h1>Google Sheets</h1>"
                "<a href='document-operations/'>Document operations</a>"
                "<a href='common-issues/'>Common issues</a>"
                "</article></body></html>"
            ),
            "https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googlesheets/document-operations/": "<html><body>document ops</body></html>",
            "https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googlesheets/common-issues/": "<html><body>common issues</body></html>",
        }
    )

    fetch_report = fetch_sources(report, cache_dir=tmp_path, client=client)

    supporting = [
        record for record in fetch_report.records if record.source_type == SourceType.SUPPORTING_PAGE
    ]
    assert sorted(record.url for record in supporting) == [
        "https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googlesheets/common-issues/",
        "https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googlesheets/document-operations/",
    ]
    assert all(record.family == Family.ACTION for record in supporting)
    assert all(
        record.source_url == "https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googlesheets/"
        for record in supporting
    )


def test_fetch_sources_uses_concurrency_for_live_requests(tmp_path: Path) -> None:
    report = DiscoveryReport(
        source_urls=["https://docs.n8n.io/integrations/builtin/app-nodes/"],
        candidates=[
            DiscoveryCandidate(
                url=f"https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.node{i}/",
                title=f"Node {i}",
                family=Family.ACTION,
                source_url="https://docs.n8n.io/integrations/builtin/app-nodes/",
            )
            for i in range(6)
        ],
    )
    active = 0
    max_active = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal active, max_active
        active += 1
        max_active = max(max_active, active)
        await asyncio.sleep(0.01)
        active -= 1
        return httpx.Response(status_code=200, request=request, text="<html><body>ok</body></html>")

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    fetch_sources(report, cache_dir=tmp_path, client=client, concurrency=4)

    assert max_active > 1
