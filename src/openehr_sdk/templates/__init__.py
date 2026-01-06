"""
Template builders and OPT parsing for openEHR.

This module provides:
- OPT (Operational Template) XML parser
- Template-specific composition builders
- Pre-built builders for common templates
"""

from .builders import (
    TemplateBuilder,
    VitalSignsBuilder,
)
from .opt_parser import (
    ArchetypeNode,
    ConstraintDefinition,
    OPTParser,
    TemplateDefinition,
)

__all__ = [
    # OPT Parser
    "OPTParser",
    "TemplateDefinition",
    "ArchetypeNode",
    "ConstraintDefinition",
    # Builders
    "TemplateBuilder",
    "VitalSignsBuilder",
]
