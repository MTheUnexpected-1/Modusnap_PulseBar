"""Generic Windows system provider -- OS build, uptime, battery, and a
driver-version summary table for every display adapter WMI knows about
(vendor-agnostic; amd_windows.py / nvidia.py still own live GPU load)."""

from __future__ import annotations
import platform
import time
from typing import Any, Dict, List

from .base import StatProvider

try:
    import psutil
except ImportError:  # pragma: no cover
    psutil = None

try:
    import wmi  # type: ignore
except ImportError:  # pragma: no cover
    wmi = None


class WindowsProvider(StatProvider):
    id = "windows"
    label = "Windows"
    priority = 15

    def is_available(self) -> bool:
        return platform.system() == "Windows"

    def _poll_impl(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "os_build": platform.version(),
            "os_release": platform.release(),
            "uptime_s": round(time.time() - psutil.boot_time(), 0) if psutil else None,
            "battery_percent": None,
            "display_adapters": self._adapter_drivers(),
        }
        if psutil and hasattr(psutil, "sensors_battery"):
            batt = psutil.sensors_battery()
            if batt:
                data["battery_percent"] = batt.percent
                data["on_ac_power"] = batt.power_plugged
        return data

    def _adapter_drivers(self) -> List[Dict[str, Any]]:
        """Every GPU's driver version/date, regardless of vendor -- useful for
        spotting a stale AMD/NVIDIA driver without opening Device Manager."""
        if wmi is None:
            return []
        c = wmi.WMI()
        adapters = []
        for ctrl in c.Win32_VideoController():
            adapters.append({
                "name": ctrl.Name,
                "driver_version": ctrl.DriverVersion,
                "driver_date": str(ctrl.DriverDate) if ctrl.DriverDate else None,
                "vram_total_gb": round(ctrl.AdapterRAM / (1024 ** 3), 2) if ctrl.AdapterRAM else None,
            })
        return adapters
