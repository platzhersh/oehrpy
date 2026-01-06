"""
Template builders and OPT parsing for openEHR.

This module provides:
- OPT (Operational Template) XML parser
- Template-specific composition builders
- Pre-built builders for common templates
- OPT-to-Builder code generator
"""

from .builder_generator import (
    BuilderGenerator,
    generate_builder_from_opt,
)
from .builders import (
    TemplateBuilder,
    VitalSignsBuilder,
)
from .opt_parser import (
    ArchetypeNode,
    ConstraintDefinition,
    OPTParser,
    TemplateDefinition,
    parse_opt,
)

__all__ = [
    # OPT Parser
    "OPTParser",
    "TemplateDefinition",
    "ArchetypeNode",
    "ConstraintDefinition",
    "parse_opt",
    # Builder Generator
    "BuilderGenerator",
    "generate_builder_from_opt",
    # Builders
    "TemplateBuilder",
    "VitalSignsBuilder",
]
