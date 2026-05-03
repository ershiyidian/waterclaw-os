import importlib.util

from fastapi import APIRouter, Depends, Header, HTTPException

from app.core.config import Settings, get_settings
from app.schemas.llm import AgentTurnRequest, AgentTurnResponse, HealthResponse
from app.services.litellm_gateway import LiteLLMGateway

router = APIRouter(prefix="/api/llm", tags=["llm"])


def require_gateway_key(
    settings: Settings = Depends(get_settings),
    x_waterclaw_llm_key: str | None = Header(default=None),
) -> None:
    if settings.waterclaw_llm_gateway_key and x_waterclaw_llm_key != settings.waterclaw_llm_gateway_key:
        raise HTTPException(status_code=401, detail="Invalid WaterClaw LLM gateway key.")


@router.get("/health", response_model=HealthResponse)
async def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    return HealthResponse(
        ok=True,
        model=settings.litellm_model,
        litellm_available=importlib.util.find_spec("litellm") is not None,
        api_base_configured=bool(settings.litellm_api_base),
        gateway_key_required=bool(settings.waterclaw_llm_gateway_key),
    )


@router.post("/agent-turn", response_model=AgentTurnResponse, dependencies=[Depends(require_gateway_key)])
async def agent_turn(req: AgentTurnRequest, settings: Settings = Depends(get_settings)) -> AgentTurnResponse:
    # Legacy compatibility endpoint. Production UI uses /api/agent/sessions/{session_id}/turn.
    gateway = LiteLLMGateway(settings)
    return await gateway.agent_turn(req)
