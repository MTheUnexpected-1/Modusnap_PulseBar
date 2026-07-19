"""AMD GPU provider for Linux/ROCm, using `rocm-smi --json` via subprocess.

Kept dependency-free (no python ROCm bindings required) since rocm-smi ships
with any working ROCm install and its JSON output is stable across versions.
"""

from __future__ import annotations
import json
import shutil
import subprocess
from typing import Any, Dict, List

from .base import StatProvider


class AMDRocmProvider(StatProvider):
    id = "amd_rocm"
    label = "AMD GPU (ROCm)"
    priority = 5

    def __init__(self) -> None:
        super().__init__()
        self._binary = shutil.which("rocm-smi")

    def is_available(self) -> bool:
        return self._binary is not None

    def _run(self, *args: str) -> Dict[str, Any]:
        out = subprocess.check_output(
            [self._binary, *args, "--json"], stderr=subprocess.DEVNULL, timeout=5
        )
        return json.loads(out.decode(errors="ignore"))

    def _driver_version(self) -> Any:
        try:
            info = self._run("--showdriverversion")
            for card_key, val in info.items():
                if card_key.startswith("card") or card_key == "system":
                    return val.get("Driver version") or val
        except Exception:
            pass
        return None

    def _poll_impl(self) -> Dict[str, Any]:
        usage = self._run("--showuse", "--showmemuse", "--showtemp", "--showpower")
        driver_version = self._driver_version()
        gpus: List[Dict[str, Any]] = []
        for card_key, info in usage.items():
            if not card_key.startswith("card"):
                continue
            gpus.append({
                "index": card_key.replace("card", ""),
                "gpu_percent": _to_float(info.get("GPU use (%)")),
                "vram_percent": _to_float(info.get("GPU memory use (%)")),
                "temp_c": _to_float(info.get("Temperature (Sensor edge) (C)")),
                "power_w": _to_float(info.get("Average Graphics Package Power (W)")),
            })
        return {"gpus": gpus, "driver_version": driver_version}


def _to_float(val: Any) -> Any:
    try:
        return float(val)
    except (TypeError, ValueError):
        return None
