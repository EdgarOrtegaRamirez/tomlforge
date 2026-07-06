"""Tests for TOML parser."""

from datetime import date, datetime, time, timezone

import pytest

from tomlforge.parser import Tokenizer, TomlError, parse


class TestBasicParsing:
    """Test basic TOML parsing."""

    def test_empty(self):
        assert parse("") == {}

    def test_simple_key_value(self):
        result = parse('key = "value"')
        assert result == {"key": "value"}

    def test_integer(self):
        result = parse("port = 8080")
        assert result["port"] == 8080

    def test_negative_integer(self):
        result = parse("neg = -42")
        assert result["neg"] == -42

    def test_float(self):
        result = parse("pi = 3.14159")
        assert result["pi"] == pytest.approx(3.14159)

    def test_negative_float(self):
        result = parse("neg = -3.14")
        assert result["neg"] == pytest.approx(-3.14)

    def test_float_with_exponent(self):
        result = parse("sci = 6.022e23")
        assert result["sci"] == pytest.approx(6.022e23)

    def test_boolean_true(self):
        result = parse("debug = true")
        assert result["debug"] is True

    def test_boolean_false(self):
        result = parse("debug = false")
        assert result["debug"] is False

    def test_string(self):
        result = parse('name = "Tom"')
        assert result["name"] == "Tom"

    def test_string_with_escapes(self):
        result = parse(r'text = "line1\nline2\ttab"')
        assert result["text"] == "line1\nline2\ttab"

    def test_literal_string(self):
        result = parse("path = 'C:\\Users\\Tom'")
        assert result["path"] == "C:\\Users\\Tom"

    def test_multiline_string(self):
        text = '''text = """
line1
line2
"""'''
        result = parse(text)
        assert "line1\nline2" in result["text"]

    def test_unicode_escape(self):
        result = parse(r'name = "\u0041\u0042"')
        assert result["name"] == "AB"


class TestHexOctalBinary:
    """Test numeric formats."""

    def test_hex(self):
        result = parse("hex = 0xDEADBEEF")
        assert result["hex"] == 0xDEADBEEF

    def test_octal(self):
        result = parse("oct = 0o755")
        assert result["oct"] == 0o755

    def test_binary(self):
        result = parse("bin = 0b11010")
        assert result["bin"] == 0b11010

    def test_underscore_separated(self):
        result = parse("big = 1_000_000")
        assert result["big"] == 1000000


class TestDateTime:
    """Test date and time parsing."""

    def test_datetime_utc(self):
        result = parse("dt = 2026-07-06T12:00:00Z")
        assert result["dt"] == datetime(2026, 7, 6, 12, 0, 0, tzinfo=timezone.utc)

    def test_date(self):
        result = parse("d = 2026-07-06")
        assert result["d"] == date(2026, 7, 6)

    def test_time(self):
        result = parse("t = 12:30:45")
        assert result["t"] == time(12, 30, 45)


class TestArrays:
    """Test array parsing."""

    def test_simple_array(self):
        result = parse("arr = [1, 2, 3]")
        assert result["arr"] == [1, 2, 3]

    def test_string_array(self):
        result = parse('arr = ["a", "b", "c"]')
        assert result["arr"] == ["a", "b", "c"]

    def test_mixed_array(self):
        result = parse('arr = [1, "two", 3.0, true]')
        assert result["arr"] == [1, "two", 3.0, True]

    def test_nested_array(self):
        result = parse("matrix = [[1, 2], [3, 4]]")
        assert result["matrix"] == [[1, 2], [3, 4]]

    def test_empty_array(self):
        result = parse("arr = []")
        assert result["arr"] == []

    def test_multiline_array(self):
        text = """arr = [
    1,
    2,
    3,
]"""
        result = parse(text)
        assert result["arr"] == [1, 2, 3]

    def test_array_with_trailing_comma(self):
        result = parse("arr = [1, 2, 3,]")
        assert result["arr"] == [1, 2, 3]


class TestTables:
    """Test table parsing."""

    def test_simple_table(self):
        text = """[server]
host = "localhost"
port = 8080"""
        result = parse(text)
        assert result["server"]["host"] == "localhost"
        assert result["server"]["port"] == 8080

    def test_nested_table(self):
        text = """[a.b]
c = 1"""
        result = parse(text)
        assert result["a"]["b"]["c"] == 1

    def test_inline_table(self):
        result = parse("point = { x = 1, y = 2 }")
        assert result["point"] == {"x": 1, "y": 2}

    def test_empty_inline_table(self):
        result = parse("empty = {}")
        assert result["empty"] == {}


class TestArrayOfTables:
    """Test array of tables ([[...]])."""

    def test_simple_array_of_tables(self):
        text = """[[products]]
name = "Hammer"
sku = 738594937

[[products]]
name = "Nail"
sku = 284758393"""
        result = parse(text)
        assert len(result["products"]) == 2
        assert result["products"][0]["name"] == "Hammer"
        assert result["products"][1]["name"] == "Nail"

    def test_array_of_tables_with_subtables(self):
        text = """[[fruit]]
  name = "apple"

  [fruit.physical]
    color = "red"
    shape = "round"

[[fruit]]
  name = "banana"

  [fruit.physical]
    color = "yellow"
    shape = "long" """
        result = parse(text)
        assert len(result["fruit"]) == 2
        assert result["fruit"][0]["physical"]["color"] == "red"
        assert result["fruit"][1]["physical"]["color"] == "yellow"


class TestComments:
    """Test comment handling."""

    def test_comment(self):
        text = """# This is a comment
key = "value"  # inline comment"""
        result = parse(text)
        assert result["key"] == "value"

    def test_comments_only(self):
        result = parse("# just a comment\n# another comment")
        assert result == {}


class TestDottedKeys:
    """Test dotted key syntax."""

    def test_dotted_key(self):
        text = """fruit.name = "banana"
fruit.color = "yellow\""""
        result = parse(text)
        assert result["fruit"]["name"] == "banana"
        assert result["fruit"]["color"] == "yellow"

    def test_dotted_key_with_table(self):
        text = """[fruit]
name = "apple"

[fruit.physical]
color = "red\""""
        result = parse(text)
        assert result["fruit"]["name"] == "apple"
        assert result["fruit"]["physical"]["color"] == "red"


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_invalid_toml(self):
        with pytest.raises(TomlError):
            parse("key = ")

    def test_duplicate_key(self):
        # This is technically invalid TOML but our parser is lenient
        result = parse('key = "first"\nkey = "second"')
        assert result["key"] == "second"

    def test_whitespace_handling(self):
        text = """
        key   =    "value"
        """
        result = parse(text)
        assert result["key"] == "value"

    def test_quoted_key(self):
        result = parse('"quoted key" = "value"')
        assert result["quoted key"] == "value"

    def test_special_characters_in_string(self):
        # Test escaped backslashes in basic string (\\\\ in TOML -> \\ in value)
        result = parse(r'path = "hello\\\\world"')
        assert result["path"] == "hello\\\\world"
        # Test newline and tab escapes
        result = parse(r'text = "line1\nline2\ttab"')
        assert result["text"] == "line1\nline2\ttab"


class TestTokenizer:
    """Test tokenizer directly."""

    def test_tokenize_key_value(self):
        tok = Tokenizer('key = "value"')
        tokens = tok.tokenize()
        types = [t.type for t in tokens if t.type != "EOF"]
        assert types == ["KEY", "EQUALS", "STRING"]

    def test_tokenize_number(self):
        tok = Tokenizer("x = 42")
        tokens = tok.tokenize()
        assert tokens[2].value == 42

    def test_tokenize_boolean(self):
        tok = Tokenizer("x = true")
        tokens = tok.tokenize()
        assert tokens[2].value is True
