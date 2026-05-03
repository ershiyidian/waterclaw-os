from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import StreamingResponse

from app.agent.events import event_stream
from app.agent.decision_log import decision_log
from app.agent.runner import AgentRunner
from app.agent.state import session_store
from app.core.auth import (
    Principal,
    require_agent_read,
    require_agent_turn,
    require_approval_approve,
    require_approval_reject,
    require_audit_read,
    require_control_request,
)
from app.core.config import Settings, get_settings
from app.mcp.manager import mcp_manager
from app.policy.audit import audit_log
from app.schemas.agent import AgentTurnRequest, ApprovalDecisionRequest, ControlRequest, McpStatusResponse, ToolManifestResponse
from app.skills.registry import skill_registry
from app.telemetry.live_stream import telemetry_stream


router = APIRouter(prefix="/api/agent", tags=["agent"])


def require_gateway_key(
    settings: Settings = Depends(get_settings),
    x_waterclaw_llm_key: str | None = Header(default=None),
) -> None:
    if settings.waterclaw_llm_gateway_key and x_waterclaw_llm_key != settings.waterclaw_llm_gateway_key:
        raise HTTPException(status_code=401, detail="Invalid WaterClaw LLM gateway key.")


@router.get("/legacy-warning")
async def legacy_warning() -> dict[str, str]:
    return {
        "status": "deprecated",
        "message": "Use /api/agent/sessions/{session_id}/turn. /api/llm/agent-turn is retained only for legacy debugging.",
    }


@router.get("/skills", response_model=ToolManifestResponse)
async def list_skills(principal: Principal = Depends(require_agent_read)) -> ToolManifestResponse:
    return ToolManifestResponse(tools=[manifest.as_public_dict() for manifest in skill_registry.list()])


@router.get("/mcp/status", response_model=McpStatusResponse)
async def mcp_status(principal: Principal = Depends(require_agent_read)) -> McpStatusResponse:
    return McpStatusResponse(servers=mcp_manager.list_status())


@router.get("/audit/recent")
async def recent_audit(limit: int = 100, principal: Principal = Depends(require_audit_read)) -> dict[str, object]:
    return {"events": audit_log.recent(limit=min(max(limit, 1), 500))}


@router.get("/audit/verify")
async def verify_audit(limit: int = 1000, principal: Principal = Depends(require_audit_read)) -> dict[str, object]:
    errors = audit_log.verify_chain(limit=min(max(limit, 1), 10000))
    return {"ok": not errors, "errors": errors}


@router.get("/sessions/{session_id}/state")
async def session_state(session_id: str, principal: Principal = Depends(require_agent_read)) -> dict[str, object]:
    return await session_store.public_state(session_id)


async def _stream_and_save(session, events):
    try:
        async for event in events:
            yield event
    finally:
        await session_store.save(session)


@router.get("/sessions/{session_id}/decisions")
async def session_decisions(session_id: str, limit: int = 100, principal: Principal = Depends(require_audit_read)) -> dict[str, object]:
    return {"decisions": decision_log.recent(session_id, limit=min(max(limit, 1), 500))}


@router.get("/sessions/{session_id}/telemetry-stream")
async def telemetry_sse(session_id: str, principal: Principal = Depends(require_agent_read)) -> StreamingResponse:
    return StreamingResponse(
        event_stream(telemetry_stream.events(session_id)),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/sessions/{session_id}/turn", dependencies=[Depends(require_gateway_key)])
async def run_turn(
    session_id: str,
    req: AgentTurnRequest,
    settings: Settings = Depends(get_settings),
    principal: Principal = Depends(require_agent_turn),
) -> StreamingResponse:
    session = await session_store.get(session_id)
    runner = AgentRunner(settings)
    return StreamingResponse(
        event_stream(_stream_and_save(session, runner.run_turn(session, req))),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/sessions/{session_id}/approvals/{approval_id}/approve", dependencies=[Depends(require_gateway_key)])
async def approve(
    session_id: str,
    approval_id: str,
    req: ApprovalDecisionRequest,
    settings: Settings = Depends(get_settings),
    principal: Principal = Depends(require_approval_approve),
) -> StreamingResponse:
    session = await session_store.get(session_id)
    runner = AgentRunner(settings)
    return StreamingResponse(
        event_stream(_stream_and_save(session, runner.execute_approved(session, approval_id, req.code, principal.subject))),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/sessions/{session_id}/approvals/{approval_id}/reject", dependencies=[Depends(require_gateway_key)])
async def reject(
    session_id: str,
    approval_id: str,
    req: ApprovalDecisionRequest,
    settings: Settings = Depends(get_settings),
    principal: Principal = Depends(require_approval_reject),
) -> StreamingResponse:
    session = await session_store.get(session_id)
    runner = AgentRunner(settings)
    return StreamingResponse(
        event_stream(_stream_and_save(session, runner.reject_approval(session, approval_id, principal.subject))),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/sessions/{session_id}/control/request", dependencies=[Depends(require_gateway_key)])
async def request_control(
    session_id: str,
    req: ControlRequest,
    settings: Settings = Depends(get_settings),
    principal: Principal = Depends(require_control_request),
) -> StreamingResponse:
    session = await session_store.get(session_id)
    runner = AgentRunner(settings)
    return StreamingResponse(
        event_stream(_stream_and_save(session, runner.request_control(session, req.action, {"usvs": req.usvs, "reason": req.reason}, principal.subject))),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
