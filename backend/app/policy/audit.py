from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any

from app.core.database import store

logger = logging.getLogger("waterclaw.audit")


class AuditLog:
    def __init__(self, path: str = "backend/.waterclaw/audit.jsonl") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self._ring: list[dict[str, Any]] = []
        self._last_hash = self._load_last_hash()

    def _load_last_hash(self) -> str | None:
        row = store.fetchone("SELECT chain_hash FROM audit_events WHERE chain_hash IS NOT NULL ORDER BY seq DESC LIMIT 1")
        return str(row["chain_hash"]) if row and row["chain_hash"] else None

    def write(self, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        ts = datetime.now(timezone.utc).isoformat()
        payload_json = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        with self._lock:
            prev_hash = self._last_hash
            chain_input = f"{ts}|{event_type}|{payload_json}|{prev_hash or 'GENESIS'}"
            chain_hash = hashlib.sha256(chain_input.encode("utf-8")).hexdigest()
            record = {
                "ts": ts,
                "event": event_type,
                "payload": payload,
                "chainHash": chain_hash,
                "prevHash": prev_hash,
            }
            line = json.dumps(record, ensure_ascii=False, separators=(",", ":"))
            with self.path.open("a", encoding="utf-8") as file:
                file.write(line + "\n")
            store.execute(
                "INSERT INTO audit_events(ts, event_type, payload_json, chain_hash, prev_hash) VALUES (?, ?, ?, ?, ?)",
                (ts, event_type, payload_json, chain_hash, prev_hash),
            )
            self._last_hash = chain_hash
            self._ring.append(record)
            self._ring = self._ring[-1000:]
        logger.info("audit_event", extra={"event_type": event_type, "chain_hash": chain_hash, "payload": payload})
        return record

    def verify_chain(self, limit: int = 1000) -> list[str]:
        rows = store.fetchall(
            "SELECT ts, event_type, payload_json, chain_hash, prev_hash FROM audit_events WHERE chain_hash IS NOT NULL ORDER BY seq ASC LIMIT ?",
            (limit,),
        )
        errors: list[str] = []
        last_hash: str | None = None
        for index, row in enumerate(rows):
            expected_prev = last_hash
            if row["prev_hash"] != expected_prev:
                errors.append(f"row {index}: prev_hash mismatch")
            chain_input = f"{row['ts']}|{row['event_type']}|{row['payload_json']}|{row['prev_hash'] or 'GENESIS'}"
            expected_hash = hashlib.sha256(chain_input.encode("utf-8")).hexdigest()
            if row["chain_hash"] != expected_hash:
                errors.append(f"row {index}: chain_hash mismatch")
            last_hash = row["chain_hash"]
        return errors

    def legacy_write(self, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "event": event_type,
            "payload": payload,
        }
        line = json.dumps(record, ensure_ascii=False, separators=(",", ":"))
        with self._lock:
            with self.path.open("a", encoding="utf-8") as file:
                file.write(line + "\n")
            store.execute(
                "INSERT INTO audit_events(ts, event_type, payload_json) VALUES (?, ?, ?)",
                (record["ts"], event_type, json.dumps(payload, ensure_ascii=False, separators=(",", ":"))),
            )
            self._ring.append(record)
            self._ring = self._ring[-1000:]
        return record

    def recent(self, limit: int = 100) -> list[dict[str, Any]]:
        rows = store.fetchall(
            "SELECT ts, event_type, payload_json, chain_hash, prev_hash FROM audit_events ORDER BY seq DESC LIMIT ?",
            (limit,),
        )
        if rows:
            return [
                {
                    "ts": row["ts"],
                    "event": row["event_type"],
                    "payload": json.loads(row["payload_json"]),
                    "chainHash": row["chain_hash"],
                    "prevHash": row["prev_hash"],
                }
                for row in rows
            ]
        with self._lock:
            return self._ring[-limit:]


audit_log = AuditLog()
