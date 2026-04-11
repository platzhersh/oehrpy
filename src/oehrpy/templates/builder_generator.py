"""
Generate template metadata classes from OPT files.

This module extracts metadata from parsed OPT (Operational Template) files and
generates Python class skeletons.  It does **not** generate FLAT path strings,
because FLAT paths cannot be reliably derived from OPT XML — they must come
from the Web Template JSON provided by the CDR (see ADR-0005).

The generated class includes:
- Template ID
- Concept name and description
- List of discovered archetypes (for documentation only)

To produce a fully functional builder with correct FLAT paths, use the Web
Template JSON as input instead (a future version of this generator may accept
Web Template JSON directly).

Example:
    >>> from oehrpy.templates.opt_parser import parse_opt
    >>> from oehrpy.templates.builder_generator import BuilderGenerator
    >>>
    >>> template = parse_opt("vital_signs.opt")
    >>> generator = BuilderGenerator()
    >>> code = generator.generate(template)
    >>> print(code)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .opt_parser import ArchetypeNode, TemplateDefinition


@dataclass
class ObservationMetadata:
    """Metadata extracted from an OBSERVATION archetype.

    This is informational only — it does not contain FLAT paths.
    FLAT paths must be sourced from the Web Template (see ADR-0005).
    """

    archetype_id: str
    node_id: str
    name: str
    short_name: str  # For documentation (e.g., "blood_pressure")
    rm_type: str = "OBSERVATION"
    elements: list[ElementMetadata] = field(default_factory=list)


@dataclass
class ElementMetadata:
    """Metadata for an ELEMENT within an observation."""

    name: str
    node_id: str
    rm_type: str = "DV_QUANTITY"  # Default to quantity


class BuilderGenerator:
    """Generate builder class skeletons from OPT templates.

    The generated output contains template metadata and a class that extends
    ``TemplateBuilder``.  It does **not** contain FLAT path strings because
    these cannot be reliably derived from OPT XML (see ADR-0005).

    To build a fully functional builder, supplement the generated skeleton
    with FLAT paths obtained from the Web Template JSON.
    """

    def __init__(self) -> None:
        """Initialize the builder generator."""
        self._observations: list[ObservationMetadata] = []
        self._template: TemplateDefinition | None = None

    def generate(self, template: TemplateDefinition, class_name: str | None = None) -> str:
        """Generate a builder class skeleton from a template.

        The generated code includes the class definition with ``template_id``
        and a docstring listing discovered archetypes, but no ``add_*``
        methods with FLAT paths.

        Args:
            template: Parsed template definition.
            class_name: Optional custom class name (defaults to derived name).

        Returns:
            Python source code for the builder class skeleton.
        """
        self._template = template

        if class_name is None:
            class_name = self._derive_class_name(template.template_id)

        # Extract observations for documentation
        self._observations = self._extract_observations(template)

        imports = self._generate_imports()
        class_def = self._generate_class_definition(template, class_name)

        return f"""{imports}

{class_def}"""

    def generate_to_file(
        self, template: TemplateDefinition, output_path: Path | str, class_name: str | None = None
    ) -> None:
        """Generate builder class skeleton and write to file.

        Args:
            template: Parsed template definition.
            output_path: Path to write the generated Python file.
            class_name: Optional custom class name.
        """
        code = self.generate(template, class_name)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(code)

    def _derive_class_name(self, template_id: str) -> str:
        """Derive a Python class name from template ID.

        Examples:
            "IDCR - Vital Signs Encounter.v1" -> "VitalSignsEncounterBuilder"
            "Problem List.v1" -> "ProblemListBuilder"
        """
        # Remove version suffix
        name = re.sub(r"\.v\d+$", "", template_id)
        # Remove common prefixes
        name = re.sub(r"^(IDCR|openEHR)\s*-\s*", "", name, flags=re.IGNORECASE)
        # Convert to PascalCase
        words = re.findall(r"[A-Za-z0-9]+", name)
        pascal = "".join(word.capitalize() for word in words)
        return f"{pascal}Builder"

    def _derive_short_name(self, text: str) -> str:
        """Derive a Python identifier from text.

        Examples:
            "Blood Pressure" -> "blood_pressure"
            "Pulse/Heart Beat" -> "pulse_heart_beat"
        """
        # Replace non-alphanumeric with spaces
        text = re.sub(r"[^A-Za-z0-9]+", " ", text)
        # Convert to snake_case
        words = text.lower().split()
        return "_".join(words)

    def _extract_observations(self, template: TemplateDefinition) -> list[ObservationMetadata]:
        """Extract all OBSERVATION archetypes from the template."""
        observations = []

        for node in template.list_observations():
            obs = self._extract_observation_metadata(node)
            if obs:
                observations.append(obs)

        return observations

    def _extract_observation_metadata(self, node: ArchetypeNode) -> ObservationMetadata | None:
        """Extract metadata from an OBSERVATION node."""
        if not node.archetype_id:
            return None

        # Derive names from archetype ID
        # e.g., "openEHR-EHR-OBSERVATION.blood_pressure.v1" -> "blood_pressure"
        archetype_parts = node.archetype_id.split(".")
        if len(archetype_parts) >= 2:
            short_name = archetype_parts[-2]  # e.g., "blood_pressure"
        else:
            short_name = self._derive_short_name(node.name)

        # Extract elements (data points like systolic, diastolic, rate, etc.)
        elements = self._extract_elements(node)

        return ObservationMetadata(
            archetype_id=node.archetype_id,
            node_id=node.node_id,
            name=node.name,
            short_name=short_name,
            rm_type=node.rm_type,
            elements=elements,
        )

    def _extract_elements(self, obs_node: ArchetypeNode) -> list[ElementMetadata]:
        """Extract ELEMENT nodes from an observation.

        This traverses the OBSERVATION -> HISTORY -> EVENT -> ITEM_TREE -> ELEMENT path.
        """
        elements = []

        def traverse(node: ArchetypeNode, depth: int = 0) -> None:
            """Recursively find ELEMENT nodes."""
            if node.rm_type == "ELEMENT" and node.name:
                element = ElementMetadata(
                    name=node.name,
                    node_id=node.node_id,
                    rm_type="DV_QUANTITY",  # Default assumption
                )
                elements.append(element)

            for child in node.children:
                traverse(child, depth + 1)

        traverse(obs_node)
        return elements

    def _generate_imports(self) -> str:
        """Generate import statements."""
        return '''"""
Generated template builder skeleton from OPT file.

This file was auto-generated. FLAT path strings are NOT included because
they cannot be reliably derived from OPT XML. Use the Web Template JSON
from the CDR to obtain correct FLAT paths (see ADR-0005).
"""

from __future__ import annotations

from .builders import TemplateBuilder'''

    def _generate_class_definition(self, template: TemplateDefinition, class_name: str) -> str:
        """Generate the class definition with metadata only."""
        doc = template.description or "Template builder skeleton"
        template_id = template.template_id

        # Build archetype list for documentation
        archetype_lines = ""
        if self._observations:
            archetype_lines = "\n    Discovered archetypes (from OPT):\n"
            for obs in self._observations:
                archetype_lines += f"        - {obs.archetype_id} ({obs.name})\n"

        return f'''

class {class_name}(TemplateBuilder):
    """Builder skeleton for {template.concept}.

    {doc}

    Template ID: {template_id}
{archetype_lines}
    .. note::

        This skeleton does not contain ``add_*`` methods with FLAT paths.
        FLAT paths must be sourced from the Web Template JSON, not the OPT
        (see ADR-0005).  Extend this class and add methods using paths
        obtained from ``EHRBaseClient.get_web_template()``.
    """

    template_id = "{template_id}"'''


def generate_builder_from_opt(
    opt_path: Path | str,
    output_path: Path | str | None = None,
    class_name: str | None = None,
    *,
    validate: bool = False,
) -> str:
    """Generate a builder class skeleton from an OPT file.

    The generated code contains template metadata (ID, concept, archetypes)
    but does **not** contain FLAT path strings.  FLAT paths cannot be
    reliably derived from OPT XML and must come from the Web Template JSON
    (see ADR-0005).

    Args:
        opt_path: Path to the OPT XML file.
        output_path: Optional path to write the generated code.
        class_name: Optional custom class name.
        validate: If True, validate the OPT before generating.
            Raises OPTValidationError if validation errors are found.

    Returns:
        Generated Python source code.

    Raises:
        oehrpy.validation.opt.OPTValidationError: If validate=True
            and the OPT has validation errors.
    """
    if validate:
        from oehrpy.validation.opt import OPTValidationError, OPTValidator

        validator = OPTValidator()
        result = validator.validate_file(opt_path)
        if not result.is_valid:
            raise OPTValidationError(result)

    from .opt_parser import parse_opt

    template = parse_opt(opt_path)
    generator = BuilderGenerator()

    code = generator.generate(template, class_name)

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(code)

    return code
