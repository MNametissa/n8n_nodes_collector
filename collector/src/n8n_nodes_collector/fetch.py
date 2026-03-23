"""Fetch and cache raw HTML sources."""

from __future__ import annotations

import asyncio
import hashlib
import json
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

from .config import DEFAULT_FETCH_CONCURRENCY, RAW_CACHE_DIR
from .discovery import canonicalize_url
from .models import DiscoveryReport, Family, FetchRecord, FetchReport, SourceType
from .progress import NullProgressReporter

USER_AGENT = "n8n-nodes-collector/0.1.0"


def fetch_sources(
    discovery_report: DiscoveryReport,
    cache_dir: Path | None = None,
    client: httpx.AsyncClient | None = None,
    progress: object | None = None,
    concurrency: int = DEFAULT_FETCH_CONCURRENCY,
) -> FetchReport:
    """Fetch and cache all URLs referenced by a discovery report."""

    return asyncio.run(
        fetch_sources_async(
            discovery_report,
            cache_dir=cache_dir,
            client=client,
            progress=progress,
            concurrency=concurrency,
        )
    )


async def fetch_sources_async(
    discovery_report: DiscoveryReport,
    cache_dir: Path | None = None,
    client: httpx.AsyncClient | None = None,
    progress: object | None = None,
    concurrency: int = DEFAULT_FETCH_CONCURRENCY,
) -> FetchReport:
    """Fetch and cache all URLs referenced by a discovery report."""

    raw_cache_dir = cache_dir or RAW_CACHE_DIR
    raw_cache_dir.mkdir(parents=True, exist_ok=True)
    reporter = progress or NullProgressReporter()

    owns_client = client is None
    http_client = client or httpx.AsyncClient(
        headers={"User-Agent": USER_AGENT},
        follow_redirects=True,
        timeout=20.0,
        limits=httpx.Limits(
            max_connections=concurrency,
            max_keepalive_connections=concurrency,
        ),
    )

    try:
        report = FetchReport()
        seen_records: set[tuple[str, SourceType]] = set()
        source_urls = sorted(set(discovery_report.source_urls))
        candidates = sorted(discovery_report.candidates, key=lambda item: item.url)
        total = len(source_urls) + len(candidates)
        reporter.stage("Fetch HTML sources", detail=f"{total} known URLs before supporting-page expansion")
        with reporter.task("fetch", total=total) as tracker:
            for record in await fetch_many(
                [
                    FetchRequest(
                        url=url,
                        source_type=SourceType.INDEX,
                    )
                    for url in source_urls
                ],
                cache_dir=raw_cache_dir,
                client=http_client,
                tracker=tracker,
                concurrency=concurrency,
            ):
                append_unique_record(
                    report,
                    seen_records,
                    record,
                )
            primary_records = await fetch_many(
                [
                    FetchRequest(
                        url=candidate.url,
                        source_type=candidate.source_type,
                        family=candidate.family,
                        source_url=candidate.source_url,
                    )
                    for candidate in candidates
                ],
                cache_dir=raw_cache_dir,
                client=http_client,
                tracker=tracker,
                concurrency=concurrency,
            )
            primary_by_url = {record.url: record for record in primary_records}
            for record in primary_records:
                append_unique_record(report, seen_records, record)
            supporting_requests: list[FetchRequest] = []
            for candidate in candidates:
                primary_record = primary_by_url[candidate.url]
                if primary_record.source_type != SourceType.NODE_PAGE:
                    continue
                supporting_urls = discover_supporting_urls(primary_record.url, Path(primary_record.cache_path))
                if supporting_urls:
                    tracker.set_total((tracker.total or 0) + len(supporting_urls))
                    supporting_requests.extend(
                        [
                            FetchRequest(
                                url=supporting_url,
                                source_type=SourceType.SUPPORTING_PAGE,
                                family=candidate.family,
                                source_url=primary_record.url,
                            )
                            for supporting_url in supporting_urls
                        ]
                    )
            if supporting_requests:
                for record in await fetch_many(
                    supporting_requests,
                    cache_dir=raw_cache_dir,
                    client=http_client,
                    tracker=tracker,
                    concurrency=concurrency,
                ):
                    append_unique_record(report, seen_records, record)
        return report
    finally:
        if owns_client:
            await http_client.aclose()


class FetchRequest:
    """Internal fetch request descriptor."""

    def __init__(
        self,
        *,
        url: str,
        source_type: SourceType,
        family: Family | None = None,
        source_url: str | None = None,
    ) -> None:
        self.url = url
        self.source_type = source_type
        self.family = family
        self.source_url = source_url


async def fetch_many(
    requests: list[FetchRequest],
    *,
    cache_dir: Path,
    client: httpx.AsyncClient,
    tracker,
    concurrency: int,
) -> list[FetchRecord]:
    """Fetch many URLs concurrently while preserving deterministic output ordering."""

    semaphore = asyncio.Semaphore(concurrency)

    async def worker(request: FetchRequest) -> FetchRecord:
        async with semaphore:
            return await fetch_one_async(
                url=request.url,
                source_type=request.source_type,
                cache_dir=cache_dir,
                client=client,
                family=request.family,
                source_url=request.source_url,
            )

    tasks = [asyncio.create_task(worker(request)) for request in requests]
    results: list[FetchRecord] = []
    for task in asyncio.as_completed(tasks):
        record = await task
        results.append(record)
        tracker.advance(item=record.url)
    return sorted(results, key=lambda item: (item.source_type, item.url))


async def fetch_one_async(
    url: str,
    source_type: SourceType,
    cache_dir: Path,
    client: httpx.AsyncClient,
    family: Family | None = None,
    source_url: str | None = None,
) -> FetchRecord:
    """Fetch a single URL and write it into the raw cache."""

    response = await client.get(url)
    response.raise_for_status()

    cache_path = cache_dir / f"{cache_key(url)}.html"
    content = response.text
    digest = sha256_text(content)
    changed = True

    if cache_path.exists():
        existing_digest = sha256_text(cache_path.read_text(encoding="utf-8"))
        changed = existing_digest != digest

    cache_path.write_text(content, encoding="utf-8")

    return FetchRecord(
        url=url,
        source_type=source_type,
        family=family,
        source_url=source_url,
        http_status=response.status_code,
        content_hash=f"sha256:{digest}",
        cache_path=str(cache_path),
        changed=changed,
    )


def write_fetch_report(report: FetchReport, output_path: Path) -> None:
    """Serialize the fetch report to disk."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report.as_sorted_payload(), indent=2) + "\n", encoding="utf-8")


def append_unique_record(
    report: FetchReport,
    seen_records: set[tuple[str, SourceType]],
    record: FetchRecord,
) -> None:
    """Append a fetch record once per URL and source type."""

    key = (record.url, record.source_type)
    if key in seen_records:
        return
    seen_records.add(key)
    report.records.append(record)


def discover_supporting_urls(node_url: str, cache_path: Path) -> list[str]:
    """Discover same-node supporting pages from a fetched primary node page."""

    soup = BeautifulSoup(cache_path.read_text(encoding="utf-8"), "lxml")
    root = soup.find("article") or soup.find("main") or soup.body
    if root is None:
        return []

    supporting_urls: set[str] = set()
    supporting_prefix = f"{node_url.rstrip('/')}/"
    for anchor in root.find_all("a", href=True):
        href = str(anchor.get("href", "")).strip()
        if not href:
            continue
        candidate_url = canonicalize_url(href, source_url=node_url)
        if candidate_url == node_url:
            continue
        if not candidate_url.startswith(supporting_prefix):
            continue
        supporting_urls.add(candidate_url)

    return sorted(supporting_urls)


def cache_key(url: str) -> str:
    """Derive a stable cache filename stem from a URL."""

    return hashlib.sha256(url.encode("utf-8")).hexdigest()


def sha256_text(content: str) -> str:
    """Hash response text deterministically."""

    normalized = content.replace("\r\n", "\n")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
