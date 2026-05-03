from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.core.database import store


@dataclass
class AgentDecisionRecord:
    session_id: str
    step_index: int
    messages_snapshot: list[dict[str, Any]]
    model_response: dict[str, Any]
    parsed_tool_calls: list[dict[str, Any]]
    policy_decisions: list[dict[str, Any]] = field(default_factory=list)
    tool_results: list[dict[str, Any]] = field(default_factory=list)
    latency_ms: int = 0
    trace_id: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class DecisionLog:
    def save(self, record: AgentDecisionRecord) -> None:
        store.execute(
            """
            INSERT INTO agent_decisions(
              session_id, step_index, timestamp, messages_json, response_json, tool_calls_json,
              policy_json, tool_results_json, latency_ms, trace_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.session_id,
                record.step_index,
                record.timestamp,
                json.dumps(record.messages_snapshot, ensure_ascii=False, separators=(",", ":")),
                json.dumps(record.model_response, ensure_ascii=False, separators=(",", ":")),
                json.dumps(record.parsed_tool_calls, ensure_ascii=False, separators=(",", ":")),
                json.dumps(record.policy_decisions, ensure_ascii=False, separators=(",", ":")),
                json.dumps(record.tool_results, ensure_ascii=False, separators=(",", ":")),
                record.latency_ms,
                record.trace_id,
            ),
        )

    def recent(self, session_id: str, limit: int = 100) -> list[dict[str, Any]]:
        rows = store.fetchall(
            """
            SELECT session_id, step_index, timestamp, messages_json, response_json, tool_calls_json,
                   policy_json, tool_results_json, latency_ms, trace_id
            FROM agent_decisions
            WHERE session_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (session_id, limit),
        )
        return [
            {
                "sessionId": row["session_id"],
                "stepIndex": row["step_index"],
                "timestamp": row["timestamp"],
                "messages": json.loads(row["messages_json"]),
                "modelResponse": json.loads(row["response_json"]),
                "parsedToolCalls": json.loads(row["tool_calls_json"]),
                "policyDecisions": json.loads(row["policy_json"]),
                "toolResults": json.loads(row["tool_results_json"]),
                "latencyMs": row["latency_ms"],
                "traceId": row["trace_id"],
            }
            for row in rows
        ]


decision_log = DecisionLog()
