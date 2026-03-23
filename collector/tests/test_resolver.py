from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from n8n_nodes_collector.cli import app
from n8n_nodes_collector.models import ExtractionReport, ExtractedNodeRecord, Family, SourceType
from n8n_nodes_collector.normalize import normalize_records
from n8n_nodes_collector.render import render_package
from n8n_nodes_collector.resolver import resolve_package_query


def build_routing_package(tmp_path: Path) -> Path:
    extraction_report = ExtractionReport(
        records=[
            ExtractedNodeRecord(
                node_url="https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.odoo/",
                display_name="Odoo node",
                family_hint=Family.ACTION,
                source_url="https://docs.n8n.io/integrations/builtin/app-nodes/",
                source_type=SourceType.NODE_PAGE,
                section_text={
                    "summary": [
                        "Use the Odoo node to automate work in Odoo and integrate ERP processes such as contacts, invoices, and opportunities."
                    ],
                    "credentials": ["Use Odoo credentials."],
                    "operations": ["Create invoice", "Update contact", "Get opportunity"],
                    "templates_examples": ["Template"],
                },
                content_hashes={"https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.odoo/": "sha256:odoo"},
            ),
            ExtractedNodeRecord(
                node_url="https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.httprequest/",
                display_name="HTTP Request node",
                family_hint=Family.CORE,
                source_url="https://docs.n8n.io/integrations/builtin/core-nodes/",
                source_type=SourceType.NODE_PAGE,
                section_text={
                    "summary": [
                        "The HTTP Request node lets you call REST APIs and generic HTTP endpoints when no specialized integration is available."
                    ],
                    "node_parameters": ["Authentication", "HTTP method", "URL"],
                    "templates_examples": ["Template"],
                },
                content_hashes={
                    "https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.httprequest/": "sha256:http"
                },
            ),
            ExtractedNodeRecord(
                node_url="https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googlesheets/",
                display_name="Google Sheets node",
                family_hint=Family.ACTION,
                source_url="https://docs.n8n.io/integrations/builtin/app-nodes/",
                source_type=SourceType.NODE_PAGE,
                section_text={
                    "summary": [
                        "Use Google Sheets to read spreadsheet data, append rows, and update existing rows."
                    ],
                    "credentials": ["Use Google Sheets credentials."],
                    "operations": ["Append row", "Read rows", "Update row"],
                },
                content_hashes={
                    "https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googlesheets/": "sha256:sheets"
                },
            ),
        ]
    )
    normalize_report = normalize_records(extraction_report, verified_at="2026-03-23")
    return render_package(normalize_report, output_dir=tmp_path / "package")


def test_resolve_package_query_prefers_specialized_node_over_generic(tmp_path: Path) -> None:
    package_dir = build_routing_package(tmp_path)

    payload = resolve_package_query(package_dir, "odoo erp api", limit=3, expand_concurrency=3)

    assert payload["candidates"][0]["id"] == "n8n.action.odoo"
    assert "specialized_preferred" in payload["candidates"][0]["reasons"]
    assert "generic_fallback_penalty" in payload["candidates"][1]["reasons"]


def test_resolve_package_query_uses_generated_aliases_and_tags(tmp_path: Path) -> None:
    package_dir = build_routing_package(tmp_path)

    payload = resolve_package_query(package_dir, "erp", limit=2)

    assert payload["candidates"][0]["id"] == "n8n.action.odoo"
    assert "alias_match" in payload["candidates"][0]["reasons"] or "tag:erp" in payload["candidates"][0]["reasons"]


def test_resolve_command_returns_ranked_json(tmp_path: Path) -> None:
    package_dir = build_routing_package(tmp_path)

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["resolve", str(package_dir), "spreadsheet append row", "--limit", "2", "--expand-concurrency", "2"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["candidates"][0]["id"] == "n8n.action.google-sheets"
