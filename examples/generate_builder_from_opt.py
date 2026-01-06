"""
Example: Generate a template builder from an OPT file.

This script demonstrates how to:
1. Parse an OPT (Operational Template) XML file
2. Generate a Python builder class automatically
3. Use the generated builder to create compositions

Usage:
    python examples/generate_builder_from_opt.py path/to/template.opt
"""

import sys
from pathlib import Path

from openehr_sdk.templates import BuilderGenerator, parse_opt


def main() -> None:
    """Generate a builder from an OPT file."""
    if len(sys.argv) < 2:
        print("Usage: python generate_builder_from_opt.py <path-to-opt-file>")
        print("\nExample:")
        print("  python generate_builder_from_opt.py tests/fixtures/vital_signs.opt")
        sys.exit(1)

    opt_path = Path(sys.argv[1])

    if not opt_path.exists():
        print(f"Error: OPT file not found: {opt_path}")
        sys.exit(1)

    print(f"Parsing OPT file: {opt_path}")
    print("=" * 70)

    # Step 1: Parse the OPT file
    template = parse_opt(opt_path)

    print("\nTemplate Information:")
    print(f"  Template ID: {template.template_id}")
    print(f"  Concept: {template.concept}")
    print(f"  Description: {template.description}")
    print(f"  Language: {template.language}")

    # Step 2: Extract observations
    observations = template.list_observations()
    print(f"\nObservations found: {len(observations)}")
    for i, obs in enumerate(observations, 1):
        print(f"  {i}. {obs.name}")
        print(f"     Archetype ID: {obs.archetype_id}")

    # Step 3: Generate builder code
    print("\n" + "=" * 70)
    print("Generating builder class...")
    print("=" * 70)

    generator = BuilderGenerator()
    code = generator.generate(template)

    # Step 4: Display the generated code
    print("\nGenerated Builder Code:")
    print("-" * 70)
    print(code)
    print("-" * 70)

    # Step 5: Optionally save to file
    output_path = opt_path.stem + "_builder.py"
    save = input(f"\nSave to {output_path}? (y/N): ").strip().lower()

    if save == "y":
        generator.generate_to_file(template, output_path)
        print(f"✓ Builder saved to: {output_path}")
        print("\nYou can now use it like this:")
        class_name = generator._derive_class_name(template.template_id)
        print(f"  from {opt_path.stem}_builder import {class_name}")
    else:
        print("\nBuilder not saved.")

    print("\nDone!")


if __name__ == "__main__":
    main()
