from __future__ import annotations

from dataclasses import dataclass
from typing import Awaitable, Callable

from app.agent.state import SessionState
from app.skills.registry import SkillManifest, skill_registry


@dataclass(frozen=True)
class ToolGateRule:
    tool_name: str
    condition: Callable[[SessionState], Awaitable[bool]]
    reason_when_blocked: str


async def _has_pending_approval(session: SessionState) -> bool:
    return session.has_pending_approval()


async def _alert_active(session: SessionState) -> bool:
    return session.current_alert_is_active()


async def _evidence_complete(session: SessionState) -> bool:
    return session.evidence_chain_is_complete()


class DynamicToolGate:
    def __init__(self) -> None:
        self._rules: dict[str, ToolGateRule] = {
            "dispatch_usv": ToolGateRule(
                tool_name="dispatch_usv",
                condition=_has_pending_approval,
                reason_when_blocked="dispatch_usv 仅在审批恢复链路中可见；常规模型回合只能请求计划或说明审批需求。",
            ),
            "rtl_usv": ToolGateRule(
                tool_name="rtl_usv",
                condition=_has_pending_approval,
                reason_when_blocked="rtl_usv 必须通过后端控制请求和 HITL 审批路径触发。",
            ),
            "request_estop": ToolGateRule(
                tool_name="request_estop",
                condition=_has_pending_approval,
                reason_when_blocked="request_estop 必须通过后端控制请求和 HITL 审批路径触发。",
            ),
            "notify_authority": ToolGateRule(
                tool_name="notify_authority",
                condition=_evidence_complete,
                reason_when_blocked="notify_authority 需要已登记事件与完整证据链。",
            ),
            "lstm_predict": ToolGateRule(
                tool_name="lstm_predict",
                condition=_alert_active,
                reason_when_blocked="lstm_predict 仅在存在活动告警或异常事件时暴露。",
            ),
        }

    async def evaluate(self, session: SessionState) -> tuple[list[SkillManifest], dict[str, str]]:
        visible: list[SkillManifest] = []
        blocked: dict[str, str] = {}
        for manifest in skill_registry.list():
            rule = self._rules.get(manifest.name)
            if rule is None:
                visible.append(manifest)
                continue
            if await rule.condition(session):
                visible.append(manifest)
            else:
                blocked[manifest.name] = rule.reason_when_blocked
        session.visible_tools = [tool.name for tool in visible]
        session.blocked_tools = blocked
        return visible, blocked


dynamic_tool_gate = DynamicToolGate()
