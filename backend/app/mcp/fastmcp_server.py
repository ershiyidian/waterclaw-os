from __future__ import annotations

import argparse
import asyncio
import json
from typing import Any

from app.agent.state import session_store
from app.mcp.waterclaw_server import read_waterclaw_resource
from app.policy.approval import approval_service
from app.skills.registry import ExecutionContext, skill_registry

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as exc:  # pragma: no cover - exercised only when env is incomplete.
    raise RuntimeError(
        "The official MCP Python SDK is not installed. Run `npm run waterclaw -- install` so Conda installs backend/requirements.txt."
    ) from exc


mcp = FastMCP("WaterClaw OS", stateless_http=True, json_response=True)


async def _execute(name: str, args: dict[str, Any]) -> dict[str, Any]:
    return await skill_registry.execute(name, args, ExecutionContext(session_id="mcp-waterclaw", operator_id="external-mcp"))


@mcp.tool()
async def get_telemetry_snapshot() -> dict[str, Any]:
    """Return a compact WaterClaw telemetry snapshot for incident triage."""
    return {
        "stations": {
            "TP-01": {"turbidityNtu": 39, "nh3nMgL": 0.42, "grade": "III"},
            "TP-03": {"turbidityNtu": 286, "nh3nMgL": 1.8, "grade": "V", "risk": "abnormal spike"},
            "TP-05": {"turbidityNtu": 63, "nh3nMgL": 0.71, "grade": "III"},
        },
        "fleet": {
            "USV-01": {"mode": "AUTO", "batteryPct": 85, "role": "intercept sampler"},
            "USV-02": {"mode": "HOLD", "batteryPct": 92, "role": "sentry monitor"},
        },
        "incident": (await session_store.get("mcp-waterclaw")).current_mission,
    }


@mcp.tool()
async def query_sensor_data(stations: list[str], window: str = "5m") -> dict[str, Any]:
    """Read recent telemetry series from WaterClaw time-series data."""
    return await _execute("query_sensor_data", {"stations": stations, "window": window})


@mcp.tool()
async def ping_sensor(sensor_id: str, checks: list[str] | None = None) -> dict[str, Any]:
    """Check sensor calibration, communication, and drift before blaming pollution."""
    return await _execute("ping_sensor", {"id": sensor_id, "checks": checks or ["calibration", "drift", "link"]})


@mcp.tool()
async def eval_gb3838(stations: list[str], target_class: str = "III") -> dict[str, Any]:
    """Evaluate stations against GB3838 target class."""
    return await _execute("eval_gb3838", {"stations": stations, "targetClass": target_class})


@mcp.tool()
async def run_hotspot_clustering(k: int = 3, features: list[str] | None = None, station: str = "TP-03") -> dict[str, Any]:
    """Locate likely pollution hotspots from multivariate telemetry."""
    return await _execute("run_kmeans", {"k": k, "features": features or ["turbidity", "nh3n", "voc"], "station": station})


@mcp.tool()
async def predict_spread(station: str = "TP-03", horizon: str = "2h", confidence: float = 0.95) -> dict[str, Any]:
    """Forecast pollution spread and uncertainty for a station."""
    return await _execute("lstm_predict", {"station": station, "horizon": horizon, "confidence": confidence})


@mcp.tool()
async def plan_usv_mission(usv: str = "USV-01", target: str = "DP-03") -> dict[str, Any]:
    """Plan a task-level USV mission without writing to MAVLink."""
    return await _execute("plan_dubins_path", {"usv": usv, "target": target})


@mcp.tool()
async def request_dispatch_approval(usv: str, mission: str, target: str, reason: str) -> dict[str, Any]:
    """Create a HITL approval request for a high-risk dispatch action; does not dispatch by itself."""
    approval = approval_service.create(
        session_id="mcp-waterclaw",
        tool_name="dispatch_usv",
        args={"usv": usv, "mission": mission, "target": target},
        risk_level="critical",
        description=f"MCP external agent requested dispatch approval. Reason: {reason}",
    )
    return {"approval": approval.public(requires_code=False), "argsHash": approval.args_hash, "summary": "审批请求已创建，等待 WaterClaw HMI 操作员确认。"}


@mcp.resource("waterclaw://stations/{station_id}")
def station_resource(station_id: str) -> str:
    """Station telemetry and target-class context."""
    return read_waterclaw_resource(f"waterclaw://stations/{station_id}")


@mcp.resource("waterclaw://drains/{drain_id}")
def drain_resource(drain_id: str) -> str:
    """Drain registry and historical anomaly context."""
    return read_waterclaw_resource(f"waterclaw://drains/{drain_id}")


@mcp.resource("waterclaw://fleet/{usv_id}")
def fleet_resource(usv_id: str) -> str:
    """USV profile and current role context."""
    return read_waterclaw_resource(f"waterclaw://fleet/{usv_id}")


@mcp.resource("waterclaw://incidents/{incident_id}")
def incident_resource(incident_id: str) -> str:
    """Incident state and suspected source context."""
    return read_waterclaw_resource(f"waterclaw://incidents/{incident_id}")


@mcp.prompt()
def incident_triage(incident_id: str = "INC-20260428-003") -> str:
    """Prompt for triaging a water-quality anomaly."""
    return (
        f"Analyze {incident_id}. First verify sensor health, then compare upstream/downstream telemetry, "
        "evaluate GB3838, correlate drainage registry and weather, forecast spread, and request HITL approval before dispatch."
    )


@mcp.prompt()
def gb3838_report(stations_json: str = '["TP-01","TP-03","TP-05"]', target_class: str = "III") -> str:
    """Prompt for generating a GB3838 compliance report."""
    try:
        stations = json.loads(stations_json)
    except json.JSONDecodeError:
        stations = stations_json
    return f"Generate a concise GB3838 {target_class} compliance report for stations {stations}. Include exceedance duration and root-cause hypotheses."


@mcp.prompt()
def dispatch_safety_check(usv: str = "USV-01", target: str = "DP-03") -> str:
    """Prompt for reviewing high-risk USV dispatch arguments."""
    return (
        f"Review whether {usv} can be dispatched to {target}. Check battery, comms, route constraints, weather, "
        "mission risk, and whether a valid WaterClaw approval token exists. Never perform direct dispatch without approval."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="WaterClaw OS MCP server")
    parser.add_argument("--transport", choices=["stdio", "streamable-http", "sse"], default="stdio")
    args = parser.parse_args()
    maybe_result = mcp.run(transport=args.transport)
    if asyncio.iscoroutine(maybe_result):
        asyncio.run(maybe_result)


if __name__ == "__main__":
    main()
