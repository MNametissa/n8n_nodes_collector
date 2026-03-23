"""Workflow orchestration for multi-stage collector commands."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from .config import INTERMEDIATE_CACHE_DIR, PACKAGE_DIR, RAW_CACHE_DIR
from .audit import audit_package, write_audit_report
from .discovery import discover_from_directory, discover_from_live_sources
from .extract import extract_records, write_extraction_report
from .fetch import fetch_sources, write_fetch_report
from .models import DiscoveryReport, FetchReport, NormalizeReport
from .normalize import build_map_entry, normalize_node_record, normalize_records, normalize_source_records, write_normalize_report
from .progress import NullProgressReporter, OverallProgressReporter
from .render import render_package
from .validate import validate_package


def run_build(
    input_dir: Path,
    package_dir: Path | None = None,
    reports_dir: Path | None = None,
    cache_dir: Path | None = None,
    fetch_concurrency: int | None = None,
) -> Path:
    """Run discover, fetch, extract, normalize, render, and validate."""

    discovery_report = discover_from_directory(input_dir)
    return run_build_from_report(
        discovery_report,
        package_dir=package_dir,
        reports_dir=reports_dir,
        cache_dir=cache_dir,
        fetch_concurrency=fetch_concurrency,
    )


def run_build_from_report(
    discovery_report: DiscoveryReport,
    package_dir: Path | None = None,
    reports_dir: Path | None = None,
    cache_dir: Path | None = None,
    progress: object | None = None,
    snapshot_every: int | None = None,
    fetch_concurrency: int | None = None,
) -> Path:
    """Run fetch, extract, normalize, render, and validate from a discovery report."""

    target_package_dir = package_dir or PACKAGE_DIR
    target_reports_dir = reports_dir or INTERMEDIATE_CACHE_DIR
    target_cache_dir = cache_dir or RAW_CACHE_DIR
    reporter = progress or NullProgressReporter()

    target_reports_dir.mkdir(parents=True, exist_ok=True)
    target_cache_dir.mkdir(parents=True, exist_ok=True)

    write_report_json(discovery_report.as_sorted_payload(), target_reports_dir / "discovery-report.json")

    fetch_kwargs = {"cache_dir": target_cache_dir, "progress": reporter}
    if fetch_concurrency is not None:
        fetch_kwargs["concurrency"] = fetch_concurrency
    fetch_report = fetch_sources(discovery_report, **fetch_kwargs)
    write_fetch_report(fetch_report, target_reports_dir / "fetch-report.json")

    extraction_report = extract_records(fetch_report, progress=reporter)
    write_extraction_report(extraction_report, target_reports_dir / "extract-report.json")

    normalize_report = normalize_with_optional_snapshots(
        extraction_report,
        package_dir=target_package_dir,
        progress=reporter,
        snapshot_every=snapshot_every,
    )
    write_normalize_report(normalize_report, target_reports_dir / "normalize-report.json")

    rendered_dir = render_package(normalize_report, output_dir=target_package_dir, progress=reporter)
    if hasattr(reporter, "add_total"):
        reporter.add_total(1)
    reporter.stage("Validate package", detail=str(rendered_dir))
    validate_package(rendered_dir)
    if hasattr(reporter, "advance"):
        reporter.advance(item="validate")
    return rendered_dir


def run_build_live(
    package_dir: Path | None = None,
    reports_dir: Path | None = None,
    cache_dir: Path | None = None,
    audit_output: Path | None = None,
    progress: object | None = None,
    snapshot_every: int = 25,
    fetch_concurrency: int | None = None,
) -> tuple[Path, Path | None]:
    """Discover live official docs pages, build the package, and optionally write an audit report."""

    target_reports_dir = reports_dir or INTERMEDIATE_CACHE_DIR
    reporter = progress or NullProgressReporter()
    aggregate = OverallProgressReporter(reporter, label="build-live")

    with aggregate.track() as tracked_reporter:
        discovery_report = discover_from_live_sources(progress=tracked_reporter)
        rendered_dir = run_build_from_report(
            discovery_report,
            package_dir=package_dir,
            reports_dir=target_reports_dir,
            cache_dir=cache_dir,
            progress=tracked_reporter,
            snapshot_every=snapshot_every,
            fetch_concurrency=fetch_concurrency,
        )

        audit_path = None
        if audit_output is not None:
            tracked_reporter.add_total(1)
            tracked_reporter.stage("Audit package", detail=str(rendered_dir))
            audit_report = audit_package(rendered_dir, discovery_report=discovery_report)
            write_audit_report(audit_report, audit_output)
            tracked_reporter.advance(item="audit")
            audit_path = audit_output

        return rendered_dir, audit_path


def normalize_with_optional_snapshots(
    extraction_report,
    package_dir: Path,
    progress,
    snapshot_every: int | None,
) -> NormalizeReport:
    """Normalize records and optionally materialize progressive package snapshots."""

    if not snapshot_every or snapshot_every <= 0:
        return normalize_records(extraction_report, progress=progress)

    records = sorted(extraction_report.records, key=lambda item: (item.family_hint, item.node_url))
    reporter = progress or NullProgressReporter()
    normalize_report = NormalizeReport()
    normalized_date = date.today().isoformat()

    reporter.stage(
        "Normalize node records",
        detail=f"{len(records)} extracted nodes with package snapshots every {snapshot_every}",
    )
    with reporter.task("normalize", total=len(records)) as tracker:
        for index, extracted in enumerate(records, start=1):
            node = normalize_node_record(extracted, verified_at=normalized_date)
            normalize_report.node_records.append(node)
            normalize_report.map_entries.append(build_map_entry(node, extracted))
            normalize_report.source_records.extend(normalize_source_records(extracted, node))
            tracker.advance(item=node.id)

            if index % snapshot_every == 0:
                render_package(normalize_report, output_dir=package_dir, progress=None)
                reporter.stage(
                    "Update map and indexes",
                    detail=f"{index}/{len(records)} normalized nodes rendered into {package_dir}",
                )

    return normalize_report


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
