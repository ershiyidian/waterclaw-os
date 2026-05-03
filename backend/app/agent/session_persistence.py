from __future__ import annotations

import json
from collections import OrderedDict
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from typing import Any, Protocol

from app.agent.state import SessionState
from app.core.database import store


class SessionPersistence(Protocol):
    async def get(self, session_id: str) -> SessionState | None:
        ...

    async def save(self, session: SessionState) -> None:
        ...


def session_to_json(session: SessionState) -> str:
    return json.dumps(asdict(session), ensure_ascii=False, separators=(",", ":"))


def session_from_json(raw: str | bytes) -> SessionState:
    data = json.loads(raw.decode("utf-8") if isinstance(raw, bytes) else raw)
    return SessionState(
        session_id=data["session_id"],
        status=data.get("status", "idle"),
        current_mission=data.get("current_mission", "桃浦河常态巡航 / Routine Patrol"),
        messages=data.get("messages") or [],
        memory=data.get("memory") or {},
        token_usage=data.get("token_usage") or {"input": 0, "output": 0, "costCny": 0},
        pending_approval_id=data.get("pending_approval_id"),
        resume_messages=data.get("resume_messages") or [],
        version=int(data.get("version") or 1),
        environment_version=data.get("environment_version"),
        visible_tools=data.get("visible_tools") or [],
        blocked_tools=data.get("blocked_tools") or {},
    )


class LocalLruCache:
    def __init__(self, max_size: int) -> None:
        self.max_size = max(1, max_size)
        self._items: OrderedDict[str, SessionState] = OrderedDict()

    def get(self, key: str) -> SessionState | None:
        value = self._items.get(key)
        if value is not None:
            self._items.move_to_end(key)
        return value

    def put(self, key: str, value: SessionState) -> None:
        self._items[key] = value
        self._items.move_to_end(key)
        while len(self._items) > self.max_size:
            self._items.popitem(last=False)


class SQLiteSessionPersistence:
    def __init__(self, ttl_seconds: int = 3600, cache_size: int = 256) -> None:
        self.ttl_seconds = ttl_seconds
        self.cache = LocalLruCache(cache_size)

    async def get(self, session_id: str) -> SessionState | None:
        cached = self.cache.get(session_id)
        row = store.fetchone("SELECT state_json, version, expires_at FROM sessions WHERE session_id = ?", (session_id,))
        if row is None:
            return cached
        expires_at = row["expires_at"]
        if expires_at and datetime.now(timezone.utc) >= datetime.fromisoformat(expires_at):
            store.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            return None
        if cached and cached.version == int(row["version"]):
            return cached
        session = session_from_json(row["state_json"])
        session.version = int(row["version"])
        self.cache.put(session_id, session)
        return session

    async def save(self, session: SessionState) -> None:
        session.version += 1
        now = datetime.now(timezone.utc)
        expires_at = (now + timedelta(seconds=self.ttl_seconds)).isoformat()
        store.execute(
            """
            INSERT INTO sessions(session_id, state_json, version, updated_at, expires_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
              state_json=excluded.state_json,
              version=excluded.version,
              updated_at=excluded.updated_at,
              expires_at=excluded.expires_at
            """,
            (session.session_id, session_to_json(session), session.version, now.isoformat(), expires_at),
        )
        self.cache.put(session.session_id, session)


class RedisSessionPersistence:
    def __init__(self, redis_url: str, ttl_seconds: int = 3600, cache_size: int = 256) -> None:
        self.redis_url = redis_url
        self.ttl_seconds = ttl_seconds
        self.cache = LocalLruCache(cache_size)
        self._redis: Any | None = None

    async def _client(self) -> Any:
        if self._redis is None:
            try:
                import redis.asyncio as redis
            except ImportError as exc:
                raise RuntimeError("redis package is required for WATERCLAW_SESSION_BACKEND=redis") from exc
            self._redis = redis.from_url(self.redis_url, decode_responses=True)
        return self._redis

    async def get(self, session_id: str) -> SessionState | None:
        redis = await self._client()
        cached = self.cache.get(session_id)
        version_raw = await redis.get(f"session:{session_id}:version")
        remote_version = int(version_raw or 0)
        if cached and cached.version == remote_version:
            return cached
        raw = await redis.get(f"session:{session_id}")
        if raw is None:
            return None
        session = session_from_json(raw)
        session.version = remote_version or session.version
        self.cache.put(session_id, session)
        return session

    async def save(self, session: SessionState) -> None:
        redis = await self._client()
        session.version += 1
        pipe = redis.pipeline()
        pipe.setex(f"session:{session.session_id}", self.ttl_seconds, session_to_json(session))
        pipe.setex(f"session:{session.session_id}:version", self.ttl_seconds, str(session.version))
        await pipe.execute()
        self.cache.put(session.session_id, session)
