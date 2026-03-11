# Template Builders

!!! note "Phase 2"
    This guide is planned for Phase 2 of the documentation site. For now, see the [Quick Start](../getting-started/quick-start.md#template-builders) for usage examples.

## Overview

oehrpy can automatically generate type-safe Python builder classes from OPT (Operational Template) files. This eliminates the need to manually construct FLAT format paths.

## Workflow

1. Obtain an OPT file for your template
2. Parse it with `parse_opt()`
3. Generate a builder class with `generate_builder_from_opt()`
4. Use the generated builder to create compositions

```python
from openehr_sdk.templates import generate_builder_from_opt, parse_opt

template = parse_opt("path/to/your-template.opt")
code = generate_builder_from_opt("path/to/your-template.opt")

# Save to a file and import in your project
with open("my_builder.py", "w") as f:
    f.write(code)
```

## Command-Line Tool

```bash
python examples/generate_builder_from_opt.py path/to/template.opt
```

## Pre-built Builders

The SDK ships with a pre-built `VitalSignsBuilder` for the "IDCR - Vital Signs Encounter.v1" template. See [Quick Start](../getting-started/quick-start.md#template-builders) for usage.
