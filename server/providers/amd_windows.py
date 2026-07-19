"""AMD GPU provider for Windows.

Tries `pyadl` (AMD Display Library bindings) first for real utilization/temp/
fan data. Falls back to WMI (name + driver VRAM only, no live load) so the
statbar still shows *something* on a bare ZLUDA setup with no ADL installed.
"""

from __future__ import annotations
import platform
from typing import Any, Dict, List

from .base import StatProvider

try:
    from pyadl import ADLManager  # type: ignore
except ImportError:  # pragma: no cover
    ADLManager = None

try:
    import wmi  # type: ignore
except ImportError:  # pragma: no cover
    wmi = None


class AMDWindowsProvider(StatProvider):
    id = "amd_windows"
    label = "AMD GPU (Windows)"
    priority = 6  # slightly after amd_rocm/nvidia so ROCm wins if both present

    def is_available(self) -> bool:
        if platform.system() != "Windows":
            return False
        return ADLManager is not None or wmi is not None

    def _poll_impl(self) -> Dict[str, Any]:
        driver_info = self._driver_versions()
        if ADLManager is not None:
            gpus = self._poll_adl()
        else:
            gpus = self._poll_wmi()
        # Merge WMI driver_version/date onto whichever list we built, matched by index.
        for i, g in enumerate(gpus):
            match = driver_info[i] if i < len(driver_info) else {}
            g["driver_version"] = match.get("driver_version")
            g["driver_date"] = match.get("driver_date")
        return {"gpus": gpus}

    def _driver_versions(self) -> List[Dict[str, Any]]:
        if wmi is None:
            return []
        c = wmi.WMI()
        out = []
        for ctrl in c.Win32_VideoController():
            name = ctrl.Name or ""
            if "AMD" not in name and "Radeon" not in name:
                continue
            out.append({
                "driver_version": ctrl.DriverVersion,
                "driver_date": str(ctrl.DriverDate) if ctrl.DriverDate else None,
            })
        return out

    def _poll_adl(self) -> List[Dict[str, Any]]:
        gpus = []
        devices = ADLManager.getInstance().getDevices()
        for i, dev in enumerate(devices):
            try:
                load = dev.getCurrentUsage()
            except Exception:
                load = None
            try:
                temp = dev.getCurrentTemperature()
            except Exception:
                temp = None
            gpus.append({
                "index": i,
                "name": dev.adapterName.decode() if isinstance(dev.adapterName, bytes) else dev.adapterName,
                "gpu_percent": load,
                "temp_c": temp,
            })
        return gpus

    def _poll_wmi(self) -> List[Dict[str, Any]]:
        c = wmi.WMI()
        gpus = []
        for i, controller in enumerate(c.Win32_VideoController()):
            if "AMD" not in (controller.Name or "") and "Radeon" not in (controller.Name or ""):
                continue
            vram_gb = None
            if controller.AdapterRAM:
                vram_gb = round(controller.AdapterRAM / (1024 ** 3), 2)
            gpus.append({
                "index": i,
                "name": controller.Name,
                "vram_total_gb": vram_gb,
                "gpu_percent": None,  # WMI has no reliable live load without ADL
                "temp_c": None,
            })
        return gpus
