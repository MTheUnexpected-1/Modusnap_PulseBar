"""Apple Silicon provider. GPU/ANE power draw needs `powermetrics`, which
requires sudo, so we only shell out to it if it's runnable without a password
prompt (i.e. already cached); otherwise we report CPU/RAM via psutil/sysctl
and leave GPU fields None rather than hang the poll loop on a sudo prompt.
"""

from __future__ import annotations
import platform
import subprocess
from typing import Any, Dict

from .base import StatProvider

try:
    import psutil
except ImportError:  # pragma: no cover
    psutil = None


class AppleProvider(StatProvider):
    id = "apple"
    label = "Apple Silicon"
    priority = 5

    def is_available(self) -> bool:
        return platform.system() == "Darwin" and platform.machine() == "arm64"

    def _macos_version(self) -> Any:
        """Apple's GPU driver ships as part of the OS build itself (Metal
        driver isn't a separately versioned component), so the OS build
        number is the closest equivalent to a 'driver version' here."""
        try:
            out = subprocess.check_output(["sw_vers", "-buildVersion"], timeout=2)
            build = out.decode().strip()
            ver = platform.mac_ver()[0]
            return f"{ver} ({build})" if ver else build
        except Exception:
            return platform.mac_ver()[0] or None

    def _poll_impl(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "gpu_percent": None,
            "cpu_power_w": None,
            "gpu_power_w": None,
            "macos_version": self._macos_version(),
        }
        if psutil:
            data["ram_used_gb"] = round(psutil.virtual_memory().used / (1024 ** 3), 2)
            data["ram_total_gb"] = round(psutil.virtual_memory().total / (1024 ** 3), 2)
            data["cpu_percent"] = psutil.cpu_percent(interval=None)

        # Only attempt powermetrics if it won't block on a password prompt.
        try:
            out = subprocess.check_output(
                ["powermetrics", "-n", "1", "-i", "200", "--samplers", "gpu_power,cpu_power"],
                stderr=subprocess.DEVNULL, timeout=2,
            ).decode(errors="ignore")
            data["gpu_percent"] = _extract(out, "GPU HW active residency")
            data["cpu_power_w"] = _extract(out, "CPU Power")
            data["gpu_power_w"] = _extract(out, "GPU Power")
        except Exception:
            pass  # no cached sudo / not installed -- CPU/RAM stats still returned above

        return data


def _extract(text: str, prefix: str) -> Any:
    for line in text.splitlines():
        if line.strip().startswith(prefix):
            digits = "".join(c for c in line if c.isdigit() or c == ".")
            try:
                return float(digits)
            except ValueError:
                return None
    return None
