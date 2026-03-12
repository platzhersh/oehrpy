"""Known RM type registry for OPT validation.

Dynamically imports the RM type set from oehrpy.rm to stay in sync.
"""

from __future__ import annotations

import inspect


def get_known_rm_types() -> frozenset[str]:
    """Return the set of all known openEHR RM 1.1.0 type names.

    Imports from the generated RM module to stay in sync automatically.
    """
    from pydantic import BaseModel

    import openehr_sdk.rm.rm_types as rm_module

    return frozenset(
        name
        for name in dir(rm_module)
        if not name.startswith("_")
        and name[0].isupper()
        and inspect.isclass(getattr(rm_module, name))
        and issubclass(getattr(rm_module, name), BaseModel)
        and name not in ("BaseModel",)
    )


# Cache the set at module level for performance
KNOWN_RM_TYPES: frozenset[str] = get_known_rm_types()


def suggest_rm_type(invalid_type: str) -> str | None:
    """Suggest a correct RM type name for a misspelled one.

    Uses substring matching and word-part overlap to find close matches.
    """
    invalid_upper = invalid_type.upper()

    # Exact case-insensitive match
    for known in KNOWN_RM_TYPES:
        if known.upper() == invalid_upper:
            return known

    # Split into parts by underscore and find best overlap
    invalid_parts = set(invalid_upper.split("_"))
    best_score = 0
    best_match: str | None = None

    for known in KNOWN_RM_TYPES:
        known_parts = set(known.upper().split("_"))
        # Count shared word parts
        shared = len(invalid_parts & known_parts)
        if shared > best_score:
            best_score = shared
            best_match = known
        elif shared == best_score and best_match is not None:
            # Prefer the shorter name (more likely the intended type)
            if len(known) < len(best_match):
                best_match = known

    # Also check substring containment
    for known in KNOWN_RM_TYPES:
        if (known.upper() in invalid_upper or invalid_upper in known.upper()) and best_score < 2:
            return known

    if best_score >= 2:
        return best_match

    return None
