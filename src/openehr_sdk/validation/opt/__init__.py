"""OPT (Operational Template) validation for openEHR.

Validates OPT 1.4 XML files for well-formedness, semantic integrity,
structural issues, and FLAT path impact before upload to a CDR.

Example:
    >>> from openehr_sdk.validation.opt import OPTValidator
    >>>
    >>> validator = OPTValidator()
    >>> result = validator.validate_file("path/to/template.opt")
    >>> if not result.is_valid:
    ...     for issue in result.issues:
    ...         if issue.severity == "error":
    ...             print(f"[{issue.code}] {issue.message}")
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal

import defusedxml.ElementTree as DefusedET  # noqa: N817

# Re-export issue codes for convenient access
from . import issue_codes  # noqa: F401
from .flat_impact import run_flat_impact_checks
from .semantic_checks import run_semantic_checks
from .structural_checks import run_structural_checks
from .xml_checks import OPT_NAMESPACE, run_xml_checks


@dataclass
class OPTValidationIssue:
    """A single validation issue found in an OPT file."""

    severity: Literal["error", "warning", "info"]
    category: Literal["wellformedness", "semantic", "structural", "flat_impact"]
    code: str
    message: str
    xpath: str | None = None
    node_id: str | None = None
    archetype_id: str | None = None
    suggestion: str | None = None


@dataclass
class OPTValidationResult:
    """Result of validating an OPT file."""

    is_valid: bool
    template_id: str | None
    concept: str | None
    issues: list[OPTValidationIssue] = field(default_factory=list)
    node_count: int = 0
    archetype_count: int = 0

    @property
    def error_count(self) -> int:
        """Number of error-severity issues."""
        return sum(1 for i in self.issues if i.severity == "error")

    @property
    def warning_count(self) -> int:
        """Number of warning-severity issues."""
        return sum(1 for i in self.issues if i.severity == "warning")

    @property
    def errors(self) -> list[OPTValidationIssue]:
        """All error-severity issues."""
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> list[OPTValidationIssue]:
        """All warning-severity issues."""
        return [i for i in self.issues if i.severity == "warning"]

    def to_dict(self) -> dict[str, object]:
        """Convert result to a plain dict (for JSON serialization)."""
        return {
            "is_valid": self.is_valid,
            "template_id": self.template_id,
            "concept": self.concept,
            "node_count": self.node_count,
            "archetype_count": self.archetype_count,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "issues": [asdict(i) for i in self.issues],
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize result to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


class OPTValidationError(Exception):
    """Raised when OPT validation finds errors.

    Attributes:
        result: The full validation result.
    """

    def __init__(self, result: OPTValidationResult) -> None:
        self.result = result
        error_count = result.error_count
        super().__init__(
            f"OPT validation failed with {error_count} error(s). "
            f"Template: {result.template_id or '(unknown)'}"
        )


class OPTValidator:
    """Validates OPT 1.4 XML files.

    Runs four categories of checks:
    - Category A: XML well-formedness (errors)
    - Category B: Semantic integrity (errors)
    - Category C: Structural warnings
    - Category D: FLAT path impact analysis (info/warnings)

    Example:
        >>> validator = OPTValidator()
        >>> result = validator.validate_file("template.opt")
        >>> print(result.is_valid)
        True
    """

    def __init__(self) -> None:
        self._ns = {
            "opt": OPT_NAMESPACE,
            "xsi": "http://www.w3.org/2001/XMLSchema-instance",
        }

    def validate_file(self, path: Path | str) -> OPTValidationResult:
        """Validate an OPT file from disk.

        Args:
            path: Path to the OPT XML file.

        Returns:
            Validation result with all issues found.
        """
        path = Path(path)
        xml_bytes = path.read_bytes()

        try:
            root = DefusedET.fromstring(xml_bytes)
        except DefusedET.ParseError as e:
            from .issue_codes import XML_INVALID

            return OPTValidationResult(
                is_valid=False,
                template_id=None,
                concept=None,
                issues=[
                    OPTValidationIssue(
                        severity="error",
                        category="wellformedness",
                        code=XML_INVALID,
                        message=f"File is not valid XML: {e}",
                    )
                ],
            )

        return self._validate_root(root, xml_bytes=xml_bytes)

    def validate_string(self, xml_content: str) -> OPTValidationResult:
        """Validate an OPT from an XML string.

        Args:
            xml_content: OPT XML content as string.

        Returns:
            Validation result with all issues found.
        """
        xml_bytes = xml_content.encode("utf-8")

        try:
            root = DefusedET.fromstring(xml_content)
        except DefusedET.ParseError as e:
            from .issue_codes import XML_INVALID

            return OPTValidationResult(
                is_valid=False,
                template_id=None,
                concept=None,
                issues=[
                    OPTValidationIssue(
                        severity="error",
                        category="wellformedness",
                        code=XML_INVALID,
                        message=f"XML is not well-formed: {e}",
                    )
                ],
            )

        return self._validate_root(root, xml_bytes=xml_bytes)

    def _validate_root(
        self,
        root: object,
        xml_bytes: bytes | None = None,
    ) -> OPTValidationResult:
        """Run all validation checks on a parsed XML root element."""
        from xml.etree.ElementTree import Element

        if not isinstance(root, Element):
            raise TypeError(f"Expected Element, got {type(root)}")

        # Detect namespace
        ns = dict(self._ns)
        if root.tag.startswith("{"):
            detected_ns = root.tag[1:].split("}")[0]
            if "openehr.org" in detected_ns:
                ns["opt"] = detected_ns

        # Extract template metadata
        template_id = self._find_text(root, "template_id/value", ns)
        concept = self._find_text(root, "concept", ns)
        language = self._find_text(root, "language/code_string", ns) or "en"

        # Count nodes and archetypes
        node_count, archetype_count = self._count_nodes(root)

        # Run all check categories
        raw_issues: list[dict[str, str | None]] = []

        raw_issues.extend(run_xml_checks(root, ns, xml_bytes))
        raw_issues.extend(run_semantic_checks(root, ns, language))
        raw_issues.extend(run_structural_checks(root, ns))
        raw_issues.extend(run_flat_impact_checks(root, ns, language))

        # Convert to typed issues
        issues = [
            OPTValidationIssue(
                severity=d.get("severity", "error"),  # type: ignore[arg-type]
                category=d.get("category", "wellformedness"),  # type: ignore[arg-type]
                code=d.get("code", "UNKNOWN") or "UNKNOWN",
                message=d.get("message", "") or "",
                xpath=d.get("xpath"),
                node_id=d.get("node_id"),
                archetype_id=d.get("archetype_id"),
                suggestion=d.get("suggestion"),
            )
            for d in raw_issues
        ]

        is_valid = not any(i.severity == "error" for i in issues)

        return OPTValidationResult(
            is_valid=is_valid,
            template_id=template_id,
            concept=concept,
            issues=issues,
            node_count=node_count,
            archetype_count=archetype_count,
        )

    def _find_text(self, element: object, path: str, ns: dict[str, str]) -> str | None:
        """Find text at a path, trying with and without namespace."""
        from xml.etree.ElementTree import Element

        if not isinstance(element, Element):
            return None

        ns_path = "/".join(
            f"opt:{p}" if p and not p.startswith(".") and ":" not in p else p
            for p in path.split("/")
        )
        el = element.find(ns_path, ns)
        if el is not None and el.text:
            return el.text.strip()
        el = element.find(path)
        if el is not None and el.text:
            return el.text.strip()
        return None

    def _count_nodes(self, root: object) -> tuple[int, int]:
        """Count total nodes and distinct archetypes."""
        from xml.etree.ElementTree import Element

        if not isinstance(root, Element):
            return (0, 0)

        node_count = 0
        archetypes: set[str] = set()

        for el in root.iter():
            tag = el.tag
            if isinstance(tag, str):
                local = tag.split("}")[-1] if "}" in tag else tag
                if local == "node_id" and el.text and el.text.strip():
                    node_count += 1
                elif local == "value" and el.text and el.text.strip():
                    text = el.text.strip()
                    if text.startswith("openEHR-"):
                        archetypes.add(text)

        return (node_count, len(archetypes))


__all__ = [
    "OPTValidationError",
    "OPTValidationIssue",
    "OPTValidationResult",
    "OPTValidator",
    "issue_codes",
]
