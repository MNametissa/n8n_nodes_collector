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
    "this node can be used as an ai tool": "ai_tool_usage",
    "inputs": "inputs",
    "outputs": "outputs",
}
IGNORED_ROOT_CLASSES = {
    "md-content__button",
    "n8n-wrap-kapa",
    "n8n-feedback-container",
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
    root = soup.select_one("article.md-content__inner") or soup.find("article") or soup.find("main") or soup.body
    if root is None:
        return "", {}

    title = extract_title(root)
    sections: dict[str, list[str]] = {}
    current_key = "summary"
    current_items: list[str] = []

    for child in root.children:
        if not isinstance(child, Tag):
            continue
        if should_skip_root_child(child):
            continue
        if child.name == "h1":
            continue
        if child.name in {"h2", "h3", "h4", "h5", "h6"}:
            flush_section(sections, current_key, current_items)
            current_key = normalize_section_name(normalized_text(child))
            current_items = []
            continue
        if child.name == "p" and is_heading_like_paragraph(child):
            flush_section(sections, current_key, current_items)
            current_key = normalize_section_name(normalized_text(child))
            current_items = []
            continue

        admonition = parse_admonition_section(child)
        if admonition is not None:
            flush_section(sections, current_key, current_items)
            admonition_key, admonition_items = admonition
            merge_section_text(sections, {admonition_key: admonition_items})
            current_key = admonition_key
            current_items = []
            continue

        append_child_content(current_items, child)

    flush_section(sections, current_key, current_items)
    return title, sections


def extract_title(root: Tag) -> str:
    """Extract the page title."""

    heading = root.find("h1")
    return normalized_text(heading) if heading else ""


def normalize_section_name(value: str) -> str:
    """Normalize a heading into a stable extraction key."""

    normalized = " ".join(
        value.lower().rstrip("#").replace("#", " ").replace("/", " ").replace("-", " ").split()
    )
    return PRIMARY_SECTION_ALIASES.get(normalized, normalized.replace(" ", "_"))


def is_heading_like_paragraph(element: Tag) -> bool:
    """Return whether a paragraph behaves like a section heading in the docs HTML."""

    text = normalized_text(element)
    if not text:
        return False
    normalized = normalize_section_name(text)
    if normalized not in PRIMARY_SECTION_ALIASES.values():
        return False
    return len(text.split()) <= 10 and not any(char in text for char in ".:")


def should_skip_root_child(element: Tag) -> bool:
    """Return whether a direct child of the article should be ignored."""

    classes = set(element.get("class", []))
    return bool(classes & IGNORED_ROOT_CLASSES)


def parse_admonition_section(element: Tag) -> tuple[str, list[str]] | None:
    """Parse note/admonition blocks that encode section headings plus content."""

    classes = set(element.get("class", []))
    if "admonition" not in classes:
        return None

    text = normalized_text(element)
    if not text:
        return None

    for label, alias in PRIMARY_SECTION_ALIASES.items():
        label_title = label.title()
        if text.startswith(label_title):
            remainder = text[len(label_title) :].strip(" :.-")
            return alias, [remainder] if remainder else []
    return None


def append_child_content(target: list[str], child: Tag) -> None:
    """Append content from a direct article child into the current section."""

    if child.name in {"p", "li"}:
        append_once(target, normalized_text(child))
        return
    if child.name in {"ul", "ol"}:
        for item in child.find_all("li", recursive=False):
            append_once(target, normalized_text(item))
        return
    if child.name == "div":
        classes = set(child.get("class", []))
        if "n8n-templates-widget" in classes:
            for text in extract_template_titles(child):
                append_once(target, text)
            return
        if "admonition" in classes:
            return
        for item in child.find_all(["p", "li"], recursive=False):
            append_once(target, normalized_text(item))


def extract_template_titles(container: Tag) -> list[str]:
    """Extract likely template titles from the templates widget."""

    titles: list[str] = []
    for link in container.find_all("a"):
        text = normalized_text(link)
        if not text or text.lower() == "view template details":
            continue
        append_once(titles, text)
    if titles:
        return titles

    # Fallback for simplified fixtures or future markup changes.
    text = normalized_text(container)
    for fragment in text.split("View template details"):
        cleaned = fragment.strip(" -")
        if cleaned:
            append_once(titles, cleaned)
    return titles


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
