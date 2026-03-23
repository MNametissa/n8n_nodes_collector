"""Fetch and cache raw HTML sources."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import httpx

from .config import RAW_CACHE_DIR
from .models import DiscoveryReport, Family, FetchRecord, FetchReport, SourceType

USER_AGENT = "n8n-nodes-collector/0.1.0"


def fetch_sources(
    discovery_report: DiscoveryReport,
    cache_dir: Path | None = None,
    client: httpx.Client | None = None,
) -> FetchReport:
    """Fetch and cache all URLs referenced by a discovery report."""

    raw_cache_dir = cache_dir or RAW_CACHE_DIR
    raw_cache_dir.mkdir(parents=True, exist_ok=True)

    owns_client = client is None
    http_client = client or httpx.Client(
        headers={"User-Agent": USER_AGENT},
        follow_redirects=True,
        timeout=20.0,
    )

    try:
        report = FetchReport()
        for url in sorted(set(discovery_report.source_urls)):
            report.records.append(
                fetch_one(
                    url=url,
                    source_type=SourceType.INDEX,
                    cache_dir=raw_cache_dir,
                    client=http_client,
                )
            )
        for candidate in sorted(discovery_report.candidates, key=lambda item: item.url):
            report.records.append(
                fetch_one(
                    url=candidate.url,
                    source_type=candidate.source_type,
                    family=candidate.family,
                    source_url=candidate.source_url,
                    cache_dir=raw_cache_dir,
                    client=http_client,
                )
            )
        return report
    finally:
        if owns_client:
            http_client.close()


def fetch_one(
    url: str,
    source_type: SourceType,
    cache_dir: Path,
    client: httpx.Client,
    family: Family | None = None,
    source_url: str | None = None,
) -> FetchRecord:
    """Fetch a single URL and write it into the raw cache."""

    response = client.get(url)
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


def cache_key(url: str) -> str:
    """Derive a stable cache filename stem from a URL."""

    return hashlib.sha256(url.encode("utf-8")).hexdigest()


def sha256_text(content: str) -> str:
    """Hash response text deterministically."""

    normalized = content.replace("\r\n", "\n")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
