"""TomlForge CLI — command-line interface for TOML processing."""

from __future__ import annotations

import json as _json
import sys
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.table import Table

from tomlforge.converter import to_json
from tomlforge.diff import diff, format_diff
from tomlforge.formatter import compact, format_toml
from tomlforge.merge import MergeConflictError, merge
from tomlforge.parser import TomlError, parse
from tomlforge.query import delete as toml_delete
from tomlforge.query import get_type, list_keys, set_value
from tomlforge.query import query as toml_query
from tomlforge.validator import format_validation, validate

console = Console()


@click.group()
@click.version_option(package_name="tomlforge")
def main() -> None:
    """TomlForge — TOML Processing Toolkit.

    Parse, query, diff, merge, convert, validate, and format TOML files.
    """


@main.command()
@click.argument("file", type=click.Path(exists=True))
@click.option(
    "-f",
    "--format",
    "fmt",
    type=click.Choice(["toml", "json"]),
    default="toml",
    help="Output format",
)
@click.option("--compact", "compact_flag", is_flag=True, help="Output compact TOML")
@click.option("-o", "--output", type=click.Path(), help="Output file (default: stdout)")
def parse_cmd(file: str, fmt: str, compact_flag: bool, output: str | None) -> None:
    """Parse and display a TOML file."""
    try:
        text = Path(file).read_text(encoding="utf-8")
        data = parse(text)

        if fmt == "json":
            result = to_json(data)
        elif compact_flag:
            result = compact(data)
        else:
            result = format_toml(data)

        if output:
            Path(output).write_text(result, encoding="utf-8")
            console.print(f"[green]Written to {output}[/green]")
        else:
            console.print(result)
    except TomlError as e:
        console.print(f"[red]Error:[/red] {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}", file=sys.stderr)
        sys.exit(1)


@main.command()
@click.argument("file", type=click.Path(exists=True))
@click.argument("path")
def get(file: str, path: str) -> None:
    """Get a value from a TOML file.

    Example: tomlforge get config.toml server.port
    """
    try:
        text = Path(file).read_text(encoding="utf-8")
        data = parse(text)
        value = toml_query(data, path)
        if isinstance(value, (dict, list)):
            console.print_json(to_json(value))
        else:
            console.print(value)
    except TomlError as e:
        console.print(f"[red]Parse Error:[/red] {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}", file=sys.stderr)
        sys.exit(1)


@main.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("-r", "--recursive", is_flag=True, help="List all keys recursively")
@click.option("--path", default="", help="Base path to list from")
def keys(file: str, recursive: bool, path: str) -> None:
    """List keys in a TOML file."""
    try:
        text = Path(file).read_text(encoding="utf-8")
        data = parse(text)
        key_list = list_keys(data, path, recursive)

        table = Table(title="Keys")
        table.add_column("Key", style="cyan")
        if recursive:
            table.add_column("Type", style="green")

        for key in key_list:
            if recursive:
                try:
                    val_type = get_type(data, key)
                    table.add_row(key, val_type)
                except Exception:
                    table.add_row(key, "unknown")
            else:
                table.add_row(key)

        console.print(table)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}", file=sys.stderr)
        sys.exit(1)


@main.command()
@click.argument("file", type=click.Path(exists=True))
@click.argument("path")
@click.argument("value")
def set_cmd(file: str, path: str, value: str) -> None:
    """Set a value in a TOML file.

    Example: tomlforge set config.toml server.port 8080
    """
    try:
        text = Path(file).read_text(encoding="utf-8")
        data = parse(text)

        # Try to parse the value
        parsed_value = _parse_cli_value(value)
        set_value(data, path, parsed_value)

        result = format_toml(data)
        Path(file).write_text(result, encoding="utf-8")
        console.print(f"[green]Set {path} = {parsed_value!r}[/green]")
    except TomlError as e:
        console.print(f"[red]Parse Error:[/red] {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}", file=sys.stderr)
        sys.exit(1)


@main.command()
@click.argument("file", type=click.Path(exists=True))
@click.argument("path")
def delete(file: str, path: str) -> None:
    """Delete a key from a TOML file.

    Example: tomlforge delete config.toml server.debug
    """
    try:
        text = Path(file).read_text(encoding="utf-8")
        data = parse(text)
        toml_delete(data, path)

        result = format_toml(data)
        Path(file).write_text(result, encoding="utf-8")
        console.print(f"[green]Deleted {path}[/green]")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}", file=sys.stderr)
        sys.exit(1)


@main.command()
@click.argument("file1", type=click.Path(exists=True))
@click.argument("file2", type=click.Path(exists=True))
@click.option(
    "-f",
    "--format",
    "fmt",
    type=click.Choice(["text", "json", "markdown"]),
    default="text",
    help="Output format",
)
def diff_cmd(file1: str, file2: str, fmt: str) -> None:
    """Diff two TOML files."""
    try:
        text1 = Path(file1).read_text(encoding="utf-8")
        text2 = Path(file2).read_text(encoding="utf-8")
        data1 = parse(text1)
        data2 = parse(text2)

        result = diff(data1, data2)
        output = format_diff(result, fmt)
        console.print(output)
    except TomlError as e:
        console.print(f"[red]Parse Error:[/red] {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}", file=sys.stderr)
        sys.exit(1)


@main.command()
@click.argument("files", nargs=-1, type=click.Path(exists=True), required=True)
@click.option(
    "-s",
    "--strategy",
    type=click.Choice(["override", "base", "union", "deep"]),
    default="override",
    help="Merge strategy",
)
@click.option(
    "-f",
    "--format",
    "fmt",
    type=click.Choice(["toml", "json"]),
    default="toml",
    help="Output format",
)
def merge_cmd(files: tuple[str, ...], strategy: str, fmt: str) -> None:
    """Merge multiple TOML files.

    Later files override earlier ones (by default).
    """
    try:
        result = {}
        for f in files:
            text = Path(f).read_text(encoding="utf-8")
            data = parse(text)
            result = merge(result, data, strategy)

        if fmt == "json":
            console.print(to_json(result))
        else:
            console.print(format_toml(result))
    except MergeConflictError as e:
        console.print(f"[red]Merge Conflict:[/red] {e}", file=sys.stderr)
        sys.exit(1)
    except TomlError as e:
        console.print(f"[red]Parse Error:[/red] {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}", file=sys.stderr)
        sys.exit(1)


@main.command()
@click.argument("file", type=click.Path(exists=True))
@click.option(
    "-f",
    "--format",
    "fmt",
    type=click.Choice(["toml", "json"]),
    default="toml",
    help="Output format",
)
@click.option("--sort-keys", is_flag=True, help="Sort keys alphabetically")
def format_file(file: str, fmt: str, sort_keys: bool) -> None:
    """Format/prettify a TOML file."""
    try:
        text = Path(file).read_text(encoding="utf-8")
        data = parse(text)

        result = to_json(data) if fmt == "json" else format_toml(data, sort_keys=sort_keys)

        console.print(result)
    except TomlError as e:
        console.print(f"[red]Parse Error:[/red] {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}", file=sys.stderr)
        sys.exit(1)


@main.command()
@click.argument("file", type=click.Path(exists=True))
@click.option(
    "-f",
    "--format",
    "fmt",
    type=click.Choice(["text", "json", "markdown"]),
    default="text",
    help="Output format",
)
@click.option("--no-naming", is_flag=True, help="Skip naming convention checks")
@click.option("--no-empty", is_flag=True, help="Skip empty table/array checks")
def validate_cmd(file: str, fmt: str, no_naming: bool, no_empty: bool) -> None:
    """Validate a TOML file."""
    try:
        text = Path(file).read_text(encoding="utf-8")
        data = parse(text)
        result = validate(
            data,
            check_naming=not no_naming,
            check_empty=not no_empty,
        )
        output = format_validation(result, fmt)
        console.print(output)
        if not result.valid:
            sys.exit(1)
    except TomlError as e:
        console.print(f"[red]Parse Error:[/red] {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}", file=sys.stderr)
        sys.exit(1)


@main.command()
@click.argument("file", type=click.Path(exists=True))
@click.option(
    "-f",
    "--format",
    "fmt",
    type=click.Choice(["json", "yaml"]),
    default="json",
    help="Output format",
)
def convert(file: str, fmt: str) -> None:
    """Convert TOML to JSON or YAML."""
    try:
        text = Path(file).read_text(encoding="utf-8")
        data = parse(text)

        if fmt == "json":
            console.print(to_json(data))
        elif fmt == "yaml":
            from tomlforge.converter import to_yaml

            console.print(to_yaml(data))
    except ImportError as e:
        console.print(f"[red]Error:[/red] {e}", file=sys.stderr)
        sys.exit(1)
    except TomlError as e:
        console.print(f"[red]Parse Error:[/red] {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}", file=sys.stderr)
        sys.exit(1)


def _parse_cli_value(value: str) -> Any:
    """Parse a CLI value string into a Python value."""
    # Try JSON parsing first
    try:
        return _json.loads(value)
    except (ValueError, _json.JSONDecodeError):
        pass

    # Boolean
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False

    # Integer
    try:
        return int(value)
    except ValueError:
        pass

    # Float
    try:
        return float(value)
    except ValueError:
        pass

    # String (default)
    return value


if __name__ == "__main__":
    main()
