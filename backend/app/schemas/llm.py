from typing import Any, Literal

from pydantic import BaseModel, Field


class SensorSnapshot(BaseModel):
    rtk: dict[str, Any] = Field(default_factory=dict)
    link: dict[str, Any] = Field(default_factory=dict)
    edge: dict[str, Any] = Field(default_factory=dict)
    weather: dict[str, Any] = Field(default_factory=dict)


class UsvSnapshot(BaseModel):
    id: str
    mode: str
    battery_pct: float
    task: str
    segment: str
    position: list[float]
    speed_mps: float
    heading_deg: float


class AgentTurnRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    session_id: str
    mission: str
    alert_level: str
    telemetry: SensorSnapshot
    fleet: list[UsvSnapshot]
    memory: dict[str, Any] = Field(default_factory=dict)
    available_tools: list[dict[str, Any]] = Field(default_factory=list)
    recent_messages: list[dict[str, Any]] = Field(default_factory=list)


class ToolIntent(BaseModel):
    tool_name: str
    args: dict[str, Any] = Field(default_factory=dict)
    reason: str = ""


class AgentTurnResponse(BaseModel):
    mode: Literal["llm"] = "llm"
    content: str
    thoughts: list[str] = Field(default_factory=list)
    tool_intents: list[ToolIntent] = Field(default_factory=list)
    confidence: float = 0.75
    model: str
    usage: dict[str, Any] = Field(default_factory=dict)
    latency_ms: int
    raw_finish_reason: str | None = None


class HealthResponse(BaseModel):
    ok: bool
    model: str
    litellm_available: bool
    api_base_configured: bool
    gateway_key_required: bool
