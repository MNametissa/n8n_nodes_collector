from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from n8n_nodes_collector.cli import app
from n8n_nodes_collector.extract import extract_records
from n8n_nodes_collector.models import ExtractedNodeRecord, Family, FetchRecord, FetchReport, SourceType

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "extract"


def build_fetch_report() -> FetchReport:
    return FetchReport(
        records=[
            FetchRecord(
                url="https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googlesheets/",
                source_type=SourceType.NODE_PAGE,
                family=Family.ACTION,
                source_url="https://docs.n8n.io/integrations/builtin/app-nodes/",
                http_status=200,
                content_hash="sha256:google",
                cache_path=str(FIXTURE_DIR / "google_sheets_node.html"),
                changed=True,
            ),
            FetchRecord(
                url="https://docs.n8n.io/integrations/builtin/cluster-nodes/root-nodes/n8n-nodes-langchain.agent/",
                source_type=SourceType.NODE_PAGE,
                family=Family.CLUSTER_ROOT,
                source_url="https://docs.n8n.io/integrations/builtin/cluster-nodes/root-nodes/",
                http_status=200,
                content_hash="sha256:agent",
                cache_path=str(FIXTURE_DIR / "ai_agent_node.html"),
                changed=True,
            ),
            FetchRecord(
                url="https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.scheduletrigger/",
                source_type=SourceType.NODE_PAGE,
                family=Family.TRIGGER,
                source_url="https://docs.n8n.io/integrations/builtin/trigger-nodes/",
                http_status=200,
                content_hash="sha256:schedule",
                cache_path=str(FIXTURE_DIR / "schedule_trigger_node.html"),
                changed=True,
            ),
        ]
    )


def build_fetch_report_with_supporting_pages() -> FetchReport:
    report = build_fetch_report()
    report.records.extend(
        [
            FetchRecord(
                url="https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googlesheets/document-operations/",
                source_type=SourceType.SUPPORTING_PAGE,
                family=Family.ACTION,
                source_url="https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googlesheets/",
                http_status=200,
                content_hash="sha256:google-doc-ops",
                cache_path=str(FIXTURE_DIR / "google_sheets_document_operations.html"),
                changed=True,
            ),
            FetchRecord(
                url="https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googlesheets/common-issues/",
                source_type=SourceType.SUPPORTING_PAGE,
                family=Family.ACTION,
                source_url="https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googlesheets/",
                http_status=200,
                content_hash="sha256:google-common",
                cache_path=str(FIXTURE_DIR / "google_sheets_common_issues.html"),
                changed=True,
            ),
        ]
    )
    return report


def test_extract_records_builds_intermediate_records() -> None:
    report = extract_records(build_fetch_report())

    assert len(report.records) == 3
    by_name = {record.display_name: record for record in report.records}
    assert isinstance(by_name["Google Sheets"], ExtractedNodeRecord)
    assert by_name["Google Sheets"].family_hint == Family.ACTION
    assert by_name["Google Sheets"].section_text["summary"] == [
        "Use Google Sheets to work with spreadsheet data inside n8n workflows."
    ]
    assert by_name["Google Sheets"].section_text["operations"] == [
        "Append row",
        "Read rows",
        "Update row",
    ]
    assert by_name["AI Agent"].section_text["node_parameters"] == [
        "Prompt",
        "System instructions",
        "Tool connections",
    ]
    assert by_name["Schedule Trigger"].family_hint == Family.TRIGGER
    assert by_name["Schedule Trigger"].section_text["templates_examples"] == [
        "Scheduled workflow templates"
    ]


def test_extract_command_writes_json_report(tmp_path: Path) -> None:
    fetch_report = build_fetch_report()
    fetch_path = tmp_path / "fetch-report.json"
    fetch_path.write_text(json.dumps(fetch_report.as_sorted_payload(), indent=2) + "\n", encoding="utf-8")

    runner = CliRunner()
    output_path = tmp_path / "extract-report.json"
    result = runner.invoke(app, ["extract", str(fetch_path), "--output", str(output_path)])

    assert result.exit_code == 0
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert len(payload["records"]) == 3
    record = next(item for item in payload["records"] if item["display_name"] == "Google Sheets")
    assert record["section_text"]["credentials"] == ["Use Google Sheets OAuth2 credentials."]


def test_extract_records_merge_supporting_page_sections() -> None:
    report = extract_records(build_fetch_report_with_supporting_pages())

    google = next(record for record in report.records if record.display_name == "Google Sheets")
    assert google.supporting_pages == [
        "https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googlesheets/common-issues/",
        "https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googlesheets/document-operations/",
    ]
    assert "Append An Array" in google.section_text["common_issues"]
    assert "Delete document" in google.section_text["operations"]
    assert google.content_hashes["https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googlesheets/common-issues/"] == "sha256:google-common"


def test_extract_records_prefers_article_root_and_paragraph_headings(tmp_path: Path) -> None:
    html = """\
<html>
  <body>
    <main class="md-main">
      <nav>
        <ul>
          <li>Using n8n</li>
          <li>Quickstarts</li>
        </ul>
      </nav>
      <article class="md-content__inner md-typeset">
        <h1>Action Network node #</h1>
        <p>Use the Action Network node to automate work in Action Network.</p>
        <p>Credentials</p>
        <p>Refer to Action Network credentials for guidance on setting up authentication.</p>
        <h2>Operations #</h2>
        <ul>
          <li>Attendance Create Get Get All</li>
          <li>Person Update</li>
        </ul>
      </article>
    </main>
  </body>
</html>
"""
    cache_path = tmp_path / "action-network.html"
    cache_path.write_text(html, encoding="utf-8")
    fetch_report = FetchReport(
        records=[
            FetchRecord(
                url="https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.actionnetwork/",
                source_type=SourceType.NODE_PAGE,
                family=Family.ACTION,
                source_url="https://docs.n8n.io/integrations/builtin/app-nodes/",
                http_status=200,
                content_hash="sha256:test",
                cache_path=str(cache_path),
                changed=True,
            )
        ]
    )

    report = extract_records(fetch_report)
    record = report.records[0]

    assert record.display_name == "Action Network node #"
    assert record.section_text["summary"] == ["Use the Action Network node to automate work in Action Network."]
    assert record.section_text["credentials"] == [
        "Refer to Action Network credentials for guidance on setting up authentication."
    ]
    assert record.section_text["operations"] == [
        "Attendance Create Get Get All",
        "Person Update",
    ]
