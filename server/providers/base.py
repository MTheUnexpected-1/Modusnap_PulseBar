"""
Base provider interface for Universal Stats.

Every hardware provider (cpu, disk, nvidia, amd_rocm, amd_windows, intel, apple)
implements this interface so the collector can poll them uniformly and the
statbar can render whatever keys come back without caring who produced them.
"""

from __future__ import annotations
import time
from typing import Any, Dict, Optional


class StatProvider:
    """Base class for a single hardware stat source."""

    # Unique key used in the merged stats payload, e.g. "cpu", "nvidia:0"
    id: str = "base"
    # Human readable label shown in the statbar tooltip
    label: str = "Base"
    # Lower priority = tried first when multiple providers could claim the same role
    priority: int = 100

    def __init__(self) -> None:
        self._last_error: Optional[str] = None
        self._last_poll: float = 0.0

    def is_available(self) -> bool:
        """Return True if this provider can run on the current machine."""
        return True

    def poll(self) -> Dict[str, Any]:
        """
        Collect fresh stats. Must never raise -- catch internally and
        populate `error` on failure so one bad provider can't take down
        the whole statbar.
        """
        try:
            data = self._poll_impl()
            self._last_error = None
        except Exception as exc:  # noqa: BLE001 - providers must be fault-isolated
            self._last_error = str(exc)
            data = {}
        self._last_poll = time.time()
        return {
            "id": self.id,
            "label": self.label,
            "ok": self._last_error is None,
            "error": self._last_error,
            "ts": self._last_poll,
            **data,
        }

    def _poll_impl(self) -> Dict[str, Any]:
        raise NotImplementedError

    def describe(self) -> Dict[str, Any]:
        return {"id": self.id, "label": self.label, "available": self.is_available()}
