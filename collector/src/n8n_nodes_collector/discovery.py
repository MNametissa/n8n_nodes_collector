"""Discovery logic for official built-in node pages."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, Tag

from .config import BUILTIN_PREFIX, LIBRARY_PATH_HINTS, OFFICIAL_DOCS_BASE
from .models import DiscoveryCandidate, DiscoveryReport, Family

HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}


def discover_from_directory(html_dir: Path) -> DiscoveryReport:
    """Discover candidates from a directory of HTML fixtures or cached pages."""

    if not html_dir.exists():
        raise FileNotFoundError(f"HTML directory does not exist: {html_dir}")

    report = DiscoveryReport()
    for path in sorted(html_dir.glob("*.html")):
        page_url = read_page_url(path)
        report.source_urls.append(page_url)
        candidates = discover_from_html(path.read_text(encoding="utf-8"), source_url=page_url)
        report.candidates.extend(candidates)

    report.candidates = dedupe_candidates(report.candidates)
    report.source_urls = sorted(set(report.source_urls))
    return report


def read_page_url(path: Path) -> str:
    """Read the canonical page URL from a fixture HTML file."""

    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "lxml")
    meta = soup.find("meta", attrs={"name": "page-url"})
    if not meta or not meta.get("content"):
        raise ValueError(f"Fixture is missing <meta name='page-url'>: {path}")
    return str(meta["content"]).strip()


def discover_from_html(html: str, source_url: str) -> list[DiscoveryCandidate]:
    """Discover node candidates from a single library page."""

    soup = BeautifulSoup(html, "lxml")
    root = soup.find("main") or soup.find("article") or soup.body
    if root is None:
        return []

    candidates: list[DiscoveryCandidate] = []
    headings: dict[int, str] = {}

    for element in root.descendants:
        if not isinstance(element, Tag):
            continue
        if element.name in HEADING_TAGS:
            level = int(element.name[1])
            headings = {key: value for key, value in headings.items() if key < level}
            text = normalized_text(element)
            if text:
                headings[level] = text
            continue
        if element.name != "a":
            continue
        href = str(element.get("href", "")).strip()
        if not href:
            continue
        candidate_url = canonicalize_url(href, source_url)
        if not is_probable_builtin_node_url(candidate_url):
            continue
        context = list(headings.values())
        family = infer_family(candidate_url, context)
        if family is None:
            continue
        candidates.append(
            DiscoveryCandidate(
                url=candidate_url,
                title=normalized_text(element),
                family=family,
                source_url=source_url,
                context=context,
            )
        )

    return dedupe_candidates(candidates)


def dedupe_candidates(candidates: Iterable[DiscoveryCandidate]) -> list[DiscoveryCandidate]:
    """Keep one candidate per URL, preferring the richest context."""

    best_by_url: dict[str, DiscoveryCandidate] = {}
    for candidate in candidates:
        current = best_by_url.get(candidate.url)
        if current is None or len(candidate.context) > len(current.context):
            best_by_url[candidate.url] = candidate
    return [best_by_url[url] for url in sorted(best_by_url)]


def infer_family(url: str, context: list[str]) -> Family | None:
    """Infer a package family from page context, not URL patterns alone."""

    context_blob = " ".join(normalize_token(text) for text in context)

    if "sub nodes" in context_blob or "sub node" in context_blob:
        return Family.CLUSTER_SUB
    if "root nodes" in context_blob or "root node" in context_blob:
        return Family.CLUSTER_ROOT
    if "trigger nodes" in context_blob or "trigger node" in context_blob:
        return Family.TRIGGER
    if "app nodes" in context_blob or "app node" in context_blob:
        return Family.ACTION
    if "action nodes" in context_blob or "action node" in context_blob:
        return Family.ACTION
    if "core nodes" in context_blob or "core node" in context_blob:
        return Family.CORE

    parsed = urlparse(url)
    parts = [segment for segment in parsed.path.split("/") if segment]

    if "root-nodes" in parts:
        return Family.CLUSTER_ROOT
    if "sub-nodes" in parts:
        return Family.CLUSTER_SUB
    if "app-nodes" in parts:
        return Family.ACTION

    return None


def is_probable_builtin_node_url(url: str) -> bool:
    """Filter links down to likely built-in node pages."""

    if not url.startswith(BUILTIN_PREFIX):
        return False

    parsed = urlparse(url)
    parts = [segment for segment in parsed.path.split("/") if segment]
    if len(parts) < 4:
        return False

    tail = parts[-1]
    if tail in LIBRARY_PATH_HINTS:
        return False

    return tail.startswith("n8n-nodes-")


def canonicalize_url(href: str, source_url: str) -> str:
    """Resolve and normalize a documentation URL."""

    candidate = urljoin(source_url, href)
    parsed = urlparse(candidate)
    normalized = parsed._replace(fragment="", query="", netloc=parsed.netloc or urlparse(OFFICIAL_DOCS_BASE).netloc)
    url = normalized.geturl()
    return url if url.endswith("/") else f"{url}/"


def normalized_text(element: Tag) -> str:
    """Collapse whitespace from an element's text."""

    return " ".join(element.get_text(" ", strip=True).split())


def normalize_token(value: str) -> str:
    """Normalize free text for context matching."""

    return " ".join(value.lower().replace("/", " ").replace("-", " ").split())

