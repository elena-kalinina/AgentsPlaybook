"""Tee stdout/stderr to a live log file the dashboard can tail."""

from __future__ import annotations

import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, TextIO


class _Tee:
    def __init__(self, stream: TextIO, sink: TextIO) -> None:
        self._stream = stream
        self._sink = sink

    def write(self, text: str) -> int:
        n = self._stream.write(text)
        self._sink.write(text)
        self._sink.flush()
        return n

    def flush(self) -> None:
        self._stream.flush()
        self._sink.flush()

    def __getattr__(self, name: str):
        return getattr(self._stream, name)


@contextmanager
def live_log(path: Path) -> Iterator[None]:
    """Duplicate stdout+stderr into `path` (truncated at start of each run)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as sink:
        orig_out, orig_err = sys.stdout, sys.stderr
        sys.stdout = _Tee(orig_out, sink)  # type: ignore[assignment]
        sys.stderr = _Tee(orig_err, sink)  # type: ignore[assignment]
        try:
            yield
        finally:
            sys.stdout, sys.stderr = orig_out, orig_err
