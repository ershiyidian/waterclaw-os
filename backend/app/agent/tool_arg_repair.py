from __future__ import annotations

import ast
import json
import re
from typing import Any


class ToolArgRepairer:
    def repair(self, raw_args: str | dict[str, Any], schema: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
        warnings: list[str] = []
        if isinstance(raw_args, dict):
            args = dict(raw_args)
        else:
            args = self._parse(str(raw_args), warnings)

        for field in schema.get("required", []):
            if field not in args:
                args[field] = None
                warnings.append(f"Missing required field '{field}', set to null")

        properties = schema.get("properties", {})
        if isinstance(properties, dict):
            for prop_name, prop_schema in properties.items():
                if prop_name in args and args[prop_name] is not None and isinstance(prop_schema, dict):
                    args[prop_name] = self._coerce(args[prop_name], prop_schema, warnings, prop_name)
        return args, warnings

    def _parse(self, raw: str, warnings: list[str]) -> dict[str, Any]:
        try:
            parsed = json.loads(raw or "{}")
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

        try:
            parsed = ast.literal_eval(raw)
            if isinstance(parsed, dict):
                warnings.append("Arguments repaired via Python literal parser")
                return parsed
        except Exception:
            pass

        balanced = self._balance_json(raw)
        if balanced != raw:
            try:
                parsed = json.loads(balanced)
                if isinstance(parsed, dict):
                    warnings.append("Arguments repaired by balancing braces")
                    return parsed
            except json.JSONDecodeError:
                pass

        extracted = self._regex_extract(raw)
        if extracted:
            warnings.append("Arguments repaired via key/value extraction")
            return extracted
        warnings.append("Arguments could not be parsed; empty object used")
        return {}

    def _balance_json(self, raw: str) -> str:
        text = raw.strip()
        if not text.startswith("{") and "{" in text:
            text = text[text.index("{") :]
        missing_braces = text.count("{") - text.count("}")
        missing_brackets = text.count("[") - text.count("]")
        if missing_brackets > 0:
            text += "]" * missing_brackets
        if missing_braces > 0:
            text += "}" * missing_braces
        text = re.sub(r",\s*([}\]])", r"\1", text)
        return text

    def _regex_extract(self, raw: str) -> dict[str, Any]:
        extracted: dict[str, Any] = {}
        for match in re.finditer(r"['\"]?([A-Za-z_][\w-]*)['\"]?\s*:\s*([^,\n}]+)", raw):
            key = match.group(1)
            value = match.group(2).strip().strip("'\"")
            extracted[key] = value
        return extracted

    def _coerce(self, value: Any, schema: dict[str, Any], warnings: list[str], field_name: str) -> Any:
        expected = schema.get("type")
        if expected == "integer" and isinstance(value, float):
            warnings.append(f"Coerced {field_name} float to integer")
            return int(value)
        if expected == "integer" and isinstance(value, str) and value.strip().isdigit():
            warnings.append(f"Coerced {field_name} string to integer")
            return int(value)
        if expected == "number" and isinstance(value, str):
            try:
                warnings.append(f"Coerced {field_name} string to number")
                return float(value)
            except ValueError:
                return value
        if expected == "string" and not isinstance(value, str):
            warnings.append(f"Coerced {field_name} to string")
            return str(value)
        if expected == "array" and isinstance(value, str):
            warnings.append(f"Coerced {field_name} comma-separated string to array")
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


tool_arg_repairer = ToolArgRepairer()
