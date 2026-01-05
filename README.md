# oehrpy - Python openEHR SDK

A Python SDK for openEHR that provides type-safe Reference Model (RM) classes and template-specific composition builders.

## Overview

This project addresses the gap in the openEHR ecosystem where no comprehensive, actively maintained Python SDK exists. It eliminates the need for developers to manually construct complex nested JSON structures when working with openEHR compositions.

## Installation

```bash
pip install openehr-sdk
```

Or install from source:

```bash
git clone https://github.com/platzhersh/oehrpy.git
cd oehrpy
pip install -e .
```

## Features

- **Type-safe RM Classes**: 110+ Pydantic models for openEHR Reference Model 1.0.4 types
- **IDE Support**: Full autocomplete and type checking support
- **Canonical JSON Serialization**: Convert RM objects to/from openEHR canonical JSON format
- **Validation**: Pydantic v2 validation for all fields

## Quick Start

### Creating RM Objects

```python
from openehr_sdk.rm import (
    DV_QUANTITY, DV_TEXT, DV_CODED_TEXT,
    CODE_PHRASE, TERMINOLOGY_ID
)

# Create a simple text value
text = DV_TEXT(value="Patient vital signs recorded")

# Create a coded text
term_id = TERMINOLOGY_ID(value="local")
code = CODE_PHRASE(terminology_id=term_id, code_string="at0001")
coded_text = DV_CODED_TEXT(value="Normal", defining_code=code)

# Create a quantity (e.g., blood pressure)
property_code = CODE_PHRASE(
    terminology_id=TERMINOLOGY_ID(value="openehr"),
    code_string="382"  # pressure
)
bp_systolic = DV_QUANTITY(
    magnitude=120.0,
    units="mm[Hg]",
    property=property_code
)

print(f"Blood pressure: {bp_systolic.magnitude} {bp_systolic.units}")
# Output: Blood pressure: 120.0 mm[Hg]
```

### Serialization

```python
from openehr_sdk.rm import DV_QUANTITY, CODE_PHRASE, TERMINOLOGY_ID
from openehr_sdk.serialization import to_canonical, from_canonical

# Create an RM object
property_code = CODE_PHRASE(
    terminology_id=TERMINOLOGY_ID(value="openehr"),
    code_string="382"
)
quantity = DV_QUANTITY(
    magnitude=120.0,
    units="mm[Hg]",
    property=property_code
)

# Serialize to canonical JSON (with _type fields)
canonical = to_canonical(quantity)
print(canonical)
# {
#   "_type": "DV_QUANTITY",
#   "magnitude": 120.0,
#   "units": "mm[Hg]",
#   "property": {
#     "_type": "CODE_PHRASE",
#     "terminology_id": {"_type": "TERMINOLOGY_ID", "value": "openehr"},
#     "code_string": "382"
#   }
# }

# Deserialize back to Python object
restored = from_canonical(canonical, expected_type=DV_QUANTITY)
assert restored.magnitude == 120.0
```

### Available RM Types

The SDK includes all major openEHR RM 1.0.4 types:

**Data Types:**
- `DV_TEXT`, `DV_CODED_TEXT`, `CODE_PHRASE`
- `DV_QUANTITY`, `DV_COUNT`, `DV_PROPORTION`
- `DV_DATE_TIME`, `DV_DATE`, `DV_TIME`, `DV_DURATION`
- `DV_BOOLEAN`, `DV_IDENTIFIER`, `DV_URI`, `DV_EHR_URI`
- `DV_MULTIMEDIA`, `DV_PARSABLE`

**Structures:**
- `COMPOSITION`, `SECTION`, `ENTRY`
- `OBSERVATION`, `EVALUATION`, `INSTRUCTION`, `ACTION`
- `ITEM_TREE`, `ITEM_LIST`, `CLUSTER`, `ELEMENT`
- `HISTORY`, `EVENT`, `POINT_EVENT`, `INTERVAL_EVENT`

**Support:**
- `PARTY_IDENTIFIED`, `PARTY_SELF`, `PARTICIPATION`
- `OBJECT_REF`, `OBJECT_ID`, `HIER_OBJECT_ID`
- `ARCHETYPED`, `LOCATABLE`, `PATHABLE`

## Development

### Prerequisites

- Python 3.10+
- pip

### Setup

```bash
# Clone the repository
git clone https://github.com/platzhersh/oehrpy.git
cd oehrpy

# Install development dependencies
pip install -e ".[dev,generator]"
```

### Running Tests

```bash
pytest tests/ -v
```

### Type Checking

```bash
mypy src/openehr_sdk
```

### Regenerating RM Classes

The RM classes are generated from openEHR BMM specifications:

```bash
python -m generator.pydantic_generator
```

## Project Structure

```
oehrpy/
├── src/openehr_sdk/       # Main package
│   ├── rm/                # Generated RM classes
│   │   └── rm_types.py    # All RM type definitions
│   └── serialization/     # JSON serialization
│       └── canonical.py   # Canonical JSON format
├── generator/             # Code generation tools
│   ├── bmm_parser.py      # BMM JSON parser
│   ├── pydantic_generator.py  # Pydantic code generator
│   └── bmm/               # BMM specification files
├── tests/                 # Test suite
└── docs/                  # Documentation
```

## Roadmap

- [ ] FLAT format serialization (EHRBase)
- [ ] Template-specific composition builders
- [ ] REST client for EHRBase
- [ ] AQL query builder

## Contributing

Contributions are welcome! Please see the documentation for guidelines.

## License

MIT

## References

- [openEHR BMM Specifications](https://github.com/openEHR/specifications-ITS-BMM)
- [openEHR RM Specification](https://specifications.openehr.org/releases/RM/latest)
- [PRD-0000: Python openEHR SDK](docs/prd/PRD-0000-python-openehr-sdk.md)
