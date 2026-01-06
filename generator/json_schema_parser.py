"""
JSON Schema parser for openEHR RM specifications.

Parses JSON Schema files from specifications-ITS-JSON repository
and converts them to a format suitable for Pydantic generation.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


@dataclass
class SchemaProperty:
    """Represents a property in a JSON Schema definition."""

    name: str
    type: str | None = None
    ref: str | None = None
    is_array: bool = False
    is_required: bool = False
    const_value: str | None = None
    items_ref: str | None = None


@dataclass
class SchemaDefinition:
    """Represents a class definition from JSON Schema."""

    name: str
    properties: dict[str, SchemaProperty] = field(default_factory=dict)
    required_fields: list[str] = field(default_factory=list)
    type_field_value: str | None = None


class JsonSchemaParser:
    """Parser for openEHR JSON Schema files."""

    def __init__(self, schema_dir: Path):
        """
        Initialize parser with schema directory.

        Args:
            schema_dir: Path to RM Release directory (e.g., Release-1.1.0/)
        """
        self.schema_dir = schema_dir
        self.definitions: dict[str, SchemaDefinition] = {}
        self._load_all_schemas()

    def _load_all_schemas(self) -> None:
        """Load all JSON Schema files from the directory tree."""
        for schema_file in self.schema_dir.rglob("*.json"):
            if schema_file.name == "main.json":
                continue  # Skip main.json (it's a discriminated union)

            try:
                with open(schema_file) as f:
                    schema_data = json.load(f)
                    self._parse_schema_file(schema_data)
            except Exception as e:
                print(f"Warning: Failed to parse {schema_file}: {e}")

    def _parse_schema_file(self, schema_data: dict[str, Any]) -> None:
        """Parse a single JSON Schema file."""
        definitions = schema_data.get("definitions", {})

        for def_name, def_data in definitions.items():
            if def_data.get("type") != "object":
                continue  # Skip non-object definitions

            schema_def = SchemaDefinition(name=def_name)
            schema_def.required_fields = def_data.get("required", [])

            # Parse properties
            properties = def_data.get("properties", {})
            for prop_name, prop_data in properties.items():
                prop = self._parse_property(prop_name, prop_data, schema_def.required_fields)
                schema_def.properties[prop_name] = prop

                # Check for _type field with const value
                if prop_name == "_type" and prop.const_value:
                    schema_def.type_field_value = prop.const_value

            self.definitions[def_name] = schema_def

    def _parse_property(
        self, name: str, prop_data: dict[str, Any], required: list[str]
    ) -> SchemaProperty:
        """Parse a property definition."""
        prop = SchemaProperty(name=name)
        prop.is_required = name in required

        # Handle $ref
        if "$ref" in prop_data:
            prop.ref = self._extract_type_from_ref(prop_data["$ref"])

        # Handle type
        elif "type" in prop_data:
            prop.type = prop_data["type"]

            # Handle const
            if "const" in prop_data:
                prop.const_value = prop_data["const"]

            # Handle array
            if prop.type == "array" and "items" in prop_data:
                prop.is_array = True
                items = prop_data["items"]
                if "$ref" in items:
                    prop.items_ref = self._extract_type_from_ref(items["$ref"])

        return prop

    def _extract_type_from_ref(self, ref: str) -> str:
        """
        Extract type name from a $ref URL.

        Example: https://.../DV_SCALE.json#/definitions/DV_SCALE -> DV_SCALE
        """
        # Parse the URL
        if "#/definitions/" in ref:
            return ref.split("#/definitions/")[-1]

        # Extract from file path
        parts = ref.split("/")
        for part in reversed(parts):
            if part.endswith(".json"):
                return part.replace(".json", "")

        return ref

    def get_definition(self, name: str) -> SchemaDefinition | None:
        """Get a schema definition by name."""
        return self.definitions.get(name)

    def get_all_definitions(self) -> dict[str, SchemaDefinition]:
        """Get all parsed definitions."""
        return self.definitions


def load_rm_schema_from_json_schema(schema_dir: Path | None = None) -> JsonSchemaParser:
    """
    Load RM schema from JSON Schema files.

    Args:
        schema_dir: Path to RM Release directory. Defaults to bundled files.

    Returns:
        Parsed schema definitions.
    """
    if schema_dir is None:
        # Use bundled JSON Schema files for RM 1.1.0
        schema_dir = (
            Path(__file__).parent
            / "specifications-ITS-JSON"
            / "components"
            / "RM"
            / "Release-1.1.0"
        )

    if not schema_dir.exists():
        raise FileNotFoundError(
            f"Schema directory not found: {schema_dir}. "
            "Please clone specifications-ITS-JSON repository."
        )

    return JsonSchemaParser(schema_dir)


if __name__ == "__main__":
    # Test the parser
    parser = load_rm_schema_from_json_schema()

    print(f"Loaded {len(parser.definitions)} definitions")
    print("\nSample definitions:")

    # Test DV_SCALE (new in RM 1.1.0)
    if dv_scale := parser.get_definition("DV_SCALE"):
        print(f"\n{dv_scale.name}:")
        print(f"  Type field: {dv_scale.type_field_value}")
        print(f"  Required: {dv_scale.required_fields}")
        print(f"  Properties:")
        for prop_name, prop in list(dv_scale.properties.items())[:5]:
            ref_info = f" -> {prop.ref}" if prop.ref else ""
            array_info = "[]" if prop.is_array else ""
            print(f"    {prop_name}: {prop.type}{ref_info}{array_info}")

    # Test DV_QUANTITY
    if dv_qty := parser.get_definition("DV_QUANTITY"):
        print(f"\n{dv_qty.name}:")
        print(f"  Type field: {dv_qty.type_field_value}")
        print(f"  Properties: {list(dv_qty.properties.keys())[:8]}")
