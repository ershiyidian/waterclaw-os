from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from app.core.config import get_settings


AgentStatus = Literal["idle", "thinking", "tool_call", "awaiting_approval"]


@dataclass
class SessionState:
    session_id: str
    status: AgentStatus = "idle"
    current_mission: str = "桃浦河常态巡航 / Routine Patrol"
    messages: list[dict[str, Any]] = field(default_factory=list)
    memory: dict[str, Any] = field(
        default_factory=lambda: {
            "shortTerm": {
                "active_reach": "TP-01 ~ TP-05",
                "current_alert": "none",
                "patrol_policy": "III类水目标，5分钟滚动评价",
            },
            "longTerm": {
                "DP-03_history": "过去30天3次夜间浊度异常，2次与化工园雨水井相关",
                "USV-01_profile": "高速采样艇，适合上游拦截和近岸视觉确认",
                "USV-02_profile": "低速续航艇，适合断面哨位和长时间蹲守",
            },
            "toolCache": [],
        }
    )
    token_usage: dict[str, float] = field(default_factory=lambda: {"input": 0, "output": 0, "costCny": 0})
    pending_approval_id: str | None = None
    resume_messages: list[dict[str, Any]] = field(default_factory=list)
    version: int = 1
    environment_version: str | None = None
    visible_tools: list[str] = field(default_factory=list)
    blocked_tools: dict[str, str] = field(default_factory=dict)

    def append_message(self, role: str, content: str, **extra: Any) -> None:
        self.messages.append({"role": role, "content": content, **extra})
        self.messages = self.messages[-40:]

    def has_pending_approval(self) -> bool:
        return self.pending_approval_id is not None

    def current_alert_is_active(self) -> bool:
        short = self.memory.get("shortTerm", {}) if isinstance(self.memory, dict) else {}
        return str(short.get("current_alert", "none")).lower() not in {"", "none", "normal"}

    def evidence_chain_is_complete(self) -> bool:
        short = self.memory.get("shortTerm", {}) if isinstance(self.memory, dict) else {}
        alert = str(short.get("current_alert", "none")).lower()
        return alert not in {"", "none", "normal"} and bool(short.get("incident_id") or short.get("evidence_chain"))


class SessionStore:
    def __init__(self) -> None:
        settings = get_settings()
        from app.agent.session_persistence import RedisSessionPersistence, SQLiteSessionPersistence

        if settings.waterclaw_session_backend == "redis" and settings.redis_url:
            self._persistence = RedisSessionPersistence(
                settings.redis_url,
                ttl_seconds=settings.waterclaw_session_ttl_seconds,
                cache_size=settings.waterclaw_session_cache_size,
            )
        else:
            self._persistence = SQLiteSessionPersistence(
                ttl_seconds=settings.waterclaw_session_ttl_seconds,
                cache_size=settings.waterclaw_session_cache_size,
            )

    async def get(self, session_id: str) -> SessionState:
        session = await self._persistence.get(session_id)
        if session is None:
            session = SessionState(session_id=session_id)
            await self.save(session)
        return session

    async def save(self, session: SessionState) -> None:
        await self._persistence.save(session)

    async def public_state(self, session_id: str) -> dict[str, Any]:
        session = await self.get(session_id)
        return {
            "sessionId": session.session_id,
            "status": session.status,
            "currentMission": session.current_mission,
            "memory": session.memory,
            "tokenUsage": session.token_usage,
            "pendingApprovalId": session.pending_approval_id,
            "version": session.version,
            "visibleTools": session.visible_tools,
            "blockedTools": session.blocked_tools,
        }


session_store = SessionStore()
