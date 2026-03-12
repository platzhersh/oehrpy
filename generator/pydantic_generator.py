"""
Pydantic code generator for openEHR Reference Model classes.

This module generates Pydantic v2 model classes from parsed BMM schemas.
"""

from __future__ import annotations

import keyword
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import TextIO

from .bmm_parser import BmmClass, BmmProperty, BmmSchema, BmmTypeRef


@dataclass
class GeneratorConfig:
    """Configuration for the code generator."""

    output_dir: Path = field(default_factory=lambda: Path("src/openehr_sdk/rm"))
    # Map of BMM type names to Python type strings
    primitive_map: dict[str, str] = field(
        default_factory=lambda: {
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
            "Iso8601_date": "str",
            "Iso8601_time": "str",
            "Iso8601_date_time": "str",
            "Iso8601_duration": "str",
            "Ordered": "Any",
            "Numeric": "Any",
            "Ordered_Numeric": "Any",
            "Temporal": "Any",
            "Iso8601_type": "str",
            "Container": "Any",
            "Terminology_code": "Any",
            "Terminology_term": "Any",
        }
    )
    # Classes that should not be generated (primitives and abstract base types)
    skip_classes: set[str] = field(
        default_factory=lambda: {
            # Abstract primitive types
            "Any",
            "Ordered",
            "Numeric",
            "Ordered_Numeric",
            "Container",
            "Temporal",
            "Iso8601_type",
            # Primitives that map to Python builtins
            "Boolean",
            "Integer",
            "Integer64",
            "Real",
            "Double",
            "String",
            "Character",
            "Byte",
            "Octet",
            "Uri",
            "Iso8601_date",
            "Iso8601_time",
            "Iso8601_date_time",
            "Iso8601_duration",
            "Terminology_code",
            "Terminology_term",
            # Container types
            "List",
            "Set",
            "Array",
            "Hash",
            "Interval",
        }
    )
    # Map source_schema_id patterns to module names
    # For now, put all classes in a single module to avoid circular imports
    # TODO: Create proper module hierarchy with TYPE_CHECKING imports
    module_map: dict[str, str] = field(
        default_factory=lambda: {
            "data_types": "rm_types",
            "data_structures": "rm_types",
            "common": "rm_types",
            "support": "rm_types",
            "ehr": "rm_types",
            "composition": "rm_types",
            "demographic": "rm_types",
            "ehr_extract": "rm_types",
            "base": "rm_types",
        }
    )


class PydanticGenerator:
    """Generate Pydantic models from BMM schema."""

    def __init__(self, schema: BmmSchema, config: GeneratorConfig | None = None):
        self.schema = schema
        self.config = config or GeneratorConfig()
        self._class_to_module: dict[str, str] = {}
        self._module_classes: dict[str, list[str]] = defaultdict(list)
        self._compute_class_modules()

    def _compute_class_modules(self) -> None:
        """Determine which module each class belongs to."""
        for name, cls in self.schema.all_classes.items():
            if name in self.config.skip_classes:
                continue

            # Determine module based on source_schema_id
            module = "base"
            source = cls.source_schema_id or ""
            for pattern, mod in self.config.module_map.items():
                if pattern in source.lower():
                    module = mod
                    break

            self._class_to_module[name] = module
            self._module_classes[module].append(name)

    def generate(self) -> None:
        """Generate all Pydantic model files."""
        self.config.output_dir.mkdir(parents=True, exist_ok=True)

        # Generate module files
        for module_name, class_names in self._module_classes.items():
            self._generate_module(module_name, class_names)

        # Generate __init__.py
        self._generate_init()

    def _generate_module(self, module_name: str, class_names: list[str]) -> None:
        """Generate a single module file."""
        file_path = self.config.output_dir / f"{module_name}.py"

        # Sort classes by dependency order
        sorted_names = self._sort_by_dependencies(class_names)

        with open(file_path, "w") as f:
            self._write_module_header(f, module_name)
            self._write_imports(f, sorted_names)
            f.write("\n\n")

            for name in sorted_names:
                cls = self.schema.get_class(name)
                if cls:
                    self._write_class(f, cls)
                    f.write("\n\n")

    def _sort_by_dependencies(self, class_names: list[str]) -> list[str]:
        """Sort classes so dependencies come first."""
        # Build dependency graph
        deps: dict[str, set[str]] = {}
        name_set = set(class_names)

        for name in class_names:
            cls = self.schema.get_class(name)
            if not cls:
                continue

            deps[name] = set()
            # Add ancestors that are in this module
            for anc in cls.ancestors:
                if anc in name_set:
                    deps[name].add(anc)

        # Topological sort
        result: list[str] = []
        visited: set[str] = set()

        def visit(name: str) -> None:
            if name in visited:
                return
            visited.add(name)
            for dep in deps.get(name, set()):
                visit(dep)
            result.append(name)

        for name in class_names:
            visit(name)

        return result

    def _write_module_header(self, f: TextIO, module_name: str) -> None:
        """Write module docstring and future imports."""
        f.write(
            f'"""\nopenEHR Reference Model - {module_name.replace("_", " ").title()} classes.\n\n'
        )
        f.write("Auto-generated from openEHR BMM specifications.\n")
        f.write("Do not edit manually.\n")
        f.write('"""\n\n')
        f.write("from __future__ import annotations\n\n")

    def _write_imports(self, f: TextIO, class_names: list[str]) -> None:
        """Write import statements."""
        f.write("from typing import TYPE_CHECKING, Any, ClassVar, Optional\n\n")
        f.write("from pydantic import BaseModel, ConfigDict, Field\n")

        # Collect cross-module imports
        cross_imports: dict[str, set[str]] = defaultdict(set)

        for name in class_names:
            cls = self.schema.get_class(name)
            if not cls:
                continue

            # Check ancestors
            for anc in cls.ancestors:
                if anc not in class_names and anc in self._class_to_module:
                    module = self._class_to_module[anc]
                    cross_imports[module].add(anc)

            # Check property types
            for prop in cls.properties.values():
                self._collect_type_imports(prop.type_ref, class_names, cross_imports)

        # Write cross-module imports
        for module, types in sorted(cross_imports.items()):
            type_list = ", ".join(sorted(types))
            f.write(f"\nfrom .{module} import {type_list}")

    def _collect_type_imports(
        self,
        type_ref: BmmTypeRef,
        local_classes: list[str],
        cross_imports: dict[str, set[str]],
    ) -> None:
        """Collect type references that need to be imported."""
        type_name = type_ref.resolved_type_name

        # Skip primitives
        if type_name in self.config.primitive_map:
            return

        # Check if it's a cross-module reference
        if type_name not in local_classes and type_name in self._class_to_module:
            module = self._class_to_module[type_name]
            cross_imports[module].add(type_name)

        # Check generic parameters
        for param in type_ref.generic_parameters:
            if param not in local_classes and param in self._class_to_module:
                module = self._class_to_module[param]
                cross_imports[module].add(param)

        # Check nested type
        if type_ref.nested_type_def:
            self._collect_type_imports(type_ref.nested_type_def, local_classes, cross_imports)

    def _write_class(self, f: TextIO, cls: BmmClass) -> None:
        """Write a single Pydantic model class."""
        # Class declaration
        bases = self._get_base_classes(cls)
        f.write(f"class {cls.name}({bases}):\n")

        # Docstring
        if cls.documentation:
            doc = cls.documentation.replace('"""', '\\"\\"\\"')
            f.write(f'    """{doc}"""\n\n')
        else:
            f.write(f'    """openEHR RM type: {cls.name}."""\n\n')

        # Model config
        f.write("    model_config = ConfigDict(\n")
        f.write("        populate_by_name=True,\n")
        f.write('        extra="forbid",\n')
        f.write("    )\n\n")

        # Type discriminator field
        type_literal = cls.name.upper() if not cls.name.startswith("DV_") else cls.name
        f.write(f'    _type_: ClassVar[str] = "{type_literal}"\n')

        # Properties
        props = list(cls.properties.values())
        if not props and not cls.is_abstract:
            f.write("    pass\n")
        else:
            for prop in props:
                self._write_property(f, prop)

    def _get_base_classes(self, cls: BmmClass) -> str:
        """Get the base class string for a class."""
        if not cls.ancestors:
            return "BaseModel"

        # Filter ancestors to only include those we generate
        valid_ancestors = [a for a in cls.ancestors if a in self._class_to_module or a == "Any"]

        if not valid_ancestors or valid_ancestors == ["Any"]:
            return "BaseModel"

        return ", ".join(valid_ancestors)

    def _write_property(self, f: TextIO, prop: BmmProperty) -> None:
        """Write a property field."""
        py_name = self._to_python_name(prop.name)
        py_type = self._to_python_type(prop.type_ref, prop.is_mandatory)

        # Build Field arguments
        field_args: list[str] = []

        # Default value
        if not prop.is_mandatory:
            field_args.append("default=None")

        # Alias if name differs
        if py_name != prop.name:
            field_args.append(f'alias="{prop.name}"')

        # Description
        if prop.documentation:
            doc = prop.documentation.replace('"', '\\"')
            field_args.append(f'description="{doc}"')

        # Write the field
        if field_args:
            args_str = ", ".join(field_args)
            f.write(f"    {py_name}: {py_type} = Field({args_str})\n")
        else:
            f.write(f"    {py_name}: {py_type}\n")

    def _to_python_name(self, name: str) -> str:
        """Convert a BMM property name to a valid Python identifier."""
        # Convert to snake_case
        py_name = name.lower()

        # Handle reserved keywords
        if keyword.iskeyword(py_name):
            py_name = f"{py_name}_"

        return py_name

    def _to_python_type(self, type_ref: BmmTypeRef, is_mandatory: bool = False) -> str:
        """Convert a BMM type reference to a Python type hint."""
        type_name = type_ref.resolved_type_name

        # Handle container types
        if type_ref.is_container:
            inner_type = self._get_inner_type(type_ref)
            container = self._map_container_type(type_ref.container_type or "List")
            result = f"{container}[{inner_type}]"
        # Handle generic types - just use the base type without parameters
        # since Pydantic models don't support Generic[T] easily
        elif type_ref.root_type and type_ref.generic_parameters:
            result = self._map_type_name(type_ref.root_type)
        # Simple type
        else:
            result = self._map_type_name(type_name)

        # Wrap in Optional if not mandatory
        if not is_mandatory:
            # Use Optional for forward references to avoid evaluation issues
            if result.startswith('"') or result.startswith("list[") or result.startswith("set["):
                result = f"Optional[{result}]"
            else:
                result = f"{result} | None"

        return result

    def _get_inner_type(self, type_ref: BmmTypeRef) -> str:
        """Get the inner type for a container."""
        if type_ref.nested_type_def:
            return self._to_python_type(type_ref.nested_type_def, is_mandatory=True)
        if type_ref.type_name:
            return self._map_type_name(type_ref.type_name)
        return "Any"

    def _map_container_type(self, container: str) -> str:
        """Map BMM container type to Python collection type."""
        container_map = {
            "List": "list",
            "Set": "set",
            "Array": "list",
            "Hash": "dict",
        }
        return container_map.get(container, "list")

    def _map_type_name_raw(self, type_name: str) -> str:
        """Map a BMM type name to a Python type without quotes."""
        # Check primitive map first
        if type_name in self.config.primitive_map:
            return self.config.primitive_map[type_name]

        # Check if it's a known class - return name without quotes
        if type_name in self._class_to_module:
            return type_name

        # Unknown type - use Any
        return "Any"

    def _map_type_name(self, type_name: str) -> str:
        """Map a BMM type name to a Python type with forward reference quotes if needed."""
        # Check primitive map first
        if type_name in self.config.primitive_map:
            return self.config.primitive_map[type_name]

        # Check if it's a known class
        if type_name in self._class_to_module:
            return f'"{type_name}"'  # Forward reference

        # Unknown type - use Any
        return "Any"

    def _generate_init(self) -> None:
        """Generate the __init__.py file."""
        init_path = self.config.output_dir / "__init__.py"

        with open(init_path, "w") as f:
            f.write('"""\nopenEHR Reference Model (RM) 1.0.4 type definitions.\n\n')
            f.write(
                "This module contains Pydantic models for all openEHR Reference Model classes,\n"
            )
            f.write("generated from the official BMM specifications.\n")
            f.write('"""\n\n')

            # Import all classes from each module
            for module_name, class_names in sorted(self._module_classes.items()):
                sorted_names = sorted(class_names)
                if sorted_names:
                    names_str = ",\n    ".join(sorted_names)
                    f.write(f"from .{module_name} import (\n    {names_str},\n)\n")

            # Write __all__
            f.write("\n__all__ = [\n")
            all_names = sorted(name for names in self._module_classes.values() for name in names)
            for name in all_names:
                f.write(f'    "{name}",\n')
            f.write("]\n")


def generate_rm_models(
    bmm_path: Path | None = None,
    output_dir: Path | None = None,
) -> None:
    """Generate Pydantic models for the openEHR Reference Model.

    Args:
        bmm_path: Path to the BMM JSON directory. Defaults to bundled BMM files.
        output_dir: Output directory for generated code. Defaults to src/openehr_sdk/rm.
    """
    from .bmm_parser import load_rm_schema

    schema = load_rm_schema(bmm_path)

    config = GeneratorConfig()
    if output_dir:
        config.output_dir = output_dir

    generator = PydanticGenerator(schema, config)
    generator.generate()

    print(f"Generated {len(generator._class_to_module)} classes")
    print(f"Modules: {list(generator._module_classes.keys())}")


if __name__ == "__main__":
    import sys

    output = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("src/openehr_sdk/rm")
    generate_rm_models(output_dir=output)
