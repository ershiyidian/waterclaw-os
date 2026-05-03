from __future__ import annotations

from typing import Any, Awaitable, Callable

from app.core.config import Settings
from app.mcp.manager import McpManager
from app.skills.registry import (
    ExecutionContext,
    dispatch_usv,
    eval_gb3838,
    lstm_predict,
    ping_sensor,
    plan_dubins_path,
    query_sensor_data,
    request_estop,
    rtl_usv,
    run_kmeans,
)

MockExecutor = Callable[[dict[str, Any], ExecutionContext], Awaitable[dict[str, Any]]]


class McpBackedExecutor:
    def __init__(
        self,
        *,
        server_id: str,
        tool_name: str,
        transform_args: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
        fallback: MockExecutor | None = None,
        fallback_label: str,
    ) -> None:
        self.server_id = server_id
        self.tool_name = tool_name
        self.transform_args = transform_args or (lambda args: args)
        self.fallback = fallback
        self.fallback_label = fallback_label

    async def __call__(self, args: dict[str, Any], ctx: ExecutionContext) -> dict[str, Any]:
        if ctx.mcp_manager is not None:
            try:
                result = await ctx.mcp_manager.call_tool(self.server_id, self.tool_name, self.transform_args(args))
                return {"source": "mcp", "server": self.server_id, "tool": self.tool_name, "result": result, "summary": self._summary(result)}
            except Exception as exc:
                if not ctx.allow_mock_fallback or self.fallback is None:
                    raise
                degraded = await self.fallback(args, ctx)
                degraded["_source"] = "degraded-fallback"
                degraded["_mcpError"] = f"{type(exc).__name__}: {exc}"
                degraded["summary"] = f"{self.fallback_label}（MCP {self.server_id}/{self.tool_name} 不可用，已显式降级）：{degraded.get('summary', '')}"
                return degraded
        if self.fallback is None or not ctx.allow_mock_fallback:
            raise ConnectionError(f"MCP manager is unavailable for {self.server_id}/{self.tool_name}")
        degraded = await self.fallback(args, ctx)
        degraded["_source"] = "local-fallback"
        degraded["summary"] = f"{self.fallback_label}（未配置 MCP manager，已显式降级）：{degraded.get('summary', '')}"
        return degraded

    def _summary(self, result: Any) -> str:
        if isinstance(result, dict):
            if isinstance(result.get("summary"), str):
                return result["summary"]
            if isinstance(result.get("content"), list) and result["content"]:
                first = result["content"][0]
                if isinstance(first, dict):
                    text = first.get("text") or first.get("content")
                    if text:
                        return str(text)[:240]
        return f"MCP {self.server_id}/{self.tool_name} 调用完成。"


def _sensor_args(args: dict[str, Any]) -> dict[str, Any]:
    return {
        "stations": args["stations"],
        "window": args.get("window", "5m"),
        "fields": ["turbidity_ntu", "nh3n_mgl", "do_mgl", "ph"],
    }


def _gb_args(args: dict[str, Any]) -> dict[str, Any]:
    return {"stations": args["stations"], "targetClass": args.get("targetClass", "III")}


def _dispatch_args(args: dict[str, Any]) -> dict[str, Any]:
    return {"usv": args["usv"], "mission": args["mission"], "target": args["target"]}


def install_mcp_executors(registry: Any, mcp_manager: McpManager, settings: Settings) -> None:
    allow_fallback = settings.waterclaw_mock_fallback_enabled
    registry.replace_executor(
        "query_sensor_data",
        McpBackedExecutor(
            server_id="influx-tsdb",
            tool_name="query_range",
            transform_args=_sensor_args,
            fallback=query_sensor_data if allow_fallback else None,
            fallback_label="传感器数据读取",
        ),
    )
    registry.replace_executor(
        "ping_sensor",
        McpBackedExecutor(
            server_id="influx-tsdb",
            tool_name="sensor_health",
            fallback=ping_sensor if allow_fallback else None,
            fallback_label="传感器自检",
        ),
    )
    registry.replace_executor(
        "eval_gb3838",
        McpBackedExecutor(
            server_id="gb3838-eval",
            tool_name="gb3838.eval",
            transform_args=_gb_args,
            fallback=eval_gb3838 if allow_fallback else None,
            fallback_label="GB3838 评价",
        ),
    )
    registry.replace_executor(
        "run_kmeans",
        McpBackedExecutor(
            server_id="influx-tsdb",
            tool_name="cluster_hotspots",
            fallback=run_kmeans if allow_fallback else None,
            fallback_label="热点聚类",
        ),
    )
    registry.replace_executor(
        "lstm_predict",
        McpBackedExecutor(
            server_id="influx-tsdb",
            tool_name="forecast_lstm",
            fallback=lstm_predict if allow_fallback else None,
            fallback_label="趋势预测",
        ),
    )
    registry.replace_executor(
        "plan_dubins_path",
        McpBackedExecutor(
            server_id="city-gis",
            tool_name="route_constraints",
            fallback=plan_dubins_path if allow_fallback else None,
            fallback_label="路径规划",
        ),
    )
    registry.replace_executor(
        "dispatch_usv",
        McpBackedExecutor(
            server_id="mavlink-bus",
            tool_name="mission.dispatch",
            transform_args=_dispatch_args,
            fallback=dispatch_usv if allow_fallback else None,
            fallback_label="USV 派遣",
        ),
    )
    registry.replace_executor(
        "rtl_usv",
        McpBackedExecutor(
            server_id="mavlink-bus",
            tool_name="mission.rtl",
            fallback=rtl_usv if allow_fallback else None,
            fallback_label="USV 返航请求",
        ),
    )
    registry.replace_executor(
        "request_estop",
        McpBackedExecutor(
            server_id="mavlink-bus",
            tool_name="safety.estop",
            fallback=request_estop if allow_fallback else None,
            fallback_label="E-STOP 请求",
        ),
    )
