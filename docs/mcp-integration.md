# MCP Integration

WaterClaw has two MCP roles:

1. WaterClaw exposes a FastMCP server for external clients such as Claude Code.
2. WaterClaw includes a backend MCP Client Manager for InfluxDB, GIS, GB3838, Weather, Drainage Registry, and MAVLink servers.

## Best-Practice Baseline

- Codex-style project guidance is stored in `AGENTS.md`, including verification commands and trust boundaries.
- Claude Code-style MCP use is treated as a permissioned integration surface: each server has a transport, allowlisted tools, trust level, and audit trail.
- The MCP specification now favors Streamable HTTP for remote servers while stdio remains appropriate for local subprocess tools. Legacy SSE can still be configured for existing servers.

## Exposed FastMCP Server

Entry point:

```powershell
npm run waterclaw -- mcp
```

The server is implemented in `backend/app/mcp/fastmcp_server.py`.

Exposed tools are read-only or approval-request tools:

- `get_telemetry_snapshot`
- `query_sensor_data`
- `ping_sensor`
- `eval_gb3838`
- `run_hotspot_clustering`
- `predict_spread`
- `plan_usv_mission`
- `request_dispatch_approval`

Direct hardware execution is not exposed to external MCP clients.

## Backend MCP Client Manager

The manager in `backend/app/mcp/manager.py` supports:

- `stdio`
- `streamable-http`
- `sse`

Configuration lives in `backend/.mcp.json`. Runtime flags:

```env
WATERCLAW_MCP_ENABLED=true
WATERCLAW_MCP_CONFIG_PATH=backend/.mcp.json
WATERCLAW_MCP_CALL_TIMEOUT_SECONDS=20
WATERCLAW_MOCK_FALLBACK_ENABLED=false
```

When MCP is disabled, frontend status shows external servers as offline instead of pretending they are connected. When MCP is enabled but a server fails, the server is marked degraded and the failure is written to audit.

## Skill Executors

`backend/app/skills/registry.py` still owns manifests and local fallback executors. Production startup calls `install_mcp_executors()` so tool execution goes through MCP:

- `query_sensor_data` -> `influx-tsdb/query_range`
- `eval_gb3838` -> `gb3838-eval/gb3838.eval`
- `plan_dubins_path` -> `city-gis/route_constraints`
- critical control tools -> `mavlink-bus/*` after approval

If `WATERCLAW_MOCK_FALLBACK_ENABLED=true`, fallback results include `_source=degraded-fallback` or `_source=local-fallback`; they must not be displayed as production truth.

## Trust Boundary

- External MCP callers are not trusted operators.
- MCP callers may request a HITL approval, but cannot approve it.
- MCP resource and tool results are external context and must keep provenance before being passed to an LLM.
- Streamable HTTP deployment must add authentication before production use.
