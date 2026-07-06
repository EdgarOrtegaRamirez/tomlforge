"""TOML formatter — pretty-print and compact TOML documents."""

from __future__ import annotations

from datetime import date, datetime, time
from typing import Any


def format_toml(
    data: dict[str, Any],
    indent: int = 4,
    sort_keys: bool = False,
    width: int = 80,
) -> str:
    """Format a TOML dict as a TOML string.

    Args:
        data: Parsed TOML dictionary.
        indent: Number of spaces for indentation.
        sort_keys: If True, sort keys alphabetically.
        width: Maximum line width (for inline tables).

    Returns:
        Formatted TOML string.
    """
    lines: list[str] = []
    _format_table(data, [], lines, indent, sort_keys, width, is_root=True)
    return "\n".join(lines) + "\n"


def compact(data: dict[str, Any]) -> str:
    """Format a TOML dict as compact TOML (minimal whitespace).

    Args:
        data: Parsed TOML dictionary.

    Returns:
        Compact TOML string.
    """
    return format_toml(data, indent=0, sort_keys=True, width=999999)


def _format_value(val: Any, indent_level: int, indent: int, width: int) -> str:
    """Format a single TOML value."""
    if isinstance(val, bool):
        return "true" if val else "false"
    if isinstance(val, int):
        return str(val)
    if isinstance(val, float):
        return repr(val)
    if isinstance(val, str):
        return _format_string(val)
    if isinstance(val, datetime):
        return val.isoformat()
    if isinstance(val, date):
        return val.isoformat()
    if isinstance(val, time):
        return val.isoformat()
    if isinstance(val, list):
        return _format_array(val, indent_level, indent, width)
    if isinstance(val, dict):
        return _format_inline_table(val, indent_level, indent, width)
    return repr(val)


def _format_string(s: str) -> str:
    """Format a string for TOML output."""
    # Use basic string with escapes
    escaped = ""
    for ch in s:
        if ch == "\\":
            escaped += "\\\\"
        elif ch == '"':
            escaped += '\\"'
        elif ch == "\n":
            escaped += "\\n"
        elif ch == "\t":
            escaped += "\\t"
        elif ch == "\r":
            escaped += "\\r"
        elif ch == "\b":
            escaped += "\\b"
        elif ch == "\f":
            escaped += "\\f"
        elif ord(ch) < 0x20 or ord(ch) == 0x7F:
            escaped += f"\\u{ord(ch):04x}"
        else:
            escaped += ch
    return f'"{escaped}"'


def _format_array(arr: list[Any], indent_level: int, indent: int, width: int) -> str:
    """Format an array."""
    if not arr:
        return "[]"

    # Try inline format first
    items = [_format_value(item, indent_level, indent, width) for item in arr]
    inline = "[" + ", ".join(items) + "]"
    if len(inline) <= width:
        return inline

    # Multiline format
    spaces = " " * (indent_level * indent + indent)
    inner_spaces = " " * ((indent_level + 1) * indent)
    lines = ["["]
    for item in arr:
        formatted = _format_value(item, indent_level + 1, indent, width)
        lines.append(f"{inner_spaces}{formatted},")
    lines.append(f"{spaces}]")
    return "\n".join(lines)


def _format_inline_table(
    tbl: dict[str, Any],
    indent_level: int,
    indent: int,
    width: int,
) -> str:
    """Format an inline table."""
    if not tbl:
        return "{}"

    items = []
    for k, v in tbl.items():
        items.append(f"{k} = {_format_value(v, indent_level, indent, width)}")
    inline = "{" + ", ".join(items) + "}"
    if len(inline) <= width:
        return inline

    # Multiline inline table
    spaces = " " * (indent_level * indent + indent)
    inner_spaces = " " * ((indent_level + 1) * indent)
    lines = ["{"]
    for k, v in tbl.items():
        formatted = _format_value(v, indent_level + 1, indent, width)
        lines.append(f"{inner_spaces}{k} = {formatted},")
    lines.append(f"{spaces}}}")
    return "\n".join(lines)


def _format_table(
    tbl: dict[str, Any],
    prefix: list[str],
    lines: list[str],
    indent: int,
    sort_keys: bool,
    width: int,
    is_root: bool = False,
) -> None:
    """Format a table recursively."""
    keys = sorted(tbl.keys()) if sort_keys else list(tbl.keys())

    # First pass: simple values (scalars and inline-able)
    simple_keys = []
    table_keys = []
    array_of_table_keys = []

    for key in keys:
        val = tbl[key]
        if isinstance(val, dict):
            table_keys.append(key)
        elif isinstance(val, list) and val and isinstance(val[0], dict):
            array_of_table_keys.append(key)
        else:
            simple_keys.append(key)

    # Format simple values
    for key in simple_keys:
        val = tbl[key]
        formatted = _format_value(val, 0, indent, width)
        lines.append(f"{key} = {formatted}")

    if simple_keys and (table_keys or array_of_table_keys):
        lines.append("")

    # Format sub-tables
    for i, key in enumerate(table_keys):
        path = prefix + [key]
        header = "[" + ".".join(path) + "]"
        lines.append(header)
        _format_table(tbl[key], path, lines, indent, sort_keys, width)
        if i < len(table_keys) - 1 or array_of_table_keys:
            lines.append("")

    # Format array of tables
    for i, key in enumerate(array_of_table_keys):
        path = prefix + [key]
        for item in tbl[key]:
            header = "[[" + ".".join(path) + "]]"
            lines.append(header)
            _format_table(item, path, lines, indent, sort_keys, width)
            if i < len(array_of_table_keys) - 1:
                lines.append("")
