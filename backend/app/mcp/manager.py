from __future__ import annotations

import asyncio
import json
import logging
import time
from contextlib import AsyncExitStack
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

from app.core.config import get_settings
from app.policy.audit import audit_log

logger = logging.getLogger("waterclaw.mcp")

ConnectionStatus = Literal["connected", "degraded", "offline", "calling"]
Permission = Literal["read-only", "read-write", "restricted"]
Transport = Literal["stdio", "sse", "streamable-http"]


@dataclass
class McpServerConfig:
    id: str
    name: str
    transport: Transport
    command: str | None = None
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    url: str | None = None
    endpoint: str = ""
    permission: Permission = "read-only"
    icon: str = "api"
    description: str = ""
    allowed_tools: list[str] = field(default_factory=list)


@dataclass
class McpServerStatus:
    id: str
    name: str
    icon: str
    endpoint: str
    status: ConnectionStatus
    permission: Permission
    capabilities: dict[str, int]
    callCount: int = 0
    latencyMs: int = 0
    lastCallAt: int | None = None
    description: str = ""
    transport: str = "configured"
    allowedTools: list[str] = field(default_factory=list)
    error: str | None = None


@dataclass
class McpConnection:
    config: McpServerConfig
    session: Any
    exit_stack: AsyncExitStack
    tools: list[Any] = field(default_factory=list)
    resources: list[Any] = field(default_factory=list)
    prompts: list[Any] = field(default_factory=list)


def _default_statuses() -> dict[str, McpServerStatus]:
    return {
        "litellm-gateway": McpServerStatus(
            id="litellm-gateway",
            name="LiteLLM-Gateway",
            icon="llm",
            endpoint="/api/agent/sessions/{session_id}/turn",
            status="connected",
            permission="restricted",
            capabilities={"resources": 1, "tools": 8, "prompts": 2},
            description="后端 Agent Host 通过 LiteLLM 执行真实 tool-calling loop。",
            allowedTools=["completion", "tool_choice"],
        ),
        "drainage-registry": McpServerStatus(
            id="drainage-registry",
            name="Drainage-Registry",
            icon="database",
            endpoint="mcp://drainage-registry.example.invalid/demo",
            status="offline",
            permission="read-only",
            capabilities={"resources": 0, "tools": 0, "prompts": 0},
            description="排污口、企业档案、历史稽核记录。",
            allowedTools=["drain.lookup", "incident.history"],
        ),
        "gb3838-eval": McpServerStatus(
            id="gb3838-eval",
            name="GB3838-Eval",
            icon="api",
            endpoint="mcp://standards.example.invalid/gb3838/evaluator",
            status="offline",
            permission="read-only",
            capabilities={"resources": 0, "tools": 0, "prompts": 0},
            description="地表水环境质量标准评价工具。",
            allowedTools=["gb3838.eval", "gb3838.thresholds"],
        ),
        "weather-api": McpServerStatus(
            id="weather-api",
            name="Weather-API",
            icon="weather",
            endpoint="mcp://weather.example.invalid/shanghai/stream",
            status="offline",
            permission="read-only",
            capabilities={"resources": 0, "tools": 0, "prompts": 0},
            description="实时气象、短临降雨、能见度。",
            allowedTools=["weather.now", "weather.forecast"],
        ),
        "mavlink-bus": McpServerStatus(
            id="mavlink-bus",
            name="MAVLink-Bus",
            icon="bus",
            endpoint="mcp://edge.example.invalid/mavlink",
            status="offline",
            permission="read-write",
            capabilities={"resources": 0, "tools": 0, "prompts": 0},
            description="USV 指令总线，高权限写入通道。critical 工具必须审批。",
            allowedTools=["mission.plan", "mission.dispatch"],
        ),
        "city-gis": McpServerStatus(
            id="city-gis",
            name="City-GIS",
            icon="map",
            endpoint="mcp://gis.example.invalid/city-gis",
            status="offline",
            permission="read-only",
            capabilities={"resources": 0, "tools": 0, "prompts": 0},
            description="河道、雨污管网、市政边界图层。",
            allowedTools=["gis.layers", "gis.route_constraints"],
        ),
        "influx-tsdb": McpServerStatus(
            id="influx-tsdb",
            name="InfluxDB-TSDB",
            icon="stream",
            endpoint="mcp://influxdb.example.invalid/waterclaw",
            status="offline",
            permission="read-only",
            capabilities={"resources": 0, "tools": 0, "prompts": 0},
            description="多源遥测时序数据库。",
            allowedTools=["query_range", "get_latest", "query.last"],
        ),
    }


class McpManager:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._servers: dict[str, McpServerStatus] = _default_statuses()
        self._configs: dict[str, McpServerConfig] = {}
        self._connections: dict[str, McpConnection] = {}
        self._startup_lock = asyncio.Lock()
        self._health_task: asyncio.Task[None] | None = None
        self._loaded = False

    def list_status(self) -> list[dict[str, Any]]:
        return [asdict(server) for server in self._servers.values()]

    async def ensure_started(self) -> None:
        if self._loaded:
            return
        async with self._startup_lock:
            if self._loaded:
                return
            self._configs = self._load_configs()
            self._apply_config_status()
            if self.settings.waterclaw_mcp_enabled:
                await self.connect_all(list(self._configs.values()))
                self.start_health_checks()
            self._loaded = True

    def _load_configs(self) -> dict[str, McpServerConfig]:
        path = Path(self.settings.waterclaw_mcp_config_path)
        if not path.exists():
            return {}
        raw = json.loads(path.read_text(encoding="utf-8"))
        servers = raw.get("mcpServers", {})
        configs: dict[str, McpServerConfig] = {}
        for server_id, cfg in servers.items():
            transport = cfg.get("transport") or ("stdio" if cfg.get("command") else "streamable-http")
            endpoint = cfg.get("url") or cfg.get("endpoint") or cfg.get("command") or f"mcp://{server_id}"
            configs[server_id] = McpServerConfig(
                id=server_id,
                name=cfg.get("name") or server_id,
                transport=transport,
                command=cfg.get("command"),
                args=list(cfg.get("args") or []),
                env={str(k): str(v) for k, v in (cfg.get("env") or {}).items()},
                url=cfg.get("url") or cfg.get("endpoint"),
                endpoint=endpoint,
                permission=cfg.get("permission", "read-only"),
                icon=cfg.get("icon", "api"),
                description=cfg.get("description", ""),
                allowed_tools=list(cfg.get("allowedTools") or cfg.get("allowed_tools") or []),
            )
        return configs

    def _apply_config_status(self) -> None:
        for config in self._configs.values():
            existing = self._servers.get(config.id)
            self._servers[config.id] = McpServerStatus(
                id=config.id,
                name=config.name,
                icon=config.icon,
                endpoint=config.endpoint or config.url or "",
                status="offline",
                permission=config.permission,
                capabilities=existing.capabilities if existing else {"resources": 0, "tools": 0, "prompts": 0},
                callCount=existing.callCount if existing else 0,
                latencyMs=existing.latencyMs if existing else 0,
                lastCallAt=existing.lastCallAt if existing else None,
                description=config.description or (existing.description if existing else ""),
                transport=config.transport,
                allowedTools=config.allowed_tools or (existing.allowedTools if existing else []),
            )

    async def connect_all(self, configs: list[McpServerConfig]) -> None:
        results = await asyncio.gather(*(self._connect_one(config) for config in configs), return_exceptions=True)
        for config, result in zip(configs, results):
            if isinstance(result, Exception):
                self._mark_status(config.id, "degraded", error=f"{type(result).__name__}: {result}")
                audit_log.write("mcp.connect_failed", {"server_id": config.id, "error": repr(result)})

    async def _connect_one(self, config: McpServerConfig) -> None:
        started = time.perf_counter()
        stack = AsyncExitStack()
        try:
            read, write = await self._open_transport(config, stack)
            from mcp import ClientSession

            session = await stack.enter_async_context(ClientSession(read, write))
            await asyncio.wait_for(session.initialize(), timeout=self.settings.waterclaw_mcp_call_timeout_seconds)
            tools = await self._safe_list(session, "list_tools")
            resources = await self._safe_list(session, "list_resources")
            prompts = await self._safe_list(session, "list_prompts")
            self._connections[config.id] = McpConnection(config=config, session=session, exit_stack=stack, tools=tools, resources=resources, prompts=prompts)
            self._mark_status(
                config.id,
                "connected",
                latency_ms=int((time.perf_counter() - started) * 1000),
                capabilities={"tools": len(tools), "resources": len(resources), "prompts": len(prompts)},
                error=None,
            )
            audit_log.write("mcp.connected", {"server_id": config.id, "transport": config.transport})
        except Exception:
            await stack.aclose()
            raise

    async def _open_transport(self, config: McpServerConfig, stack: AsyncExitStack) -> tuple[Any, Any]:
        if config.transport == "stdio":
            if not config.command:
                raise ValueError(f"MCP stdio server {config.id} missing command")
            from mcp.client.stdio import StdioServerParameters, stdio_client

            params = StdioServerParameters(command=config.command, args=config.args, env=config.env or None)
            return await stack.enter_async_context(stdio_client(params))
        if config.transport == "sse":
            if not config.url:
                raise ValueError(f"MCP SSE server {config.id} missing url")
            from mcp.client.sse import sse_client

            return await stack.enter_async_context(sse_client(config.url))
        if not config.url:
            raise ValueError(f"MCP streamable-http server {config.id} missing url")
        from mcp.client.streamable_http import streamablehttp_client

        read, write, _ = await stack.enter_async_context(streamablehttp_client(config.url))
        return read, write

    async def _safe_list(self, session: Any, method_name: str) -> list[Any]:
        try:
            result = await asyncio.wait_for(getattr(session, method_name)(), timeout=self.settings.waterclaw_mcp_call_timeout_seconds)
        except Exception:
            return []
        if hasattr(result, "tools"):
            return list(result.tools)
        if hasattr(result, "resources"):
            return list(result.resources)
        if hasattr(result, "prompts"):
            return list(result.prompts)
        if isinstance(result, list):
            return result
        return []

    def register_call(self, server_id: str, latency_ms: int | None = None) -> None:
        server = self._servers.get(server_id)
        if not server:
            return
        server.callCount += 1
        server.lastCallAt = int(time.time() * 1000)
        if latency_ms is not None:
            server.latencyMs = latency_ms
        if server.status != "degraded":
            server.status = "connected"

    def mark_calling(self, server_id: str) -> None:
        server = self._servers.get(server_id)
        if not server:
            return
        server.callCount += 1
        server.lastCallAt = int(time.time() * 1000)
        server.status = "calling"

    def mark_degraded(self, server_id: str, latency_ms: int | None = None) -> None:
        self._mark_status(server_id, "degraded", latency_ms=latency_ms)

    def _mark_status(
        self,
        server_id: str,
        status: ConnectionStatus,
        *,
        latency_ms: int | None = None,
        capabilities: dict[str, int] | None = None,
        error: str | None = None,
    ) -> None:
        server = self._servers.get(server_id)
        if not server:
            return
        server.status = status
        server.error = error
        if latency_ms is not None:
            server.latencyMs = latency_ms
        if capabilities is not None:
            server.capabilities = capabilities

    async def call_tool(self, server_id: str, tool_name: str, arguments: dict[str, Any]) -> Any:
        await self.ensure_started()
        conn = self._connections.get(server_id)
        if conn is None:
            raise ConnectionError(f"MCP server is not connected: {server_id}")
        if conn.config.allowed_tools and tool_name not in conn.config.allowed_tools:
            raise PermissionError(f"MCP tool not allowed for {server_id}: {tool_name}")
        started = time.perf_counter()
        self.mark_calling(server_id)
        try:
            result = await asyncio.wait_for(conn.session.call_tool(tool_name, arguments), timeout=self.settings.waterclaw_mcp_call_timeout_seconds)
            latency_ms = int((time.perf_counter() - started) * 1000)
            self.register_call(server_id, latency_ms)
            audit_log.write("mcp.tool_called", {"server_id": server_id, "tool": tool_name, "latency_ms": latency_ms})
            return self._normalize_result(result)
        except Exception as exc:
            self._mark_status(server_id, "degraded", error=f"{type(exc).__name__}: {exc}")
            audit_log.write("mcp.tool_failed", {"server_id": server_id, "tool": tool_name, "error": repr(exc)})
            raise

    async def list_resources(self, server_id: str) -> list[dict[str, Any]]:
        await self.ensure_started()
        conn = self._connections.get(server_id)
        if conn is None:
            self.register_call(server_id)
            return []
        return [self._object_to_dict(item) for item in conn.resources]

    async def read_resource(self, uri: str) -> dict[str, Any]:
        await self.ensure_started()
        for server_id, conn in self._connections.items():
            started = time.perf_counter()
            try:
                result = await asyncio.wait_for(conn.session.read_resource(uri), timeout=self.settings.waterclaw_mcp_call_timeout_seconds)
                self.register_call(server_id, int((time.perf_counter() - started) * 1000))
                audit_log.write("mcp.resource_read", {"server_id": server_id, "uri": uri})
                return self._normalize_result(result)
            except Exception:
                continue
        raise KeyError(f"MCP resource not found or unreadable: {uri}")

    def start_health_checks(self, interval: float = 30.0) -> None:
        if self._health_task and not self._health_task.done():
            return

        async def _loop() -> None:
            while True:
                await asyncio.sleep(interval)
                for server_id, conn in list(self._connections.items()):
                    try:
                        if hasattr(conn.session, "send_ping"):
                            await asyncio.wait_for(conn.session.send_ping(), timeout=5)
                        self._mark_status(server_id, "connected", error=None)
                    except Exception as exc:
                        self._mark_status(server_id, "degraded", error=f"{type(exc).__name__}: {exc}")

        self._health_task = asyncio.create_task(_loop())

    async def shutdown(self) -> None:
        if self._health_task:
            self._health_task.cancel()
        for conn in list(self._connections.values()):
            await conn.exit_stack.aclose()
        self._connections.clear()

    def _normalize_result(self, result: Any) -> dict[str, Any]:
        if hasattr(result, "model_dump"):
            return result.model_dump(mode="json", exclude_none=True)
        if isinstance(result, dict):
            return result
        if isinstance(result, list):
            return {"items": [self._object_to_dict(item) for item in result]}
        return {"value": result}

    def _object_to_dict(self, item: Any) -> dict[str, Any]:
        if hasattr(item, "model_dump"):
            return item.model_dump(mode="json", exclude_none=True)
        if isinstance(item, dict):
            return item
        return {key: value for key, value in vars(item).items() if not key.startswith("_")} if hasattr(item, "__dict__") else {"value": str(item)}


mcp_manager = McpManager()

