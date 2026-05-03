from __future__ import annotations

import json
from typing import Any

from app.skills.registry import ExecutionContext, skill_registry


async def call_waterclaw_tool(name: str, args: dict[str, Any], session_id: str = "mcp-session") -> dict[str, Any]:
    return await skill_registry.execute(name, args, ExecutionContext(session_id=session_id, operator_id="external-mcp"))


def list_waterclaw_tools() -> list[dict[str, Any]]:
    return [
        {
            "name": f"waterclaw.{manifest.name}",
            "description": manifest.description,
            "inputSchema": manifest.input_schema,
            "riskLevel": manifest.risk_level,
            "requiredMcp": manifest.required_mcp,
        }
        for manifest in skill_registry.list()
        if manifest.name not in {"dispatch_usv", "notify_authority"}
    ] + [
        {
            "name": "waterclaw.request_dispatch_approval",
            "description": "Create a backend HITL approval request for a high-risk dispatch action. Direct dispatch is not exposed to external agents.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "usv": {"type": "string"},
                    "mission": {"type": "string"},
                    "target": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["usv", "mission", "target", "reason"],
            },
            "riskLevel": "critical",
            "requiredMcp": ["mavlink-bus"],
        }
    ]


def list_waterclaw_resources() -> list[dict[str, str]]:
    return [
        {"uri": "waterclaw://stations/TP-03", "name": "TP-03 station context", "mimeType": "application/json"},
        {"uri": "waterclaw://drains/DP-03", "name": "DP-03 drainage registry", "mimeType": "application/json"},
        {"uri": "waterclaw://fleet/USV-01", "name": "USV-01 fleet state", "mimeType": "application/json"},
        {"uri": "waterclaw://incidents/INC-20260428-003", "name": "Current illegal discharge incident", "mimeType": "application/json"},
    ]


def read_waterclaw_resource(uri: str) -> str:
    resources = {
        "waterclaw://stations/TP-03": {"station": "TP-03", "targetClass": "III", "risk": "turbidity spikes in last 5 minutes"},
        "waterclaw://drains/DP-03": {"drain": "DP-03", "owner": "化工园雨水井", "history": "30天内3次夜间异常"},
        "waterclaw://fleet/USV-01": {"usv": "USV-01", "role": "intercept sampler", "batteryPct": 85},
        "waterclaw://incidents/INC-20260428-003": {"incident": "INC-20260428-003", "status": "triage", "suspectedSource": "DP-03"},
    }
    return json.dumps(resources.get(uri, {"uri": uri, "error": "not found"}), ensure_ascii=False)


def list_waterclaw_prompts() -> list[dict[str, str]]:
    return [
        {"name": "waterclaw.incident_triage", "description": "Triage a water-quality anomaly before USV dispatch."},
        {"name": "waterclaw.gb3838_report", "description": "Generate a GB3838 compliance report from station telemetry."},
        {"name": "waterclaw.dispatch_safety_check", "description": "Review high-risk USV dispatch args before HITL approval."},
    ]
