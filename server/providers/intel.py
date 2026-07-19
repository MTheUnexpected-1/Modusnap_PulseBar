"""Intel provider: CPU package temp/power via psutil sensors, plus integrated
GPU name detection. Intel discrete Arc utilization needs `intel_gpu_top`
(Linux) which we shell out to when present; otherwise GPU fields stay None.
"""

from __future__ import annotations
import platform
import re
import shutil
import subprocess
from typing import Any, Dict

from .base import StatProvider

try:
    import psutil
except ImportError:  # pragma: no cover
    psutil = None

try:
    import wmi  # type: ignore
except ImportError:  # pragma: no cover
    wmi = None


class IntelProvider(StatProvider):
    id = "intel"
    label = "Intel"
    priority = 30

    def __init__(self) -> None:
        super().__init__()
        self._gpu_top = shutil.which("intel_gpu_top")

    def is_available(self) -> bool:
        return platform.processor().lower().find("intel") != -1 or psutil is not None

    def _poll_impl(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "package_temp_c": None,
            "gpu_percent": None,
            "driver_version": self._driver_version(),
        }
        if psutil and hasattr(psutil, "sensors_temperatures"):
            temps = psutil.sensors_temperatures() or {}
            for key in ("coretemp", "cpu_thermal"):
                if key in temps and temps[key]:
                    data["package_temp_c"] = temps[key][0].current
                    break
        if self._gpu_top:
            data["gpu_percent"] = self._read_gpu_top()
        return data

    def _driver_version(self) -> Any:
        """Windows: pull the Intel adapter's driver string from WMI. Linux:
        the i915/xe kernel driver has no separate 'version' the way vendor
        drivers do, so report the kernel release instead."""
        if platform.system() == "Windows" and wmi is not None:
            try:
                c = wmi.WMI()
                for ctrl in c.Win32_VideoController():
                    if "Intel" in (ctrl.Name or ""):
                        return ctrl.DriverVersion
            except Exception:
                return None
        elif platform.system() == "Linux":
            return platform.release()  # i915/xe ships in-kernel, no standalone version
        return None

    def _read_gpu_top(self) -> Any:
        try:
            out = subprocess.check_output(
                [self._gpu_top, "-J", "-s", "1", "-o", "-"],
                stderr=subprocess.DEVNULL, timeout=3,
            ).decode(errors="ignore")
            match = re.search(r'"Render/3D/0":\s*{\s*"busy":\s*([\d.]+)', out)
            return float(match.group(1)) if match else None
        except Exception:
            return None
