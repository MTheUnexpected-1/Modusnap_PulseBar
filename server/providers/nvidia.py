"""NVIDIA GPU provider via pynvml (NVML). Reports per-GPU util/vram/temp/power."""

from __future__ import annotations
from typing import Any, Dict, List

from .base import StatProvider

try:
    import pynvml
except ImportError:  # pragma: no cover
    pynvml = None


class NvidiaProvider(StatProvider):
    id = "nvidia"
    label = "NVIDIA GPU"
    priority = 5  # try before generic/base providers

    def __init__(self) -> None:
        super().__init__()
        self._initialized = False

    def is_available(self) -> bool:
        if pynvml is None:
            return False
        try:
            pynvml.nvmlInit()
            self._initialized = True
            return pynvml.nvmlDeviceGetCount() > 0
        except Exception:
            return False

    def _poll_impl(self) -> Dict[str, Any]:
        if not self._initialized:
            pynvml.nvmlInit()
            self._initialized = True

        try:
            driver_version = pynvml.nvmlSystemGetDriverVersion()
            if isinstance(driver_version, bytes):
                driver_version = driver_version.decode()
        except Exception:
            driver_version = None
        try:
            cuda_version = pynvml.nvmlSystemGetCudaDriverVersion()
        except Exception:
            cuda_version = None

        gpus: List[Dict[str, Any]] = []
        for i in range(pynvml.nvmlDeviceGetCount()):
            handle = pynvml.nvmlDeviceGetHandleByIndex(i)
            mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
            util = pynvml.nvmlDeviceGetUtilizationRates(handle)
            try:
                temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
            except Exception:
                temp = None
            try:
                power_w = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0
            except Exception:
                power_w = None
            gpus.append({
                "index": i,
                "name": pynvml.nvmlDeviceGetName(handle) if isinstance(
                    pynvml.nvmlDeviceGetName(handle), str
                ) else pynvml.nvmlDeviceGetName(handle).decode(),
                "vram_used_gb": round(mem.used / (1024 ** 3), 2),
                "vram_total_gb": round(mem.total / (1024 ** 3), 2),
                "gpu_percent": util.gpu,
                "vram_percent": round(mem.used / mem.total * 100, 1) if mem.total else None,
                "temp_c": temp,
                "power_w": round(power_w, 1) if power_w is not None else None,
            })
        return {"gpus": gpus, "driver_version": driver_version, "cuda_version": cuda_version}
