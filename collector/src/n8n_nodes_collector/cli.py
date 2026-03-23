"""Typer CLI entrypoint."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from .discovery import discover_from_directory
from .extract import extract_records, write_extraction_report
from .fetch import fetch_sources, write_fetch_report
from .models import DiscoveryReport, ExtractionReport, FetchReport
from .normalize import normalize_records, write_normalize_report

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


@app.command()
def fetch(
    discovery_report: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True),
    output: Path = typer.Option(..., "--output", "-o", help="Path to write the fetch report."),
    cache_dir: Path = typer.Option(
        None,
        "--cache-dir",
        help="Directory for cached raw HTML. Defaults to the configured raw cache path.",
    ),
) -> None:
    """Fetch and cache URLs from a discovery report."""

    report = DiscoveryReport.from_path(discovery_report)
    fetch_report = fetch_sources(report, cache_dir=cache_dir)
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
def build() -> None:
    """Reserved for the full build phase."""

    raise typer.Exit(code=1)


@app.command()
def validate() -> None:
    """Reserved for the validation phase."""

    raise typer.Exit(code=1)


def main() -> None:
    """Console script entrypoint."""

    app()


if __name__ == "__main__":
    main()
