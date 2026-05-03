from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.policy.declarative import RuleEvaluator
from app.skills.registry import SkillManifest


@dataclass(frozen=True)
class RiskDecision:
    risk_level: str
    requires_approval: bool
    reason: str


class PolicyEngine:
    def __init__(self) -> None:
        self.rules = RuleEvaluator()

    def classify(self, manifest: SkillManifest, args: dict[str, Any]) -> RiskDecision:
        if manifest.risk_level == "critical":
            return RiskDecision(
                risk_level="critical",
                requires_approval=True,
                reason=manifest.approval.get("reason", "高风险工具需要人工审批。") if manifest.approval else "高风险工具需要人工审批。",
            )
        if manifest.risk_level == "confirm":
            return RiskDecision(
                risk_level="confirm",
                requires_approval=False,
                reason="该工具只生成计划或建议，不直接写入控制总线。",
            )
        return RiskDecision(risk_level="safe", requires_approval=False, reason="只读或无副作用工具，可自动执行。")

    def validate_args_policy(self, manifest: SkillManifest, args: dict[str, Any], context: dict[str, Any] | None = None) -> None:
        context = context or {}
        violations = self.rules.evaluate(manifest.name, args, context)
        if violations:
            raise PermissionError("; ".join(violations))
        if manifest.name == "dispatch_usv":
            self._validate_dispatch_dynamic(args, context)
        elif manifest.name == "notify_authority":
            self._validate_notify_dynamic(args, context)

    def _validate_dispatch_dynamic(self, args: dict[str, Any], context: dict[str, Any]) -> None:
        usv = str(args.get("usv"))
        fleet = {str(item.get("id")): item for item in context.get("fleet", []) if isinstance(item, dict)}
        telemetry = context.get("telemetry", {}) if isinstance(context.get("telemetry"), dict) else {}
        weather = telemetry.get("weather", {}) if isinstance(telemetry.get("weather"), dict) else {}

        if usv in fleet and float(fleet[usv].get("battery_pct", 0)) < 30:
            raise PermissionError(f"{usv} battery is below dispatch threshold.")
        if float(weather.get("rainfallMm", 0) or 0) > 5:
            raise PermissionError("Rainfall exceeds dispatch operating window.")

    def _validate_notify_dynamic(self, args: dict[str, Any], context: dict[str, Any]) -> None:
        memory = context.get("memory", {}) if isinstance(context.get("memory"), dict) else {}
        short = memory.get("shortTerm", {}) if isinstance(memory.get("shortTerm"), dict) else {}
        if short.get("current_alert") in (None, "none"):
            raise PermissionError("Authority notification requires an active incident evidence chain.")

    def assert_allowed_after_approval(self, manifest: SkillManifest) -> None:
        if manifest.risk_level != "critical":
            return
        write_scopes = manifest.permissions.get("write", [])
        if not write_scopes:
            raise PermissionError("Critical tools must declare explicit write permissions.")


policy_engine = PolicyEngine()
