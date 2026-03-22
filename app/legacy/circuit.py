from __future__ import annotations

import time


class CircuitOpen(Exception):
    pass


class CircuitBreaker:
    def __init__(self, failure_threshold: int, open_seconds: float) -> None:
        self.failure_threshold = failure_threshold
        self.open_seconds = open_seconds
        self._failures = 0
        self._open_until: float | None = None

    def before_call(self) -> None:
        if self._open_until and time.monotonic() < self._open_until:
            raise CircuitOpen("Legacy API circuit is open; try again shortly")
        if self._open_until and time.monotonic() >= self._open_until:
            self._open_until = None
            self._failures = 0

    def on_success(self) -> None:
        self._failures = 0
        self._open_until = None

    def on_failure(self) -> None:
        self._failures += 1
        if self._failures >= self.failure_threshold:
            self._open_until = time.monotonic() + self.open_seconds
            self._failures = 0
