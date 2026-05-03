from __future__ import annotations

import hashlib
import json
from typing import Any

from app.agent.prompts import SYSTEM_PROMPT
from app.agent.state import SessionState
from app.schemas.agent import AgentTurnRequest
from app.skills.registry import SkillManifest


class ContextBuilder:
    async def build(
        self,
        *,
        session: SessionState,
        req: AgentTurnRequest,
        visible_tools: list[SkillManifest],
        blocked_tools: dict[str, str],
    ) -> list[dict[str, Any]]:
        messages: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]
        env_hash = self._env_hash(req)
        if session.environment_version != env_hash:
            messages.append({"role": "system", "content": "[Environment]\n" + self._environment_summary(session, req)})
            session.environment_version = env_hash
        messages.append({"role": "system", "content": "[Memory]\n" + self._memory_snapshot(session.memory)})
        messages.append({"role": "system", "content": "[Tool Availability]\n" + self._tool_availability_summary(visible_tools, blocked_tools)})
        messages.extend(self._recent_history(session.messages[-8:]))
        if req.recent_messages:
            messages.append({"role": "system", "content": "[HMI Recent Feed]\n" + self._feed_summary(req.recent_messages[-6:])})
        messages.append({"role": "user", "content": req.message})
        messages.extend(session.resume_messages)
        session.resume_messages = []
        return messages

    def _env_hash(self, req: AgentTurnRequest) -> str:
        payload = {
            "mission": req.mission,
            "alert_level": req.alert_level,
            "fleet": [
                {
                    "id": item.get("id"),
                    "mode": item.get("mode"),
                    "battery_pct": item.get("battery_pct"),
                    "task": item.get("task"),
                    "segment": item.get("segment"),
                }
                for item in req.fleet
                if isinstance(item, dict)
            ],
            "telemetry": self._telemetry_digest(req.telemetry),
        }
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _environment_summary(self, session: SessionState, req: AgentTurnRequest) -> str:
        fleet_lines = []
        for item in req.fleet[:8]:
            if not isinstance(item, dict):
                continue
            fleet_lines.append(
                f"- {item.get('id')}: mode={item.get('mode')}, battery={item.get('battery_pct')}%, "
                f"task={item.get('task')}, segment={item.get('segment')}"
            )
        telemetry = self._telemetry_digest(req.telemetry)
        return "\n".join(
            [
                f"session={session.session_id}",
                f"mission={req.mission}",
                f"alert_level={req.alert_level}",
                "fleet:",
                *(fleet_lines or ["- none"]),
                "telemetry_digest=" + json.dumps(telemetry, ensure_ascii=False, separators=(",", ":")),
            ]
        )

    def _telemetry_digest(self, telemetry: dict[str, Any]) -> dict[str, Any]:
        weather = telemetry.get("weather", {}) if isinstance(telemetry, dict) else {}
        link = telemetry.get("link", {}) if isinstance(telemetry, dict) else {}
        edge = telemetry.get("edge", {}) if isinstance(telemetry, dict) else {}
        return {
            "weather": {
                "windSpeedMps": weather.get("windSpeedMps"),
                "rainfallMm": weather.get("rainfallMm"),
                "visibilityKm": weather.get("visibilityKm"),
                "condition": weather.get("condition"),
            },
            "link": {
                "heartbeatMs": link.get("heartbeatMs"),
                "packetLossPct": (link.get("primary") or {}).get("packetLossPct") if isinstance(link.get("primary"), dict) else None,
            },
            "edge": {
                "loadPct": edge.get("loadPct"),
                "queueDepth": edge.get("queueDepth"),
            },
        }

    def _memory_snapshot(self, memory: dict[str, Any]) -> str:
        short = memory.get("shortTerm", {}) if isinstance(memory, dict) else {}
        long = memory.get("longTerm", {}) if isinstance(memory, dict) else {}
        cache = memory.get("toolCache", []) if isinstance(memory, dict) else []
        return "\n".join(
            [
                "shortTerm=" + json.dumps(short, ensure_ascii=False, separators=(",", ":"))[:600],
                "longTerm_keys=" + ", ".join(list(long.keys())[:8]),
                "toolCache=" + json.dumps(cache[-5:], ensure_ascii=False, separators=(",", ":"))[:700] if isinstance(cache, list) else "toolCache=[]",
            ]
        )

    def _tool_availability_summary(self, visible_tools: list[SkillManifest], blocked_tools: dict[str, str]) -> str:
        visible = [f"- {tool.name}: {tool.description[:100]} [risk={tool.risk_level}]" for tool in visible_tools]
        blocked = [f"- {name}: blocked, {reason}" for name, reason in blocked_tools.items()]
        return "visible:\n" + "\n".join(visible) + "\nblocked:\n" + ("\n".join(blocked) if blocked else "- none")

    def _recent_history(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        compact: list[dict[str, Any]] = []
        for message in messages:
            role = str(message.get("role", "user"))
            content = str(message.get("content", ""))[:1000]
            if role in {"user", "assistant", "tool"} and content:
                compact.append({"role": role, "content": content})
        return compact

    def _feed_summary(self, feed: list[dict[str, Any]]) -> str:
        lines: list[str] = []
        for item in feed:
            if not isinstance(item, dict):
                continue
            lines.append(f"- {item.get('role')} {item.get('severity', '')}: {str(item.get('content', ''))[:180]}")
        return "\n".join(lines)


context_builder = ContextBuilder()
