from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from fastapi import Depends, Header, HTTPException

from app.core.config import Settings, get_settings


Role = Literal["operator", "supervisor", "admin", "auditor", "external_agent"]


@dataclass(frozen=True)
class Principal:
    subject: str
    role: Role
    scopes: set[str]

    def require_scope(self, scope: str) -> None:
        if scope not in self.scopes and "*" not in self.scopes:
            raise HTTPException(status_code=403, detail=f"Missing required scope: {scope}")

    def require_role(self, *roles: Role) -> None:
        if self.role not in roles:
            raise HTTPException(status_code=403, detail=f"Role {self.role} is not allowed.")


LOCAL_DEV_PRINCIPAL = Principal(
    subject="operator-local",
    role="supervisor",
    scopes={
        "agent:read",
        "agent:turn",
        "approval:approve",
        "approval:reject",
        "audit:read",
        "control:request",
        "mcp:read",
        "tool:replay",
    },
)


def require_principal(
    settings: Settings = Depends(get_settings),
    authorization: str | None = Header(default=None),
    x_waterclaw_agent_key: str | None = Header(default=None),
) -> Principal:
    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    token = token or x_waterclaw_agent_key

    expected = settings.waterclaw_agent_api_key or settings.waterclaw_llm_gateway_key
    if not expected:
        return LOCAL_DEV_PRINCIPAL
    if token != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing WaterClaw Agent API credential.")

    return LOCAL_DEV_PRINCIPAL


def require_agent_read(principal: Principal = Depends(require_principal)) -> Principal:
    principal.require_scope("agent:read")
    return principal


def require_agent_turn(principal: Principal = Depends(require_principal)) -> Principal:
    principal.require_scope("agent:turn")
    return principal


def require_approval_approve(principal: Principal = Depends(require_principal)) -> Principal:
    principal.require_scope("approval:approve")
    principal.require_role("supervisor", "admin")
    return principal


def require_approval_reject(principal: Principal = Depends(require_principal)) -> Principal:
    principal.require_scope("approval:reject")
    return principal


def require_audit_read(principal: Principal = Depends(require_principal)) -> Principal:
    principal.require_scope("audit:read")
    principal.require_role("auditor", "admin", "supervisor")
    return principal


def require_control_request(principal: Principal = Depends(require_principal)) -> Principal:
    principal.require_scope("control:request")
    return principal
