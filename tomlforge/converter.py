"""TOML converter — convert between TOML, JSON, and YAML."""

from __future__ import annotations

import json
from datetime import date, datetime, time
from typing import Any


def to_json(data: dict[str, Any], indent: int = 2) -> str:
    """Convert TOML dict to JSON string.

    Args:
        data: Parsed TOML dictionary.
        indent: JSON indentation.

    Returns:
        JSON string.
    """
    return json.dumps(data, indent=indent, default=_json_default, ensure_ascii=False)


def to_yaml(data: dict[str, Any]) -> str:
    """Convert TOML dict to YAML string.

    Args:
        data: Parsed TOML dictionary.

    Returns:
        YAML string.

    Raises:
        ImportError: If PyYAML is not installed.
    """
    try:
        import yaml
    except ImportError:
        raise ImportError(
            "PyYAML is required for YAML conversion. Install it with: pip install tomlforge[yaml]"
        ) from None

    return yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)


def from_json(text: str) -> dict[str, Any]:
    """Parse JSON string into a dict (compatible with TOML structure).

    Args:
        text: JSON string.

    Returns:
        Parsed dictionary.
    """
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("JSON root must be an object")
    return data


def from_yaml(text: str) -> dict[str, Any]:
    """Parse YAML string into a dict (compatible with TOML structure).

    Args:
        text: YAML string.

    Returns:
        Parsed dictionary.

    Raises:
        ImportError: If PyYAML is not installed.
    """
    try:
        import yaml
    except ImportError:
        raise ImportError(
            "PyYAML is required for YAML conversion. Install it with: pip install tomlforge[yaml]"
        ) from None

    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError("YAML root must be a mapping")
    return data


def _json_default(obj: Any) -> Any:
    """JSON serializer fallback for non-serializable types."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, date):
        return obj.isoformat()
    if isinstance(obj, time):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")
