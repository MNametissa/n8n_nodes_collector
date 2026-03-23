"""Extract intermediate node records from cached HTML."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from bs4 import BeautifulSoup, Tag

from .models import (
    ExtractedNodeRecord,
    ExtractionReport,
    FetchRecord,
    FetchReport,
    SourceType,
)
from .progress import NullProgressReporter

HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}
PRIMARY_SECTION_ALIASES = {
    "credentials": "credentials",
    "operations": "operations",
    "node parameters": "node_parameters",
    "parameters": "node_parameters",
    "templates and examples": "templates_examples",
    "examples and templates": "templates_examples",
    "related resources": "related_resources",
    "common issues": "common_issues",
    "version notes": "version_notes",
    "inputs": "inputs",
    "outputs": "outputs",
}


def extract_records(fetch_report: FetchReport, progress: object | None = None) -> ExtractionReport:
    """Extract intermediate records from cached node HTML."""

    reporter = progress or NullProgressReporter()
    grouped: dict[str, list[FetchRecord]] = defaultdict(list)
    for record in fetch_report.records:
        if record.source_type not in {SourceType.NODE_PAGE, SourceType.SUPPORTING_PAGE}:
            continue
        node_key = record.url if record.source_type == SourceType.NODE_PAGE else record.source_url or record.url
        grouped[node_key].append(record)

    extracted: list[ExtractedNodeRecord] = []
    node_urls = sorted(grouped)
    reporter.stage("Extract node records", detail=f"{len(node_urls)} grouped nodes")
    with reporter.task("extract", total=len(node_urls)) as tracker:
        for node_url in node_urls:
            records = sorted(grouped[node_url], key=lambda item: (item.source_type, item.url))
            primary = next((record for record in records if record.source_type == SourceType.NODE_PAGE), None)
            if primary is None:
                continue
            extracted.append(extract_node_group(node_url=node_url, primary=primary, related_records=records))
            tracker.advance(item=node_url)

    return ExtractionReport(records=extracted)


def extract_node_group(
    node_url: str,
    primary: FetchRecord,
    related_records: list[FetchRecord],
) -> ExtractedNodeRecord:
    """Extract a single node record from its primary and supporting pages."""

    primary_html = Path(primary.cache_path).read_text(encoding="utf-8")
    display_name, section_text = extract_sections(primary_html)
    supporting_pages = [record.url for record in related_records if record.source_type == SourceType.SUPPORTING_PAGE]
    content_hashes = {record.url: record.content_hash for record in related_records}

    for supporting_record in related_records:
        if supporting_record.source_type != SourceType.SUPPORTING_PAGE:
            continue
        _, supporting_sections = extract_sections(Path(supporting_record.cache_path).read_text(encoding="utf-8"))
        supporting_sections = normalize_supporting_sections(supporting_record.url, supporting_sections)
        merge_section_text(section_text, supporting_sections)

    return ExtractedNodeRecord(
        node_url=node_url,
        display_name=display_name,
        family_hint=primary.family,
        source_url=primary.source_url,
        source_type=primary.source_type,
        section_text=section_text,
        supporting_pages=supporting_pages,
        content_hashes=content_hashes,
    )


def extract_sections(html: str) -> tuple[str, dict[str, list[str]]]:
    """Extract section text from a node page."""

    soup = BeautifulSoup(html, "lxml")
    root = soup.find("main") or soup.find("article") or soup.body
    if root is None:
        return "", {}

    title = extract_title(root)
    sections: dict[str, list[str]] = {}
    current_key = "summary"
    current_items: list[str] = []

    for element in root.descendants:
        if not isinstance(element, Tag):
            continue
        if element.name == "h1":
            continue
        if element.name in {"h2", "h3"}:
            flush_section(sections, current_key, current_items)
            current_key = normalize_section_name(normalized_text(element))
            current_items = []
            continue
        if element.name in {"p", "li"}:
            text = normalized_text(element)
            if text:
                current_items.append(text)

    flush_section(sections, current_key, current_items)
    return title, sections


def extract_title(root: Tag) -> str:
    """Extract the page title."""

    heading = root.find("h1")
    return normalized_text(heading) if heading else ""


def normalize_section_name(value: str) -> str:
    """Normalize a heading into a stable extraction key."""

    normalized = " ".join(value.lower().replace("/", " ").replace("-", " ").split())
    return PRIMARY_SECTION_ALIASES.get(normalized, normalized.replace(" ", "_"))


def merge_section_text(target: dict[str, list[str]], source: dict[str, list[str]]) -> None:
    """Merge supporting section text into the primary section map."""

    for key, values in source.items():
        existing = target.setdefault(key, [])
        for value in values:
            if value not in existing:
                existing.append(value)


def normalize_supporting_sections(url: str, sections: dict[str, list[str]]) -> dict[str, list[str]]:
    """Coerce supporting-page content into canonical section buckets when headings are page-specific."""

    coerced_key = infer_supporting_section_key(url)
    if coerced_key is None or coerced_key in sections:
        return sections

    flattened = flatten_supporting_sections(sections, include_heading_labels=coerced_key in {"common_issues", "operations"})
    if not flattened:
        return sections

    normalized = dict(sections)
    normalized[coerced_key] = flattened
    return normalized


def infer_supporting_section_key(url: str) -> str | None:
    """Infer the canonical destination section from a supporting-page URL."""

    slug = url.rstrip("/").split("/")[-1]
    if slug == "common-issues":
        return "common_issues"
    if slug == "templates-and-examples":
        return "templates_examples"
    if "operation" in slug:
        return "operations"
    return None


def flatten_supporting_sections(
    sections: dict[str, list[str]],
    include_heading_labels: bool,
) -> list[str]:
    """Flatten page-specific sections into a single canonical bucket."""

    flattened: list[str] = []
    for key, values in sections.items():
        if key != "summary" and include_heading_labels:
            append_once(flattened, humanize_section_key(key))
        for value in values:
            append_once(flattened, value)
    return flattened


def flush_section(sections: dict[str, list[str]], key: str, items: list[str]) -> None:
    """Persist the current section if any content was collected."""

    if not items:
        return
    sections.setdefault(key, []).extend(items)


def append_once(target: list[str], value: str) -> None:
    """Append a string once while preserving order."""

    if value and value not in target:
        target.append(value)


def normalized_text(element: Tag) -> str:
    """Collapse whitespace from an element's text."""

    return " ".join(element.get_text(" ", strip=True).split())


def humanize_section_key(value: str) -> str:
    """Convert a normalized section key back into human-readable text."""

    return value.replace("_", " ").strip().title()


def write_extraction_report(report: ExtractionReport, output_path: Path) -> None:
    """Serialize the extraction report to disk."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report.as_sorted_payload(), indent=2) + "\n", encoding="utf-8")
