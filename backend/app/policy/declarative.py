from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


class RuleEvaluator:
    def __init__(self, rules_path: str = "backend/config/policy.yaml") -> None:
        self.rules_path = self._resolve_path(rules_path)
        self._policies = self._load()

    def _resolve_path(self, rules_path: str) -> Path:
        candidates = [
            Path(rules_path),
            Path.cwd() / rules_path,
            Path.cwd() / "config" / "policy.yaml",
            Path(__file__).resolve().parents[3] / "config" / "policy.yaml",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return candidates[0]

    def _load(self) -> list[dict[str, Any]]:
        if not self.rules_path.exists():
            return []
        try:
            import yaml
        except ImportError:
            return self._load_minimal_yaml(self.rules_path.read_text(encoding="utf-8"))
        loaded = yaml.safe_load(self.rules_path.read_text(encoding="utf-8")) or {}
        return list(loaded.get("policies") or [])

    def _load_minimal_yaml(self, text: str) -> list[dict[str, Any]]:
        # JSON is valid YAML; this fallback keeps tests usable when PyYAML is unavailable.
        try:
            loaded = json.loads(text)
            return list(loaded.get("policies") or [])
        except json.JSONDecodeError:
            return []

    def evaluate(self, tool_name: str, args: dict[str, Any], context: dict[str, Any] | None = None) -> list[str]:
        violations: list[str] = []
        for policy in self._policies:
            if tool_name not in (policy.get("applies_to") or []):
                continue
            for rule in policy.get("rules") or []:
                value = self._resolve_field(str(rule.get("field", "")), args, context or {})
                if not self._check(rule, value):
                    violations.append(self._format_error(rule, value, args))
        return violations

    def _resolve_field(self, field: str, args: dict[str, Any], context: dict[str, Any]) -> Any:
        value: Any = args
        for part in field.split("."):
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None
        return value

    def _check(self, rule: dict[str, Any], value: Any) -> bool:
        operator = rule.get("operator")
        if operator == "in":
            return value in set(rule.get("values") or [])
        if operator == "subset":
            allowed = set(rule.get("values") or [])
            if not isinstance(value, list):
                return False
            return all(item in allowed for item in value)
        if operator == "gte":
            return float(value) >= float(rule.get("value"))
        if operator == "lte":
            return float(value) <= float(rule.get("value"))
        if operator == "matches":
            return bool(re.search(str(rule.get("value", "")), str(value or "")))
        return True

    def _format_error(self, rule: dict[str, Any], value: Any, args: dict[str, Any]) -> str:
        try:
            return str(rule.get("error", "Policy violation: {value}")).format(**args, value=value)
        except Exception:
            return f"{rule.get('error', 'Policy violation')}: {value}"
