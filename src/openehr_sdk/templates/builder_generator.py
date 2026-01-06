"""
Generate template-specific builder classes from OPT files.

This module generates type-safe Python builder classes from parsed OPT
(Operational Template) files, eliminating the need for manual FLAT path construction.

Example:
    >>> from openehr_sdk.templates.opt_parser import parse_opt
    >>> from openehr_sdk.templates.builder_generator import BuilderGenerator
    >>>
    >>> template = parse_opt("vital_signs.opt")
    >>> generator = BuilderGenerator()
    >>> code = generator.generate(template)
    >>> print(code)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .opt_parser import ArchetypeNode, TemplateDefinition


@dataclass
class ObservationMetadata:
    """Metadata extracted from an OBSERVATION archetype."""

    archetype_id: str
    node_id: str
    name: str
    short_name: str  # For method/variable names (e.g., "blood_pressure")
    flat_path: str  # Base FLAT path (e.g., "vital_signs/blood_pressure")
    elements: list[ElementMetadata]


@dataclass
class ElementMetadata:
    """Metadata for an ELEMENT within an observation."""

    name: str
    node_id: str
    rm_type: str = "DV_QUANTITY"  # Default to quantity
    unit: str | None = None


class BuilderGenerator:
    """Generate builder classes from OPT templates."""

    def __init__(self) -> None:
        """Initialize the builder generator."""
        self._observations: list[ObservationMetadata] = []
        self._template: TemplateDefinition | None = None

    def generate(self, template: TemplateDefinition, class_name: str | None = None) -> str:
        """Generate a complete builder class from a template.

        Args:
            template: Parsed template definition.
            class_name: Optional custom class name (defaults to derived name).

        Returns:
            Python source code for the builder class.
        """
        # Store template for use in path generation
        self._template = template

        if class_name is None:
            class_name = self._derive_class_name(template.template_id)

        # Extract observations from template
        self._observations = self._extract_observations(template)

        # Generate code sections
        imports = self._generate_imports()
        class_def = self._generate_class_definition(template, class_name)
        methods = self._generate_methods()

        return f"""{imports}

{class_def}
{methods}"""

    def generate_to_file(
        self, template: TemplateDefinition, output_path: Path | str, class_name: str | None = None
    ) -> None:
        """Generate builder class and write to file.

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

        # Build FLAT path (simplified - assumes composition root)
        flat_path = self._build_flat_path(node, short_name)

        # Extract elements (data points like systolic, diastolic, rate, etc.)
        elements = self._extract_elements(node)

        return ObservationMetadata(
            archetype_id=node.archetype_id,
            node_id=node.node_id,
            name=node.name,
            short_name=short_name,
            flat_path=flat_path,
            elements=elements,
        )

    def _build_flat_path(self, node: ArchetypeNode, short_name: str) -> str:
        """Build the FLAT format path prefix for an observation.

        Derives the composition name from the template to build correct paths.
        """
        # Derive composition name from template
        composition_name = self._derive_composition_name()

        # Standard pattern: "composition_name/observation_name"
        return f"{composition_name}/{short_name}"

    def _derive_composition_name(self) -> str:
        """Derive the composition name from the template.

        Uses the template concept or template_id to create a snake_case name.
        """
        if not self._template:
            return "composition"

        # Use concept if available, otherwise template_id
        name = self._template.concept or self._template.template_id

        # Remove common prefixes and suffixes
        name = re.sub(r"\s+(composition|encounter|template)$", "", name, flags=re.IGNORECASE)
        name = re.sub(r"^(IDCR|openEHR)\s*-\s*", "", name, flags=re.IGNORECASE)

        # Convert to snake_case
        return self._derive_short_name(name)

    def _extract_elements(self, obs_node: ArchetypeNode) -> list[ElementMetadata]:
        """Extract ELEMENT nodes from an observation.

        This traverses the OBSERVATION -> HISTORY -> EVENT -> ITEM_TREE -> ELEMENT path.
        """
        elements = []

        def traverse(node: ArchetypeNode, depth: int = 0) -> None:
            """Recursively find ELEMENT nodes."""
            if node.rm_type == "ELEMENT" and node.name:
                # Found a data element
                element = ElementMetadata(
                    name=node.name,
                    node_id=node.node_id,
                    rm_type="DV_QUANTITY",  # Default assumption
                )
                elements.append(element)

            # Traverse children
            for child in node.children:
                traverse(child, depth + 1)

        traverse(obs_node)
        return elements

    def _generate_imports(self) -> str:
        """Generate import statements."""
        return '''"""
Generated template builder from OPT file.

This file was auto-generated. Do not edit manually.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ..serialization.flat import FlatBuilder
from .builders import TemplateBuilder'''

    def _generate_class_definition(self, template: TemplateDefinition, class_name: str) -> str:
        """Generate the class definition and __init__ method."""
        doc = template.description or "Template builder"
        template_id = template.template_id

        return f'''

class {class_name}(TemplateBuilder):
    """Builder for {template.concept}.

    {doc}

    Template ID: {template_id}
    """

    template_id = "{template_id}"'''

    def _generate_methods(self) -> str:
        """Generate add_* methods for each observation."""
        methods = []

        for obs in self._observations:
            method = self._generate_observation_method(obs)
            methods.append(method)

        return "\n\n".join(methods)

    def _generate_observation_method(self, obs: ObservationMetadata) -> str:
        """Generate an add_* method for a specific observation type."""
        method_name = f"add_{obs.short_name}"

        # Generate parameters from elements
        params = self._generate_method_params(obs.elements)
        param_docs = self._generate_param_docs(obs.elements)

        # Generate method body
        body = self._generate_method_body(obs)

        return f'''
    def {method_name}(
        self,
{params}
        time: datetime | str | None = None,
        event_index: int | None = None,
    ) -> TemplateBuilder:
        """Add a {obs.name} observation.

        Args:
{param_docs}
            time: Measurement time (defaults to now).
            event_index: Optional specific event index.

        Returns:
            Self for method chaining.
        """
{body}
        return self'''

    def _generate_method_params(self, elements: list[ElementMetadata]) -> str:
        """Generate method parameters from elements."""
        if not elements:
            return ""

        params = []
        for elem in elements:
            param_name = self._derive_short_name(elem.name)
            params.append(f"        {param_name}: float,")

        return "\n".join(params)

    def _generate_param_docs(self, elements: list[ElementMetadata]) -> str:
        """Generate parameter documentation."""
        if not elements:
            return ""

        docs = []
        for elem in elements:
            param_name = self._derive_short_name(elem.name)
            docs.append(f"            {param_name}: {elem.name} value.")

        return "\n".join(docs)

    def _generate_method_body(self, obs: ObservationMetadata) -> str:
        """Generate the method body for adding an observation."""
        lines = []

        # Get event index
        lines.append("        if event_index is None:")
        lines.append(f'            event_index = self._next_event_index("{obs.short_name}")')
        lines.append("")

        # Build path prefix
        path_template = f"{obs.flat_path}:{{event_index}}/any_event:{{event_index}}"
        lines.append(f'        prefix = f"{path_template}"')
        lines.append("")

        # Set time
        lines.append("        # Set time")
        lines.append("        time_str = self._format_time(time)")
        lines.append('        self._flat.set(f"{prefix}/time", time_str)')
        lines.append("")

        # Set elements
        if obs.elements:
            lines.append("        # Set measurements")
            for elem in obs.elements:
                elem_name = self._derive_short_name(elem.name)
                elem_path = self._derive_short_name(elem.name)
                # Default unit based on common patterns
                unit = self._guess_unit(elem.name)
                quantity_call = (
                    f"        self._flat.set_quantity("
                    f'f"{{{{prefix}}}}/{elem_path}", {elem_name}, "{unit}")'
                )
                lines.append(quantity_call)

        return "\n".join(lines)

    def _guess_unit(self, element_name: str) -> str:
        """Guess the unit for a data element based on its name."""
        name_lower = element_name.lower()

        # Blood pressure
        if "systolic" in name_lower or "diastolic" in name_lower or "pressure" in name_lower:
            return "mm[Hg]"

        # Heart rate / pulse
        if "rate" in name_lower or "pulse" in name_lower or "heart" in name_lower:
            return "/min"

        # Temperature
        if "temperature" in name_lower or "temp" in name_lower:
            return "Cel"

        # Respiration
        if "respiration" in name_lower or "breathing" in name_lower:
            return "/min"

        # Oxygen saturation
        if "spo2" in name_lower or "saturation" in name_lower or "oxygen" in name_lower:
            return "%"

        # Weight
        if "weight" in name_lower:
            return "kg"

        # Height
        if "height" in name_lower:
            return "cm"

        # Default
        return "1"


def generate_builder_from_opt(
    opt_path: Path | str,
    output_path: Path | str | None = None,
    class_name: str | None = None,
) -> str:
    """Generate a builder class from an OPT file.

    Args:
        opt_path: Path to the OPT XML file.
        output_path: Optional path to write the generated code.
        class_name: Optional custom class name.

    Returns:
        Generated Python source code.
    """
    from .opt_parser import parse_opt

    template = parse_opt(opt_path)
    generator = BuilderGenerator()

    # Generate once
    code = generator.generate(template, class_name)

    # Write to file if requested
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(code)

    return code
