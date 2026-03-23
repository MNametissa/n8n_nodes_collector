from __future__ import annotations

from io import StringIO

from n8n_nodes_collector.progress import TerminalProgressReporter


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
