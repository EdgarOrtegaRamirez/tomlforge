# TomlForge

TOML Processing Toolkit — parse, query, diff, merge, convert, validate, and format TOML files.

## Features

- **Hand-written TOML v1.0.0 parser** — no external parser dependencies
- **Query engine** — dot-notation path access (e.g., `server.host`)
- **Diff engine** — structural comparison of two TOML documents
- **Merge engine** — deep merge with multiple strategies (override, base, union)
- **Converter** — TOML ↔ JSON ↔ YAML
- **Formatter** — pretty-print and compact TOML
- **Validator** — check for issues and style violations
- **CLI** — full-featured command-line interface

## Installation

```bash
pip install tomlforge
```

Or with YAML support:

```bash
pip install tomlforge[yaml]
```

## Quick Start

### Parse TOML

```python
from tomlforge import parse

toml_text = """
[server]
host = "localhost"
port = 8080

[database]
driver = "postgres"
url = "postgres://localhost/mydb"
"""

data = parse(toml_text)
print(data["server"]["host"])  # "localhost"
```

### Query Values

```python
from tomlforge import parse, query

data = parse(toml_text)
port = query(data, "server.port")  # 8080
```

### Diff TOML Files

```python
from tomlforge import parse, diff

old = parse(old_toml)
new = parse(new_toml)
result = diff(old, new)

print(result.summary)  # {'added': 1, 'removed': 0, 'modified': 2, 'total': 3}
```

### Merge TOML Files

```python
from tomlforge import parse, merge

base = parse(base_toml)
override = parse(override_toml)
merged = merge(base, override, strategy="override")
```

### Format TOML

```python
from tomlforge import parse, format_toml

data = parse(toml_text)
print(format_toml(data, sort_keys=True))
```

### Validate TOML

```python
from tomlforge import parse, validate

data = parse(toml_text)
result = validate(data)
print(result.valid)  # True
print(result.summary)  # {'errors': 0, 'warnings': 1, 'infos': 0, 'total': 1}
```

### Convert to JSON

```python
from tomlforge import parse, to_json

data = parse(toml_text)
print(to_json(data))
```

## CLI Usage

```bash
# Parse and display
tomlforge parse config.toml

# Query a value
tomlforge get config.toml server.port

# List keys
tomlforge keys config.toml --recursive

# Diff two files
tomlforge diff old.toml new.toml

# Merge files
tomlforge merge base.toml override.toml

# Format/prettify
tomlforge format config.toml --sort-keys

# Validate
tomlforge validate config.toml

# Convert to JSON
tomlforge convert config.toml -f json
```

## Supported TOML Features

- Strings (basic, multi-line, literal, literal multi-line)
- Integers (decimal, hex, octal, binary)
- Floats (with exponents)
- Booleans
- Datetimes (local, offset, UTC)
- Dates
- Times
- Arrays (inline and multiline)
- Tables (standard and inline)
- Array of tables
- Comments
- Dotted keys
- Key/value pairs
- Unicode escapes (`\uXXXX`, `\UXXXXXXXX`)

## Architecture

```
tomlforge/
├── __init__.py       # Public API
├── parser.py         # Hand-written tokenizer + recursive descent parser
├── query.py          # Dot-notation path access
├── diff.py           # Structural comparison engine
├── merge.py          # Deep merge with strategies
├── formatter.py      # Pretty-print and compact formatting
├── validator.py      # Issue detection and style checks
├── converter.py      # TOML ↔ JSON ↔ YAML conversion
└── cli.py            # Click-based CLI
```

## Algorithm Details

### Parser

The parser uses a hand-written **tokenizer** that converts TOML text into tokens, followed by a **recursive descent parser** that builds a Python dictionary. This approach:
- Provides clear error messages with line/column numbers
- Handles all TOML v1.0.0 features
- Has no external parser dependencies
- Is O(n) in the size of the input

### Diff Engine

The diff engine recursively compares two TOML documents using a **structural comparison algorithm**:
1. Compare table keys (added, removed, modified)
2. For matching keys, compare values recursively
3. For arrays, compare element-by-element
4. Record all changes with their paths

### Merge Engine

The merge engine supports four strategies:
- **override** (default): Later values win
- **base**: Original values win
- **union**: Combine arrays, fail on scalar conflicts
- **deep**: Recursive merge (same as override for dicts)

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=tomlforge

# Run specific test file
pytest tests/test_parser.py
```

## License

MIT
