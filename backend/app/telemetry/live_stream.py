from __future__ import annotations

import asyncio
import math
import time
from typing import Any

from app.agent.events import AgentEvent
from app.core.config import get_settings
from app.mcp.manager import mcp_manager


class TelemetryStream:
    def __init__(self) -> None:
        self._subscribers: dict[str, asyncio.Queue[dict[str, Any]]] = {}
        self._poll_task: asyncio.Task[None] | None = None

    async def subscribe(self, session_id: str) -> asyncio.Queue[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=32)
        self._subscribers[session_id] = queue
        self.ensure_started()
        await self._put_latest(queue)
        return queue

    def unsubscribe(self, session_id: str) -> None:
        self._subscribers.pop(session_id, None)

    def ensure_started(self) -> None:
        if self._poll_task and not self._poll_task.done():
            return
        self._poll_task = asyncio.create_task(self.poll_loop())

    async def poll_loop(self) -> None:
        while True:
            telemetry = await self._latest()
            for queue in list(self._subscribers.values()):
                await self._put(queue, telemetry)
            await asyncio.sleep(1.5)

    async def _put_latest(self, queue: asyncio.Queue[dict[str, Any]]) -> None:
        await self._put(queue, await self._latest())

    async def _put(self, queue: asyncio.Queue[dict[str, Any]], telemetry: dict[str, Any]) -> None:
        try:
            queue.put_nowait(telemetry)
        except asyncio.QueueFull:
            _ = queue.get_nowait()
            queue.put_nowait(telemetry)

    async def _latest(self) -> dict[str, Any]:
        settings = get_settings()
        if settings.waterclaw_mcp_enabled:
            try:
                result = await mcp_manager.call_tool("influx-tsdb", "get_latest", {})
                if isinstance(result, dict) and "telemetry" in result:
                    return result["telemetry"]
                if isinstance(result, dict):
                    return result
            except Exception:
                if not settings.waterclaw_mock_fallback_enabled:
                    raise
        return self._fallback_snapshot()

    def _fallback_snapshot(self) -> dict[str, Any]:
        now = time.time()
        wave = math.sin(now / 8)
        return {
            "rtk": {
                "status": "FIXED",
                "precisionCm": round(1.2 + wave * 0.2, 1),
                "hdop": round(0.8 + wave * 0.06, 2),
                "satellites": {"gps": 12, "bds": 8, "gal": 6, "glo": 3},
                "skyPlot": [],
            },
            "link": {
                "primary": {"name": "4G", "rssiDbm": int(-67 + wave * 4), "latencyMs": int(28 + wave * 8), "packetLossPct": round(0.2 + abs(wave) * 0.3, 1)},
                "backup": {"name": "BDS-SMS", "online": True, "latencyMs": 780},
                "heartbeatMs": int(28 + wave * 8),
            },
            "edge": {"loadPct": int(44 + wave * 8), "temperatureC": int(54 + wave * 3), "fps": 28, "targetFps": 30, "model": "YOLOv8s-water-v2.3", "queueDepth": 0, "queueCapacity": 16},
            "weather": {"windDirection": "东南", "windDeg": 130, "windSpeedMps": round(2.4 + wave * 0.4, 1), "pressureHpa": 1017, "rainfallMm": 0, "visibilityKm": 8.6, "condition": "晴"},
            "_source": "backend-fallback",
        }

    async def events(self, session_id: str):
        queue = await self.subscribe(session_id)
        try:
            while True:
                telemetry = await queue.get()
                yield AgentEvent("telemetry.snapshot", {"telemetry": telemetry})
        finally:
            self.unsubscribe(session_id)


telemetry_stream = TelemetryStream()
