"""Disk usage + I/O provider. Reports on the drive ComfyUI's models/output live on."""

from __future__ import annotations
import os
from typing import Any, Dict

from .base import StatProvider

try:
    import psutil
except ImportError:  # pragma: no cover
    psutil = None


class DiskProvider(StatProvider):
    id = "disk"
    label = "Disk"
    priority = 20

    def __init__(self, watch_path: str = ".") -> None:
        super().__init__()
        self.watch_path = os.path.abspath(watch_path)
        self._prev_io = None

    def is_available(self) -> bool:
        return psutil is not None

    def _poll_impl(self) -> Dict[str, Any]:
        usage = psutil.disk_usage(self.watch_path)
        io = psutil.disk_io_counters()
        read_mb, write_mb = None, None
        if io and self._prev_io:
            read_mb = round((io.read_bytes - self._prev_io.read_bytes) / (1024 ** 2), 2)
            write_mb = round((io.write_bytes - self._prev_io.write_bytes) / (1024 ** 2), 2)
        self._prev_io = io
        return {
            "path": self.watch_path,
            "used_gb": round(usage.used / (1024 ** 3), 2),
            "total_gb": round(usage.total / (1024 ** 3), 2),
            "percent": usage.percent,
            "read_mb_per_tick": read_mb,
            "write_mb_per_tick": write_mb,
        }
