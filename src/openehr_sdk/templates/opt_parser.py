"""
OPT (Operational Template) XML parser.

This module parses OPT 1.4 XML files to extract template definitions,
archetype constraints, and terminology bindings.

OPT files define the constraints on archetypes used within a specific
clinical template, including:
- Which archetypes are used
- Which nodes are included/excluded
- Terminology bindings
- Default values
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from xml.etree.ElementTree import Element  # For type hints

import defusedxml.ElementTree as ET

# OPT XML Namespaces
NAMESPACES = {
    "opt": "http://schemas.openehr.org/v1",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
}


@dataclass
class TermBinding:
    """Terminology binding for a code."""

    code: str
    terminology_id: str
    value: str | None = None


@dataclass
class ConstraintDefinition:
    """Constraint on a node within a template."""

    node_id: str
    path: str
    rm_type: str
    name: str | None = None
    occurrences_min: int = 0
    occurrences_max: int | None = None  # None means unbounded
    is_mandatory: bool = False
    default_value: Any | None = None
    allowed_values: list[str] = field(default_factory=list)
    term_bindings: list[TermBinding] = field(default_factory=list)

    @property
    def is_multiple(self) -> bool:
        """Check if this node allows multiple occurrences."""
        return self.occurrences_max is None or self.occurrences_max > 1


@dataclass
class ArchetypeNode:
    """Represents an archetype slot in the template."""

    archetype_id: str
    node_id: str
    rm_type: str
    name: str
    path: str
    children: list[ArchetypeNode] = field(default_factory=list)
    constraints: list[ConstraintDefinition] = field(default_factory=list)

    def find_node(self, node_id: str) -> ArchetypeNode | None:
        """Find a child node by ID."""
        for child in self.children:
            if child.node_id == node_id:
                return child
            found = child.find_node(node_id)
            if found:
                return found
        return None

    def get_flat_path(self, child_path: str = "") -> str:
        """Get the FLAT format path for this node."""
        # Convert archetype path to FLAT path
        path = self.path.lstrip("/")
        # Replace archetype node IDs with names
        path = re.sub(r"\[at\d+\]", "", path)
        if child_path:
            return f"{path}/{child_path}"
        return path


@dataclass
class TemplateDefinition:
    """Parsed template definition from OPT file."""

    template_id: str
    concept: str
    description: str | None = None
    language: str = "en"
    archetype_id: str | None = None
    rm_type: str = "COMPOSITION"
    root: ArchetypeNode | None = None
    all_nodes: dict[str, ArchetypeNode] = field(default_factory=dict)

    def get_node(self, path: str) -> ArchetypeNode | None:
        """Get a node by its path."""
        return self.all_nodes.get(path)

    def list_observations(self) -> list[ArchetypeNode]:
        """List all OBSERVATION archetypes in the template."""
        return [n for n in self.all_nodes.values() if n.rm_type == "OBSERVATION"]

    def list_entries(self) -> list[ArchetypeNode]:
        """List all ENTRY archetypes (OBSERVATION, EVALUATION, etc.)."""
        entry_types = {"OBSERVATION", "EVALUATION", "INSTRUCTION", "ACTION", "ADMIN_ENTRY"}
        return [n for n in self.all_nodes.values() if n.rm_type in entry_types]


class OPTParser:
    """Parser for OPT 1.4 XML files."""

    def __init__(self) -> None:
        self._namespaces = NAMESPACES

    def parse_file(self, path: Path | str) -> TemplateDefinition:
        """Parse an OPT file from disk.

        Args:
            path: Path to the OPT XML file.

        Returns:
            Parsed TemplateDefinition.
        """
        tree = ET.parse(path)
        root = tree.getroot()
        if root is None:
            raise ValueError(f"Failed to parse XML from {path}: no root element")
        return self._parse_root(root)

    def parse_string(self, xml_content: str) -> TemplateDefinition:
        """Parse OPT from XML string.

        Args:
            xml_content: OPT XML content.

        Returns:
            Parsed TemplateDefinition.
        """
        root = ET.fromstring(xml_content)
        if root is None:
            raise ValueError("Failed to parse XML string: no root element")
        return self._parse_root(root)

    def _parse_root(self, root: Element) -> TemplateDefinition:
        """Parse the root element of an OPT file."""
        # Handle namespace prefixes
        self._detect_namespaces(root)

        template = TemplateDefinition(
            template_id=self._get_text(root, ".//template_id/value") or "",
            concept=self._get_text(root, ".//concept") or "",
            description=self._get_text(root, ".//description/details/purpose"),
            language=self._get_text(root, ".//language/code_string") or "en",
        )

        # Parse the definition (root archetype)
        definition = root.find("opt:definition", self._namespaces)
        if definition is None:
            # Try without namespace
            definition = root.find(".//definition")

        if definition is not None:
            template.archetype_id = self._get_text(definition, "archetype_id/value")
            xsi_type_key = "{{{}}}type".format(self._namespaces.get("xsi", ""))
            template.rm_type = (
                definition.get(xsi_type_key) or definition.get("type") or "COMPOSITION"
            )
            template.rm_type = template.rm_type.split(":")[-1]  # Remove namespace prefix

            template.root = self._parse_node(definition, "/")
            if template.root:
                self._collect_nodes(template.root, template.all_nodes)

        return template

    def _detect_namespaces(self, root: Element) -> None:
        """Detect namespaces used in the document."""
        # Extract namespace from root element tag
        if root.tag.startswith("{"):
            ns = root.tag[1:].split("}")[0]
            if "openehr.org" in ns or "schemas.openehr.org" in ns:
                self._namespaces["opt"] = ns

        # Also try to extract from attributes
        for key, _value in root.attrib.items():
            if key.startswith("{"):
                ns = key[1:].split("}")[0]
                if "openehr.org" in ns:
                    self._namespaces["opt"] = ns

    def _get_text(self, element: Element, xpath: str) -> str | None:
        """Get text content from xpath, trying with and without namespaces."""
        # Try with namespace prefix in XPath
        if "opt" in self._namespaces:
            # Convert simple xpath to namespaced version
            # .//template_id/value -> .//opt:template_id/opt:value
            parts = xpath.split("/")
            ns_parts = []
            for part in parts:
                if part and not part.startswith(".") and ":" not in part:
                    ns_parts.append(f"opt:{part}")
                else:
                    ns_parts.append(part)
            ns_xpath = "/".join(ns_parts)

            child = element.find(ns_xpath, self._namespaces)
            if child is not None and child.text is not None:
                return child.text.strip()

        # Try with namespace without prefix (for ElementTree default namespace)
        child = element.find(xpath, self._namespaces)
        if child is not None and child.text is not None:
            return child.text.strip()

        # Try without namespace
        child = element.find(xpath)
        if child is not None and child.text is not None:
            return child.text.strip()

        return None

    def _parse_node(self, element: Element, parent_path: str) -> ArchetypeNode | None:
        """Parse an archetype node from an XML element."""
        node_id = self._get_text(element, "node_id") or ""
        archetype_id = self._get_text(element, "archetype_id/value") or ""

        # Get RM type from xsi:type attribute
        rm_type = (
            element.get("{{{}}}type".format(self._namespaces.get("xsi", "")))
            or element.get("type")
            or ""
        )
        rm_type = rm_type.split(":")[-1]  # Remove namespace prefix like "opt:C_ARCHETYPE_ROOT"

        # Map constraint types to RM types
        rm_type_map = {
            "C_ARCHETYPE_ROOT": self._get_rm_type_from_archetype(archetype_id),
            "C_COMPLEX_OBJECT": self._get_text(element, "rm_type_name") or "ITEM",
        }
        if rm_type in rm_type_map:
            rm_type = rm_type_map[rm_type]

        # Get name from ontology or term_definitions
        name = (
            self._get_text(element, "name/value")
            or self._get_term_text(element, node_id)
            or node_id
        )

        path = f"{parent_path}/{node_id}" if node_id else parent_path

        node = ArchetypeNode(
            archetype_id=archetype_id,
            node_id=node_id,
            rm_type=rm_type,
            name=name,
            path=path,
        )

        # Parse child attributes
        attrs_with_ns = element.findall("opt:attributes", self._namespaces)
        attrs_without_ns = element.findall("attributes") if not attrs_with_ns else []
        for attr in attrs_with_ns or attrs_without_ns:
            attr_name = self._get_text(attr, "rm_attribute_name") or ""

            children_with_ns = attr.findall("opt:children", self._namespaces)
            children_without_ns = attr.findall("children") if not children_with_ns else []
            for child in children_with_ns or children_without_ns:
                child_node = self._parse_node(child, f"{path}/{attr_name}")
                if child_node:
                    node.children.append(child_node)

        # Parse constraints
        constraints = self._parse_constraints(element, path)
        node.constraints = constraints

        return node

    def _parse_constraints(self, element: Element, path: str) -> list[ConstraintDefinition]:
        """Parse constraint definitions from an element."""
        constraints = []

        # Parse occurrences
        occ = element.find("opt:occurrences", self._namespaces) or element.find("occurrences")
        if occ is not None:
            lower = self._get_text(occ, "lower") or "0"
            upper = self._get_text(occ, "upper")
            upper_unbounded = self._get_text(occ, "upper_unbounded") == "true"

            constraint = ConstraintDefinition(
                node_id=self._get_text(element, "node_id") or "",
                path=path,
                rm_type=self._get_text(element, "rm_type_name") or "",
                occurrences_min=int(lower),
                occurrences_max=None if upper_unbounded else (int(upper) if upper else None),
            )
            constraint.is_mandatory = constraint.occurrences_min > 0
            constraints.append(constraint)

        return constraints

    def _get_term_text(self, element: Element, node_id: str) -> str | None:
        """Get term text from ontology for a node ID."""
        # This is a simplified implementation - full implementation would
        # look up terms in the ontology section
        return None

    def _get_rm_type_from_archetype(self, archetype_id: str) -> str:
        """Extract RM type from archetype ID."""
        if not archetype_id:
            return "ITEM"

        # Archetype ID format: openEHR-EHR-OBSERVATION.blood_pressure.v1
        parts = archetype_id.split("-")
        if len(parts) >= 3:
            return parts[2].split(".")[0]
        return "ITEM"

    def _collect_nodes(self, node: ArchetypeNode, nodes: dict[str, ArchetypeNode]) -> None:
        """Collect all nodes into a flat dictionary."""
        if node.path:
            nodes[node.path] = node
        for child in node.children:
            self._collect_nodes(child, nodes)


def parse_opt(source: str | Path) -> TemplateDefinition:
    """Convenience function to parse an OPT file.

    Args:
        source: Path to OPT file or XML string.

    Returns:
        Parsed TemplateDefinition.
    """
    parser = OPTParser()
    if isinstance(source, Path) or (isinstance(source, str) and not source.strip().startswith("<")):
        return parser.parse_file(source)
    return parser.parse_string(source)
