from __future__ import annotations

import secrets
from dataclasses import dataclass
from typing import Any, Literal, Protocol


class SubAgent(Protocol):
    name: str
    description: str

    async def run(self, context: dict[str, Any]) -> dict[str, Any]:
        ...


@dataclass
class DelegatedTask:
    task_id: str
    sub_agent_name: str
    input: dict[str, Any]
    status: Literal["pending", "running", "done", "failed"]
    result: dict[str, Any] | None = None


class RuleBasedSubAgent:
    def __init__(self, name: str, description: str, focus: str) -> None:
        self.name = name
        self.description = description
        self.focus = focus

    async def run(self, context: dict[str, Any]) -> dict[str, Any]:
        return {
            "agent": self.name,
            "focus": self.focus,
            "findings": self._findings(context),
            "summary": f"{self.description} 已完成专项分析。",
        }

    def _findings(self, context: dict[str, Any]) -> list[str]:
        text = str(context)[:2000]
        findings = [f"输入范围 {len(text)} chars，已按 {self.focus} 维度压缩。"]
        if "TP-03" in text or "DP-03" in text:
            findings.append("检测到 TP-03/DP-03 相关线索，建议优先核验传感器健康、上下游差异和排口历史。")
        if "battery" in text or "battery_pct" in text:
            findings.append("检测到艇端电量上下文，调度前应执行电量、链路、天气三项门控。")
        return findings


class AgentTaskDelegator:
    def __init__(self) -> None:
        self._sub_agents: dict[str, SubAgent] = {}
        self.register(RuleBasedSubAgent("water-quality-analyst", "水质异常分析子 Agent", "GB3838、水质趋势、污染源假设"))
        self.register(RuleBasedSubAgent("usv-path-planner", "USV 路径规划子 Agent", "任务级航线、约束、调度风险"))
        self.register(RuleBasedSubAgent("compliance-checker", "合规检查子 Agent", "审批、证据链、对外上报边界"))

    def register(self, agent: SubAgent) -> None:
        self._sub_agents[agent.name] = agent

    def public_agents(self) -> list[dict[str, str]]:
        return [{"name": agent.name, "description": agent.description} for agent in self._sub_agents.values()]

    async def delegate(self, sub_agent_name: str, input_data: dict[str, Any]) -> DelegatedTask:
        if sub_agent_name not in self._sub_agents:
            raise KeyError(f"Sub-agent not registered: {sub_agent_name}")
        task = DelegatedTask(
            task_id=f"sub-{secrets.token_urlsafe(6)}",
            sub_agent_name=sub_agent_name,
            input=input_data,
            status="running",
        )
        try:
            task.result = await self._sub_agents[sub_agent_name].run(input_data)
            task.status = "done"
        except Exception as exc:
            task.result = {"error": f"{type(exc).__name__}: {exc}"}
            task.status = "failed"
        return task


task_delegator = AgentTaskDelegator()
