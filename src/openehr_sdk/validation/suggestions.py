"""Fuzzy matching for "did you mean?" suggestions."""

from __future__ import annotations

import difflib


def suggest_path(invalid_path: str, valid_paths: list[str], max_suggestions: int = 3) -> list[str]:
    """Find the closest matching valid paths for an invalid path.

    Uses difflib.get_close_matches which is based on SequenceMatcher
    (Ratcliff/Obershelp pattern matching). This is in the stdlib so
    we need no extra dependencies.

    Args:
        invalid_path: The path that failed validation.
        valid_paths: All valid paths to match against.
        max_suggestions: Maximum number of suggestions to return.

    Returns:
        List of suggested valid paths, ordered by similarity.
    """
    return difflib.get_close_matches(invalid_path, valid_paths, n=max_suggestions, cutoff=0.4)


def suggest_segment(
    invalid_segment: str, valid_segments: list[str], max_suggestions: int = 3
) -> list[str]:
    """Find the closest matching path segment (node id).

    This is used for more targeted suggestions when we know exactly
    which segment is wrong.

    Args:
        invalid_segment: The segment that wasn't found.
        valid_segments: All valid segments at this level.
        max_suggestions: Maximum number of suggestions to return.

    Returns:
        List of suggested valid segments, ordered by similarity.
    """
    return difflib.get_close_matches(invalid_segment, valid_segments, n=max_suggestions, cutoff=0.3)
