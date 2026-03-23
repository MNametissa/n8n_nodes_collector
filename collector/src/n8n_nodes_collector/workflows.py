"""Workflow orchestration for multi-stage collector commands."""

from __future__ import annotations

import json
from pathlib import Path

from .config import INTERMEDIATE_CACHE_DIR, PACKAGE_DIR, RAW_CACHE_DIR
from .discovery import discover_from_directory
from .extract import extract_records, write_extraction_report
from .fetch import fetch_sources, write_fetch_report
from .models import DiscoveryReport, FetchReport
from .normalize import normalize_records, write_normalize_report
from .render import render_package
from .validate import validate_package


def run_build(
    input_dir: Path,
    package_dir: Path | None = None,
    reports_dir: Path | None = None,
    cache_dir: Path | None = None,
) -> Path:
    """Run discover, fetch, extract, normalize, render, and validate."""

    target_package_dir = package_dir or PACKAGE_DIR
    target_reports_dir = reports_dir or INTERMEDIATE_CACHE_DIR
    target_cache_dir = cache_dir or RAW_CACHE_DIR

    target_reports_dir.mkdir(parents=True, exist_ok=True)
    target_cache_dir.mkdir(parents=True, exist_ok=True)

    discovery_report = discover_from_directory(input_dir)
    write_report_json(discovery_report.as_sorted_payload(), target_reports_dir / "discovery-report.json")

    fetch_report = fetch_sources(discovery_report, cache_dir=target_cache_dir)
    write_fetch_report(fetch_report, target_reports_dir / "fetch-report.json")

    extraction_report = extract_records(fetch_report)
    write_extraction_report(extraction_report, target_reports_dir / "extract-report.json")

    normalize_report = normalize_records(extraction_report)
    write_normalize_report(normalize_report, target_reports_dir / "normalize-report.json")

    rendered_dir = render_package(normalize_report, output_dir=target_package_dir)
    validate_package(rendered_dir)
    return rendered_dir


def write_report_json(payload: dict, path: Path) -> None:
    """Write a generic JSON report."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def run_refresh(mode: str) -> None:
    """Placeholder for workflow orchestration."""

    raise NotImplementedError(f"The refresh workflow is not implemented yet: {mode}")
