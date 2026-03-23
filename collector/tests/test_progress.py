from __future__ import annotations

from io import StringIO

from n8n_nodes_collector.progress import OverallProgressReporter, TerminalProgressReporter


def test_terminal_progress_reporter_renders_stage_and_bar() -> None:
    stream = StringIO()
    reporter = TerminalProgressReporter(stream=stream, force=True)

    reporter.stage("Fetch HTML sources", detail="3 URLs")
    with reporter.task("fetch", total=3) as tracker:
        tracker.advance(item="one")
        tracker.advance(item="two")
        tracker.advance(item="three")

    output = stream.getvalue()
    assert "[stage] Fetch HTML sources - 3 URLs" in output
    assert "[fetch]" in output
    assert "100%" in output
    assert "3/3" in output


def test_overall_progress_reporter_aggregates_nested_tasks() -> None:
    stream = StringIO()
    base = TerminalProgressReporter(stream=stream, force=True)
    reporter = OverallProgressReporter(base, label="build-live")

    with reporter.track() as tracked:
        tracked.stage("Discover live sources", detail="2 library pages")
        with tracked.task("discover", total=2) as tracker:
            tracker.advance(item="one")
            tracker.advance(item="two")
        with tracked.task("fetch", total=1) as tracker:
            tracker.advance(item="three")
        tracked.add_total(1)
        tracked.advance(item="validate")

    output = stream.getvalue()
    assert "[build-live]" in output
    assert "4/4" in output
    assert "100%" in output
