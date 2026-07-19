"""Background collector: polls every available provider on a timer and keeps
the latest merged snapshot in memory for routes.py to serve instantly.
Runs on its own thread so a slow provider (e.g. Apple powermetrics) never
blocks ComfyUI's main event loop or a queued prompt.
"""

from __future__ import annotations
import threading
import time
from typing import Any, Dict, List

from .providers import available_providers, StatProvider


class Collector:
    def __init__(self, interval_s: float = 1.0) -> None:
        self.interval_s = interval_s
        self.providers: List[StatProvider] = available_providers()
        self._snapshot: Dict[str, Any] = {"ts": 0, "providers": {}}
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True, name="universal-stats-collector")
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)

    def _run(self) -> None:
        while not self._stop.is_set():
            self._poll_once()
            self._stop.wait(self.interval_s)

    def _poll_once(self) -> None:
        result = {}
        for provider in self.providers:
            result[provider.id] = provider.poll()
        with self._lock:
            self._snapshot = {"ts": time.time(), "providers": result}

    def get_snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._snapshot)

    def describe_providers(self) -> List[Dict[str, Any]]:
        return [p.describe() for p in self.providers]


# Module-level singleton so routes.py and __init__.py share one collector/thread.
collector = Collector()
