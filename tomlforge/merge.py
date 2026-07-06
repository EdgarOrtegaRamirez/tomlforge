"""TOML merge engine — deep merge of TOML documents."""

from __future__ import annotations

from typing import Any


class MergeConflictError(Exception):
    """Raised when a merge conflict occurs."""

    def __init__(self, path: str, old_value: Any, new_value: Any):
        self.path = path
        self.old_value = old_value
        self.new_value = new_value
        super().__init__(f"Conflict at '{path}': {old_value!r} vs {new_value!r}")


def merge(
    base: dict[str, Any],
    override: dict[str, Any],
    strategy: str = "override",
) -> dict[str, Any]:
    """Deep merge two TOML documents.

    Args:
        base: The base (original) TOML document.
        override: The override TOML document.
        strategy: Merge strategy:
            - "override": override values win (default)
            - "base": base values win
            - "union": combine arrays, fail on scalar conflicts
            - "deep": recursive deep merge (same as override for dicts)

    Returns:
        New merged dictionary (base is not modified).

    Raises:
        MergeConflict: If strategy is "union" and there's a scalar conflict.
    """
    result = _deep_copy(base)
    _merge_dict(result, override, "", strategy)
    return result


def _merge_dict(
    base: dict[str, Any],
    override: dict[str, Any],
    prefix: str,
    strategy: str,
) -> None:
    """Recursively merge override into base."""
    for key, new_val in override.items():
        path = f"{prefix}.{key}" if prefix else key

        if key not in base:
            base[key] = _deep_copy(new_val)
            continue

        old_val = base[key]

        # Both dicts — recursive merge
        if isinstance(old_val, dict) and isinstance(new_val, dict):
            _merge_dict(old_val, new_val, path, strategy)
            continue

        # Both lists — handle differently based on strategy
        if isinstance(old_val, list) and isinstance(new_val, list):
            if strategy == "union":
                base[key] = old_val + new_val
            elif strategy == "base":
                pass  # keep base
            else:
                base[key] = _deep_copy(new_val)
            continue

        # Scalar conflict
        if old_val != new_val:
            if strategy == "union":
                raise MergeConflictError(path, old_val, new_val)
            elif strategy == "base":
                pass  # keep base
            else:
                base[key] = _deep_copy(new_val)


def _deep_copy(val: Any) -> Any:
    """Deep copy a value."""
    if isinstance(val, dict):
        return {k: _deep_copy(v) for k, v in val.items()}
    if isinstance(val, list):
        return [_deep_copy(item) for item in val]
    return val


def flatten(data: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    """Flatten a nested TOML dict into dot-separated keys.

    Args:
        data: Nested TOML dictionary.
        prefix: Key prefix.

    Returns:
        Flattened dictionary with dot-separated keys.
    """
    result = {}
    for key, value in data.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            result.update(flatten(value, full_key))
        elif isinstance(value, list):
            for i, item in enumerate(value):
                item_key = f"{full_key}.{i}"
                if isinstance(item, dict):
                    result.update(flatten(item, item_key))
                else:
                    result[item_key] = item
        else:
            result[full_key] = value
    return result


def unflatten(data: dict[str, Any]) -> dict[str, Any]:
    """Unflatten a dot-separated dict back to nested structure.

    Args:
        data: Flattened dictionary with dot-separated keys.

    Returns:
        Nested TOML dictionary.
    """
    result: dict[str, Any] = {}
    for key, value in data.items():
        parts = key.split(".")
        current: Any = result
        for i, part in enumerate(parts[:-1]):
            if part.isdigit():
                # Array index
                idx = int(part)
                if i > 0:
                    prev = parts[i - 1]
                    if not isinstance(current.get(prev), list):
                        current[prev] = []
                    arr = current[prev]
                    while len(arr) <= idx:
                        arr.append({})
                    current = arr[idx]
            else:
                if part not in current:
                    next_part = parts[i + 1] if i + 1 < len(parts) - 1 else parts[-1]
                    if next_part.isdigit():
                        current[part] = []
                    else:
                        current[part] = {}
                current = current[part]

        # Set the value
        last = parts[-1]
        if last.isdigit():
            idx = int(last)
            arr = current
            while len(arr) <= idx:
                arr.append(None)
            arr[idx] = value
        else:
            current[last] = value

    return result
