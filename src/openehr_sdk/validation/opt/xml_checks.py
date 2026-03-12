"""Category A: XML well-formedness checks for OPT validation.

Validates XML integrity, required fields, archetype ID format,
duplicate node_ids, RM type names, and occurrences constraints.
"""

from __future__ import annotations

import re
from typing import Literal
from xml.etree.ElementTree import Element

from .issue_codes import (
    DUPLICATE_NODE_ID,
    INVALID_ARCHETYPE_ID_FORMAT,
    INVALID_LANGUAGE_CODE,
    INVALID_OCCURRENCES,
    INVALID_RM_TYPE,
    INVALID_ROOT_RM_TYPE,
    INVALID_TEMPLATE_ID_FORMAT,
    MISSING_CONCEPT,
    MISSING_LANGUAGE,
    MISSING_TEMPLATE_ID,
    XML_ENCODING_ISSUE,
    XML_WRONG_NAMESPACE,
)
from .rm_types import KNOWN_RM_TYPES, suggest_rm_type

# OPT 1.4 expected namespace
OPT_NAMESPACE = "http://schemas.openehr.org/v1"

# Archetype ID pattern: openEHR-<originator>-<RM_CLASS>.<concept>.<version>
ARCHETYPE_ID_PATTERN = re.compile(
    r"^openEHR-[A-Z]+-[A-Z][A-Z_]+\.[a-z][a-z0-9_]*(-[a-z][a-z0-9_]*)*\.v\d+$"
)

# Template ID allowed characters
TEMPLATE_ID_PATTERN = re.compile(r"^[a-zA-Z0-9 ._\-]+$")

# ISO 639-1 two-letter language codes (common subset)
ISO_639_1_CODES = frozenset(
    {
        "aa",
        "ab",
        "af",
        "ak",
        "am",
        "an",
        "ar",
        "as",
        "av",
        "ay",
        "az",
        "ba",
        "be",
        "bg",
        "bh",
        "bi",
        "bm",
        "bn",
        "bo",
        "br",
        "bs",
        "ca",
        "ce",
        "ch",
        "co",
        "cr",
        "cs",
        "cu",
        "cv",
        "cy",
        "da",
        "de",
        "dv",
        "dz",
        "ee",
        "el",
        "en",
        "eo",
        "es",
        "et",
        "eu",
        "fa",
        "ff",
        "fi",
        "fj",
        "fo",
        "fr",
        "fy",
        "ga",
        "gd",
        "gl",
        "gn",
        "gu",
        "gv",
        "ha",
        "he",
        "hi",
        "ho",
        "hr",
        "ht",
        "hu",
        "hy",
        "hz",
        "ia",
        "id",
        "ie",
        "ig",
        "ii",
        "ik",
        "io",
        "is",
        "it",
        "iu",
        "ja",
        "jv",
        "ka",
        "kg",
        "ki",
        "kj",
        "kk",
        "kl",
        "km",
        "kn",
        "ko",
        "kr",
        "ks",
        "ku",
        "kv",
        "kw",
        "ky",
        "la",
        "lb",
        "lg",
        "li",
        "ln",
        "lo",
        "lt",
        "lu",
        "lv",
        "mg",
        "mh",
        "mi",
        "mk",
        "ml",
        "mn",
        "mr",
        "ms",
        "mt",
        "my",
        "na",
        "nb",
        "nd",
        "ne",
        "ng",
        "nl",
        "nn",
        "no",
        "nr",
        "nv",
        "ny",
        "oc",
        "oj",
        "om",
        "or",
        "os",
        "pa",
        "pi",
        "pl",
        "ps",
        "pt",
        "qu",
        "rm",
        "rn",
        "ro",
        "ru",
        "rw",
        "sa",
        "sc",
        "sd",
        "se",
        "sg",
        "si",
        "sk",
        "sl",
        "sm",
        "sn",
        "so",
        "sq",
        "sr",
        "ss",
        "st",
        "su",
        "sv",
        "sw",
        "ta",
        "te",
        "tg",
        "th",
        "ti",
        "tk",
        "tl",
        "tn",
        "to",
        "tr",
        "ts",
        "tt",
        "tw",
        "ty",
        "ug",
        "uk",
        "ur",
        "uz",
        "ve",
        "vi",
        "vo",
        "wa",
        "wo",
        "xh",
        "yi",
        "yo",
        "za",
        "zh",
        "zu",
    }
)


IssueData = dict[str, str | None]


def _find_child(element: Element, tag: str) -> Element | None:
    """Find a child element, trying with namespace first then without.

    Uses explicit ``is not None`` checks to avoid the ElementTree gotcha
    where ``bool(element)`` is ``False`` for elements with no children.
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
        "category": "wellformedness",
        "code": code,
        "message": message,
        "xpath": xpath,
        "node_id": node_id,
        "archetype_id": archetype_id,
        "suggestion": suggestion,
    }


def _ns(tag: str) -> str:
    """Wrap a tag name with the OPT namespace."""
    return f"{{{OPT_NAMESPACE}}}{tag}"


def _find_text(element: Element, path: str, ns: dict[str, str]) -> str | None:
    """Find text at a path, trying with and without namespace."""
    # Try with namespace
    ns_path = "/".join(
        f"opt:{p}" if p and not p.startswith(".") and ":" not in p else p for p in path.split("/")
    )
    el = element.find(ns_path, ns)
    if el is not None and el.text:
        return el.text.strip()

    # Try without namespace
    el = element.find(path)
    if el is not None and el.text:
        return el.text.strip()

    return None


def _find_all(element: Element, path: str, ns: dict[str, str]) -> list[Element]:
    """Find all elements at a path, trying with and without namespace."""
    ns_path = "/".join(
        f"opt:{p}" if p and not p.startswith(".") and ":" not in p else p for p in path.split("/")
    )
    results = element.findall(ns_path, ns)
    if not results:
        results = element.findall(path)
    return results


def check_xml_namespace(root: Element) -> list[IssueData]:
    """Check that the root element has the correct OPT namespace."""
    issues: list[IssueData] = []

    tag = root.tag
    # Extract namespace from tag
    if tag.startswith("{"):
        ns = tag[1:].split("}")[0]
        tag_name = tag.split("}")[1]
    else:
        ns = ""
        tag_name = tag

    if tag_name != "template":
        issues.append(
            _make_issue(
                XML_WRONG_NAMESPACE,
                f"Root element is '{tag_name}', expected 'template'.",
                xpath="/",
            )
        )

    if ns and ns != OPT_NAMESPACE:
        issues.append(
            _make_issue(
                XML_WRONG_NAMESPACE,
                f"Root namespace is '{ns}', expected '{OPT_NAMESPACE}'.",
                xpath="/template",
            )
        )

    return issues


def check_encoding(xml_bytes: bytes) -> list[IssueData]:
    """Check for null bytes and invalid characters in XML content."""
    issues: list[IssueData] = []

    if b"\x00" in xml_bytes:
        issues.append(
            _make_issue(
                XML_ENCODING_ISSUE,
                "XML content contains null bytes.",
                xpath="/",
            )
        )

    return issues


def check_required_fields(root: Element, ns: dict[str, str]) -> list[IssueData]:
    """Check that all required top-level OPT fields are present."""
    issues: list[IssueData] = []

    # template_id/value
    template_id = _find_text(root, "template_id/value", ns)
    if not template_id:
        issues.append(
            _make_issue(
                MISSING_TEMPLATE_ID,
                "Required field 'template_id/value' is absent or empty.",
                xpath="/template/template_id/value",
                suggestion="Add a <template_id><value>...</value></template_id> element.",
            )
        )
    else:
        if not TEMPLATE_ID_PATTERN.match(template_id):
            issues.append(
                _make_issue(
                    INVALID_TEMPLATE_ID_FORMAT,
                    f"Template ID '{template_id}' contains invalid characters. "
                    "Allowed: [a-zA-Z0-9 ._-]",
                    xpath="/template/template_id/value",
                )
            )

    # concept
    concept = _find_text(root, "concept", ns)
    if not concept:
        issues.append(
            _make_issue(
                MISSING_CONCEPT,
                "Required field 'concept' is absent or empty.",
                xpath="/template/concept",
                suggestion="Add a <concept>...</concept> element.",
            )
        )

    # language/code_string
    lang_code = _find_text(root, "language/code_string", ns)
    if not lang_code:
        issues.append(
            _make_issue(
                MISSING_LANGUAGE,
                "Required field 'language/code_string' is absent or empty.",
                xpath="/template/language/code_string",
            )
        )
    elif lang_code.lower() not in ISO_639_1_CODES:
        issues.append(
            _make_issue(
                INVALID_LANGUAGE_CODE,
                f"Language code '{lang_code}' is not a valid ISO 639-1 two-letter code.",
                xpath="/template/language/code_string",
            )
        )

    # language/terminology_id/value
    term_id = _find_text(root, "language/terminology_id/value", ns)
    if term_id and term_id != "ISO_639-1":
        issues.append(
            _make_issue(
                INVALID_LANGUAGE_CODE,
                f"Language terminology_id is '{term_id}', expected 'ISO_639-1'.",
                xpath="/template/language/terminology_id/value",
            )
        )

    # definition/rm_type_name must be COMPOSITION
    definition = _find_child(root, "definition")
    if definition is not None:
        rm_type = _find_text(definition, "rm_type_name", ns)
        if rm_type and rm_type != "COMPOSITION":
            issues.append(
                _make_issue(
                    INVALID_ROOT_RM_TYPE,
                    f"Root definition rm_type_name is '{rm_type}', expected 'COMPOSITION'.",
                    xpath="/template/definition/rm_type_name",
                    suggestion="The root definition of an OPT must be a COMPOSITION.",
                )
            )

        # definition/archetype_id/value must start with openEHR-EHR-COMPOSITION
        arch_id = _find_text(definition, "archetype_id/value", ns)
        if arch_id and not arch_id.startswith("openEHR-EHR-COMPOSITION."):
            issues.append(
                _make_issue(
                    INVALID_ARCHETYPE_ID_FORMAT,
                    f"Root archetype_id '{arch_id}' does not start with "
                    "'openEHR-EHR-COMPOSITION.'.",
                    xpath="/template/definition/archetype_id/value",
                )
            )

    return issues


def check_archetype_ids(root: Element, ns: dict[str, str]) -> list[IssueData]:
    """Validate all archetype_id/value elements match the required format."""
    issues: list[IssueData] = []

    # Find all archetype_id/value elements in the tree
    for arch_el in root.iter():
        tag = arch_el.tag
        if isinstance(tag, str):
            local = tag.split("}")[-1] if "}" in tag else tag
            if local == "value":
                text = arch_el.text
                if not text or not text.strip():
                    continue
                text = text.strip()

                # Only check values that look like they could be archetype IDs
                if not text.startswith("openEHR-") and "." in text and "-" in text:
                    # Might be a malformed archetype ID
                    if re.match(r"^[a-zA-Z].*\.[a-zA-Z].*\.v\d+$", text):
                        issues.append(
                            _make_issue(
                                INVALID_ARCHETYPE_ID_FORMAT,
                                f"Archetype ID '{text}' does not follow the "
                                "openEHR-<originator>-<class>.<concept>.<version> format.",
                                archetype_id=text,
                                suggestion="Archetype IDs must start with 'openEHR-'.",
                            )
                        )
                elif text.startswith("openEHR-") and not ARCHETYPE_ID_PATTERN.match(text):
                    issues.append(
                        _make_issue(
                            INVALID_ARCHETYPE_ID_FORMAT,
                            f"Archetype ID '{text}' does not match the required format "
                            "'openEHR-<originator>-<CLASS>.<concept>.<vN>'.",
                            archetype_id=text,
                        )
                    )

    return issues


def check_duplicate_node_ids(root: Element, ns: dict[str, str]) -> list[IssueData]:
    """Detect duplicate node_id values within each archetype scope."""
    issues: list[IssueData] = []

    def _collect_in_scope(
        element: Element,
        current_archetype: str | None,
        scope_node_ids: dict[str, str | None],
    ) -> None:
        """Recursively collect node_ids within archetype scopes."""
        # Check if this element starts a new archetype scope
        arch_id_el = _find_child(element, "archetype_id")
        if arch_id_el is not None:
            val_el = _find_child(arch_id_el, "value")
            if val_el is not None and val_el.text and val_el.text.strip():
                # New archetype scope - start fresh tracking
                new_archetype = val_el.text.strip()
                new_scope: dict[str, str | None] = {}
                # Process this scope's node_id
                _process_node_id(element, new_archetype, new_scope, issues, ns)
                # Recurse into children with the new scope
                for child in element:
                    _collect_in_scope(child, new_archetype, new_scope)
                return

        # Same scope - check node_id
        if current_archetype is not None:
            _process_node_id(element, current_archetype, scope_node_ids, issues, ns)

        # Recurse into children
        for child in element:
            _collect_in_scope(child, current_archetype, scope_node_ids)

    definition = _find_child(root, "definition")
    if definition is not None:
        _collect_in_scope(definition, None, {})

    return issues


def _process_node_id(
    element: Element,
    archetype_id: str,
    scope_ids: dict[str, str | None],
    issues: list[IssueData],
    ns: dict[str, str],
) -> None:
    """Check a single element's node_id for duplicates within its scope."""
    node_id_el = _find_child(element, "node_id")
    if node_id_el is not None and node_id_el.text and node_id_el.text.strip():
        nid = node_id_el.text.strip()
        if not nid:
            return

        if nid in scope_ids:
            issues.append(
                _make_issue(
                    DUPLICATE_NODE_ID,
                    f"Duplicate node_id '{nid}' within archetype scope '{archetype_id}'.",
                    node_id=nid,
                    archetype_id=archetype_id,
                    suggestion="Each node_id must be unique within its archetype scope.",
                )
            )
        else:
            scope_ids[nid] = archetype_id


def check_rm_type_names(root: Element, ns: dict[str, str]) -> list[IssueData]:
    """Validate all rm_type_name values against the RM 1.1.0 type registry."""
    issues: list[IssueData] = []

    for el in root.iter():
        tag = el.tag
        if isinstance(tag, str):
            local = tag.split("}")[-1] if "}" in tag else tag
            if local == "rm_type_name" and el.text and el.text.strip():
                rm_type = el.text.strip()
                if rm_type not in KNOWN_RM_TYPES:
                    suggestion = suggest_rm_type(rm_type)
                    msg = f"rm_type_name '{rm_type}' is not a valid openEHR RM 1.1.0 type."
                    sug = None
                    if suggestion:
                        sug = f"Did you mean '{suggestion}'?"
                    issues.append(
                        _make_issue(
                            INVALID_RM_TYPE,
                            msg,
                            suggestion=sug,
                        )
                    )

    return issues


def check_occurrences(root: Element, ns: dict[str, str]) -> list[IssueData]:
    """Validate occurrences constraints (min <= max, non-negative)."""
    issues: list[IssueData] = []

    for el in root.iter():
        tag = el.tag
        if isinstance(tag, str):
            local = tag.split("}")[-1] if "}" in tag else tag
            if local == "occurrences":
                lower_text = _find_text(el, "lower", ns)
                upper_text = _find_text(el, "upper", ns)
                upper_unbounded = _find_text(el, "upper_unbounded", ns)

                if lower_text is not None:
                    try:
                        lower = int(lower_text)
                    except ValueError:
                        issues.append(
                            _make_issue(
                                INVALID_OCCURRENCES,
                                f"Occurrences lower value '{lower_text}' is not a valid integer.",
                            )
                        )
                        continue

                    if lower < 0:
                        issues.append(
                            _make_issue(
                                INVALID_OCCURRENCES,
                                f"Occurrences lower value {lower} is negative.",
                            )
                        )

                    if upper_text is not None and upper_unbounded != "true":
                        try:
                            upper = int(upper_text)
                        except ValueError:
                            issues.append(
                                _make_issue(
                                    INVALID_OCCURRENCES,
                                    f"Occurrences upper value '{upper_text}' is not a valid integer.",  # noqa: E501
                                )
                            )
                            continue

                        if upper < lower:
                            issues.append(
                                _make_issue(
                                    INVALID_OCCURRENCES,
                                    f"Occurrences min ({lower}) > max ({upper}).",
                                    suggestion="Ensure lower <= upper in occurrences constraints.",
                                )
                            )

    return issues


def run_xml_checks(
    root: Element,
    ns: dict[str, str],
    xml_bytes: bytes | None = None,
) -> list[IssueData]:
    """Run all Category A well-formedness checks.

    Args:
        root: Parsed XML root element.
        ns: Namespace dict for XPath queries.
        xml_bytes: Raw XML bytes for encoding checks (optional).

    Returns:
        List of issue dicts.
    """
    issues: list[IssueData] = []

    if xml_bytes is not None:
        issues.extend(check_encoding(xml_bytes))

    issues.extend(check_xml_namespace(root))
    issues.extend(check_required_fields(root, ns))
    issues.extend(check_archetype_ids(root, ns))
    issues.extend(check_duplicate_node_ids(root, ns))
    issues.extend(check_rm_type_names(root, ns))
    issues.extend(check_occurrences(root, ns))

    return issues
