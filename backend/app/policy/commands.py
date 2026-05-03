from __future__ import annotations

import hashlib
import json
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal

from app.core.database import store
from app.policy.approval import hash_args
from app.policy.audit import audit_log


CommandStatus = Literal["created", "executing", "sent", "acknowledged", "failed", "cancelled"]


@dataclass
class CommandRecord:
    command_id: str
    idempotency_key: str
    approval_id: str | None
    session_id: str
    tool_name: str
    args_hash: str
    args: dict[str, Any]
    status: CommandStatus
    requested_by: str
    created_at: str
    updated_at: str
    bus_ack_id: str | None = None
    result: dict[str, Any] | None = None
    error: str | None = None

    def public(self) -> dict[str, Any]:
        return {
            "commandId": self.command_id,
            "idempotencyKey": self.idempotency_key,
            "approvalId": self.approval_id,
            "toolName": self.tool_name,
            "argsHash": self.args_hash,
            "args": self.args,
            "status": self.status,
            "requestedBy": self.requested_by,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
            "busAckId": self.bus_ack_id,
            "result": self.result,
            "error": self.error,
        }


def command_key(approval_id: str | None, tool_name: str, args: dict[str, Any]) -> str:
    raw = json.dumps(
        {"approval_id": approval_id, "tool_name": tool_name, "args_hash": hash_args(args)},
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class CommandService:
    def get_by_key(self, idempotency_key: str) -> CommandRecord | None:
        row = store.fetchone("SELECT * FROM control_commands WHERE idempotency_key = ?", (idempotency_key,))
        return self._row_to_record(row) if row else None

    def create_or_get(
        self,
        *,
        approval_id: str | None,
        session_id: str,
        tool_name: str,
        args: dict[str, Any],
        requested_by: str,
    ) -> CommandRecord:
        key = command_key(approval_id, tool_name, args)
        existing = self.get_by_key(key)
        if existing:
            audit_log.write("command.idempotent_reuse", existing.public())
            return existing
        now = datetime.now(timezone.utc).isoformat()
        command_id = f"cmd-{secrets.token_urlsafe(10)}"
        args_json = json.dumps(args, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        store.execute(
            """
            INSERT INTO control_commands(
              command_id, idempotency_key, approval_id, session_id, tool_name, args_hash, args_json,
              status, requested_by, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (command_id, key, approval_id, session_id, tool_name, hash_args(args), args_json, "created", requested_by, now, now),
        )
        record = self.get_by_key(key)
        if record is None:
            raise RuntimeError("Failed to create command record.")
        audit_log.write("command.created", record.public())
        return record

    def mark(self, command_id: str, status: CommandStatus, *, result: dict[str, Any] | None = None, error: str | None = None, bus_ack_id: str | None = None) -> CommandRecord:
        now = datetime.now(timezone.utc).isoformat()
        store.execute(
            """
            UPDATE control_commands
            SET status = ?, updated_at = ?, result_json = COALESCE(?, result_json),
                error = COALESCE(?, error), bus_ack_id = COALESCE(?, bus_ack_id)
            WHERE command_id = ?
            """,
            (
                status,
                now,
                json.dumps(result, ensure_ascii=False, separators=(",", ":")) if result is not None else None,
                error,
                bus_ack_id,
                command_id,
            ),
        )
        row = store.fetchone("SELECT * FROM control_commands WHERE command_id = ?", (command_id,))
        if row is None:
            raise KeyError(command_id)
        record = self._row_to_record(row)
        audit_log.write(f"command.{status}", record.public())
        return record

    def _row_to_record(self, row: Any) -> CommandRecord:
        return CommandRecord(
            command_id=row["command_id"],
            idempotency_key=row["idempotency_key"],
            approval_id=row["approval_id"],
            session_id=row["session_id"],
            tool_name=row["tool_name"],
            args_hash=row["args_hash"],
            args=json.loads(row["args_json"]),
            status=row["status"],
            requested_by=row["requested_by"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            bus_ack_id=row["bus_ack_id"],
            result=json.loads(row["result_json"]) if row["result_json"] else None,
            error=row["error"],
        )


command_service = CommandService()
