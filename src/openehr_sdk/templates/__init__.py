"""
Template builders and OPT parsing for openEHR.

This module provides:
- OPT (Operational Template) XML parser
- Template-specific composition builders
- Pre-built builders for common templates
"""

from .opt_parser import (
    OPTParser,
    TemplateDefinition,
    ArchetypeNode,
    ConstraintDefinition,
)
from .builders import (
    TemplateBuilder,
    VitalSignsBuilder,
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
