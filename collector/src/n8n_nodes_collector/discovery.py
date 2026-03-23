"""Discovery logic for official built-in node pages."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup, Tag

from .config import BUILTIN_PREFIX, DISCOVERY_LIBRARY_URLS, LIBRARY_PATH_HINTS, OFFICIAL_DOCS_BASE
from .models import DiscoveryCandidate, DiscoveryReport, Family
from .progress import NullProgressReporter

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


def discover_from_live_sources(
    source_urls: list[str] | None = None,
    client: httpx.Client | None = None,
    progress: object | None = None,
) -> DiscoveryReport:
    """Discover built-in node candidates from official live library pages."""

    library_urls = source_urls or DISCOVERY_LIBRARY_URLS
    owns_client = client is None
    http_client = client or httpx.Client(follow_redirects=True, timeout=20.0)
    reporter = progress or NullProgressReporter()

    try:
        report = DiscoveryReport()
        reporter.stage("Discover live libraries", detail=f"{len(library_urls)} source pages")
        with reporter.task("discover", total=len(library_urls)) as tracker:
            for source_url in library_urls:
                response = http_client.get(source_url)
                response.raise_for_status()
                resolved_url = str(response.url)
                report.source_urls.append(resolved_url)
                report.candidates.extend(discover_from_navigation_html(response.text, source_url=resolved_url))
                tracker.advance(item=resolved_url)
        report.candidates = dedupe_candidates(report.candidates)
        report.source_urls = sorted(set(report.source_urls))
        return report
    finally:
        if owns_client:
            http_client.close()


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
        title = normalized_text(element)
        family = infer_family(candidate_url, context, title=title)
        if family is None:
            continue
        candidates.append(
            DiscoveryCandidate(
                url=candidate_url,
                title=title,
                family=family,
                source_url=source_url,
                context=context,
            )
        )

    return dedupe_candidates(candidates)


def discover_from_navigation_html(html: str, source_url: str) -> list[DiscoveryCandidate]:
    """Discover node candidates from the active navigation branch of a live library page."""

    soup = BeautifulSoup(html, "lxml")
    current_link = find_current_library_link(soup)
    if current_link is None:
        return discover_from_html(html, source_url=source_url)

    current_item = current_link.find_parent("li")
    if current_item is None:
        return discover_from_html(html, source_url=source_url)

    nested_nav = current_item.find("nav")
    if nested_nav is None:
        return []

    context = library_context_for(current_link)
    candidates: list[DiscoveryCandidate] = []
    for item in iter_library_nav_items(nested_nav):
        anchor = find_nav_item_anchor(item)
        if anchor is None:
            continue
        href = str(anchor.get("href", "")).strip()
        if not href:
            continue
        candidate_url = canonicalize_url(href, source_url)
        if not is_probable_builtin_node_url(candidate_url):
            continue
        title = normalized_text(anchor)
        family = infer_family(candidate_url, context, title=title)
        if family is None:
            continue
        candidates.append(
            DiscoveryCandidate(
                url=candidate_url,
                title=title,
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


def find_current_library_link(soup: BeautifulSoup) -> Tag | None:
    """Find the active library link in the docs navigation tree."""

    matches = soup.select("li.md-nav__item--active > a.md-nav__link[href='./']")
    if matches:
        return matches[-1]
    return soup.select_one("a.md-nav__link[href='./']")


def library_context_for(current_link: Tag) -> list[str]:
    """Build discovery context from the active navigation trail."""

    context: list[str] = []
    current_item = current_link.find_parent("li")
    if current_item is None:
        return [normalized_text(current_link)]

    active_items = list(reversed(current_item.find_parents("li", class_="md-nav__item--active")))
    active_items.append(current_item)

    seen: set[str] = set()
    for item in active_items:
        anchor = find_nav_item_anchor(item)
        if anchor is None:
            continue
        text = normalized_text(anchor)
        if text and text not in seen:
            context.append(text)
            seen.add(text)
    return context


def iter_library_nav_items(nested_nav: Tag) -> list[Tag]:
    """Return the direct nav items that represent primary nodes in a library branch."""

    nav_list = nested_nav.find("ul")
    if nav_list is None:
        return []
    return [item for item in nav_list.find_all("li", recursive=False)]


def find_nav_item_anchor(item: Tag) -> Tag | None:
    """Return the primary anchor for a navigation list item."""

    container = item.find("div", class_="md-nav__container", recursive=False)
    if container is not None:
        anchor = container.find("a", href=True, recursive=False)
        if anchor is not None:
            return anchor
    return item.find("a", href=True, recursive=False)


def infer_family(url: str, context: list[str], title: str = "") -> Family | None:
    """Infer a package family from page context, not URL patterns alone."""

    context_blob = " ".join(normalize_token(text) for text in context)
    title_blob = normalize_token(title)

    if "trigger" in title_blob:
        return Family.TRIGGER

    if "sub nodes" in context_blob or "sub node" in context_blob:
        return Family.CLUSTER_SUB
    if "root nodes" in context_blob or "root node" in context_blob:
        return Family.CLUSTER_ROOT
    if "trigger nodes" in context_blob or "trigger node" in context_blob or "triggers" in context_blob:
        return Family.TRIGGER
    if "app nodes" in context_blob or "app node" in context_blob or "actions" in context_blob:
        return Family.ACTION
    if "action nodes" in context_blob or "action node" in context_blob:
        return Family.ACTION
    if "core nodes" in context_blob or "core node" in context_blob or "core" in context_blob:
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
