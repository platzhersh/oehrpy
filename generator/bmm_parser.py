"""
BMM (Basic Meta-Model) JSON parser for openEHR specifications.

This module parses BMM JSON files from the openEHR specifications-ITS-BMM
repository and creates an internal representation of the type hierarchy.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class BmmGenericParameter:
    """Generic type parameter definition."""

    name: str
    conforms_to_type: str | None = None


@dataclass
class BmmTypeRef:
    """Reference to a type, which may be simple, generic, or a container."""

    type_name: str | None = None
    root_type: str | None = None
    generic_parameters: list[str] = field(default_factory=list)
    container_type: str | None = None
    nested_type_def: BmmTypeRef | None = None

    @property
    def resolved_type_name(self) -> str:
        """Get the base type name for this reference."""
        if self.type_name:
            return self.type_name
        if self.root_type:
            return self.root_type
        if self.nested_type_def:
            return self.nested_type_def.resolved_type_name
        return "Any"

    @property
    def is_container(self) -> bool:
        """Check if this is a container type (List, Set, etc.)."""
        return self.container_type is not None

    def __repr__(self) -> str:
        if self.container_type:
            inner = self.nested_type_def or self.type_name or "?"
            return f"{self.container_type}[{inner}]"
        if self.root_type and self.generic_parameters:
            params = ", ".join(self.generic_parameters)
            return f"{self.root_type}[{params}]"
        return self.type_name or self.root_type or "?"


@dataclass
class BmmProperty:
    """Property definition within a BMM class."""

    name: str
    type_ref: BmmTypeRef
    is_mandatory: bool = False
    is_computed: bool = False
    documentation: str | None = None
    cardinality_lower: int | None = None
    cardinality_upper: int | None = None
    cardinality_upper_unbounded: bool = False


@dataclass
class BmmClass:
    """BMM class definition."""

    name: str
    ancestors: list[str] = field(default_factory=list)
    properties: dict[str, BmmProperty] = field(default_factory=dict)
    is_abstract: bool = False
    documentation: str | None = None
    source_schema_id: str | None = None
    generic_parameters: dict[str, BmmGenericParameter] = field(default_factory=dict)
    is_primitive: bool = False


@dataclass
class BmmSchema:
    """Parsed BMM schema containing all classes."""

    schema_name: str
    rm_publisher: str
    rm_release: str
    primitive_types: dict[str, BmmClass] = field(default_factory=dict)
    class_definitions: dict[str, BmmClass] = field(default_factory=dict)
    includes: list[str] = field(default_factory=list)

    @property
    def all_classes(self) -> dict[str, BmmClass]:
        """Get all classes including primitives."""
        return {**self.primitive_types, **self.class_definitions}

    def get_class(self, name: str) -> BmmClass | None:
        """Get a class by name."""
        return self.class_definitions.get(name) or self.primitive_types.get(name)


class BmmParser:
    """Parser for BMM JSON files."""

    # Primitive types that map directly to Python built-in types
    PRIMITIVE_TYPE_MAP: dict[str, str] = {
        "Any": "Any",
        "Boolean": "bool",
        "Integer": "int",
        "Integer64": "int",
        "Real": "float",
        "Double": "float",
        "String": "str",
        "Character": "str",
        "Byte": "bytes",
        "Octet": "bytes",
        "Uri": "str",
    }

    def __init__(self) -> None:
        self._schemas: dict[str, BmmSchema] = {}

    def parse_file(self, path: Path) -> BmmSchema:
        """Parse a BMM JSON file and return the schema."""
        with open(path) as f:
            data = json.load(f)
        return self._parse_schema(data)

    def parse_directory(self, path: Path, pattern: str = "*.bmm.json") -> list[BmmSchema]:
        """Parse all BMM JSON files in a directory."""
        schemas = []
        for file_path in path.glob(pattern):
            schema = self.parse_file(file_path)
            schemas.append(schema)
            self._schemas[schema.schema_name] = schema
        return schemas

    def _parse_schema(self, data: dict[str, Any]) -> BmmSchema:
        """Parse a BMM schema from JSON data."""
        schema = BmmSchema(
            schema_name=data.get("schema_name", "unknown"),
            rm_publisher=data.get("rm_publisher", ""),
            rm_release=data.get("rm_release", ""),
        )

        # Parse includes
        for inc in data.get("includes", []):
            if isinstance(inc, dict) and "id" in inc:
                schema.includes.append(inc["id"])
            elif isinstance(inc, str):
                schema.includes.append(inc)

        # Parse primitive types
        for name, type_data in data.get("primitive_types", {}).items():
            bmm_class = self._parse_class(type_data, is_primitive=True)
            schema.primitive_types[name] = bmm_class

        # Parse class definitions
        for name, class_data in data.get("class_definitions", {}).items():
            bmm_class = self._parse_class(class_data, is_primitive=False)
            schema.class_definitions[name] = bmm_class

        return schema

    def _parse_class(self, data: dict[str, Any], is_primitive: bool = False) -> BmmClass:
        """Parse a BMM class definition."""
        bmm_class = BmmClass(
            name=data.get("name", ""),
            ancestors=data.get("ancestors", []),
            is_abstract=data.get("is_abstract", False),
            documentation=data.get("documentation"),
            source_schema_id=data.get("source_schema_id"),
            is_primitive=is_primitive,
        )

        # Parse generic parameters
        for param_name, param_data in data.get("generic_parameter_defs", {}).items():
            bmm_class.generic_parameters[param_name] = BmmGenericParameter(
                name=param_data.get("name", param_name),
                conforms_to_type=param_data.get("conforms_to_type"),
            )

        # Parse properties
        for prop_name, prop_data in data.get("properties", {}).items():
            prop = self._parse_property(prop_data)
            bmm_class.properties[prop_name] = prop

        return bmm_class

    def _parse_property(self, data: dict[str, Any]) -> BmmProperty:
        """Parse a BMM property definition."""
        prop = BmmProperty(
            name=data.get("name", ""),
            type_ref=self._parse_type_ref(data),
            is_mandatory=data.get("is_mandatory", False),
            is_computed=data.get("is_computed", False),
            documentation=data.get("documentation"),
        )

        # Parse cardinality
        card = data.get("cardinality", {})
        if card:
            prop.cardinality_lower = card.get("lower")
            prop.cardinality_upper = card.get("upper")
            prop.cardinality_upper_unbounded = card.get("upper_unbounded", False)

        return prop

    def _parse_type_ref(self, data: dict[str, Any]) -> BmmTypeRef:
        """Parse a type reference from property data."""
        # Simple type reference
        if "type" in data and isinstance(data["type"], str):
            return BmmTypeRef(type_name=data["type"])

        # Complex type definition
        type_def = data.get("type_def", {})
        if not type_def:
            # Check if type is a dict (shouldn't happen but handle it)
            if "type" in data and isinstance(data["type"], dict):
                type_def = data["type"]
            else:
                return BmmTypeRef(type_name="Any")

        return self._parse_type_def(type_def)

    def _parse_type_def(self, type_def: dict[str, Any]) -> BmmTypeRef:
        """Parse a complex type definition."""
        ref = BmmTypeRef()

        # Container type (List, Set, etc.)
        if "container_type" in type_def:
            ref.container_type = type_def["container_type"]

            # Nested type can be either direct 'type' or another 'type_def'
            if "type" in type_def:
                ref.type_name = type_def["type"]
            elif "type_def" in type_def:
                ref.nested_type_def = self._parse_type_def(type_def["type_def"])

        # Generic type (e.g., DV_INTERVAL<DV_QUANTITY>)
        if "root_type" in type_def:
            ref.root_type = type_def["root_type"]
            ref.generic_parameters = type_def.get("generic_parameters", [])

        # Simple type in type_def
        if "type" in type_def and not ref.container_type:
            ref.type_name = type_def["type"]

        return ref


def load_rm_schema(bmm_path: Path | None = None) -> BmmSchema:
    """Load the openEHR RM 1.0.4 schema.

    Args:
        bmm_path: Path to the BMM JSON directory. Defaults to the bundled BMM files.

    Returns:
        A merged BmmSchema containing all RM classes.
    """
    if bmm_path is None:
        # Use bundled BMM files
        bmm_path = (
            Path(__file__).parent
            / "bmm"
            / "specifications-ITS-BMM"
            / "components"
            / "RM"
            / "Release-1.0.4"
            / "json"
        )

    parser = BmmParser()

    # Parse the main EHR schema (contains all types due to flattening)
    ehr_schema = parser.parse_file(bmm_path / "openehr_rm_ehr_1.0.4.bmm.json")

    return ehr_schema


if __name__ == "__main__":
    # Test the parser
    schema = load_rm_schema()
    print(f"Loaded schema: {schema.schema_name}")
    print(f"Primitive types: {len(schema.primitive_types)}")
    print(f"Class definitions: {len(schema.class_definitions)}")
    print(f"Total classes: {len(schema.all_classes)}")
    print()
    print("Sample classes:")
    for name in ["DV_QUANTITY", "COMPOSITION", "OBSERVATION", "LOCATABLE"]:
        cls = schema.get_class(name)
        if cls:
            print(
                f"  {name}: ancestors={cls.ancestors}, props={list(cls.properties.keys())[:5]}..."
            )
