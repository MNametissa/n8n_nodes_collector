"""Workflow orchestration for multi-stage collector commands."""

from __future__ import annotations

import json
from pathlib import Path

from .config import INTERMEDIATE_CACHE_DIR, PACKAGE_DIR, RAW_CACHE_DIR
from .audit import audit_package, write_audit_report
from .discovery import discover_from_directory, discover_from_live_sources
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

    discovery_report = discover_from_directory(input_dir)
    return run_build_from_report(
        discovery_report,
        package_dir=package_dir,
        reports_dir=reports_dir,
        cache_dir=cache_dir,
    )


def run_build_from_report(
    discovery_report: DiscoveryReport,
    package_dir: Path | None = None,
    reports_dir: Path | None = None,
    cache_dir: Path | None = None,
) -> Path:
    """Run fetch, extract, normalize, render, and validate from a discovery report."""

    target_package_dir = package_dir or PACKAGE_DIR
    target_reports_dir = reports_dir or INTERMEDIATE_CACHE_DIR
    target_cache_dir = cache_dir or RAW_CACHE_DIR

    target_reports_dir.mkdir(parents=True, exist_ok=True)
    target_cache_dir.mkdir(parents=True, exist_ok=True)

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


def run_build_live(
    package_dir: Path | None = None,
    reports_dir: Path | None = None,
    cache_dir: Path | None = None,
    audit_output: Path | None = None,
) -> tuple[Path, Path | None]:
    """Discover live official docs pages, build the package, and optionally write an audit report."""

    target_reports_dir = reports_dir or INTERMEDIATE_CACHE_DIR
    discovery_report = discover_from_live_sources()
    rendered_dir = run_build_from_report(
        discovery_report,
        package_dir=package_dir,
        reports_dir=target_reports_dir,
        cache_dir=cache_dir,
    )

    audit_path = None
    if audit_output is not None:
        audit_report = audit_package(rendered_dir, discovery_report=discovery_report)
        write_audit_report(audit_report, audit_output)
        audit_path = audit_output

    return rendered_dir, audit_path


def write_report_json(payload: dict, path: Path) -> None:
    """Write a generic JSON report."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def run_refresh(mode: str) -> None:
    """Run a refresh workflow mode."""

    raise NotImplementedError("Use refresh_package with explicit paths.")


def refresh_package(
    mode: str,
    input_dir: Path | None = None,
    package_dir: Path | None = None,
    reports_dir: Path | None = None,
    cache_dir: Path | None = None,
) -> Path:
    """Dispatch refresh modes to the appropriate workflow."""

    if mode not in {"daily", "weekly", "monthly"}:
        raise ValueError(f"Unsupported refresh mode: {mode}")

    if mode in {"daily", "weekly"}:
        if input_dir is None:
            raise ValueError(f"{mode} refresh requires input_dir")
        return run_build(input_dir, package_dir=package_dir, reports_dir=reports_dir, cache_dir=cache_dir)

    target_package_dir = package_dir or PACKAGE_DIR
    validate_package(target_package_dir)
    return target_package_dir
