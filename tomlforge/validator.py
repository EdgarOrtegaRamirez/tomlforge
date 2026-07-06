"""TOML validator — check for issues and style violations."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class Severity(Enum):
    """Issue severity."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class Issue:
    """A validation issue."""

    severity: Severity
    code: str
    message: str
    path: str = ""

    def __str__(self) -> str:
        prefix = self.severity.value.upper()
        loc = f" [{self.path}]" if self.path else ""
        return f"{prefix} {self.code}{loc}: {self.message}"


@dataclass
class ValidationResult:
    """Result of validation."""

    issues: list[Issue] = None  # type: ignore[assignment]
    valid: bool = True

    def __post_init__(self):
        if self.issues is None:
            self.issues = []

    @property
    def errors(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == Severity.ERROR]

    @property
    def warnings(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == Severity.WARNING]

    @property
    def infos(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == Severity.INFO]

    @property
    def summary(self) -> dict[str, int]:
        return {
            "errors": len(self.errors),
            "warnings": len(self.warnings),
            "infos": len(self.infos),
            "total": len(self.issues),
        }


def validate(
    data: dict[str, Any],
    *,
    check_dupe_keys: bool = True,
    check_naming: bool = True,
    check_empty: bool = True,
    check_types: bool = True,
    max_depth: int = 10,
) -> ValidationResult:
    """Validate a TOML document.

    Args:
        data: Parsed TOML dictionary.
        check_dupe_keys: Check for potential duplicate key patterns.
        check_naming: Check key naming conventions.
        check_empty: Check for empty tables/arrays.
        check_types: Check for mixed-type arrays.
        max_depth: Maximum nesting depth.

    Returns:
        ValidationResult with any issues found.
    """
    result = ValidationResult()
    _validate_table(data, "", result, max_depth, 0, check_naming, check_empty, check_types)
    result.valid = len(result.errors) == 0
    return result


def _validate_table(
    tbl: dict[str, Any],
    prefix: str,
    result: ValidationResult,
    max_depth: int,
    depth: int,
    check_naming: bool,
    check_empty: bool,
    check_types: bool,
) -> None:
    """Recursively validate a table."""
    if depth > max_depth:
        result.issues.append(
            Issue(
                severity=Severity.ERROR,
                code="TOO_DEEP",
                message=f"Nesting depth {depth} exceeds maximum {max_depth}",
                path=prefix,
            )
        )
        return

    for key, value in tbl.items():
        path = f"{prefix}.{key}" if prefix else key

        # Check naming conventions
        if check_naming:
            _check_naming(key, path, result)

        # Check for empty values
        if check_empty:
            if isinstance(value, dict) and not value:
                result.issues.append(
                    Issue(
                        severity=Severity.INFO,
                        code="EMPTY_TABLE",
                        message=f"Empty table '{key}'",
                        path=path,
                    )
                )
            elif isinstance(value, list) and not value:
                result.issues.append(
                    Issue(
                        severity=Severity.INFO,
                        code="EMPTY_ARRAY",
                        message=f"Empty array '{key}'",
                        path=path,
                    )
                )

        # Check for mixed-type arrays
        if check_types and isinstance(value, list):
            _check_array_types(value, path, result)

        # Recurse into nested tables
        if isinstance(value, dict):
            _validate_table(
                value, path, result, max_depth, depth + 1, check_naming, check_empty, check_types
            )
        elif isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    _validate_table(
                        item,
                        f"{path}.{i}",
                        result,
                        max_depth,
                        depth + 1,
                        check_naming,
                        check_empty,
                        check_types,
                    )


def _check_naming(key: str, path: str, result: ValidationResult) -> None:
    """Check key naming conventions."""
    # Check for unusual characters
    if not key.replace("-", "").replace("_", "").replace(".", "").isalnum():
        result.issues.append(
            Issue(
                severity=Severity.WARNING,
                code="UNUSUAL_KEY",
                message=f"Key '{key}' contains unusual characters",
                path=path,
            )
        )

    # Check for leading/trailing hyphens
    if key.startswith("-") or key.endswith("-"):
        result.issues.append(
            Issue(
                severity=Severity.WARNING,
                code="HYPHEN_KEY",
                message=f"Key '{key}' starts or ends with a hyphen",
                path=path,
            )
        )

    # Check for ALL_CAPS (might be a constant, not a key)
    if key.isupper() and len(key) > 1:
        result.issues.append(
            Issue(
                severity=Severity.INFO,
                code="CONSTANT_KEY",
                message=f"Key '{key}' is ALL_CAPS — is this intentional?",
                path=path,
            )
        )


def _check_array_types(arr: list[Any], path: str, result: ValidationResult) -> None:
    """Check for mixed-type arrays."""
    if not arr:
        return

    types = set()
    for item in arr:
        if isinstance(item, bool):
            types.add("boolean")
        elif isinstance(item, int):
            types.add("integer")
        elif isinstance(item, float):
            types.add("float")
        elif isinstance(item, str):
            types.add("string")
        elif isinstance(item, dict):
            types.add("table")
        elif isinstance(item, list):
            types.add("array")
        else:
            types.add("unknown")

    # TOML allows mixed integer/float
    numeric_types = types - {"integer", "float"}
    if len(numeric_types) > 1 or (numeric_types and "table" in numeric_types):
        result.issues.append(
            Issue(
                severity=Severity.WARNING,
                code="MIXED_ARRAY",
                message=f"Array contains mixed types: {', '.join(sorted(types))}",
                path=path,
            )
        )


def format_validation(result: ValidationResult, fmt: str = "text") -> str:
    """Format validation results.

    Args:
        result: Validation result.
        format: Output format: "text", "json", or "markdown".

    Returns:
        Formatted string.
    """
    if fmt == "json":
        import json

        data = {
            "valid": result.valid,
            "summary": result.summary,
            "issues": [
                {
                    "severity": i.severity.value,
                    "code": i.code,
                    "message": i.message,
                    "path": i.path,
                }
                for i in result.issues
            ],
        }
        return json.dumps(data, indent=2)

    if fmt == "markdown":
        lines = ["# TOML Validation Report\n"]
        if result.valid:
            lines.append("✅ **Valid TOML**\n")
        else:
            lines.append("❌ **Invalid TOML**\n")

        s = result.summary
        lines.append(
            f"**Summary:** {s['errors']} errors, {s['warnings']} warnings, {s['infos']} info\n"
        )

        if result.issues:
            lines.append("## Issues\n")
            for i in result.issues:
                icon = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}[i.severity.value]
                lines.append(
                    f"- {icon} **{i.code}** {i.message}" + (f" (`{i.path}`)" if i.path else "")
                )
            lines.append("")

        return "\n".join(lines)

    # Text format
    lines = []
    if result.valid:
        lines.append("✅ Valid TOML")
    else:
        lines.append("❌ Invalid TOML")

    s = result.summary
    lines.append(f"Summary: {s['errors']} errors, {s['warnings']} warnings, {s['infos']} info")

    if result.issues:
        lines.append("")
        for i in result.issues:
            lines.append(f"  {i}")

    return "\n".join(lines)
