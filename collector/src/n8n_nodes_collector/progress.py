"""Terminal progress helpers for long-running collector workflows."""

from __future__ import annotations

import sys
from contextlib import contextmanager
from dataclasses import dataclass
from typing import TextIO


class NullProgressReporter:
    """No-op progress reporter."""

    def stage(self, title: str, detail: str | None = None) -> None:
        return

    @contextmanager
    def task(self, label: str, total: int | None = None):
        yield NullTaskTracker()


class NullTaskTracker:
    """No-op task tracker."""

    def __init__(self) -> None:
        self.total: int | None = None

    def advance(self, step: int = 1, item: str | None = None) -> None:
        return

    def set_total(self, total: int | None) -> None:
        self.total = total
        return

    def finish(self, detail: str | None = None) -> None:
        return


@dataclass
class TerminalProgressReporter:
    """Simple terminal progress reporter with ASCII progress bars."""

    stream: TextIO = sys.stderr
    force: bool = False

    def stage(self, title: str, detail: str | None = None) -> None:
        if not self._enabled:
            return
        message = f"[stage] {title}"
        if detail:
            message = f"{message} - {detail}"
        print(message, file=self.stream, flush=True)

    @contextmanager
    def task(self, label: str, total: int | None = None):
        tracker = TerminalTaskTracker(
            label=label,
            total=total,
            stream=self.stream,
            enabled=self._enabled,
        )
        tracker.render()
        try:
            yield tracker
        finally:
            tracker.finish()

    @property
    def _enabled(self) -> bool:
        return self.force or self.stream.isatty()


@dataclass
class TerminalTaskTracker:
    """Mutable progress state for a single task."""

    label: str
    total: int | None
    stream: TextIO
    enabled: bool = True
    current: int = 0
    last_item: str = ""
    _spinner_index: int = 0

    SPINNER_FRAMES = ["|", "/", "-", "\\"]
    BAR_WIDTH = 28

    def advance(self, step: int = 1, item: str | None = None) -> None:
        self.current += step
        if item:
            self.last_item = item
        self._spinner_index = (self._spinner_index + 1) % len(self.SPINNER_FRAMES)
        self.render()

    def set_total(self, total: int | None) -> None:
        self.total = total
        self.render()

    def finish(self, detail: str | None = None) -> None:
        if not self.enabled:
            return
        suffix = detail or "done"
        line = self._line(final=True)
        print(f"\r{line} {suffix}".rstrip(), file=self.stream, flush=True)

    def render(self) -> None:
        if not self.enabled:
            return
        print(f"\r{self._line()}".rstrip(), end="", file=self.stream, flush=True)

    def _line(self, final: bool = False) -> str:
        if self.total:
            ratio = min(1.0, self.current / self.total) if self.total else 0.0
            filled = int(self.BAR_WIDTH * ratio)
            bar = "#" * filled + "." * (self.BAR_WIDTH - filled)
            percent = f"{int(ratio * 100):>3}%"
            counter = f"{self.current}/{self.total}"
            item = self._trimmed_item()
            return f"[{self.label}] [{bar}] {percent} {counter} {item}".rstrip()

        frame = self.SPINNER_FRAMES[self._spinner_index]
        item = self._trimmed_item()
        return f"[{self.label}] {frame} {self.current} {item}".rstrip()

    def _trimmed_item(self) -> str:
        if not self.last_item:
            return ""
        return self.last_item[:48]
