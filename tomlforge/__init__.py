"""TomlForge: TOML Processing Toolkit."""

from tomlforge.converter import from_json, from_yaml, to_json, to_yaml
from tomlforge.diff import DiffResult, diff
from tomlforge.formatter import compact, format_toml
from tomlforge.merge import merge
from tomlforge.parser import TomlParser, parse
from tomlforge.query import delete, query, set_value
from tomlforge.validator import ValidationResult, validate

__version__ = "0.1.0"
__all__ = [
    "TomlParser",
    "parse",
    "query",
    "set_value",
    "delete",
    "diff",
    "DiffResult",
    "merge",
    "format_toml",
    "compact",
    "validate",
    "ValidationResult",
    "to_json",
    "to_yaml",
    "from_json",
    "from_yaml",
]
