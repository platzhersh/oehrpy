"""Validation for openEHR compositions and templates.

Provides two validators:
- **FlatValidator**: Validates FLAT format compositions against Web Templates
- **OPTValidator**: Validates OPT 1.4 XML templates for well-formedness,
  semantic integrity, and FLAT path impact

Example (FLAT validation):
    >>> from openehr_sdk.validation import FlatValidator
    >>>
    >>> validator = FlatValidator.from_web_template(wt_json, platform="ehrbase")
    >>> result = validator.validate(flat_composition)
    >>> if not result.is_valid:
    ...     for error in result.errors:
    ...         print(f"{error.path}: {error.message}")

Example (OPT validation):
    >>> from openehr_sdk.validation import OPTValidator
    >>>
    >>> validator = OPTValidator()
    >>> result = validator.validate_file("template.opt")
    >>> if not result.is_valid:
    ...     for issue in result.errors:
    ...         print(f"[{issue.code}] {issue.message}")
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from openehr_sdk.validation.opt import (
    OPTValidationError,
    OPTValidationIssue,
    OPTValidationResult,
    OPTValidator,
)
from openehr_sdk.validation.path_checker import (
    ValidationError,
    ValidationInfo,
    ValidationResult,
    validate_composition,
)
from openehr_sdk.validation.platforms import PlatformType
from openehr_sdk.validation.web_template import (
    ParsedWebTemplate,
    WebTemplateNode,
    enumerate_valid_paths,
    parse_web_template,
)

if TYPE_CHECKING:
    from openehr_sdk.client.ehrbase import EHRBaseClient


class FlatValidator:
    """Validates FLAT format compositions against a Web Template.

    Use one of the factory methods to create an instance:

        validator = FlatValidator.from_web_template(wt_json, platform="ehrbase")
        result = validator.validate(flat_composition)
    """

    def __init__(
        self,
        parsed: ParsedWebTemplate,
        platform: PlatformType = "ehrbase",
    ) -> None:
        self._parsed = parsed
        self._platform = platform
        self._valid_paths = enumerate_valid_paths(parsed, platform)

    @classmethod
    def from_web_template(
        cls,
        web_template: dict[str, Any],
        platform: PlatformType = "ehrbase",
    ) -> FlatValidator:
        """Create a validator from a Web Template JSON dict.

        Args:
            web_template: The Web Template JSON (must contain a "tree" key).
            platform: CDR platform dialect ("ehrbase" or "better").
        """
        parsed = parse_web_template(web_template)
        return cls(parsed=parsed, platform=platform)

    @classmethod
    async def from_ehrbase(
        cls,
        client: EHRBaseClient,
        template_id: str,
        platform: PlatformType = "ehrbase",
    ) -> FlatValidator:
        """Create a validator by fetching a Web Template from EHRBase.

        Uses :meth:`EHRBaseClient.get_web_template` which requests the Web
        Template JSON format (``Accept: application/openehr.wt+json``) and
        caches the result (see ADR-0005).

        Args:
            client: An EHRBaseClient instance.
            template_id: The template ID to fetch.
            platform: CDR platform dialect.
        """
        web_template = await client.get_web_template(template_id)
        return cls.from_web_template(web_template, platform=platform)

    @property
    def template_id(self) -> str:
        """The template ID from the Web Template."""
        return self._parsed.template_id

    @property
    def tree_id(self) -> str:
        """The tree root ID (composition prefix)."""
        return self._parsed.tree_id

    @property
    def platform(self) -> PlatformType:
        """The CDR platform dialect."""
        return self._platform

    @property
    def valid_paths(self) -> list[str]:
        """All valid FLAT paths for this template and platform."""
        return list(self._valid_paths)

    def validate(self, flat_composition: dict[str, object]) -> ValidationResult:
        """Validate a FLAT composition dict.

        Args:
            flat_composition: A dict mapping FLAT paths to values.

        Returns:
            A ValidationResult with errors and warnings.
        """
        return validate_composition(flat_composition, self._parsed, self._platform)


__all__ = [
    # OPT validation
    "OPTValidationError",
    "OPTValidationIssue",
    "OPTValidationResult",
    "OPTValidator",
    # FLAT validation
    "FlatValidator",
    "ParsedWebTemplate",
    "ValidationError",
    "ValidationInfo",
    "ValidationResult",
    "WebTemplateNode",
    "enumerate_valid_paths",
    "parse_web_template",
]
