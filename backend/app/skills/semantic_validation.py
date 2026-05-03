from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, Field, ValidationError, field_validator

from app.skills.registry import SkillManifest

KNOWN_STATIONS = {"TP-01", "TP-02", "TP-03", "TP-04", "TP-05"}
KNOWN_USVS = {"USV-01", "USV-02"}
KNOWN_TARGETS = {"DP-01", "DP-02", "DP-03", "DP-04", "DP-05", "BASE", "TP-01", "TP-02", "TP-03", "TP-04", "TP-05"}
WINDOW_RE = re.compile(r"^\d+[smhd]$")


class StationWindowArgs(BaseModel):
    stations: list[str] = Field(min_length=1)
    window: str = "5m"

    @field_validator("stations")
    @classmethod
    def stations_must_exist(cls, value: list[str]) -> list[str]:
        invalid = sorted(set(value) - KNOWN_STATIONS)
        if invalid:
            raise ValueError(f"Unknown stations: {', '.join(invalid)}")
        return value

    @field_validator("window")
    @classmethod
    def window_format(cls, value: str) -> str:
        if not WINDOW_RE.match(value):
            raise ValueError("Window must match pattern like 5m, 30m, 2h, or 1d")
        return value


class EvalGb3838Args(BaseModel):
    stations: list[str] = Field(min_length=1)
    targetClass: str

    @field_validator("stations")
    @classmethod
    def stations_must_exist(cls, value: list[str]) -> list[str]:
        invalid = sorted(set(value) - KNOWN_STATIONS)
        if invalid:
            raise ValueError(f"Unknown stations: {', '.join(invalid)}")
        return value


class StationHorizonArgs(BaseModel):
    station: str
    horizon: str
    confidence: float = 0.95

    @field_validator("station")
    @classmethod
    def station_must_exist(cls, value: str) -> str:
        if value not in KNOWN_STATIONS:
            raise ValueError(f"Unknown station: {value}")
        return value

    @field_validator("horizon")
    @classmethod
    def horizon_format(cls, value: str) -> str:
        if not WINDOW_RE.match(value):
            raise ValueError("Horizon must match pattern like 30m, 2h, or 1d")
        return value


class PlanPathArgs(BaseModel):
    usv: str
    target: str

    @field_validator("usv")
    @classmethod
    def usv_must_exist(cls, value: str) -> str:
        if value not in KNOWN_USVS:
            raise ValueError(f"Unknown USV: {value}")
        return value

    @field_validator("target")
    @classmethod
    def target_must_exist(cls, value: str) -> str:
        if value not in KNOWN_TARGETS:
            raise ValueError(f"Unknown target: {value}")
        return value


class DispatchArgs(PlanPathArgs):
    mission: str = Field(min_length=4, max_length=120)


class NotifyArgs(BaseModel):
    incidentId: str = Field(pattern=r"^INC-")
    channel: str = Field(min_length=2, max_length=80)


SEMANTIC_MODELS: dict[str, type[BaseModel]] = {
    "query_sensor_data": StationWindowArgs,
    "eval_gb3838": EvalGb3838Args,
    "lstm_predict": StationHorizonArgs,
    "plan_dubins_path": PlanPathArgs,
    "dispatch_usv": DispatchArgs,
    "notify_authority": NotifyArgs,
}


class SemanticArgumentError(ValueError):
    pass


def validate_semantics(manifest: SkillManifest, args: dict[str, Any]) -> dict[str, Any]:
    model = SEMANTIC_MODELS.get(manifest.name)
    if model is None:
        return args
    try:
        return model(**args).model_dump()
    except ValidationError as exc:
        raise SemanticArgumentError("; ".join(f"{'.'.join(str(p) for p in error['loc'])}: {error['msg']}" for error in exc.errors())) from exc
