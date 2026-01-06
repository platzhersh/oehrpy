"""
Generate Pydantic models for openEHR RM 1.1.0 from JSON Schema files.

This is a simplified generator that creates all RM types in a single module.
"""

from __future__ import annotations

from pathlib import Path
from typing import TextIO

from generator.json_schema_parser import JsonSchemaParser, SchemaDefinition, SchemaProperty


class SimpleRMGenerator:
    """Simple generator for RM classes from JSON Schema."""

    # Python type mappings
    TYPE_MAP = {
        "string": "str",
        "number": "float",
        "integer": "int",
        "boolean": "bool",
        "array": "list",
        "object": "dict",
    }

    # Types to skip (too generic or will cause issues)
    SKIP_TYPES = {
        "Any",
        "DV_ANY",  # Too generic
        "LOCATABLE",  # Will be handled separately if needed
    }

    def __init__(self, rm_schema_dir: Path | None = None, base_schema_dir: Path | None = None):
        """Initialize generator with both RM and BASE schemas."""
        # Load RM types
        if rm_schema_dir is None:
            rm_schema_dir = (
                Path(__file__).parent
                / "specifications-ITS-JSON"
                / "components"
                / "RM"
                / "Release-1.1.0"
            )

        # Load BASE types
        if base_schema_dir is None:
            base_schema_dir = (
                Path(__file__).parent
                / "specifications-ITS-JSON"
                / "components"
                / "BASE"
                / "Release-1.1.0"
            )

        print(f"Loading RM types from {rm_schema_dir}")
        rm_parser = JsonSchemaParser(rm_schema_dir)

        print(f"Loading BASE types from {base_schema_dir}")
        base_parser = JsonSchemaParser(base_schema_dir)

        # Combine all definitions
        self.definitions = {}
        self.definitions.update(base_parser.get_all_definitions())
        self.definitions.update(rm_parser.get_all_definitions())

        print(
            f"Total definitions loaded: {len(self.definitions)} ({len(base_parser.definitions)} BASE + {len(rm_parser.definitions)} RM)"
        )

    def _python_type_for_property(self, prop: SchemaProperty) -> str:
        """Get Python type annotation for a property."""
        if prop.ref:
            # Reference to another type - use Optional for forward references
            type_name = prop.ref
            if prop.is_array:
                return f'Optional[list["{type_name}"]]'
            return f'Optional["{type_name}"]'

        if prop.items_ref:
            # Array with referenced items - use Optional for forward references
            return f'Optional[list["{prop.items_ref}"]]'

        if prop.type:
            # Primitive type
            py_type = self.TYPE_MAP.get(prop.type, "Any")
            if prop.const_value:
                # Constant value (like _type field)
                return f"str"
            if prop.is_required:
                return py_type
            return f"Optional[{py_type}]"

        return "Optional[Any]"

    def _write_class(self, f: TextIO, definition: SchemaDefinition) -> None:
        """Write a single class definition."""
        # Skip certain types
        if definition.name in self.SKIP_TYPES:
            return

        # Class definition
        f.write(f"\n\nclass {definition.name}(BaseModel):\n")

        # Add docstring if this is a 1.1.0 specific type
        if definition.name == "DV_SCALE":
            f.write(f'    """{definition.name} - New in RM 1.1.0.\n\n')
            f.write("    Data type for scales/scores with decimal values.\n")
            f.write("    Extends DV_ORDINAL for non-integer scale values.\n")
            f.write('    """\n\n')
        else:
            f.write(f'    """{definition.name}."""\n\n')

        # Special handling for _type field
        if definition.type_field_value:
            f.write(
                f'    type: str = Field(default="{definition.type_field_value}", alias="_type")\n'
            )

        # Write properties
        if not definition.properties:
            f.write("    pass\n")
            return

        for prop_name, prop in definition.properties.items():
            if prop_name == "_type":
                continue  # Already handled above
            if prop_name == "type" and definition.type_field_value:
                continue  # Skip duplicate type field when we have a type discriminator

            py_type = self._python_type_for_property(prop)

            # Skip if type is too complex
            if "dict" in py_type or py_type == "Any | None":
                continue

            # Generate field
            if prop.const_value:
                # Constant field
                f.write(f'    {prop_name}: {py_type} = Field(default="{prop.const_value}")\n')
            elif prop.is_required:
                # Required field
                f.write(f"    {prop_name}: {py_type}\n")
            else:
                # Optional field
                f.write(f"    {prop_name}: {py_type} = None\n")

        # Add model config
        f.write("\n    model_config = ConfigDict(populate_by_name=True)\n")

    def generate(self, output_file: Path) -> None:
        """Generate all RM classes to a single file."""
        print(f"Generating {len(self.definitions)} classes to {output_file}")

        with open(output_file, "w") as f:
            # File header
            f.write('"""')
            f.write("\nGenerated Pydantic models for openEHR Reference Model 1.1.0.\n\n")
            f.write("Includes both RM and BASE types from specifications-ITS-JSON.\n")
            f.write("Auto-generated - DO NOT EDIT MANUALLY.\n")
            f.write('"""\n\n')
            f.write("from __future__ import annotations\n\n")
            f.write("from typing import Any, Optional\n\n")
            f.write("from pydantic import BaseModel, ConfigDict, Field\n\n")
            f.write("# openEHR RM 1.1.0 and BASE Types\n")

            # Sort definitions for consistent output
            sorted_defs = sorted(self.definitions.values(), key=lambda d: d.name)

            # Write all classes
            for definition in sorted_defs:
                self._write_class(f, definition)

            # Add model_rebuild calls to resolve forward references
            f.write("\n\n# Rebuild all models to resolve forward references\n")
            f.write("import sys as _sys\n")
            f.write("_module = _sys.modules[__name__]\n")
            f.write("for _name in dir(_module):\n")
            f.write("    _obj = getattr(_module, _name)\n")
            f.write(
                "    if isinstance(_obj, type) and issubclass(_obj, BaseModel) and _obj is not BaseModel:\n"
            )
            f.write("        try:\n")
            f.write("            _obj.model_rebuild()\n")
            f.write("        except Exception:\n")
            f.write("            pass  # Skip if rebuild fails\n")

        print(f"✓ Generated {len(self.definitions)} classes")


def main():
    """Generate RM 1.1.0 and BASE classes."""
    generator = SimpleRMGenerator()

    output_file = Path("src/openehr_sdk/rm/rm_types.py")
    print(f"\n{'=' * 60}")
    print(f"Generating RM 1.1.0 + BASE types")
    print(f"{'=' * 60}")
    print(f"Output: {output_file}")

    generator.generate(output_file)

    print("\n✓ Generation complete!")
    print(f"  - Total classes: {len(generator.definitions)}")
    print(f"  - New in RM 1.1.0: DV_SCALE")
    print(f"  - Enhanced: CODE_PHRASE (with preferred_term field)")
    print(f"  - Includes: BASE types (TERMINOLOGY_ID, etc.)")


if __name__ == "__main__":
    main()
