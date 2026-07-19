"""HTTP + WebSocket routes for Universal Stats, registered on ComfyUI's
existing aiohttp PromptServer instance (no separate port needed).
"""

from __future__ import annotations
import asyncio
import json

from aiohttp import web

from .collector import collector

try:
    from server import PromptServer  # ComfyUI's server module
except ImportError:  # pragma: no cover - allows standalone import/testing
    PromptServer = None


def register_routes() -> None:
    """Call once from __init__.py to attach our endpoints to ComfyUI's server."""
    if PromptServer is None:
        return

    routes = PromptServer.instance.routes

    @routes.get("/universal_stats/snapshot")
    async def get_snapshot(request: web.Request) -> web.Response:
        return web.json_response(collector.get_snapshot())

    @routes.get("/universal_stats/providers")
    async def get_providers(request: web.Request) -> web.Response:
        return web.json_response(collector.describe_providers())

    @routes.get("/universal_stats/ws")
    async def stats_ws(request: web.Request) -> web.WebSocketResponse:
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        try:
            while not ws.closed:
                await ws.send_str(json.dumps(collector.get_snapshot()))
                await asyncio.sleep(collector.interval_s)
        except (ConnectionResetError, asyncio.CancelledError):
            pass
        finally:
            if not ws.closed:
                await ws.close()
        return ws

    collector.start()
