"""Category B: Semantic integrity checks for OPT validation.

Validates ontology completeness, terminology binding consistency,
and mandatory node name coverage.
"""

from __future__ import annotations

from typing import Literal
from xml.etree.ElementTree import Element

from .issue_codes import (
    MANDATORY_NODE_NO_NAME,
    MISSING_TERM_DEF,
    ORPHAN_TERMINOLOGY_BINDING,
)

IssueData = dict[str, str | None]

# OPT namespace
OPT_NAMESPACE = "http://schemas.openehr.org/v1"


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
    severity: Literal["error", "warning", "info"] = "error",
    xpath: str | None = None,
    node_id: str | None = None,
    archetype_id: str | None = None,
    suggestion: str | None = None,
) -> IssueData:
    return {
        "severity": severity,
        "category": "semantic",
        "code": code,
        "message": message,
        "xpath": xpath,
        "node_id": node_id,
        "archetype_id": archetype_id,
        "suggestion": suggestion,
    }


def _collect_node_ids(element: Element) -> set[str]:
    """Collect all node_id values from the definition tree."""
    node_ids: set[str] = set()
    for el in element.iter():
        tag = el.tag
        if isinstance(tag, str):
            local = tag.split("}")[-1] if "}" in tag else tag
            if local == "node_id" and el.text and el.text.strip():
                nid = el.text.strip()
                if nid:  # Skip empty node_ids
                    node_ids.add(nid)
    return node_ids


def _collect_term_definitions(root: Element, language: str) -> dict[str, str]:
    """Collect all term definitions for the given language.

    Returns a dict mapping at-codes to their text values.
    """
    terms: dict[str, str] = {}

    # Search for ontology section
    for el in root.iter():
        tag = el.tag
        if isinstance(tag, str):
            local = tag.split("}")[-1] if "}" in tag else tag
            if local == "term_definitions":
                lang_attr = el.get("language", "")
                if lang_attr == language:
                    # Find all items with code attribute
                    for item in el:
                        item_tag = item.tag
                        if isinstance(item_tag, str):
                            item_local = item_tag.split("}")[-1] if "}" in item_tag else item_tag
                            if item_local == "items":
                                code = item.get("code", "")
                                if code:
                                    # Find the text value
                                    text_val = _get_term_text(item)
                                    terms[code] = text_val or ""
    return terms


def _get_term_text(items_element: Element) -> str | None:
    """Extract text value from a term_definitions items element."""
    for sub in items_element:
        tag = sub.tag
        if isinstance(tag, str):
            local = tag.split("}")[-1] if "}" in tag else tag
            if local == "items":
                item_id = sub.get("id", "")
                if item_id == "text":
                    # Get the value child
                    for val in sub:
                        val_tag = val.tag
                        if isinstance(val_tag, str):
                            val_local = val_tag.split("}")[-1] if "}" in val_tag else val_tag
                            if val_local == "value" and val.text:
                                return val.text.strip()
                    # Fallback: direct text
                    if sub.text and sub.text.strip():
                        return sub.text.strip()
    return None


def _collect_terminology_bindings(
    root: Element,
) -> list[tuple[str, str]]:
    """Collect terminology bindings as (code, terminology_id) pairs."""
    bindings: list[tuple[str, str]] = []

    for el in root.iter():
        tag = el.tag
        if isinstance(tag, str):
            local = tag.split("}")[-1] if "}" in tag else tag
            if local == "term_bindings":
                terminology = el.get("terminology", "")
                for item in el:
                    item_tag = item.tag
                    if isinstance(item_tag, str):
                        item_local = item_tag.split("}")[-1] if "}" in item_tag else item_tag
                        if item_local == "items":
                            code = item.get("code", "")
                            if code:
                                bindings.append((code, terminology))

    return bindings


def check_ontology_completeness(
    root: Element,
    ns: dict[str, str],
    language: str = "en",
) -> list[IssueData]:
    """Check that every node_id has a corresponding term definition."""
    issues: list[IssueData] = []

    definition = _find_child(root, "definition")
    if definition is None:
        return issues

    node_ids = _collect_node_ids(definition)
    term_defs = _collect_term_definitions(root, language)

    for nid in sorted(node_ids):
        # Skip empty-ish node IDs
        if not nid.startswith("at"):
            continue
        if nid not in term_defs:
            issues.append(
                _make_issue(
                    MISSING_TERM_DEF,
                    f"node_id '{nid}' has no term definition in language '{language}'.",
                    node_id=nid,
                    suggestion=(
                        f"Add a term_definition entry for '{nid}' in the ontology section."
                    ),
                )
            )

    return issues


def check_terminology_bindings(
    root: Element,
    ns: dict[str, str],
) -> list[IssueData]:
    """Check that terminology bindings reference existing node_ids."""
    issues: list[IssueData] = []

    definition = _find_child(root, "definition")
    if definition is None:
        return issues

    node_ids = _collect_node_ids(definition)
    bindings = _collect_terminology_bindings(root)

    for code, terminology in bindings:
        if code.startswith("at") and code not in node_ids:
            issues.append(
                _make_issue(
                    ORPHAN_TERMINOLOGY_BINDING,
                    f"Terminology binding for '{code}' (terminology: {terminology}) "
                    "references a node_id not present in the definition tree.",
                    node_id=code,
                    suggestion=(
                        f"Remove the orphan binding for '{code}' or add "
                        "the corresponding node to the definition."
                    ),
                )
            )

    return issues


def check_mandatory_node_names(
    root: Element,
    ns: dict[str, str],
    language: str = "en",
) -> list[IssueData]:
    """Check that mandatory nodes (min >= 1) have resolvable names."""
    issues: list[IssueData] = []

    definition = _find_child(root, "definition")
    if definition is None:
        return issues

    term_defs = _collect_term_definitions(root, language)

    def _check_element(el: Element, path: str) -> None:
        # Get node_id
        node_id_el = _find_child(el, "node_id")
        node_id = ""
        if node_id_el is not None and node_id_el.text:
            node_id = node_id_el.text.strip()

        # Check occurrences
        occ = _find_child(el, "occurrences")
        is_mandatory = False
        if occ is not None:
            lower_el = _find_child(occ, "lower")
            if lower_el is not None and lower_el.text:
                try:
                    lower = int(lower_el.text.strip())
                    is_mandatory = lower >= 1
                except ValueError:
                    pass

        if is_mandatory and node_id and node_id.startswith("at"):
            # Check if there's a name element
            name_el = _find_child(el, "name")
            has_name = False
            if name_el is not None:
                val = _find_child(name_el, "value")
                if val is not None and val.text and val.text.strip():
                    has_name = True

            # Check term definitions
            has_term = node_id in term_defs and bool(term_defs[node_id])

            if not has_name and not has_term:
                issues.append(
                    _make_issue(
                        MANDATORY_NODE_NO_NAME,
                        f"Mandatory node '{node_id}' at '{path}' has no resolvable name "
                        "(no <name> element and no term definition).",
                        node_id=node_id,
                        suggestion=(
                            f"Add a term_definition for '{node_id}' or add a "
                            "<name><value>...</value></name> element."
                        ),
                    )
                )

        # Recurse
        child_path = f"{path}/{node_id}" if node_id else path
        for child in el:
            _check_element(child, child_path)

    _check_element(definition, "/definition")

    return issues


def run_semantic_checks(
    root: Element,
    ns: dict[str, str],
    language: str = "en",
) -> list[IssueData]:
    """Run all Category B semantic integrity checks.

    Args:
        root: Parsed XML root element.
        ns: Namespace dict.
        language: Primary template language.

    Returns:
        List of issue dicts.
    """
    issues: list[IssueData] = []
    issues.extend(check_ontology_completeness(root, ns, language))
    issues.extend(check_terminology_bindings(root, ns))
    issues.extend(check_mandatory_node_names(root, ns, language))
    return issues
