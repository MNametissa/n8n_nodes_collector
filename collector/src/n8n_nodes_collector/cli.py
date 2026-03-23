"""Typer CLI entrypoint."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from .audit import audit_package, write_audit_report
from .config import DEFAULT_FETCH_CONCURRENCY
from .discovery import discover_from_directory, discover_from_live_sources
from .extract import extract_records, write_extraction_report
from .fetch import fetch_sources, write_fetch_report
from .installers import (
    default_bin_path,
    default_claude_shared_skills_dir,
    default_claude_skills_dir,
    default_codex_skills_dir,
    default_install_root,
    install_skill,
    uninstall_cli,
    uninstall_skill,
)
from .models import DiscoveryReport, ExtractionReport, FetchReport, NormalizeReport
from .normalize import normalize_records, write_normalize_report
from .progress import TerminalProgressReporter
from .render import render_package
from .resolver import resolve_package_query
from .validate import PackageValidationError, validate_package
from .workflows import refresh_package, run_build, run_build_from_report, run_build_live

app = typer.Typer(help="Collector for the n8n nodes knowledge package.")


@app.command()
def discover(
    input_dir: Path = typer.Argument(..., exists=True, file_okay=False, dir_okay=True),
    output: Path = typer.Option(..., "--output", "-o", help="Path to write the discovery report."),
) -> None:
    """Discover built-in node pages from local HTML pages."""

    report = discover_from_directory(input_dir)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report.as_sorted_payload(), indent=2) + "\n", encoding="utf-8")
    typer.echo(f"Wrote {output}")


@app.command("discover-live")
def discover_live(
    output: Path = typer.Option(..., "--output", "-o", help="Path to write the discovery report."),
) -> None:
    """Discover built-in node pages from the official live n8n docs navigation."""

    report = discover_from_live_sources(progress=TerminalProgressReporter(force=True))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report.as_sorted_payload(), indent=2) + "\n", encoding="utf-8")
    typer.echo(f"Wrote {output}")


@app.command()
def fetch(
    discovery_report: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True),
    output: Path = typer.Option(..., "--output", "-o", help="Path to write the fetch report."),
    cache_dir: Path = typer.Option(
        None,
        "--cache-dir",
        help="Directory for cached raw HTML. Defaults to the configured raw cache path.",
    ),
    concurrency: int = typer.Option(
        DEFAULT_FETCH_CONCURRENCY,
        "--concurrency",
        min=1,
        help="Maximum concurrent fetch requests.",
    ),
) -> None:
    """Fetch and cache URLs from a discovery report."""

    report = DiscoveryReport.from_path(discovery_report)
    fetch_report = fetch_sources(report, cache_dir=cache_dir, concurrency=concurrency)
    write_fetch_report(fetch_report, output)
    typer.echo(f"Wrote {output}")


@app.command()
def extract(
    fetch_report: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True),
    output: Path = typer.Option(..., "--output", "-o", help="Path to write the extraction report."),
) -> None:
    """Extract intermediate records from cached HTML referenced by a fetch report."""

    report = FetchReport.from_path(fetch_report)
    extraction_report = extract_records(report)
    write_extraction_report(extraction_report, output)
    typer.echo(f"Wrote {output}")


@app.command()
def normalize(
    extraction_report: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True),
    output: Path = typer.Option(..., "--output", "-o", help="Path to write the normalization report."),
) -> None:
    """Normalize extracted records into canonical package-shaped records."""

    report = ExtractionReport.from_path(extraction_report)
    normalize_report = normalize_records(report)
    write_normalize_report(normalize_report, output)
    typer.echo(f"Wrote {output}")


@app.command()
def render(
    normalize_report: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True),
    output_dir: Path = typer.Option(None, "--output-dir", "-o", help="Directory to render the package into."),
) -> None:
    """Render canonical package artifacts from a normalization report."""

    normalized = NormalizeReport.model_validate_json(normalize_report.read_text(encoding="utf-8"))
    target = render_package(normalized, output_dir=output_dir)
    typer.echo(f"Rendered {target}")


@app.command()
def validate(
    package_dir: Path = typer.Argument(..., exists=True, file_okay=False, dir_okay=True),
) -> None:
    """Validate a rendered package tree."""

    try:
        validate_package(package_dir)
    except PackageValidationError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"Validated {package_dir}")


@app.command()
def build(
    input_dir: Path = typer.Argument(..., exists=True, file_okay=False, dir_okay=True),
    output_dir: Path = typer.Option(None, "--output-dir", "-o", help="Directory to render the package into."),
    reports_dir: Path = typer.Option(
        None,
        "--reports-dir",
        help="Directory to write intermediate JSON reports into.",
    ),
    cache_dir: Path = typer.Option(
        None,
        "--cache-dir",
        help="Directory to write raw HTML cache entries into.",
    ),
    fetch_concurrency: int = typer.Option(
        DEFAULT_FETCH_CONCURRENCY,
        "--fetch-concurrency",
        min=1,
        help="Maximum concurrent fetch requests during the build.",
    ),
) -> None:
    """Run the full collector build workflow."""

    target = run_build(
        input_dir,
        package_dir=output_dir,
        reports_dir=reports_dir,
        cache_dir=cache_dir,
        fetch_concurrency=fetch_concurrency,
    )
    typer.echo(f"Built {target}")


@app.command("build-report")
def build_report(
    discovery_report: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True),
    output_dir: Path = typer.Option(None, "--output-dir", "-o", help="Directory to render the package into."),
    reports_dir: Path = typer.Option(
        None,
        "--reports-dir",
        help="Directory to write intermediate JSON reports into.",
    ),
    cache_dir: Path = typer.Option(
        None,
        "--cache-dir",
        help="Directory to write raw HTML cache entries into.",
    ),
    fetch_concurrency: int = typer.Option(
        DEFAULT_FETCH_CONCURRENCY,
        "--fetch-concurrency",
        min=1,
        help="Maximum concurrent fetch requests during the build.",
    ),
) -> None:
    """Run the build workflow from a precomputed discovery report."""

    report = DiscoveryReport.from_path(discovery_report)
    target = run_build_from_report(
        report,
        package_dir=output_dir,
        reports_dir=reports_dir,
        cache_dir=cache_dir,
        fetch_concurrency=fetch_concurrency,
    )
    typer.echo(f"Built {target}")


@app.command("build-live")
def build_live(
    output_dir: Path = typer.Option(None, "--output-dir", "-o", help="Directory to render the package into."),
    reports_dir: Path = typer.Option(
        None,
        "--reports-dir",
        help="Directory to write intermediate JSON reports into.",
    ),
    cache_dir: Path = typer.Option(
        None,
        "--cache-dir",
        help="Directory to write raw HTML cache entries into.",
    ),
    audit_output: Path = typer.Option(
        None,
        "--audit-output",
        help="Optional path to write a readiness audit JSON report.",
    ),
    snapshot_every: int = typer.Option(
        25,
        "--snapshot-every",
        help="Render incremental package snapshots every N normalized nodes during build-live.",
    ),
    fetch_concurrency: int = typer.Option(
        DEFAULT_FETCH_CONCURRENCY,
        "--fetch-concurrency",
        min=1,
        help="Maximum concurrent fetch requests during the live build.",
    ),
) -> None:
    """Run live discovery plus the full build workflow from official n8n docs."""

    progress = TerminalProgressReporter(force=True)
    target, audit_path = run_build_live(
        package_dir=output_dir,
        reports_dir=reports_dir,
        cache_dir=cache_dir,
        audit_output=audit_output,
        progress=progress,
        snapshot_every=snapshot_every,
        fetch_concurrency=fetch_concurrency,
    )
    typer.echo(f"Built {target}")
    if audit_path is not None:
        typer.echo(f"Wrote {audit_path}")


@app.command()
def refresh(
    mode: str = typer.Option(..., "--mode", help="Refresh mode: daily, weekly, or monthly."),
    input_dir: Path = typer.Option(
        None,
        "--input-dir",
        help="Discovery HTML directory required for daily and weekly refresh.",
    ),
    package_dir: Path = typer.Option(
        None,
        "--package-dir",
        help="Target package directory or existing package directory for monthly validation.",
    ),
    reports_dir: Path = typer.Option(
        None,
        "--reports-dir",
        help="Directory to write intermediate JSON reports into for build-backed refreshes.",
    ),
    cache_dir: Path = typer.Option(
        None,
        "--cache-dir",
        help="Directory to write raw HTML cache entries into for build-backed refreshes.",
    ),
) -> None:
    """Run a refresh workflow mode."""

    try:
        target = refresh_package(
            mode=mode,
            input_dir=input_dir,
            package_dir=package_dir,
            reports_dir=reports_dir,
            cache_dir=cache_dir,
        )
    except (PackageValidationError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"Refreshed {target}")


@app.command("audit-package")
def audit_package_command(
    package_dir: Path = typer.Argument(..., exists=True, file_okay=False, dir_okay=True),
    output: Path = typer.Option(..., "--output", "-o", help="Path to write the audit report."),
    discovery_report: Path = typer.Option(
        None,
        "--discovery-report",
        help="Optional discovery report used to compute coverage against the rendered package.",
    ),
) -> None:
    """Audit package readiness for professional workflow-development use."""

    report = audit_package(
        package_dir,
        discovery_report=DiscoveryReport.from_path(discovery_report) if discovery_report else None,
    )
    write_audit_report(report, output)
    typer.echo(f"Wrote {output}")


@app.command()
def resolve(
    package_dir: Path = typer.Argument(..., exists=True, file_okay=False, dir_okay=True),
    query: str = typer.Argument(..., help="Free-form node lookup query."),
    family: str = typer.Option(None, "--family", help="Optional family filter."),
    limit: int = typer.Option(5, "--limit", min=1, help="Maximum number of ranked candidates to return."),
    expand_concurrency: int = typer.Option(
        4,
        "--expand-concurrency",
        min=1,
        help="Maximum concurrent node.json reads during candidate expansion.",
    ),
) -> None:
    """Resolve a query against a rendered package with specialized-first ranking."""

    payload = resolve_package_query(
        package_dir,
        query,
        family=family,
        limit=limit,
        expand_concurrency=expand_concurrency,
    )
    typer.echo(json.dumps(payload, indent=2) + "\n")


@app.command("install-skill")
def install_skill_command(
    codex_dir: Path = typer.Option(
        default_codex_skills_dir(),
        "--codex-dir",
        help="Codex skills directory.",
    ),
    claude_shared_dir: Path = typer.Option(
        default_claude_shared_skills_dir(),
        "--claude-shared-dir",
        help="Claude shared skills directory.",
    ),
    claude_dir: Path = typer.Option(
        default_claude_skills_dir(),
        "--claude-dir",
        help="Claude local skills directory.",
    ),
) -> None:
    """Install the repository-aligned n8n routing skill into Codex and Claude Code."""

    paths = install_skill(
        codex_skills_dir=codex_dir,
        claude_shared_skills_dir=claude_shared_dir,
        claude_skills_dir=claude_dir,
    )
    typer.echo(f"Installed skill in Codex: {paths['codex']}")
    typer.echo(f"Installed skill in Claude shared: {paths['claude_shared']}")
    typer.echo(f"Installed skill in Claude local: {paths['claude_local']}")


@app.command("uninstall-skill")
def uninstall_skill_command(
    codex_dir: Path = typer.Option(
        default_codex_skills_dir(),
        "--codex-dir",
        help="Codex skills directory.",
    ),
    claude_shared_dir: Path = typer.Option(
        default_claude_shared_skills_dir(),
        "--claude-shared-dir",
        help="Claude shared skills directory.",
    ),
    claude_dir: Path = typer.Option(
        default_claude_skills_dir(),
        "--claude-dir",
        help="Claude local skills directory.",
    ),
) -> None:
    """Uninstall the repository-aligned n8n routing skill from Codex and Claude Code."""

    paths = uninstall_skill(
        codex_skills_dir=codex_dir,
        claude_shared_skills_dir=claude_shared_dir,
        claude_skills_dir=claude_dir,
    )
    typer.echo(f"Uninstalled skill from Codex target: {paths['codex']}")
    typer.echo(f"Uninstalled skill from Claude shared target: {paths['claude_shared']}")
    typer.echo(f"Uninstalled skill from Claude local target: {paths['claude_local']}")


@app.command("self-uninstall")
def self_uninstall(
    install_root: Path = typer.Option(
        default_install_root(),
        "--install-root",
        help="Collector install root. Defaults to the detected dedicated install root.",
    ),
    bin_path: Path = typer.Option(
        default_bin_path(),
        "--bin-path",
        help="Path to the exposed collector executable symlink.",
    ),
) -> None:
    """Remove the installed collector CLI and its default binary link."""

    try:
        paths = uninstall_cli(install_root=install_root, bin_path=bin_path)
    except ValueError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"Removed install root: {paths['install_root']}")
    typer.echo(f"Removed bin link if matched: {paths['bin_path']}")


def main() -> None:
    """Console script entrypoint."""

    app()


if __name__ == "__main__":
    main()
