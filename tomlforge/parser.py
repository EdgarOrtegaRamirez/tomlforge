"""Hand-written TOML v1.0.0 parser with tokenizer and recursive descent."""

from __future__ import annotations

from datetime import date, datetime, time, timezone
from typing import Any


class TomlError(Exception):
    """Raised when TOML parsing fails."""

    def __init__(self, message: str, line: int = 0, col: int = 0):
        self.line = line
        self.col = col
        super().__init__(f"Line {line}, Col {col}: {message}")


# ── Token types ──────────────────────────────────────────────────────


class TT:
    """Token types."""

    # Literals
    STRING = "STRING"
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"
    BOOLEAN = "BOOLEAN"
    DATETIME = "DATETIME"
    DATE = "DATE"
    TIME = "TIME"
    # Punctuation
    DOT = "DOT"
    EQUALS = "EQUALS"
    COMMA = "COMMA"
    COLON = "COLON"
    LBRACKET = "LBRACKET"  # [
    RBRACKET = "RBRACKET"  # ]
    LLBRACKET = "LLBRACKET"  # [[
    RRBRACKET = "RRBRACKET"  # ]]
    LBRACE = "LBRACE"  # {
    RBRACE = "RBRACE"  # }
    # Special
    NEWLINE = "NEWLINE"
    EOF = "EOF"
    KEY = "KEY"


# ── Token ─────────────────────────────────────────────────────────────


class Token:
    __slots__ = ("type", "value", "line", "col")

    def __init__(self, token_type: str, value: Any, line: int = 0, col: int = 0):
        self.type = token_type
        self.value = value
        self.line = line
        self.col = col

    def __repr__(self) -> str:
        return f"Token({self.type}, {self.value!r}, L{self.line}:{self.col})"


# ── Tokenizer ─────────────────────────────────────────────────────────

_ESCAPE_MAP = {
    "n": "\n",
    "t": "\t",
    "r": "\r",
    "\\": "\\",
    '"': '"',
    "b": "\b",
    "f": "\f",
    "u": None,  # handled separately
    "U": None,  # handled separately
}


def _unescape_basic(s: str) -> str:
    """Unescape a basic TOML string."""
    result = []
    i = 0
    while i < len(s):
        if s[i] == "\\" and i + 1 < len(s):
            next_ch = s[i + 1]
            if next_ch == "u" or next_ch == "U":
                # Unicode escape
                if next_ch == "u":
                    hex_str = s[i + 2 : i + 6]
                    if len(hex_str) < 4:
                        raise TomlError(f"Invalid \\u escape: \\u{hex_str}")
                    code = int(hex_str, 16)
                    result.append(chr(code))
                    i += 6
                else:
                    hex_str = s[i + 2 : i + 10]
                    if len(hex_str) < 8:
                        raise TomlError(f"Invalid \\U escape: \\U{hex_str}")
                    code = int(hex_str, 16)
                    result.append(chr(code))
                    i += 10
            elif next_ch in _ESCAPE_MAP:
                result.append(_ESCAPE_MAP[next_ch])
                i += 2
            else:
                raise TomlError(f"Invalid escape: \\{next_ch}")
        else:
            result.append(s[i])
            i += 1
    return "".join(result)


class Tokenizer:
    """Tokenizes TOML input into a list of tokens."""

    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens: list[Token] = []

    def _peek(self, offset: int = 0) -> str:
        p = self.pos + offset
        return self.text[p] if p < len(self.text) else ""

    def _advance(self) -> str:
        ch = self.text[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def _skip_whitespace(self) -> None:
        while self.pos < len(self.text) and self.text[self.pos] in " \t":
            self._advance()

    def _skip_comment(self) -> None:
        while self.pos < len(self.text) and self.text[self.pos] != "\n":
            self._advance()

    def _read_string(self, multiline: bool = False) -> str:
        """Read a basic or literal string."""
        is_literal = self._peek() == "'"
        quote_char = "'" if is_literal else '"'
        self._advance()  # skip opening quote

        if multiline and self._peek() == quote_char and self._peek(1) == quote_char:
            self._advance()  # second quote
            self._advance()  # third quote
            if self._peek() == "\n":
                self._advance()  # skip newline after opening
            result = []
            while self.pos < len(self.text):
                if self._peek() == quote_char:
                    if self._peek(1) == quote_char and self._peek(2) == quote_char:
                        self._advance()
                        self._advance()
                        self._advance()
                        return "".join(result)
                    else:
                        result.append(self._advance())
                elif self._peek() == "\\" and not is_literal:
                    self._advance()
                    esc = self._advance()
                    if esc == "\n":
                        continue  # line continuation
                    if esc in _ESCAPE_MAP:
                        if esc in ("u", "U"):
                            if esc == "u":
                                hex_str = ""
                                for _ in range(4):
                                    hex_str += self._advance()
                                result.append(chr(int(hex_str, 16)))
                            else:
                                hex_str = ""
                                for _ in range(8):
                                    hex_str += self._advance()
                                result.append(chr(int(hex_str, 16)))
                        else:
                            result.append(_ESCAPE_MAP[esc])
                    else:
                        raise TomlError(f"Invalid escape: \\{esc}")
                else:
                    result.append(self._advance())
            raise TomlError("Unterminated multiline string")
        else:
            result = []
            while self.pos < len(self.text):
                ch = self._peek()
                if ch == quote_char:
                    self._advance()
                    return "".join(result)
                elif ch == "\\" and not is_literal:
                    self._advance()
                    esc = self._advance()
                    if esc in _ESCAPE_MAP:
                        if esc in ("u", "U"):
                            if esc == "u":
                                hex_str = ""
                                for _ in range(4):
                                    hex_str += self._advance()
                                result.append(chr(int(hex_str, 16)))
                            else:
                                hex_str = ""
                                for _ in range(8):
                                    hex_str += self._advance()
                                result.append(chr(int(hex_str, 16)))
                        else:
                            result.append(_ESCAPE_MAP[esc])
                    else:
                        raise TomlError(f"Invalid escape: \\{esc}")
                elif ch == "\n" and not multiline or ch == "":
                    raise TomlError("Unterminated string")
                else:
                    result.append(self._advance())
            raise TomlError("Unterminated string")

    def _read_integer(self) -> int:
        if self._peek() == "-":
            self._advance()
        if self._peek() == "0" and self._peek(1) in ("x", "X"):
            self._advance()
            self._advance()
            hex_str = ""
            while self.pos < len(self.text) and (self._peek() in "0123456789abcdefABCDEF_"):
                if self._peek() != "_":
                    hex_str += self._advance()
                else:
                    self._advance()
            return int(hex_str, 16)
        if self._peek() == "0" and self._peek(1) in ("o", "O"):
            self._advance()
            self._advance()
            oct_str = ""
            while self.pos < len(self.text) and (self._peek() in "01234567_"):
                if self._peek() != "_":
                    oct_str += self._advance()
                else:
                    self._advance()
            return int(oct_str, 8)
        if self._peek() == "0" and self._peek(1) in ("b", "B"):
            self._advance()
            self._advance()
            bin_str = ""
            while self.pos < len(self.text) and (self._peek() in "01_"):
                if self._peek() != "_":
                    bin_str += self._advance()
                else:
                    self._advance()
            return int(bin_str, 2)
        num_str = ""
        while self.pos < len(self.text) and (self._peek() in "0123456789_"):
            if self._peek() != "_":
                num_str += self._advance()
            else:
                self._advance()
        if not num_str:
            raise TomlError("Expected integer", self.line, self.col)
        return int(num_str)

    def _read_number(self) -> int | float:
        """Read an integer or float."""

        neg = False
        if self._peek() == "-":
            self._advance()
            neg = True

        # Check for hex, octal, binary
        if self._peek() == "0" and self._peek(1) in ("x", "X", "o", "O", "b", "B"):
            val = self._read_integer()
            return -val if neg else val

        # Read digits
        int_part = ""
        while self.pos < len(self.text) and self._peek() in "0123456789_":
            if self._peek() != "_":
                int_part += self._advance()
            else:
                self._advance()

        # Check for float
        is_float = False
        if self._peek() == ".":
            is_float = True
            self._advance()
            frac = ""
            while self.pos < len(self.text) and self._peek() in "0123456789_":
                if self._peek() != "_":
                    frac += self._advance()
                else:
                    self._advance()
            int_part = int_part + "." + frac

        if self._peek() in ("e", "E"):
            is_float = True
            int_part += self._advance()  # e/E
            if self._peek() in ("+", "-"):
                int_part += self._advance()
            while self.pos < len(self.text) and self._peek() in "0123456789_":
                if self._peek() != "_":
                    int_part += self._advance()
                else:
                    self._advance()

        if is_float:
            val = float(int_part)
            return -val if neg else val
        else:
            val = int(int_part)
            return -val if neg else val

    def _read_datetime(self) -> datetime | date | time:
        """Read a datetime, date, or time literal."""
        # Try to read date-time: YYYY-MM-DDTHH:MM:SS
        date_str = ""
        for _ in range(4):
            date_str += self._advance()
        if self._peek() == "-":
            date_str += self._advance()
            for _ in range(2):
                date_str += self._advance()
            if self._peek() == "-":
                date_str += self._advance()
                for _ in range(2):
                    date_str += self._advance()
                if self._peek() in ("T", " "):
                    self._advance()
                    time_str = ""
                    for _ in range(2):
                        time_str += self._advance()
                    if self._peek() == ":":
                        time_str += self._advance()
                        for _ in range(2):
                            time_str += self._advance()
                        if self._peek() == ":":
                            time_str += self._advance()
                            for _ in range(2):
                                time_str += self._advance()
                            # Check for fractional seconds
                            if self._peek() == ".":
                                time_str += self._advance()
                                while self.pos < len(self.text) and self._peek().isdigit():
                                    time_str += self._advance()
                            # Check for timezone
                            if self._peek() == "Z":
                                time_str += self._advance()
                                dt = datetime.fromisoformat(f"{date_str}T{time_str}")
                                return dt.replace(tzinfo=timezone.utc)
                            elif self._peek() in ("+", "-"):
                                tz_sign = self._advance()
                                tz_hours = ""
                                for _ in range(2):
                                    tz_hours += self._advance()
                                if self._peek() == ":":
                                    self._advance()
                                    tz_mins = ""
                                    for _ in range(2):
                                        tz_mins += self._advance()
                                    tz_str = f"{tz_sign}{tz_hours}:{tz_mins}"
                                else:
                                    tz_str = f"{tz_sign}{tz_hours}"
                                dt = datetime.fromisoformat(f"{date_str}T{time_str}{tz_str}")
                                return dt
                            else:
                                # Local date-time (no timezone)
                                dt = datetime.fromisoformat(f"{date_str}T{time_str}")
                                return dt
                else:
                    # Just a date: YYYY-MM-DD
                    d = date.fromisoformat(date_str)
                    return d
            else:
                raise TomlError("Invalid date format")
        else:
            raise TomlError("Invalid date format")

    def _read_time(self) -> time:
        """Read a time literal: HH:MM:SS[.fractional]"""
        time_str = ""
        for _ in range(2):
            time_str += self._advance()
        if self._peek() == ":":
            time_str += self._advance()
            for _ in range(2):
                time_str += self._advance()
            if self._peek() == ":":
                time_str += self._advance()
                for _ in range(2):
                    time_str += self._advance()
                if self._peek() == ".":
                    time_str += self._advance()
                    while self.pos < len(self.text) and self._peek().isdigit():
                        time_str += self._advance()
                return time.fromisoformat(time_str)
        raise TomlError("Invalid time format")

    def _read_key(self) -> str:
        """Read a key (bare or quoted)."""
        self._skip_whitespace()
        if self._peek() == '"' or self._peek() == "'":
            return self._read_string(multiline=False)
        else:
            # Bare key — stop at dots too so tokenizer can emit DOT tokens
            key = ""
            while self.pos < len(self.text) and self._peek() not in (
                "=",
                "\n",
                "\r",
                " ",
                "\t",
                "#",
                "[",
                "]",
                "{",
                "}",
                ",",
                ":",
                ".",
            ):
                key += self._advance()
            if not key:
                raise TomlError("Expected key", self.line, self.col)
            return key

    def tokenize(self) -> list[Token]:
        """Tokenize the entire input."""
        while self.pos < len(self.text):
            self._skip_whitespace()
            if self.pos >= len(self.text):
                break

            ch = self._peek()

            # Skip comments
            if ch == "#":
                self._skip_comment()
                continue

            # Newlines
            if ch == "\n":
                self._advance()
                continue
            if ch == "\r":
                self._advance()
                if self._peek() == "\n":
                    self._advance()
                continue

            # Skip whitespace
            if ch in " \t":
                self._skip_whitespace()
                continue

            # [ table ] or [[ array of tables ]] - always emit single LBRACKET
            if ch == "[":
                line, col = self.line, self.col
                self._advance()
                self.tokens.append(Token(TT.LBRACKET, "[", line, col))
                continue

            # ] - always emit single RBRACKET
            if ch == "]":
                line, col = self.line, self.col
                self._advance()
                self.tokens.append(Token(TT.RBRACKET, "]", line, col))
                continue

            # { inline table }
            if ch == "{":
                line, col = self.line, self.col
                self._advance()
                self.tokens.append(Token(TT.LBRACE, "{", line, col))
                continue

            if ch == "}":
                line, col = self.line, self.col
                self._advance()
                self.tokens.append(Token(TT.RBRACE, "}", line, col))
                continue

            # = equals
            if ch == "=":
                line, col = self.line, self.col
                self._advance()
                self.tokens.append(Token(TT.EQUALS, "=", line, col))
                continue

            # , comma
            if ch == ",":
                line, col = self.line, self.col
                self._advance()
                self.tokens.append(Token(TT.COMMA, ",", line, col))
                continue

            # : colon (in inline tables / arrays)
            if ch == ":" and self._peek(1) not in (" ", "\t", "\n"):
                line, col = self.line, self.col
                self._advance()
                self.tokens.append(Token(TT.COLON, ":", line, col))
                continue

            # Strings
            if ch in ('"', "'"):
                line, col = self.line, self.col
                # Check for multiline
                if (
                    ch == '"'
                    and self._peek(1) == '"'
                    and self._peek(2) == '"'
                    or ch == "'"
                    and self._peek(1) == "'"
                    and self._peek(2) == "'"
                ):
                    val = self._read_string(multiline=True)
                    self.tokens.append(Token(TT.STRING, val, line, col))
                else:
                    val = self._read_string(multiline=False)
                    self.tokens.append(Token(TT.STRING, val, line, col))
                continue

            # Numbers (including negative)
            if ch.isdigit() or (ch == "-" and self._peek(1).isdigit()):
                line, col = self.line, self.col
                # Check if it's a datetime/date/time
                if ch.isdigit():
                    # Could be date: YYYY-MM-DD
                    peek_digits = ""
                    for i in range(4):
                        if self.pos + i < len(self.text) and self.text[self.pos + i].isdigit():
                            peek_digits += self.text[self.pos + i]
                        else:
                            break
                    if len(peek_digits) == 4 and self._peek(4) == "-" and self._peek(7) == "-":
                        val = self._read_datetime()
                        if isinstance(val, datetime):
                            self.tokens.append(Token(TT.DATETIME, val, line, col))
                        elif isinstance(val, date):
                            self.tokens.append(Token(TT.DATE, val, line, col))
                        else:
                            self.tokens.append(Token(TT.TIME, val, line, col))
                        continue
                    # Could be time: HH:MM:SS
                    if len(peek_digits) == 2 and self._peek(2) == ":":
                        val = self._read_time()
                        self.tokens.append(Token(TT.TIME, val, line, col))
                        continue
                val = self._read_number()
                if isinstance(val, float):
                    self.tokens.append(Token(TT.FLOAT, val, line, col))
                else:
                    self.tokens.append(Token(TT.INTEGER, val, line, col))
                continue

            # Booleans
            if self.text[self.pos : self.pos + 4] == "true":
                line, col = self.line, self.col
                for _ in range(4):
                    self._advance()
                self.tokens.append(Token(TT.BOOLEAN, True, line, col))
                continue
            if self.text[self.pos : self.pos + 5] == "false":
                line, col = self.line, self.col
                for _ in range(5):
                    self._advance()
                self.tokens.append(Token(TT.BOOLEAN, False, line, col))
                continue

            # Dot (in dotted keys like fruit.name)
            if ch == ".":
                line, col = self.line, self.col
                self._advance()
                self.tokens.append(Token(TT.DOT, ".", line, col))
                continue

            # Keys (before =)
            if ch not in ("=", "\n", "\r", "#", "[", "]", "{", "}", ",", ":", "."):
                line, col = self.line, self.col
                key = self._read_key()
                self.tokens.append(Token(TT.KEY, key, line, col))
                continue

            raise TomlError(f"Unexpected character: {ch!r}", self.line, self.col)

        self.tokens.append(Token(TT.EOF, None, self.line, self.col))
        return self.tokens


# ── Parser ────────────────────────────────────────────────────────────


class TomlParser:
    """Recursive descent parser for TOML v1.0.0."""

    def __init__(self):
        self.tokens: list[Token] = []
        self.pos = 0

    def _peek(self, offset: int = 0) -> Token:
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return Token(TT.EOF, None)

    def _advance(self) -> Token:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def _expect(self, tt: str) -> Token:
        tok = self._peek()
        if tok.type != tt:
            raise TomlError(f"Expected {tt}, got {tok.type} ({tok.value!r})", tok.line, tok.col)
        return self._advance()

    def _skip_newlines(self) -> None:
        while self._peek().type == TT.NEWLINE:
            self._advance()

    def parse(self, text: str) -> dict[str, Any]:
        """Parse TOML text into a Python dict."""
        tokenizer = Tokenizer(text)
        self.tokens = tokenizer.tokenize()
        self.pos = 0
        result: dict[str, Any] = {}
        current_path: list[str] = []
        current_table = result

        while self._peek().type != TT.EOF:
            self._skip_newlines()
            if self._peek().type == TT.EOF:
                break

            tok = self._peek()

            # [table] or [[array of tables]] header
            if tok.type == TT.LBRACKET:
                self._advance()
                # Check for [[array of tables]]
                if self._peek().type == TT.LBRACKET:
                    self._advance()  # second [
                    key_path = self._parse_key_path()
                    # Expect ]]
                    self._expect(TT.RBRACKET)
                    self._expect(TT.RBRACKET)
                    self._skip_newlines_and_comments()

                    current_path = key_path
                    # Initialize array if needed
                    obj = result
                    for _i, k in enumerate(key_path):
                        if _i == len(key_path) - 1:
                            if k not in obj:
                                obj[k] = []
                            elif not isinstance(obj[k], list):
                                raise TomlError(f"Key '{k}' is not an array")
                        else:
                            if k not in obj:
                                obj[k] = {}
                            obj = obj[k]

                    # Append new entry
                    new_entry: dict[str, Any] = {}
                    arr = result
                    for k in key_path[:-1]:
                        arr = arr[k]
                    arr[key_path[-1]].append(new_entry)
                    current_table = new_entry
                    continue
                else:
                    # Regular [table] header
                    key_path = self._parse_key_path()
                    self._expect(TT.RBRACKET)
                    self._skip_newlines_and_comments()
                    current_path = key_path

                    # Check if this table header is a subtable of current AOT
                    # e.g. [fruit.physical] inside [[fruit]]
                    obj = result
                    if (
                        current_path
                        and current_path[0] == current_path[0]
                        and len(current_path) > 1
                    ):
                        # Check if first key is an AOT (list)
                        test_obj = obj
                        if current_path[0] in test_obj and isinstance(
                            test_obj[current_path[0]], list
                        ):
                            # This is a subtable of the current AOT
                            test_obj = test_obj[current_path[0]][-1]  # last entry

                    # Navigate: if the first key points to an array (AOT),
                    # navigate into its last element instead
                    obj = result
                    for _i, k in enumerate(key_path):
                        if k in obj and isinstance(obj[k], list):
                            # AOT — navigate into last entry
                            if obj[k]:
                                obj = obj[k][-1]
                            else:
                                # Empty array, create first entry
                                new_entry = {}
                                obj[k].append(new_entry)
                                obj = new_entry
                        else:
                            if k not in obj:
                                obj[k] = {}
                            obj = obj[k]
                    current_table = obj
                    continue

            # key = value (handle quoted keys)
            if tok.type == TT.KEY:
                self._parse_key_value(current_table)
                self._skip_newlines_and_comments()
                continue

            # Quoted key = value (STRING followed by EQUALS)
            if tok.type == TT.STRING and self._peek(1).type == TT.EQUALS:
                # Treat string as a key
                self._parse_key_value(current_table)
                self._skip_newlines_and_comments()
                continue

            raise TomlError(f"Unexpected token: {tok.type} ({tok.value!r})", tok.line, tok.col)

        return result

    def _parse_key_path(self) -> list[str]:
        """Parse a dotted key path like a.b.c."""
        keys = []
        key_tok = self._advance()
        if key_tok.type == TT.KEY or key_tok.type == TT.STRING:
            keys.append(key_tok.value)
        else:
            raise TomlError(f"Expected key, got {key_tok.type}", key_tok.line, key_tok.col)

        while self._peek().type == TT.DOT:
            self._advance()  # skip dot
            next_key = self._advance()
            if next_key.type == TT.KEY or next_key.type == TT.STRING:
                keys.append(next_key.value)
            else:
                raise TomlError(
                    f"Expected key after dot, got {next_key.type}", next_key.line, next_key.col
                )
        return keys

    def _parse_key_value(self, table: dict[str, Any]) -> None:
        """Parse a key = value pair."""
        key_path = self._parse_key_path()
        self._expect(TT.EQUALS)
        value = self._parse_value()
        self._skip_newlines_and_comments()

        # Set value in table
        obj = table
        for k in key_path[:-1]:
            if k not in obj:
                obj[k] = {}
            elif not isinstance(obj[k], dict):
                raise TomlError(f"Key '{k}' is not a table")
            obj = obj[k]
        obj[key_path[-1]] = value

    def _parse_value(self) -> Any:
        """Parse a TOML value."""
        self._skip_whitespace_tokens()
        tok = self._peek()

        if tok.type == TT.STRING:
            self._advance()
            return tok.value
        if tok.type == TT.INTEGER:
            self._advance()
            return tok.value
        if tok.type == TT.FLOAT:
            self._advance()
            return tok.value
        if tok.type == TT.BOOLEAN:
            self._advance()
            return tok.value
        if tok.type == TT.DATETIME:
            self._advance()
            return tok.value
        if tok.type == TT.DATE:
            self._advance()
            return tok.value
        if tok.type == TT.TIME:
            self._advance()
            return tok.value
        if tok.type == TT.LBRACKET:
            return self._parse_array()
        if tok.type == TT.LBRACE:
            return self._parse_inline_table()

        raise TomlError(
            f"Unexpected token for value: {tok.type} ({tok.value!r})", tok.line, tok.col
        )

    def _parse_array(self) -> list[Any]:
        """Parse an array [...]."""
        self._expect(TT.LBRACKET)
        self._skip_newlines_and_comments()
        items: list[Any] = []

        while self._peek().type not in (TT.RBRACKET, TT.EOF):
            items.append(self._parse_value())
            self._skip_newlines_and_comments()
            if self._peek().type == TT.COMMA:
                self._advance()
                self._skip_newlines_and_comments()

        self._expect(TT.RBRACKET)
        return items

    def _parse_inline_table(self) -> dict[str, Any]:
        """Parse an inline table {...}."""
        self._expect(TT.LBRACE)
        self._skip_whitespace_tokens()
        table: dict[str, Any] = {}

        while self._peek().type not in (TT.RBRACE, TT.EOF):
            key_path = self._parse_key_path()
            self._expect(TT.EQUALS)
            value = self._parse_value()
            self._skip_whitespace_tokens()

            # Set value
            obj = table
            for k in key_path[:-1]:
                if k not in obj:
                    obj[k] = {}
                obj = obj[k]
            obj[key_path[-1]] = value

            if self._peek().type == TT.COMMA:
                self._advance()
                self._skip_whitespace_tokens()

        self._expect(TT.RBRACE)
        return table

    def _skip_whitespace_tokens(self) -> None:
        """Skip NEWLINE and EOF tokens (whitespace handling)."""
        while self._peek().type == TT.NEWLINE:
            self._advance()

    def _skip_newlines_and_comments(self) -> None:
        """Skip newlines after a statement."""
        while self._peek().type == TT.NEWLINE:
            self._advance()


# ── Public API ────────────────────────────────────────────────────────


def parse(text: str) -> dict[str, Any]:
    """Parse TOML text into a Python dict.

    Args:
        text: TOML string to parse.

    Returns:
        Parsed TOML as a nested dictionary.

    Raises:
        TomlError: If the TOML is invalid.
    """
    parser = TomlParser()
    return parser.parse(text)


def parse_file(path: str) -> dict[str, Any]:
    """Parse a TOML file.

    Args:
        path: Path to TOML file.

    Returns:
        Parsed TOML as a nested dictionary.

    Raises:
        TomlError: If the TOML is invalid.
        FileNotFoundError: If the file doesn't exist.
    """
    with open(path, encoding="utf-8") as f:
        return parse(f.read())
