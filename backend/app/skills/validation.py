from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError

from app.skills.registry import SkillManifest
from app.skills.semantic_validation import SemanticArgumentError, validate_semantics


class ToolArgumentError(ValueError):
    pass


@dataclass(frozen=True)
class ValidationResult:
    args: dict[str, Any]


def validate_tool_args(manifest: SkillManifest, args: dict[str, Any]) -> ValidationResult:
    schema = dict(manifest.input_schema)
    if "$schema" not in schema:
        schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(args), key=lambda err: list(err.path))
    if errors:
        raise ToolArgumentError("; ".join(_format_error(error) for error in errors[:5]))
    try:
        args = validate_semantics(manifest, args)
    except SemanticArgumentError as exc:
        raise ToolArgumentError(str(exc)) from exc
    return ValidationResult(args=args)


def _format_error(error: ValidationError) -> str:
    path = ".".join(str(item) for item in error.path) or "<root>"
    return f"{path}: {error.message}"
