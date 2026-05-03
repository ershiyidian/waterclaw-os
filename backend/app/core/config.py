from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="backend/.env", env_file_encoding="utf-8", extra="ignore")

    waterclaw_environment: str = Field(default="development", alias="WATERCLAW_ENVIRONMENT")
    litellm_model: str = Field(default="openai/gpt-4o-mini", alias="LITELLM_MODEL")
    litellm_api_base: str | None = Field(default=None, alias="LITELLM_API_BASE")
    litellm_timeout_seconds: float = Field(default=45, alias="LITELLM_TIMEOUT_SECONDS")
    litellm_max_tokens: int = Field(default=900, alias="LITELLM_MAX_TOKENS")
    litellm_temperature: float = Field(default=0.2, alias="LITELLM_TEMPERATURE")
    waterclaw_agent_max_steps: int = Field(default=8, alias="WATERCLAW_AGENT_MAX_STEPS")
    waterclaw_llm_gateway_key: str | None = Field(default=None, alias="WATERCLAW_LLM_GATEWAY_KEY")
    waterclaw_agent_api_key: str | None = Field(default=None, alias="WATERCLAW_AGENT_API_KEY")
    waterclaw_approval_code: str | None = Field(default=None, alias="WATERCLAW_APPROVAL_CODE")
    waterclaw_approval_pepper: str = Field(default="dev-only-change-me", alias="WATERCLAW_APPROVAL_PEPPER")
    waterclaw_sqlite_path: str = Field(default="backend/.waterclaw/waterclaw.db", alias="WATERCLAW_SQLITE_PATH")
    waterclaw_cors_origins: str = Field(default="http://127.0.0.1:5173,http://localhost:5173", alias="WATERCLAW_CORS_ORIGINS")
    waterclaw_session_backend: str = Field(default="sqlite", alias="WATERCLAW_SESSION_BACKEND")
    waterclaw_session_ttl_seconds: int = Field(default=3600, alias="WATERCLAW_SESSION_TTL_SECONDS")
    waterclaw_session_cache_size: int = Field(default=256, alias="WATERCLAW_SESSION_CACHE_SIZE")
    redis_url: str | None = Field(default=None, alias="REDIS_URL")
    waterclaw_mcp_config_path: str = Field(default="backend/.mcp.json", alias="WATERCLAW_MCP_CONFIG_PATH")
    waterclaw_mcp_enabled: bool = Field(default=False, alias="WATERCLAW_MCP_ENABLED")
    waterclaw_mcp_call_timeout_seconds: float = Field(default=20, alias="WATERCLAW_MCP_CALL_TIMEOUT_SECONDS")
    waterclaw_mock_fallback_enabled: bool = Field(default=True, alias="WATERCLAW_MOCK_FALLBACK_ENABLED")
    otel_enabled: bool = Field(default=False, alias="OTEL_ENABLED")
    otel_exporter_otlp_endpoint: str | None = Field(default=None, alias="OTEL_EXPORTER_OTLP_ENDPOINT")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.waterclaw_cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
