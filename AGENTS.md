# AGENTS.md

## Project Overview

TomlForge is a comprehensive TOML processing toolkit in Python with a hand-written TOML v1.0.0 parser, query engine, diff engine, merge engine, converter, formatter, validator, and CLI.

## Architecture

- `tomlforge/parser.py` — Hand-written tokenizer + recursive descent parser (no external TOML dependencies)
- `tomlforge/query.py` — Dot-notation path access
- `tomlforge/diff.py` — Structural comparison engine
- `tomlforge/merge.py` — Deep merge with 4 strategies
- `tomlforge/formatter.py` — Pretty-print and compact TOML
- `tomlforge/validator.py` — Issue detection and style checks
- `tomlforge/converter.py` — TOML ↔ JSON ↔ YAML conversion
- `tomlforge/cli.py` — Click-based CLI with 8 commands

## Development Commands

```bash
# Install dependencies
uv sync --dev

# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=tomlforge

# Lint
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/

# Run CLI
uv run tomlforge --help
```

## Key Algorithms

1. **TOML Parser**: Tokenizer + recursive descent parser. O(n) in input size.
2. **Diff Engine**: Recursive structural comparison with path tracking.
3. **Merge Engine**: Deep merge with 4 strategies (override, base, union, deep).
4. **Query Engine**: Dot-notation path splitting with array index support.

## Testing Conventions

- Table-driven tests for multiple scenarios
- Edge cases: empty input, nested structures, arrays, unicode, inline tables
- Integration tests via CLI commands
