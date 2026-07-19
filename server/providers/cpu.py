"""CPU stat provider. Works everywhere psutil works; this is the universal fallback."""

from __future__ import annotations
from typing import Any, Dict

from .base import StatProvider

try:
    import psutil
except ImportError:  # pragma: no cover
    psutil = None


class CPUProvider(StatProvider):
    id = "cpu"
    label = "CPU"
    priority = 10

    def is_available(self) -> bool:
        return psutil is not None

    def _poll_impl(self) -> Dict[str, Any]:
        freq = psutil.cpu_freq()
        load = psutil.getloadavg() if hasattr(psutil, "getloadavg") else (None, None, None)
        return {
            "percent": psutil.cpu_percent(interval=None),
            "per_core": psutil.cpu_percent(interval=None, percpu=True),
            "freq_mhz": round(freq.current, 1) if freq else None,
            "freq_max_mhz": round(freq.max, 1) if freq and freq.max else None,
            "cores_physical": psutil.cpu_count(logical=False),
            "cores_logical": psutil.cpu_count(logical=True),
            "load_avg_1m": load[0],
            "ram_used_gb": round(psutil.virtual_memory().used / (1024 ** 3), 2),
            "ram_total_gb": round(psutil.virtual_memory().total / (1024 ** 3), 2),
            "ram_percent": psutil.virtual_memory().percent,
        }
