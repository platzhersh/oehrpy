"""Category C: Structural warning checks for OPT validation.

Detects suspicious patterns that are not necessarily errors but worth flagging.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Literal
from xml.etree.ElementTree import Element

from .issue_codes import (
    ARCHETYPE_OVERUSE,
    CONCEPT_SPECIAL_CHARS,
    DRAFT_LIFECYCLE,
    NO_DESCRIPTION_DETAILS,
    PROHIBITED_NODE_IN_TREE,
    SPECIAL_CHARS_IN_NAME,
    UNCONSTRAINED_ARCHETYPE_SLOT,
    UNSTABLE_ARCHETYPE_VERSION,
)

IssueData = dict[str, str | None]

OPT_NAMESPACE = "http://schemas.openehr.org/v1"

# Characters that complicate FLAT paths
FLAT_PATH_SPECIAL_CHARS = re.compile(r"[/\\|:]")


def _ns(tag: str) -> str:
    return f"{{{OPT_NAMESPACE}}}{tag}"


def _find_child(element: Element, tag: str) -> Element | None:
    """Find a child element, trying namespaced then plain tag.

    Uses ``is not None`` to avoid ElementTree's falsy empty-element gotcha.
    """
    result = element.find(_ns(tag))
    if result is not None:
        return result
    result = element.find(tag)
    if result is not None:
        return result
    return None


def _make_issue(
    code: str,
    message: str,
    severity: Literal["error", "warning", "info"] = "warning",
    xpath: str | None = None,
    node_id: str | None = None,
    archetype_id: str | None = None,
    suggestion: str | None = None,
) -> IssueData:
    return {
        "severity": severity,
        "category": "structural",
        "code": code,
        "message": message,
        "xpath": xpath,
        "node_id": node_id,
        "archetype_id": archetype_id,
        "suggestion": suggestion,
    }


def _find_text(element: Element, path: str, ns: dict[str, str]) -> str | None:
    ns_path = "/".join(
        f"opt:{p}" if p and not p.startswith(".") and ":" not in p else p for p in path.split("/")
    )
    el = element.find(ns_path, ns)
    if el is not None and el.text:
        return el.text.strip()
    el = element.find(path)
    if el is not None and el.text:
        return el.text.strip()
    return None


def check_lifecycle_state(root: Element, ns: dict[str, str]) -> list[IssueData]:
    """Warn if lifecycle_state is not 'published'."""
    issues: list[IssueData] = []

    state = _find_text(root, "description/lifecycle_state", ns)
    if state and state.lower() not in ("published",):
        issues.append(
            _make_issue(
                DRAFT_LIFECYCLE,
                f"description/lifecycle_state is '{state}'. "
                "Templates in non-published state may change.",
                xpath="/template/description/lifecycle_state",
            )
        )

    return issues


def check_archetype_versions(root: Element, ns: dict[str, str]) -> list[IssueData]:
    """Warn about v0 archetype references."""
    issues: list[IssueData] = []

    for el in root.iter():
        tag = el.tag
        if isinstance(tag, str):
            local = tag.split("}")[-1] if "}" in tag else tag
            if local == "value" and el.text and el.text.strip():
                text = el.text.strip()
                if text.startswith("openEHR-") and text.endswith(".v0"):
                    issues.append(
                        _make_issue(
                            UNSTABLE_ARCHETYPE_VERSION,
                            f"Archetype '{text}' uses v0 (experimental/unstable).",
                            archetype_id=text,
                            suggestion="Consider using a stable version (v1+).",
                        )
                    )

    return issues


def check_prohibited_nodes(root: Element, ns: dict[str, str]) -> list[IssueData]:
    """Warn about nodes with max=0 (prohibited) that exist in the tree."""
    issues: list[IssueData] = []

    for el in root.iter():
        tag = el.tag
        if isinstance(tag, str):
            local = tag.split("}")[-1] if "}" in tag else tag
            if local == "occurrences":
                upper_el = _find_child(el, "upper")
                upper_unbounded = _find_text(el, "upper_unbounded", ns)
                if (
                    upper_el is not None
                    and upper_el.text
                    and upper_el.text.strip() == "0"
                    and upper_unbounded != "true"
                ):
                    # Walk up isn't directly supported, so we note it generically
                    issues.append(
                        _make_issue(
                            PROHIBITED_NODE_IN_TREE,
                            "Node with max=0 (prohibited) exists in the definition tree. "
                            "This node will never be instantiated.",
                            suggestion=(
                                "Remove the prohibited node from the template, "
                                "or set max >= 1 if the node should be allowed."
                            ),
                        )
                    )

    return issues


def check_archetype_slots(root: Element, ns: dict[str, str]) -> list[IssueData]:
    """Warn about ARCHETYPE_SLOT with no include/exclude expressions."""
    issues: list[IssueData] = []

    xsi_ns = "http://www.w3.org/2001/XMLSchema-instance"

    for el in root.iter():
        xsi_type = el.get(f"{{{xsi_ns}}}type", "")
        local_type = xsi_type.split(":")[-1] if ":" in xsi_type else xsi_type

        if local_type == "ARCHETYPE_SLOT":
            has_includes = _find_child(el, "includes") is not None
            has_excludes = _find_child(el, "excludes") is not None
            if not has_includes and not has_excludes:
                issues.append(
                    _make_issue(
                        UNCONSTRAINED_ARCHETYPE_SLOT,
                        "ARCHETYPE_SLOT with no include/exclude expressions. "
                        "This slot accepts any archetype.",
                    )
                )

    return issues


def check_concept_special_chars(root: Element, ns: dict[str, str]) -> list[IssueData]:
    """Warn if concept name contains characters that complicate FLAT paths."""
    issues: list[IssueData] = []

    concept = _find_text(root, "concept", ns)
    if concept and re.search(r"[^a-zA-Z0-9 _]", concept):
        issues.append(
            _make_issue(
                CONCEPT_SPECIAL_CHARS,
                f"Template concept '{concept}' contains special characters "
                "that will be transformed in FLAT path prefix.",
                xpath="/template/concept",
                suggestion=(
                    "EHRBase derives the FLAT path prefix from the concept name. "
                    "Verify the derived path after upload."
                ),
            )
        )

    return issues


def check_description_details(root: Element, ns: dict[str, str]) -> list[IssueData]:
    """Warn if description/details is missing."""
    issues: list[IssueData] = []

    details = root.find(f"{_ns('description')}/{_ns('details')}")
    if details is None:
        details = root.find("description/details")
    if details is None:
        issues.append(
            _make_issue(
                NO_DESCRIPTION_DETAILS,
                "No description/details provided. Consider adding documentation.",
                xpath="/template/description/details",
            )
        )

    return issues


def check_archetype_overuse(root: Element, ns: dict[str, str]) -> list[IssueData]:
    """Warn if the same archetype is used more than 3 times."""
    issues: list[IssueData] = []

    archetype_counts: Counter[str] = Counter()
    for el in root.iter():
        tag = el.tag
        if isinstance(tag, str):
            local = tag.split("}")[-1] if "}" in tag else tag
            if local == "value" and el.text and el.text.strip():
                text = el.text.strip()
                if text.startswith("openEHR-"):
                    archetype_counts[text] += 1

    for arch_id, count in archetype_counts.items():
        if count > 3:
            issues.append(
                _make_issue(
                    ARCHETYPE_OVERUSE,
                    f"Archetype '{arch_id}' is used {count} times in the template.",
                    archetype_id=arch_id,
                    suggestion=(
                        "Using the same archetype many times may indicate over-specialization."
                    ),
                )
            )

    return issues


def check_term_name_special_chars(root: Element, ns: dict[str, str]) -> list[IssueData]:
    """Warn about term definition names with FLAT-path-problematic characters."""
    issues: list[IssueData] = []

    for el in root.iter():
        tag = el.tag
        if isinstance(tag, str):
            local = tag.split("}")[-1] if "}" in tag else tag
            if local == "items":
                item_id = el.get("id", "")
                if item_id == "text":
                    for val in el:
                        val_tag = val.tag
                        if isinstance(val_tag, str):
                            val_local = val_tag.split("}")[-1] if "}" in val_tag else val_tag
                            if val_local == "value" and val.text:
                                text = val.text.strip()
                                if FLAT_PATH_SPECIAL_CHARS.search(text):
                                    issues.append(
                                        _make_issue(
                                            SPECIAL_CHARS_IN_NAME,
                                            f"Term name '{text}' contains characters "
                                            "(/, \\, |, :) that complicate FLAT paths.",
                                        )
                                    )

    return issues


def run_structural_checks(root: Element, ns: dict[str, str]) -> list[IssueData]:
    """Run all Category C structural warning checks.

    Args:
        root: Parsed XML root element.
        ns: Namespace dict.

    Returns:
        List of issue dicts.
    """
    issues: list[IssueData] = []
    issues.extend(check_lifecycle_state(root, ns))
    issues.extend(check_archetype_versions(root, ns))
    issues.extend(check_prohibited_nodes(root, ns))
    issues.extend(check_archetype_slots(root, ns))
    issues.extend(check_concept_special_chars(root, ns))
    issues.extend(check_description_details(root, ns))
    issues.extend(check_archetype_overuse(root, ns))
    issues.extend(check_term_name_special_chars(root, ns))
    return issues
