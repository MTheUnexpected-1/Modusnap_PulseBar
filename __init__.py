"""
Universal Stats - a ComfyUI custom node package that adds a live hardware
statbar (CPU/RAM/disk/GPU) to the top menu bar, next to the extensions icons.

Install: drop this folder in ComfyUI/custom_nodes/, restart ComfyUI.
No workflow nodes are registered -- this package only adds a server-side
polling collector + REST/WebSocket routes + a JS extension for the UI.
"""

from __future__ import annotations

from .server.routes import register_routes
from .web.statbar import WEB_DIR

# ComfyUI serves this directory at /extensions/universal_stats/*
WEB_DIRECTORY = "./web"

# No custom graph nodes -- this package is UI/telemetry only.
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

register_routes()

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
