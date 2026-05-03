from __future__ import annotations

import json
from typing import Any


AgentEvent = dict[str, Any]


def encode_sse_event(event: AgentEvent) -> str:
    return f"event: {event['type']}\ndata: {json.dumps(event['data'], ensure_ascii=False, separators=(',', ':'))}\n\n"


def parse_sse_events(payload: str) -> list[AgentEvent]:
    events: list[AgentEvent] = []
    for block in payload.split("\n\n"):
        if not block.strip():
            continue
        event_type = "message.final"
        data_lines: list[str] = []
        for line in block.splitlines():
            if line.startswith("event:"):
                event_type = line.removeprefix("event:").strip()
            if line.startswith("data:"):
                data_lines.append(line.removeprefix("data:").strip())
        events.append({"type": event_type, "data": json.loads("\n".join(data_lines))})
    return events


def validate_formal_agent_sequence(events: list[AgentEvent]) -> list[str]:
    errors: list[str] = []
    started: set[str] = set()
    finished: set[str] = set()
    approvals: set[str] = set()

    for index, event in enumerate(events):
        event_type = event.get("type")
        data = event.get("data") or {}

        if event_type == "tool.started":
            call = data.get("call") or {}
            call_id = call.get("id")
            if not isinstance(call_id, str) or not call_id:
                errors.append(f"event {index}: tool.started missing call.id")
            else:
                started.add(call_id)

        if event_type in {"tool.finished", "tool.failed", "tool.awaiting_approval"}:
            call_id = str(data.get("callId") or "")
            if call_id not in started:
                errors.append(f"event {index}: {event_type} references unknown callId {call_id}")
            if event_type == "tool.finished":
                finished.add(call_id)

        if event_type == "approval.required":
            approval = data.get("approval") or {}
            approval_id = approval.get("id")
            if not isinstance(approval_id, str) or not approval_id:
                errors.append(f"event {index}: approval.required missing approval.id")
            else:
                approvals.add(approval_id)
            if "two_factor_code" in approval:
                errors.append(f"event {index}: approval.required leaks a plaintext approval code")

        if event_type == "approval.resolved":
            approval_id = str(data.get("approvalId") or "")
            if approval_id not in approvals:
                errors.append(f"event {index}: approval.resolved references unknown approvalId {approval_id}")

    if not any(event.get("type") == "state.patch" for event in events):
        errors.append("missing state.patch")
    if not any(event.get("type") == "react.step" for event in events):
        errors.append("missing react.step")
    if not any(event.get("type") == "message.final" for event in events):
        errors.append("missing message.final")
    if not started:
        errors.append("missing tool.started")
    if not finished:
        errors.append("missing successful tool.finished")

    return errors
