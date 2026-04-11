"""
Template builders and OPT parsing for openEHR.

This module provides:
- OPT (Operational Template) XML parser — for metadata extraction only
- Template-specific composition builders with FLAT paths sourced from
  Web Template JSON (see ADR-0005)
- Pre-built builders for common templates (e.g. ``VitalSignsBuilder``)
- OPT-to-Builder skeleton generator (metadata only, no FLAT paths)

.. note::

    FLAT paths are derived exclusively from the Web Template JSON, never
    from OPT XML.  The ``BuilderGenerator`` produces class skeletons
    without FLAT path strings.  See ``docs/adr/0005-*.md`` for details.
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
