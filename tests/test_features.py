"""Tests for query, diff, merge, formatter, validator, and converter."""

import pytest

from tomlforge.converter import from_json, to_json
from tomlforge.diff import diff, format_diff
from tomlforge.formatter import compact, format_toml
from tomlforge.merge import MergeConflictError, flatten, merge, unflatten
from tomlforge.parser import parse
from tomlforge.query import QueryError, delete, exists, get_type, list_keys, query, set_value
from tomlforge.validator import format_validation, validate

# ── Query Tests ──────────────────────────────────────────────────────


class TestQuery:
    def setup_method(self):
        self.data = parse("""
[server]
host = "localhost"
port = 8080

[database]
driver = "postgres"
url = "postgres://localhost/db"

[[servers]]
name = "alpha"
ip = "10.0.0.1"

[[servers]]
name = "beta"
ip = "10.0.0.2"
""")

    def test_simple_query(self):
        assert query(self.data, "server.host") == "localhost"

    def test_nested_query(self):
        assert query(self.data, "server.port") == 8080

    def test_array_index_query(self):
        assert query(self.data, "servers.0.name") == "alpha"

    def test_query_nonexistent(self):
        with pytest.raises(QueryError):
            query(self.data, "nonexistent.key")

    def test_set_value(self):
        set_value(self.data, "server.port", 9090)
        assert self.data["server"]["port"] == 9090

    def test_set_new_key(self):
        set_value(self.data, "server.ssl", True)
        assert self.data["server"]["ssl"] is True

    def test_delete(self):
        deleted = delete(self.data, "server.host")
        assert deleted == "localhost"
        assert "host" not in self.data["server"]

    def test_delete_nonexistent(self):
        with pytest.raises(QueryError):
            delete(self.data, "nonexistent.key")

    def test_list_keys(self):
        keys = list_keys(self.data)
        assert "server" in keys
        assert "database" in keys

    def test_list_keys_recursive(self):
        keys = list_keys(self.data, recursive=True)
        assert "server.host" in keys
        assert "server.port" in keys

    def test_exists(self):
        assert exists(self.data, "server.host") is True
        assert exists(self.data, "nonexistent") is False

    def test_get_type(self):
        assert get_type(self.data, "server.host") == "string"
        assert get_type(self.data, "server.port") == "integer"
        assert get_type(self.data, "server") == "table"


# ── Diff Tests ───────────────────────────────────────────────────────


class TestDiff:
    def test_identical(self):
        data = parse('key = "value"')
        result = diff(data, data)
        assert result.identical is True
        assert len(result.changes) == 0

    def test_added_key(self):
        old = parse("a = 1")
        new = parse("a = 1\nb = 2")
        result = diff(old, new)
        assert result.identical is False
        assert len(result.added) == 1
        assert result.added[0].path == "b"

    def test_removed_key(self):
        old = parse("a = 1\nb = 2")
        new = parse("a = 1")
        result = diff(old, new)
        assert len(result.removed) == 1
        assert result.removed[0].path == "b"

    def test_modified_key(self):
        old = parse("a = 1")
        new = parse("a = 2")
        result = diff(old, new)
        assert len(result.modified) == 1
        assert result.modified[0].old_value == 1
        assert result.modified[0].new_value == 2

    def test_nested_diff(self):
        old = parse('[server]\nhost = "localhost"')
        new = parse('[server]\nhost = "0.0.0.0"')
        result = diff(old, new)
        assert result.modified[0].path == "server.host"

    def test_format_text(self):
        old = parse("a = 1")
        new = parse("a = 2")
        result = diff(old, new)
        output = format_diff(result, "text")
        assert "~ a" in output

    def test_format_json(self):
        old = parse("a = 1")
        new = parse("a = 2")
        result = diff(old, new)
        output = format_diff(result, "json")
        assert '"added"' in output

    def test_format_markdown(self):
        old = parse("a = 1")
        new = parse("a = 2")
        result = diff(old, new)
        output = format_diff(result, "markdown")
        assert "# TOML Diff" in output


# ── Merge Tests ──────────────────────────────────────────────────────


class TestMerge:
    def test_simple_merge(self):
        base = parse("a = 1\nb = 1")
        override = parse("b = 2\nc = 3")
        result = merge(base, override)
        assert result["a"] == 1
        assert result["b"] == 2
        assert result["c"] == 3

    def test_deep_merge(self):
        base = parse('[server]\nhost = "localhost"\nport = 8080')
        override = parse("[server]\nport = 9090")
        result = merge(base, override)
        assert result["server"]["host"] == "localhost"
        assert result["server"]["port"] == 9090

    def test_merge_strategy_base(self):
        base = parse("a = 1")
        override = parse("a = 2")
        result = merge(base, override, strategy="base")
        assert result["a"] == 1

    def test_merge_strategy_union(self):
        base = parse("arr = [1, 2]")
        override = parse("arr = [3, 4]")
        result = merge(base, override, strategy="union")
        assert result["arr"] == [1, 2, 3, 4]

    def test_merge_conflict(self):
        base = parse("a = 1")
        override = parse("a = 2")
        with pytest.raises(MergeConflictError):
            merge(base, override, strategy="union")

    def test_flatten(self):
        data = parse("[a]\nb = 1")
        flat = flatten(data)
        assert flat["a.b"] == 1

    def test_unflatten(self):
        flat = {"a.b": 1, "a.c": 2}
        result = unflatten(flat)
        assert result["a"]["b"] == 1
        assert result["a"]["c"] == 2


# ── Formatter Tests ──────────────────────────────────────────────────


class TestFormatter:
    def test_format_simple(self):
        data = parse('key = "value"')
        result = format_toml(data)
        assert "key" in result
        assert "value" in result

    def test_format_sort_keys(self):
        data = parse("b = 2\na = 1")
        result = format_toml(data, sort_keys=True)
        lines = result.strip().split("\n")
        assert lines[0].startswith("a")
        assert lines[1].startswith("b")

    def test_compact(self):
        data = parse('[server]\nhost = "localhost"')
        result = compact(data)
        assert "\n\n" not in result  # No blank lines in compact

    def test_format_preserves_values(self):
        data = parse("port = 8080\ndebug = true")
        result = format_toml(data)
        assert "8080" in result
        assert "true" in result


# ── Validator Tests ──────────────────────────────────────────────────


class TestValidator:
    def test_valid_toml(self):
        data = parse('[server]\nhost = "localhost"')
        result = validate(data)
        assert result.valid is True
        assert len(result.errors) == 0

    def test_empty_table_warning(self):
        data = parse('[empty]\n\n[server]\nhost = "localhost"')
        result = validate(data, check_empty=True)
        assert len(result.warnings) == 0  # INFO, not WARNING

    def test_constant_key_info(self):
        data = parse("ALL_CAPS = 1")
        result = validate(data, check_naming=True)
        assert any(i.code == "CONSTANT_KEY" for i in result.infos)

    def test_format_text(self):
        data = parse("ALL_CAPS = 1")
        result = validate(data, check_naming=True)
        output = format_validation(result, "text")
        assert "Valid TOML" in output

    def test_format_json(self):
        data = parse("ALL_CAPS = 1")
        result = validate(data, check_naming=True)
        output = format_validation(result, "json")
        assert '"valid"' in output


# ── Converter Tests ──────────────────────────────────────────────────


class TestConverter:
    def test_to_json(self):
        data = parse('key = "value"\nnum = 42')
        json_str = to_json(data)
        assert '"key"' in json_str
        assert '"value"' in json_str

    def test_from_json(self):
        json_str = '{"key": "value", "num": 42}'
        data = from_json(json_str)
        assert data["key"] == "value"
        assert data["num"] == 42

    def test_json_roundtrip(self):
        data = parse('key = "value"\nnum = 42\ndebug = true')
        json_str = to_json(data)
        data2 = from_json(json_str)
        assert data2["key"] == "value"
        assert data2["num"] == 42
        assert data2["debug"] is True
