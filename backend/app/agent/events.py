from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, AsyncIterator
import time


@dataclass
class AgentEvent:
    type: str
    data: dict[str, Any] = field(default_factory=dict)
    id: str | None = None


def sse_encode(event: AgentEvent) -> str:
    payload = json.dumps(event.data, ensure_ascii=False, separators=(",", ":"))
    event_id = event.id or f"{int(time.time() * 1000)}"
    return f"id: {event_id}\nevent: {event.type}\ndata: {payload}\n\n"


async def event_stream(events: AsyncIterator[AgentEvent]) -> AsyncIterator[str]:
    async for event in events:
        yield sse_encode(event)
