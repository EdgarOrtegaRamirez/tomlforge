"""TOML diff engine — structural comparison of two TOML documents."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ChangeType(Enum):
    """Type of change."""

    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"


@dataclass
class Change:
    """A single change between two TOML documents."""

    path: str
    change_type: ChangeType
    old_value: Any = None
    new_value: Any = None

    def __str__(self) -> str:
        if self.change_type == ChangeType.ADDED:
            return f"+ {self.path} = {self._fmt_value(self.new_value)}"
        elif self.change_type == ChangeType.REMOVED:
            return f"- {self.path} = {self._fmt_value(self.old_value)}"
        else:
            old = self._fmt_value(self.old_value)
            new = self._fmt_value(self.new_value)
            return f"~ {self.path}: {old} -> {new}"

    @staticmethod
    def _fmt_value(val: Any) -> str:
        if isinstance(val, str):
            return f'"{val}"'
        if isinstance(val, dict):
            return "{...}"
        if isinstance(val, list):
            return f"[... ({len(val)} items)]"
        return repr(val)


@dataclass
class DiffResult:
    """Result of comparing two TOML documents."""

    changes: list[Change] = field(default_factory=list)
    identical: bool = True

    @property
    def added(self) -> list[Change]:
        return [c for c in self.changes if c.change_type == ChangeType.ADDED]

    @property
    def removed(self) -> list[Change]:
        return [c for c in self.changes if c.change_type == ChangeType.REMOVED]

    @property
    def modified(self) -> list[Change]:
        return [c for c in self.changes if c.change_type == ChangeType.MODIFIED]

    @property
    def summary(self) -> dict[str, int]:
        return {
            "added": len(self.added),
            "removed": len(self.removed),
            "modified": len(self.modified),
            "total": len(self.changes),
        }


def diff(old: dict[str, Any], new: dict[str, Any]) -> DiffResult:
    """Compare two TOML documents and return the differences.

    Args:
        old: The old (original) TOML document.
        new: The new (modified) TOML document.

    Returns:
        DiffResult with all changes found.
    """
    result = DiffResult()
    _compare_tables(old, new, "", result)
    result.identical = len(result.changes) == 0
    return result


def _compare_tables(
    old: dict[str, Any], new: dict[str, Any], prefix: str, result: DiffResult
) -> None:
    """Recursively compare two tables."""
    all_keys = set(old.keys()) | set(new.keys())

    for key in sorted(all_keys):
        path = f"{prefix}.{key}" if prefix else key

        if key not in old:
            # Key added
            result.changes.append(
                Change(
                    path=path,
                    change_type=ChangeType.ADDED,
                    new_value=new[key],
                )
            )
        elif key not in new:
            # Key removed
            result.changes.append(
                Change(
                    path=path,
                    change_type=ChangeType.REMOVED,
                    old_value=old[key],
                )
            )
        else:
            # Both have the key — compare values
            _compare_values(old[key], new[key], path, result)


def _compare_values(old: Any, new: Any, path: str, result: DiffResult) -> None:
    """Compare two values and record differences."""
    # Type change is always a modification
    if type(old) is not type(new):
        result.changes.append(
            Change(
                path=path,
                change_type=ChangeType.MODIFIED,
                old_value=old,
                new_value=new,
            )
        )
        return

    if isinstance(old, dict) and isinstance(new, dict):
        _compare_tables(old, new, path, result)
    elif isinstance(old, list) and isinstance(new, list):
        _compare_arrays(old, new, path, result)
    elif old != new:
        result.changes.append(
            Change(
                path=path,
                change_type=ChangeType.MODIFIED,
                old_value=old,
                new_value=new,
            )
        )


def _compare_arrays(old: list[Any], new: list[Any], path: str, result: DiffResult) -> None:
    """Compare two arrays."""
    max_len = max(len(old), len(new))

    for i in range(max_len):
        item_path = f"{path}.{i}"

        if i >= len(old):
            result.changes.append(
                Change(
                    path=item_path,
                    change_type=ChangeType.ADDED,
                    new_value=new[i],
                )
            )
        elif i >= len(new):
            result.changes.append(
                Change(
                    path=item_path,
                    change_type=ChangeType.REMOVED,
                    old_value=old[i],
                )
            )
        else:
            _compare_values(old[i], new[i], item_path, result)


def format_diff(result: DiffResult, fmt: str = "text") -> str:
    """Format a diff result as a string.

    Args:
        result: The diff result to format.
        format: Output format: "text", "json", or "markdown".

    Returns:
        Formatted diff string.
    """
    if fmt == "json":
        import json

        data = {
            "identical": result.identical,
            "summary": result.summary,
            "changes": [
                {
                    "path": c.path,
                    "type": c.change_type.value,
                    "old": str(c.old_value) if c.old_value is not None else None,
                    "new": str(c.new_value) if c.new_value is not None else None,
                }
                for c in result.changes
            ],
        }
        return json.dumps(data, indent=2)

    if fmt == "markdown":
        lines = ["# TOML Diff\n"]
        if result.identical:
            lines.append("No differences found.\n")
            return "\n".join(lines)

        s = result.summary
        lines.append(
            f"**Summary:** {s['added']} added, {s['removed']} removed, {s['modified']} modified\n"
        )

        if result.added:
            lines.append("## Added\n")
            for c in result.added:
                lines.append(f"- `{c.path}` = `{c.new_value}`")
            lines.append("")

        if result.removed:
            lines.append("## Removed\n")
            for c in result.removed:
                lines.append(f"- `{c.path}` = `{c.old_value}`")
            lines.append("")

        if result.modified:
            lines.append("## Modified\n")
            for c in result.modified:
                lines.append(f"- `{c.path}`: `{c.old_value}` → `{c.new_value}`")
            lines.append("")

        return "\n".join(lines)

    # Default: text format
    if result.identical:
        return "No differences found."

    lines = []
    s = result.summary
    lines.append(
        f"--- Summary: {s['added']} added, {s['removed']} removed, {s['modified']} modified ---"
    )
    lines.append("")

    for c in result.changes:
        lines.append(str(c))

    return "\n".join(lines)
