from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AgentTurnRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    mission: str = "桃浦河常态巡航 / Routine Patrol"
    alert_level: str = "normal"
    telemetry: dict[str, Any] = Field(default_factory=dict)
    fleet: list[dict[str, Any]] = Field(default_factory=list)
    memory: dict[str, Any] = Field(default_factory=dict)
    recent_messages: list[dict[str, Any]] = Field(default_factory=list)


class ApprovalDecisionRequest(BaseModel):
    code: str = ""


class ToolReplayRequest(BaseModel):
    tool_name: str
    args: dict[str, Any] = Field(default_factory=dict)


class ControlRequest(BaseModel):
    action: str = Field(pattern="^(rtl_usv|request_estop)$")
    usvs: list[str] = Field(min_length=1)
    reason: str = Field(min_length=4, max_length=240)


class ToolManifestResponse(BaseModel):
    tools: list[dict[str, Any]]


class McpStatusResponse(BaseModel):
    servers: list[dict[str, Any]]
