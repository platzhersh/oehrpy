"""Command-line interface for FLAT composition validation.

This CLI exposes the :class:`~oehrpy.validation.FlatValidator` and the Web
Template path enumerator as machine-readable commands. It is intended for
CI/scripting use and as the optional Python backend for external tooling
(for example, the oehrpy VS Code extension, which otherwise validates
in-process).

Usage::

    python -m oehrpy.validation --version

    python -m oehrpy.validation validate-flat \\
        --web-template web_template.json \\
        --composition composition.flat.json \\
        [--platform ehrbase|better] [--output json|text]

    python -m oehrpy.validation web-template inspect \\
        --web-template web_template.json \\
        --path "vital_signs/blood_pressure/systolic"

    python -m oehrpy.validation show-paths \\
        --web-template web_template.json \\
        [--platform ehrbase|better] [--output json|text]

JSON output is stable and suitable for parsing by other programs.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from oehrpy import __version__
from oehrpy.validation import FlatValidator
from oehrpy.validation.path_checker import ValidationError, ValidationResult
from oehrpy.validation.platforms import PlatformType
from oehrpy.validation.required_fields import VALID_SUFFIXES
from oehrpy.validation.web_template import (
    enumerate_valid_paths,
    parse_web_template,
)


def _load_json(path: str) -> Any:
    """Load and parse a JSON file, raising a clear error on failure."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        msg = f"Could not read file '{path}': {exc}"
        raise SystemExit(msg) from exc

    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        msg = f"Invalid JSON in '{path}': {exc}"
        raise SystemExit(msg) from exc


def _serialize_error(error: ValidationError) -> dict[str, Any]:
    """Serialize a ValidationError to a JSON-friendly dict."""
    return {
        "path": error.path,
        "error_type": error.error_type,
        "message": error.message,
        "suggestion": error.suggestion,
        "valid_alternatives": list(error.valid_alternatives),
    }


def _serialize_result(result: ValidationResult) -> dict[str, Any]:
    """Serialize a ValidationResult to a JSON-friendly dict."""
    return {
        "is_valid": result.is_valid,
        "errors": [_serialize_error(e) for e in result.errors],
        "warnings": [_serialize_error(w) for w in result.warnings],
        "info": [note.message for note in result.info],
        "platform": result.platform,
        "template_id": result.template_id,
        "valid_path_count": result.valid_path_count,
        "checked_path_count": result.checked_path_count,
    }


def _strip_indices(path: str) -> str:
    """Remove all ``:N`` index notations from a path."""
    return re.sub(r":\d+", "", path)


def _cmd_validate_flat(args: argparse.Namespace) -> int:
    """Validate a FLAT composition against a Web Template."""
    web_template = _load_json(args.web_template)
    composition = _load_json(args.composition)

    if not isinstance(composition, dict):
        raise SystemExit(
            f"Composition '{args.composition}' must be a JSON object of FLAT paths to values."
        )

    platform: PlatformType = args.platform
    validator = FlatValidator.from_web_template(web_template, platform=platform)
    result = validator.validate(composition)

    if args.output == "json":
        print(json.dumps(_serialize_result(result), indent=2))
    else:
        _print_result_text(result)

    return 0 if result.is_valid else 1


def _print_result_text(result: ValidationResult) -> None:
    """Print a human-readable summary of a validation result."""
    if result.is_valid:
        print(f"✓ Valid ({result.checked_path_count} paths checked)")
    else:
        print(f"✗ Invalid — {len(result.errors)} error(s)")

    for error in result.errors:
        print(f"  [error] {error.path}: {error.message}")
        if error.suggestion:
            print(f"          → did you mean: {error.suggestion}")
    for warning in result.warnings:
        print(f"  [warn]  {warning.path}: {warning.message}")


def _cmd_web_template_inspect(args: argparse.Namespace) -> int:
    """Inspect a single FLAT path's node metadata for documentation/hover."""
    web_template = _load_json(args.web_template)
    parsed = parse_web_template(web_template)

    base_path = args.path.split("|")[0]
    node = parsed.get_node(base_path) or parsed.get_node(_strip_indices(base_path))

    if node is None:
        # No output; non-zero exit lets callers treat the path as unknown.
        return 1

    payload = {
        "id": node.id,
        "name": node.name,
        "rm_type": node.rm_type,
        "path": node.path,
        "min": node.min,
        "max": node.max,
        "valid_suffixes": list(VALID_SUFFIXES.get(node.rm_type, [])),
    }
    print(json.dumps(payload, indent=2))
    return 0


def _cmd_show_paths(args: argparse.Namespace) -> int:
    """List all valid FLAT paths for a Web Template and platform."""
    web_template = _load_json(args.web_template)
    parsed = parse_web_template(web_template)
    platform: PlatformType = args.platform
    paths = enumerate_valid_paths(parsed, platform)

    if args.output == "json":
        print(json.dumps(paths, indent=2))
    else:
        for path in paths:
            print(path)

    return 0


def _build_parser() -> argparse.ArgumentParser:
    """Build the argument parser with all subcommands."""
    parser = argparse.ArgumentParser(
        prog="python -m oehrpy.validation",
        description="Validate openEHR FLAT compositions against Web Templates.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"oehrpy {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command")

    # validate-flat
    validate = subparsers.add_parser(
        "validate-flat",
        help="Validate a FLAT composition against a Web Template.",
    )
    validate.add_argument("--web-template", required=True, help="Web Template JSON path.")
    validate.add_argument("--composition", required=True, help="FLAT composition JSON path.")
    validate.add_argument(
        "--platform",
        choices=["ehrbase", "better"],
        default="ehrbase",
        help="CDR platform dialect (default: ehrbase).",
    )
    validate.add_argument(
        "--output",
        choices=["json", "text"],
        default="text",
        help="Output format (default: text).",
    )
    validate.set_defaults(func=_cmd_validate_flat)

    # web-template <inspect>
    web_template = subparsers.add_parser(
        "web-template",
        help="Web Template inspection commands.",
    )
    wt_sub = web_template.add_subparsers(dest="web_template_command")
    inspect = wt_sub.add_parser(
        "inspect",
        help="Inspect a single FLAT path's node metadata.",
    )
    inspect.add_argument("--web-template", required=True, help="Web Template JSON path.")
    inspect.add_argument("--path", required=True, help="FLAT path to inspect (suffix optional).")
    inspect.set_defaults(func=_cmd_web_template_inspect)

    # show-paths
    show_paths = subparsers.add_parser(
        "show-paths",
        help="List all valid FLAT paths for a Web Template.",
    )
    show_paths.add_argument("--web-template", required=True, help="Web Template JSON path.")
    show_paths.add_argument(
        "--platform",
        choices=["ehrbase", "better"],
        default="ehrbase",
        help="CDR platform dialect (default: ehrbase).",
    )
    show_paths.add_argument(
        "--output",
        choices=["json", "text"],
        default="text",
        help="Output format (default: text).",
    )
    show_paths.set_defaults(func=_cmd_show_paths)

    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the validation CLI.

    Args:
        argv: Command-line arguments (defaults to ``sys.argv[1:]``).

    Returns:
        Exit code: ``0`` on success/valid, ``1`` on validation failure or an
        unresolved path, ``2`` on usage error.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    func = getattr(args, "func", None)
    if func is None:
        # `web-template` with no subcommand, or no command at all.
        parser.print_help(sys.stderr)
        return 2

    return int(func(args))


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:
        # Output was piped into a command that closed early (e.g. `head`).
        sys.exit(0)
