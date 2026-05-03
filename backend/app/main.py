from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agent.routes import router as agent_router
from app.core.config import get_settings
from app.mcp.manager import mcp_manager
from app.otel import setup_otel
from app.routers.llm import router as llm_router
from app.skills.real_executors import install_mcp_executors
from app.skills.registry import skill_registry


settings = get_settings()

app = FastAPI(
    title="WaterClaw OS Agent Host",
    version="0.2.0",
    description="LiteLLM-powered Agent Host with backend Skill execution, MCP status, HITL approval, and audit.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

setup_otel(app, settings)

app.include_router(llm_router)
app.include_router(agent_router)


@app.on_event("startup")
async def startup() -> None:
    await mcp_manager.ensure_started()
    if settings.waterclaw_mcp_enabled or settings.waterclaw_environment == "production":
        install_mcp_executors(skill_registry, mcp_manager, settings)


@app.on_event("shutdown")
async def shutdown() -> None:
    await mcp_manager.shutdown()


@app.get("/api/health")
async def api_health() -> dict[str, str]:
    return {"status": "ok"}
