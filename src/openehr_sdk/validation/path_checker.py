"""Path validation logic and suffix checking."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

from openehr_sdk.validation.platforms import PlatformType
from openehr_sdk.validation.required_fields import (
    REQUIRED_FIELD_GROUPS,
    VALID_SUFFIXES,
)
from openehr_sdk.validation.suggestions import suggest_path, suggest_segment
from openehr_sdk.validation.web_template import ParsedWebTemplate, enumerate_valid_paths

ErrorType = Literal["unknown_path", "wrong_suffix", "missing_required", "index_mismatch"]

# Static allowlist of ctx/ shorthand keys defined in the openEHR simSDT specification.
# These are resolved by the CDR at ingest time and are not part of the Web Template tree.
_CTX_ALLOWED_BASES: frozenset[str] = frozenset(
    {
        "ctx/language",
        "ctx/territory",
        "ctx/composer_name",
        "ctx/composer_id",
        "ctx/id_scheme",
        "ctx/id_namespace",
        "ctx/time",
        "ctx/end_time",
        "ctx/history_origin",
        "ctx/health_care_facility",
        "ctx/participation_name",
        "ctx/participation_function",
        "ctx/participation_mode",
        "ctx/participation_id",
        "ctx/setting",
    }
)


def _is_valid_ctx_path(path: str) -> bool:
    """Return True if *path* is a known ctx/ shorthand (with or without |attribute)."""
    base = path.split("|")[0]
    return base in _CTX_ALLOWED_BASES


@dataclass
class ValidationError:
    """A single validation error or warning."""

    path: str
    error_type: ErrorType
    message: str
    suggestion: str | None = None
    valid_alternatives: list[str] = field(default_factory=list)


@dataclass
class ValidationResult:
    """Result of validating a FLAT composition."""

    is_valid: bool
    errors: list[ValidationError]
    warnings: list[ValidationError]
    platform: PlatformType
    template_id: str
    valid_path_count: int
    checked_path_count: int


def _strip_indices(path: str) -> str:
    """Remove all :N index notations from a path."""
    return re.sub(r":\d+", "", path)


def _check_index_issues(
    path: str,
    platform: PlatformType,
    valid_path_set: set[str],
) -> ValidationError | None:
    """Check if the error is due to index notation mismatch."""
    if platform == "ehrbase" and re.search(r":\d+", path):
        # Try removing indices
        stripped = _strip_indices(path)
        if stripped in valid_path_set:
            return ValidationError(
                path=path,
                error_type="index_mismatch",
                message=(
                    "EHRBase 2.x does not use index notation (:0) for "
                    "single-occurrence items. Remove the index."
                ),
                suggestion=stripped,
            )

    if platform == "better" and not re.search(r":\d+", path):
        # Try adding :0 to segments
        # This is a heuristic — try the last segment
        parts = path.split("|")
        base = parts[0]
        suffix = "|" + parts[1] if len(parts) > 1 else ""
        segments = base.split("/")
        for i in range(len(segments) - 1, 0, -1):
            indexed = segments.copy()
            indexed[i] = indexed[i] + ":0"
            candidate = "/".join(indexed) + suffix
            if candidate in valid_path_set:
                return ValidationError(
                    path=path,
                    error_type="index_mismatch",
                    message="Better platform requires :0 index notation on array paths.",
                    suggestion=candidate,
                )

    return None


def _check_any_event_issue(path: str, platform: PlatformType) -> str | None:
    """Check if the path uses /any_event/ which EHRBase 2.x doesn't use."""
    if platform == "ehrbase" and "/any_event" in path:
        return "EHRBase 2.x does not include /any_event/ in FLAT paths. Use direct paths."
    return None


def _check_suffix_issue(
    path: str,
    parsed: ParsedWebTemplate,
) -> ValidationError | None:
    """Check if the path has a wrong suffix for its RM data type."""
    if "|" not in path:
        return None

    base_path, suffix = path.rsplit("|", 1)
    suffix_with_pipe = "|" + suffix

    # Strip indices from base path for node lookup
    lookup_path = _strip_indices(base_path)

    node = parsed.get_node(lookup_path)
    if node is None:
        # Also try the raw base_path
        node = parsed.get_node(base_path)
    if node is None:
        return None

    valid = VALID_SUFFIXES.get(node.rm_type)
    if valid is None:
        return None

    if not valid:
        # This type takes no suffix
        return ValidationError(
            path=path,
            error_type="wrong_suffix",
            message=f"{node.rm_type} does not accept any suffix. Use the bare path.",
            suggestion=base_path,
            valid_alternatives=[base_path],
        )

    if suffix_with_pipe not in valid:
        alternatives = [base_path + s for s in valid]
        valid_suffix_str = ", ".join(valid)
        return ValidationError(
            path=path,
            error_type="wrong_suffix",
            message=(
                f"Invalid suffix '|{suffix}' for {node.rm_type}. Valid suffixes: {valid_suffix_str}"
            ),
            suggestion=alternatives[0] if alternatives else None,
            valid_alternatives=alternatives,
        )

    return None


def _check_renamed_segment(
    path: str,
    parsed: ParsedWebTemplate,
) -> tuple[str | None, str | None]:
    """Check if a path segment matches a renamed node's original name.

    Returns:
        A tuple of (message, suggested_fix_path) or (None, None).
    """
    # Strip suffix for segment analysis
    base_path = path.split("|")[0]
    base_path_clean = _strip_indices(base_path)
    segments = base_path_clean.split("/")
    suffix_part = "|" + path.split("|")[1] if "|" in path else ""

    from openehr_sdk.validation.web_template import _slugify

    for node in parsed.nodes.values():
        if node.original_name is None:
            continue
        original_slug = _slugify(node.original_name)
        # Also check individual words from the original name
        original_words = [_slugify(w) for w in re.split(r"[\s/]+", node.original_name) if w]
        for i, segment in enumerate(segments):
            if segment == original_slug or segment in original_words:
                message = (
                    f"Node was renamed in this template. "
                    f'Original name "{node.original_name}" is now "{node.id}".'
                )
                # Build the corrected path by replacing the renamed segment
                fixed_segments = segments.copy()
                fixed_segments[i] = node.id
                fixed_path = "/".join(fixed_segments) + suffix_part
                return message, fixed_path

    return None, None


def validate_composition(
    flat_composition: dict[str, object],
    parsed: ParsedWebTemplate,
    platform: PlatformType = "ehrbase",
) -> ValidationResult:
    """Validate a FLAT composition against a parsed Web Template.

    Args:
        flat_composition: The FLAT format composition dict (path -> value).
        parsed: The parsed Web Template.
        platform: The CDR platform dialect.

    Returns:
        A ValidationResult with errors and warnings.
    """
    valid_paths = enumerate_valid_paths(parsed, platform)
    valid_path_set = set(valid_paths)

    errors: list[ValidationError] = []
    warnings: list[ValidationError] = []
    checked_count = 0

    for path in flat_composition:
        checked_count += 1

        # Handle ctx/ shorthand paths (not in the Web Template tree)
        if path.startswith("ctx/"):
            if not _is_valid_ctx_path(path):
                warnings.append(
                    ValidationError(
                        path=path,
                        error_type="unknown_path",
                        message="Unknown ctx/ shorthand",
                    )
                )
            continue

        if path in valid_path_set:
            continue

        # Try to diagnose WHY it's invalid, in order of specificity

        # 1. Check for index notation mismatch
        index_error = _check_index_issues(path, platform, valid_path_set)
        if index_error is not None:
            errors.append(index_error)
            continue

        # 2. Check for /any_event/ usage on EHRBase
        any_event_msg = _check_any_event_issue(path, platform)
        if any_event_msg is not None:
            suggestion_paths = suggest_path(path, valid_paths)
            errors.append(
                ValidationError(
                    path=path,
                    error_type="unknown_path",
                    message=any_event_msg,
                    suggestion=suggestion_paths[0] if suggestion_paths else None,
                )
            )
            continue

        # 3. Check for wrong data type suffix
        suffix_error = _check_suffix_issue(path, parsed)
        if suffix_error is not None:
            errors.append(suffix_error)
            continue

        # 4. Check if this is a renamed node
        rename_msg, rename_fix = _check_renamed_segment(path, parsed)
        message = rename_msg or "Path not found in Web Template."

        # 5. Find suggestions — prefer rename-derived fix, then segment-level,
        # then full-path fuzzy matching.
        suggestions: list[str] = []

        if rename_fix:
            suggestions = [rename_fix]
        else:
            base = path.split("|")[0]
            base = _strip_indices(base)
            segments = base.split("/")
            suffix_part = "|" + path.split("|")[1] if "|" in path else ""

            if len(segments) > 1:
                parent_path = "/".join(segments[:-1])
                valid_children = parsed.get_children_ids(parent_path)
                if valid_children:
                    seg_suggestions = suggest_segment(segments[-1], valid_children)
                    if seg_suggestions:
                        suggestions = [
                            "/".join(segments[:-1]) + "/" + s + suffix_part for s in seg_suggestions
                        ]

            if not suggestions:
                suggestions = suggest_path(path, valid_paths)

        errors.append(
            ValidationError(
                path=path,
                error_type="unknown_path",
                message=message,
                suggestion=suggestions[0] if suggestions else None,
                valid_alternatives=suggestions,
            )
        )

    # Check required fields
    flat_keys = set(flat_composition.keys())
    for group in REQUIRED_FIELD_GROUPS:
        found = any(f"{parsed.tree_id}/{f}" in flat_keys for f in group)
        if not found:
            full_path = f"{parsed.tree_id}/{group[0]}"
            warnings.append(
                ValidationError(
                    path=full_path,
                    error_type="missing_required",
                    message="Required composition field is missing.",
                )
            )

    is_valid = len(errors) == 0

    return ValidationResult(
        is_valid=is_valid,
        errors=errors,
        warnings=warnings,
        platform=platform,
        template_id=parsed.template_id,
        valid_path_count=len(valid_paths),
        checked_path_count=checked_count,
    )
