"""Provider registry. `available_providers()` returns instances of every
provider whose is_available() check passes on this machine, ordered by
priority so the collector polls GPUs before generic fallbacks."""

from __future__ import annotations
from typing import List

from .base import StatProvider
from .cpu import CPUProvider
from .disk import DiskProvider
from .nvidia import NvidiaProvider
from .amd_rocm import AMDRocmProvider
from .amd_windows import AMDWindowsProvider
from .intel import IntelProvider
from .apple import AppleProvider
from .windows import WindowsProvider

ALL_PROVIDER_CLASSES = [
    NvidiaProvider,
    AMDRocmProvider,
    AMDWindowsProvider,
    AppleProvider,
    IntelProvider,
    WindowsProvider,
    CPUProvider,
    DiskProvider,
]


def available_providers() -> List[StatProvider]:
    instances = []
    for cls in ALL_PROVIDER_CLASSES:
        try:
            inst = cls()
            if inst.is_available():
                instances.append(inst)
        except Exception:
            continue  # a broken provider (missing lib, bad env) never blocks the rest
    return sorted(instances, key=lambda p: p.priority)


__all__ = [
    "StatProvider",
    "CPUProvider",
    "DiskProvider",
    "NvidiaProvider",
    "AMDRocmProvider",
    "AMDWindowsProvider",
    "IntelProvider",
    "AppleProvider",
    "WindowsProvider",
    "available_providers",
]
