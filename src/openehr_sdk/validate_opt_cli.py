"""CLI entry point for OPT validation.

Usage:
    python -m openehr_sdk.validate_opt_cli path/to/template.opt [options]

Options:
    --output json    Output results as JSON (for CI/CD integration)
    --strict         Treat warnings as errors
    --show-flat-paths  Show FLAT path impact analysis details
"""

from __future__ import annotations

import argparse
import glob
import sys
from pathlib import Path

from openehr_sdk.validation.opt import OPTValidator


def main(argv: list[str] | None = None) -> int:
    """Run OPT validation from the command line.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:]).

    Returns:
        Exit code (0 = valid, 1 = errors found).
    """
    parser = argparse.ArgumentParser(
        prog="oehrpy-validate-opt",
        description="Validate OPT 1.4 XML files for openEHR.",
    )
    parser.add_argument(
        "files",
        nargs="+",
        help="OPT file(s) to validate. Supports glob patterns.",
    )
    parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors.",
    )
    parser.add_argument(
        "--show-flat-paths",
        action="store_true",
        help="Show FLAT path impact analysis details.",
    )

    args = parser.parse_args(argv)

    # Expand glob patterns
    files: list[str] = []
    for pattern in args.files:
        expanded = glob.glob(pattern)
        if expanded:
            files.extend(expanded)
        else:
            files.append(pattern)

    if not files:
        print("No files specified.", file=sys.stderr)
        return 1

    validator = OPTValidator()
    any_invalid = False

    for filepath in files:
        path = Path(filepath)

        if not path.exists():
            print(f"File not found: {filepath}", file=sys.stderr)
            any_invalid = True
            continue

        result = validator.validate_file(path)

        if args.output == "json":
            print(result.to_json())
        else:
            _print_text_result(result, filepath, args.show_flat_paths)

        if not result.is_valid or args.strict and result.warning_count > 0:
            any_invalid = True

    return 1 if any_invalid else 0


def _print_text_result(
    result: object,
    filepath: str,
    show_flat_paths: bool,
) -> None:
    """Print validation result in human-readable text format."""
    from openehr_sdk.validation.opt import OPTValidationResult

    if not isinstance(result, OPTValidationResult):
        return

    print(f"\nValidating: {filepath}")
    print(f"Template ID: {result.template_id or '(unknown)'}")
    print(f"Concept: {result.concept or '(unknown)'}")
    print(f"Archetypes: {result.archetype_count} | Nodes: {result.node_count}")

    errors = [i for i in result.issues if i.severity == "error"]
    warnings = [i for i in result.issues if i.severity == "warning"]
    infos = [i for i in result.issues if i.severity == "info"]

    if errors:
        print(f"\nERRORS ({len(errors)})")
        print("-" * 40)
        for issue in errors:
            print(f"  [{issue.code}] {issue.message}")
            if issue.xpath:
                print(f"    at: {issue.xpath}")
            if issue.suggestion:
                print(f"    -> {issue.suggestion}")

    if warnings:
        print(f"\nWARNINGS ({len(warnings)})")
        print("-" * 40)
        for issue in warnings:
            print(f"  [{issue.code}] {issue.message}")
            if issue.suggestion:
                print(f"    -> {issue.suggestion}")

    if show_flat_paths and infos:
        print("\nFLAT PATH IMPACT")
        print("-" * 40)
        for issue in infos:
            if issue.category == "flat_impact":
                print(f"  [{issue.code}] {issue.message}")

    status = "VALID" if result.is_valid else "INVALID"

    summary = f"\nResult: {status}"
    if result.error_count > 0 or result.warning_count > 0:
        summary += f"  ({result.error_count} error(s), {result.warning_count} warning(s))"
    print(summary)


if __name__ == "__main__":
    sys.exit(main())
