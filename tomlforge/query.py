"""TOML query engine — dot-notation path access."""

from __future__ import annotations

from typing import Any


class QueryError(Exception):
    """Raised when a query fails."""


def query(data: dict[str, Any], path: str) -> Any:
    """Query a TOML dict using dot-notation path.

    Args:
        data: Parsed TOML dictionary.
        path: Dot-separated key path (e.g., "server.host").

    Returns:
        The value at the path.

    Raises:
        QueryError: If the path doesn't exist.
    """
    keys = _parse_path(path)
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        elif isinstance(current, list) and key.isdigit():
            idx = int(key)
            if 0 <= idx < len(current):
                current = current[idx]
            else:
                raise QueryError(f"Index {idx} out of range (length {len(current)})")
        else:
            raise QueryError(f"Key '{key}' not found in path '{path}'")
    return current


def set_value(data: dict[str, Any], path: str, value: Any) -> None:
    """Set a value in a TOML dict using dot-notation path.

    Args:
        data: Parsed TOML dictionary (modified in place).
        path: Dot-separated key path (e.g., "server.port").
        value: Value to set.

    Raises:
        QueryError: If the path structure is invalid.
    """
    keys = _parse_path(path)
    current = data
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        elif not isinstance(current[key], dict):
            raise QueryError(f"Cannot set path '{path}': '{key}' is not a table")
        current = current[key]
    current[keys[-1]] = value


def delete(data: dict[str, Any], path: str) -> Any:
    """Delete a value from a TOML dict using dot-notation path.

    Args:
        data: Parsed TOML dictionary (modified in place).
        path: Dot-separated key path (e.g., "server.host").

    Returns:
        The deleted value.

    Raises:
        QueryError: If the path doesn't exist.
    """
    keys = _parse_path(path)
    current = data
    for key in keys[:-1]:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            raise QueryError(f"Key '{key}' not found in path '{path}'")

    if isinstance(current, dict) and keys[-1] in current:
        deleted = current[keys[-1]]
        del current[keys[-1]]
        return deleted
    raise QueryError(f"Key '{keys[-1]}' not found in path '{path}'")


def list_keys(data: dict[str, Any], path: str = "", recursive: bool = False) -> list[str]:
    """List keys at a given path.

    Args:
        data: Parsed TOML dictionary.
        path: Dot-separated key path. Empty string means root.
        recursive: If True, list all keys recursively.

    Returns:
        List of key names.
    """
    current = query(data, path) if path else data

    if not isinstance(current, dict):
        return []

    keys = list(current.keys())
    if not recursive:
        return keys

    result = []
    for key in keys:
        full_path = f"{path}.{key}" if path else key
        result.append(full_path)
        if isinstance(current[key], dict):
            result.extend(list_keys(data, full_path, recursive=True))
        elif isinstance(current[key], list):
            for i, item in enumerate(current[key]):
                if isinstance(item, dict):
                    item_path = f"{full_path}.{i}"
                    result.append(item_path)
                    result.extend(list_keys(data, item_path, recursive=True))
    return result


def exists(data: dict[str, Any], path: str) -> bool:
    """Check if a path exists in the TOML dict.

    Args:
        data: Parsed TOML dictionary.
        path: Dot-separated key path.

    Returns:
        True if the path exists.
    """
    try:
        query(data, path)
        return True
    except QueryError:
        return False


def get_type(data: dict[str, Any], path: str) -> str:
    """Get the TOML type of a value at the given path.

    Args:
        data: Parsed TOML dictionary.
        path: Dot-separated key path.

    Returns:
        Type name: "table", "array", "string", "integer", "float",
        "boolean", "datetime", "date", "time", or "unknown".
    """
    val = query(data, path)
    if isinstance(val, dict):
        return "table"
    if isinstance(val, list):
        return "array"
    if isinstance(val, str):
        return "string"
    if isinstance(val, int):
        return "integer"
    if isinstance(val, float):
        return "float"
    if isinstance(val, bool):
        return "boolean"
    from datetime import date, datetime, time

    if isinstance(val, datetime):
        return "datetime"
    if isinstance(val, date):
        return "date"
    if isinstance(val, time):
        return "time"
    return "unknown"


def _parse_path(path: str) -> list[str]:
    """Parse a dot-separated key path into a list of keys."""
    if not path:
        return []
    parts = path.split(".")
    result = []
    for part in parts:
        # Handle quoted keys
        if (part.startswith('"') and part.endswith('"')) or (
            part.startswith("'") and part.endswith("'")
        ):
            result.append(part[1:-1])
        else:
            result.append(part)
    return result
