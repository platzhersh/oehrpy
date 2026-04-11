"""Category D: FLAT path impact analysis for OPT validation.

Analyzes how the OPT structure maps to FLAT format paths and detects
renamed nodes and potential path collisions.
"""

from __future__ import annotations

import re
from typing import Literal
from xml.etree.ElementTree import Element

from .issue_codes import (
    CONCEPT_SPECIAL_CHARS,
    FLAT_PATH_COLLISION,
    RENAMED_NODE_DETECTED,
)

IssueData = dict[str, str | None]

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
    severity: Literal["error", "warning", "info"] = "info",
    xpath: str | None = None,
    node_id: str | None = None,
    archetype_id: str | None = None,
    suggestion: str | None = None,
) -> IssueData:
    return {
        "severity": severity,
        "category": "flat_impact",
        "code": code,
        "message": message,
        "xpath": xpath,
        "node_id": node_id,
        "archetype_id": archetype_id,
        "suggestion": suggestion,
    }


def _to_flat_segment(name: str) -> str:
    """Convert a human-readable name to a FLAT path segment.

    Mimics EHRBase's path derivation: lowercase, replace non-alphanumeric
    with underscores, collapse multiple underscores.
    """
    segment = name.lower()
    segment = re.sub(r"[^a-z0-9]+", "_", segment)
    segment = segment.strip("_")
    return segment


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


def _collect_term_definitions(root: Element, language: str) -> dict[str, str]:
    """Collect term definitions for a language."""
    terms: dict[str, str] = {}
    for el in root.iter():
        tag = el.tag
        if isinstance(tag, str):
            local = tag.split("}")[-1] if "}" in tag else tag
            if local == "term_definitions":
                lang_attr = el.get("language", "")
                if lang_attr == language:
                    for item in el:
                        item_tag = item.tag
                        if isinstance(item_tag, str):
                            item_local = item_tag.split("}")[-1] if "}" in item_tag else item_tag
                            if item_local == "items":
                                code = item.get("code", "")
                                if code:
                                    text_val = _get_term_text(item)
                                    if text_val:
                                        terms[code] = text_val
    return terms


def _get_term_text(items_element: Element) -> str | None:
    """Extract text value from term_definitions items."""
    for sub in items_element:
        tag = sub.tag
        if isinstance(tag, str):
            local = tag.split("}")[-1] if "}" in tag else tag
            if local == "items":
                item_id = sub.get("id", "")
                if item_id == "text":
                    for val in sub:
                        val_tag = val.tag
                        if isinstance(val_tag, str):
                            val_local = val_tag.split("}")[-1] if "}" in val_tag else val_tag
                            if val_local == "value" and val.text:
                                return val.text.strip()
                    if sub.text and sub.text.strip():
                        return sub.text.strip()
    return None


def analyze_concept_path(root: Element, ns: dict[str, str]) -> list[IssueData]:
    """Analyze how the template concept maps to a FLAT path prefix."""
    issues: list[IssueData] = []

    concept = _find_text(root, "concept", ns)
    if concept:
        flat_prefix = _to_flat_segment(concept)
        if flat_prefix != concept.lower().replace(" ", "_"):
            issues.append(
                _make_issue(
                    CONCEPT_SPECIAL_CHARS,
                    f"Template concept '{concept}' maps to FLAT prefix '{flat_prefix}'. "
                    "Special characters are transformed.",
                    xpath="/template/concept",
                    suggestion=(
                        "Verify the derived FLAT path prefix matches your expectations. "
                        "Use /example?format=FLAT after upload to confirm."
                    ),
                )
            )

    return issues


def detect_renamed_nodes(
    root: Element,
    ns: dict[str, str],
    language: str = "en",
) -> list[IssueData]:
    """Detect nodes where the template overrides the archetype default name.

    When a template provides a <name><value> for a node, the FLAT path
    uses the template name rather than the archetype's default name from
    the ontology.
    """
    issues: list[IssueData] = []

    term_defs = _collect_term_definitions(root, language)

    def _check_node(element: Element, current_archetype: str | None) -> None:
        # Check for archetype_id (new scope)
        arch_id_el = _find_child(element, "archetype_id")
        if arch_id_el is not None:
            val_el = _find_child(arch_id_el, "value")
            if val_el is not None and val_el.text and val_el.text.strip():
                current_archetype = val_el.text.strip()

        # Get node_id
        node_id_el = _find_child(element, "node_id")
        node_id = ""
        if node_id_el is not None and node_id_el.text:
            node_id = node_id_el.text.strip()

        # Get explicit name override
        name_el = _find_child(element, "name")
        if name_el is not None and node_id and node_id.startswith("at"):
            val_el = _find_child(name_el, "value")
            if val_el is not None and val_el.text and val_el.text.strip():
                override_name = val_el.text.strip()
                # Check against ontology name
                ontology_name = term_defs.get(node_id, "")
                if ontology_name and override_name != ontology_name:
                    override_segment = _to_flat_segment(override_name)
                    ontology_segment = _to_flat_segment(ontology_name)
                    if override_segment != ontology_segment:
                        issues.append(
                            _make_issue(
                                RENAMED_NODE_DETECTED,
                                f"{node_id}: ontology name '{ontology_name}' overridden "
                                f"to '{override_name}' in template. "
                                f"FLAT path will use '{override_segment}' "
                                f"(not '{ontology_segment}').",
                                node_id=node_id,
                                archetype_id=current_archetype,
                            )
                        )

        # Recurse
        for child in element:
            _check_node(child, current_archetype)

    definition = _find_child(root, "definition")
    if definition is not None:
        _check_node(definition, None)

    return issues


def detect_flat_path_collisions(
    root: Element,
    ns: dict[str, str],
    language: str = "en",
) -> list[IssueData]:
    """Detect cases where two sibling nodes produce the same FLAT path segment."""
    issues: list[IssueData] = []

    term_defs = _collect_term_definitions(root, language)

    def _check_siblings(element: Element) -> None:
        # Collect FLAT segments for children of this element
        segments: dict[str, list[str]] = {}

        for child in element:
            child_tag = child.tag
            if isinstance(child_tag, str):
                local = child_tag.split("}")[-1] if "}" in child_tag else child_tag
                if local in ("children", "attributes"):
                    # Check children within this structural node
                    _check_siblings(child)
                    continue

            # Get node_id
            node_id_el = _find_child(child, "node_id")
            if node_id_el is None or not node_id_el.text:
                continue
            node_id = node_id_el.text.strip()
            if not node_id:
                continue

            # Determine the name that will be used for FLAT path
            name_el = _find_child(child, "name")
            name = ""
            if name_el is not None:
                val_el = _find_child(name_el, "value")
                if val_el is not None and val_el.text:
                    name = val_el.text.strip()
            if not name:
                name = term_defs.get(node_id, node_id)

            segment = _to_flat_segment(name)
            if segment in segments:
                segments[segment].append(node_id)
            else:
                segments[segment] = [node_id]

        for segment, nids in segments.items():
            if len(nids) > 1:
                issues.append(
                    _make_issue(
                        FLAT_PATH_COLLISION,
                        f"Multiple nodes ({', '.join(nids)}) produce the same "
                        f"FLAT path segment '{segment}'.",
                        severity="warning",
                        suggestion=(
                            "Rename one of the nodes in the template to avoid ambiguous FLAT paths."
                        ),
                    )
                )

        # Recurse into children
        for child in element:
            _check_siblings(child)

    definition = _find_child(root, "definition")
    if definition is not None:
        _check_siblings(definition)

    return issues


def run_flat_impact_checks(
    root: Element,
    ns: dict[str, str],
    language: str = "en",
) -> list[IssueData]:
    """Run all Category D FLAT path impact analysis checks.

    Args:
        root: Parsed XML root element.
        ns: Namespace dict.
        language: Primary template language.

    Returns:
        List of issue dicts.
    """
    issues: list[IssueData] = []
    issues.extend(analyze_concept_path(root, ns))
    issues.extend(detect_renamed_nodes(root, ns, language))
    issues.extend(detect_flat_path_collisions(root, ns, language))
    return issues
