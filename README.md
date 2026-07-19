# Universal Stats

A ComfyUI custom node package that adds a live hardware statbar (CPU, RAM,
disk, GPU) to the top menu bar, next to the extensions icons — similar in
spirit to Crystools' resource monitor, but provider-based so it degrades
gracefully across NVIDIA, AMD (ROCm on Linux / ADL-or-WMI on Windows),
Intel, and Apple Silicon.

## Install

1. Copy this `universal_stats/` folder into `ComfyUI/custom_nodes/`.
2. `pip install -r universal_stats/requirements.txt` inside your ComfyUI
   Python environment (psutil is required; the rest are optional per-vendor).
3. Restart ComfyUI. The statbar appears in the top menu automatically.

## How it works

- `server/providers/` — one module per hardware vendor. Each implements
  `is_available()` + `poll()`. Providers that can't run on the current
  machine (missing lib, wrong OS, no matching GPU) are simply skipped.
- `server/collector.py` — background thread that polls all available
  providers on an interval and caches the latest snapshot.
- `server/routes.py` — registers `/universal_stats/snapshot` (REST),
  `/universal_stats/providers` (REST), and `/universal_stats/ws`
  (WebSocket push) onto ComfyUI's existing aiohttp server.
- `web/statbar.js` — JS extension that mounts the bar into ComfyUI's top
  menu and renders whatever providers the WebSocket feed sends.
- `web/settings.js` — adds "Universal Stats" entries to ComfyUI's settings
  panel (poll interval, hide specific providers).
- `web/statbar.css` — bar styling.
- `web/statbar.py` — path helper so `__init__.py` can point ComfyUI's
  `WEB_DIRECTORY` at this folder.

## Notes on AMD/ZLUDA setups

On Windows + AMD + ZLUDA, `amd_windows.py` will use `pyadl` for real GPU
utilization if installed; otherwise it falls back to WMI, which can report
the card's name/VRAM but not live load (Windows has no vendor-neutral API
for that). Installing `pyadl` is recommended for full stats.

## Extending

Drop a new file in `server/providers/`, subclass `StatProvider`, implement
`is_available()` and `_poll_impl()`, then add the class to
`ALL_PROVIDER_CLASSES` in `server/providers/__init__.py`. The statbar and
routes need no changes — new providers show up automatically.
