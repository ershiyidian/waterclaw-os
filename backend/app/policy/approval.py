from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

from app.core.database import store
from app.core.config import get_settings
from app.policy.audit import audit_log


ApprovalStatus = Literal["pending", "approved", "executing", "used", "rejected", "expired", "failed", "cancelled"]


def canonical_args(args: dict[str, Any]) -> str:
    return json.dumps(args, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def hash_args(args: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_args(args).encode("utf-8")).hexdigest()


def hash_token(token: str) -> str:
    pepper = get_settings().waterclaw_approval_pepper
    return hmac.new(pepper.encode("utf-8"), token.encode("utf-8"), hashlib.sha256).hexdigest()


@dataclass
class ApprovalRecord:
    id: str
    session_id: str
    tool_name: str
    args: dict[str, Any]
    args_hash: str
    risk_level: str
    title: str
    description: str
    requested_at: str
    expires_at: str
    status: ApprovalStatus
    requested_by_model: bool = True
    approved_by: str | None = None
    approved_at: str | None = None
    token_hash: str | None = None
    used_at: str | None = None
    schema_version: str = "v1"
    operator_role: str | None = None
    idempotency_key: str | None = None
    command_id: str | None = None

    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) >= datetime.fromisoformat(self.expires_at)

    def public(self, *, requires_code: bool = False) -> dict[str, Any]:
        expires = datetime.fromisoformat(self.expires_at)
        requested = datetime.fromisoformat(self.requested_at)
        remaining = max(0, int((expires - datetime.now(timezone.utc)).total_seconds()))
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "riskLevel": self.risk_level,
            "autoCancelSeconds": max(1, int((expires - requested).total_seconds())),
            "remainingSeconds": remaining,
            "requestedAt": int(requested.timestamp() * 1000),
            "command": self.tool_name,
            "payload": self.args,
            "argsHash": self.args_hash,
            "requiresHoldMs": 2200 if self.risk_level == "critical" else 1200,
            "requiresCode": bool(requires_code and self.risk_level == "critical"),
            "status": self.status,
        }


class ApprovalService:
    def create(
        self,
        session_id: str,
        tool_name: str,
        args: dict[str, Any],
        risk_level: str,
        description: str,
        ttl_seconds: int = 60,
        schema_version: str = "v1",
    ) -> ApprovalRecord:
        now = datetime.now(timezone.utc)
        record = ApprovalRecord(
            id=f"approval-{secrets.token_urlsafe(10)}",
            session_id=session_id,
            tool_name=tool_name,
            args=args,
            args_hash=hash_args(args),
            risk_level=risk_level,
            title=f"审批高权限工具：{tool_name}",
            description=description,
            requested_at=now.isoformat(),
            expires_at=(now + timedelta(seconds=ttl_seconds)).isoformat(),
            status="pending",
            schema_version=schema_version,
        )
        self._insert(record)
        audit_log.write("approval.created", asdict(record))
        return record

    def get(self, approval_id: str) -> ApprovalRecord:
        row = store.fetchone("SELECT * FROM approvals WHERE id = ?", (approval_id,))
        if row is None:
            raise KeyError(f"Approval not found: {approval_id}")
        record = self._row_to_record(row)
        if record.status == "pending" and record.is_expired():
            record.status = "expired"
            self._update(record)
            audit_log.write("approval.expired", asdict(record))
        return record

    def reject(self, approval_id: str, operator_id: str) -> ApprovalRecord:
        record = self.get(approval_id)
        if record.status != "pending":
            return record
        record.status = "rejected"
        record.approved_by = operator_id
        self._update(record)
        audit_log.write("approval.rejected", asdict(record))
        return record

    def approve(
        self,
        approval_id: str,
        code: str,
        operator_id: str,
        operator_role: str = "supervisor",
        expected_code: str | None = None,
    ) -> tuple[ApprovalRecord, str]:
        record = self.get(approval_id)
        if record.status != "pending":
            raise ValueError(f"Approval is not pending: {record.status}")
        if record.risk_level == "critical" and expected_code and not hmac.compare_digest(code or "", expected_code):
            audit_log.write("approval.invalid_code", {"approval_id": approval_id, "operator_id": operator_id})
            raise PermissionError("Invalid two-factor approval code.")
        token = secrets.token_urlsafe(24)
        record.status = "approved"
        record.approved_by = operator_id
        record.operator_role = operator_role
        record.approved_at = datetime.now(timezone.utc).isoformat()
        record.token_hash = hash_token(token)
        self._update(record)
        audit_log.write("approval.approved", asdict(record))
        return record, token

    def start_execution(self, approval_id: str, token: str, args: dict[str, Any], command_id: str, idempotency_key: str) -> ApprovalRecord:
        record = self.get(approval_id)
        if record.status not in {"approved", "executing"}:
            raise PermissionError(f"Approval is not executable: {record.status}")
        if record.token_hash is None or not hmac.compare_digest(record.token_hash, hash_token(token)):
            raise PermissionError("Invalid approval token.")
        if record.args_hash != hash_args(args):
            raise PermissionError("Approval args hash mismatch.")
        record.status = "executing"
        record.command_id = command_id
        record.idempotency_key = idempotency_key
        self._update(record)
        audit_log.write("approval.executing", asdict(record))
        return record

    def mark_used(self, approval_id: str) -> ApprovalRecord:
        record = self.get(approval_id)
        if record.status not in {"approved", "executing"}:
            return record
        record.status = "used"
        record.used_at = datetime.now(timezone.utc).isoformat()
        self._update(record)
        audit_log.write("approval.used", asdict(record))
        return record

    def mark_failed(self, approval_id: str, error: str) -> ApprovalRecord:
        record = self.get(approval_id)
        record.status = "failed"
        self._update(record)
        audit_log.write("approval.failed", {**asdict(record), "error": error})
        return record

    def find_pending_for_session(self, session_id: str) -> ApprovalRecord | None:
        rows = store.fetchall(
            "SELECT * FROM approvals WHERE session_id = ? AND status = 'pending' ORDER BY requested_at DESC LIMIT 1",
            (session_id,),
        )
        if not rows:
            return None
        return self.get(rows[0]["id"])

    def _insert(self, record: ApprovalRecord) -> None:
        store.execute(
            """
            INSERT INTO approvals(
              id, session_id, tool_name, args_json, args_hash, risk_level, title, description,
              requested_at, expires_at, status, requested_by_model, approved_by, approved_at,
              token_hash, used_at, schema_version, operator_role, idempotency_key, command_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            self._params(record),
        )

    def _update(self, record: ApprovalRecord) -> None:
        params = self._params(record)
        store.execute(
            """
            UPDATE approvals
            SET session_id=?, tool_name=?, args_json=?, args_hash=?, risk_level=?, title=?, description=?,
                requested_at=?, expires_at=?, status=?, requested_by_model=?, approved_by=?, approved_at=?,
                token_hash=?, used_at=?, schema_version=?, operator_role=?, idempotency_key=?, command_id=?
            WHERE id=?
            """,
            params[1:] + (record.id,),
        )

    def _params(self, record: ApprovalRecord) -> tuple[Any, ...]:
        return (
            record.id,
            record.session_id,
            record.tool_name,
            canonical_args(record.args),
            record.args_hash,
            record.risk_level,
            record.title,
            record.description,
            record.requested_at,
            record.expires_at,
            record.status,
            1 if record.requested_by_model else 0,
            record.approved_by,
            record.approved_at,
            record.token_hash,
            record.used_at,
            record.schema_version,
            record.operator_role,
            record.idempotency_key,
            record.command_id,
        )

    def _row_to_record(self, row: Any) -> ApprovalRecord:
        return ApprovalRecord(
            id=row["id"],
            session_id=row["session_id"],
            tool_name=row["tool_name"],
            args=json.loads(row["args_json"]),
            args_hash=row["args_hash"],
            risk_level=row["risk_level"],
            title=row["title"],
            description=row["description"],
            requested_at=row["requested_at"],
            expires_at=row["expires_at"],
            status=row["status"],
            requested_by_model=bool(row["requested_by_model"]),
            approved_by=row["approved_by"],
            approved_at=row["approved_at"],
            token_hash=row["token_hash"],
            used_at=row["used_at"],
            schema_version=row["schema_version"],
            operator_role=row["operator_role"],
            idempotency_key=row["idempotency_key"],
            command_id=row["command_id"],
        )


approval_service = ApprovalService()
