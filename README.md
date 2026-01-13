# oehrpy - Python openEHR SDK

> **Pronunciation:** /oʊ.ɛər.paɪ/ ("o-air-pie") — short for "openehrpy", where "ehr" is pronounced like "air" (as in openEHR).

A comprehensive Python SDK for openEHR that provides type-safe Reference Model classes, template-specific composition builders, EHRBase client, and AQL query builder.

## Overview

This project addresses the gap in the openEHR ecosystem where no comprehensive, actively maintained Python SDK exists. It eliminates the need for developers to manually construct complex nested JSON structures when working with openEHR compositions.

## Installation

```bash
pip install oehrpy
```

Or install from source:

```bash
git clone https://github.com/platzhersh/oehrpy.git
cd oehrpy
pip install -e .
```

## Compatibility

- **Python:** 3.10+
- **openEHR RM:** 1.1.0
- **EHRBase:** 2.26.0+ (uses new FLAT format with composition tree IDs)

> **Note:** EHRBase 2.0+ introduced breaking changes to the FLAT format. This SDK implements the **new format** used by EHRBase 2.26.0. For details, see [FLAT Format Versions](docs/FLAT_FORMAT_VERSIONS.md).

## Features

- **Type-safe RM Classes**: 134 Pydantic models for openEHR Reference Model 1.1.0 types (includes BASE types)
- **Template Builders**: Pre-built composition builders for common templates (Vital Signs)
- **OPT Parser & Generator**: Parse OPT files and auto-generate type-safe builder classes
- **FLAT Format**: Full support for EHRBase 2.26.0+ FLAT format serialization
- **Canonical JSON**: Convert RM objects to/from openEHR canonical JSON format
- **EHRBase Client**: Async REST client for EHRBase CDR operations
- **AQL Builder**: Fluent API for building type-safe AQL queries
- **IDE Support**: Full autocomplete and type checking support
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

# Create a quantity (e.g., blood pressure)
bp_systolic = DV_QUANTITY(
    magnitude=120.0,
    units="mm[Hg]",
    property=CODE_PHRASE(
        terminology_id=TERMINOLOGY_ID(value="openehr"),
        code_string="382"
    )
)
print(f"Blood pressure: {bp_systolic.magnitude} {bp_systolic.units}")
```

### Template Builders

Build compositions using type-safe builders without knowing FLAT paths:

```python
from openehr_sdk.templates import VitalSignsBuilder

# Create a vital signs composition
builder = VitalSignsBuilder(composer_name="Dr. Smith")
builder.add_blood_pressure(systolic=120, diastolic=80)
builder.add_pulse(rate=72)
builder.add_temperature(37.2)
builder.add_respiration(rate=16)
builder.add_oxygen_saturation(spo2=98)

# Get FLAT format for EHRBase submission
flat_data = builder.build()
# {
#   "vital_signs_observations/language|code": "en",
#   "vital_signs_observations/territory|code": "US",
#   "vital_signs_observations/composer|name": "Dr. Smith",
#   "vital_signs_observations/category|code": "433",
#   "vital_signs_observations/vital_signs/blood_pressure/systolic|magnitude": 120,
#   "vital_signs_observations/vital_signs/blood_pressure/systolic|unit": "mm[Hg]",
#   "vital_signs_observations/vital_signs/body_temperature/temperature|unit": "°C",
#   ...
# }
```

### Generate Builders from OPT Files

Automatically generate template-specific builder classes from OPT (Operational Template) files:

```python
from openehr_sdk.templates import generate_builder_from_opt, parse_opt

# Parse an OPT file
template = parse_opt("path/to/your-template.opt")
print(f"Template: {template.template_id}")
print(f"Observations: {len(template.list_observations())}")

# Generate Python builder code
code = generate_builder_from_opt("path/to/your-template.opt")
print(code)  # Full Python class ready to use

# Or save directly to a file
from openehr_sdk.templates import BuilderGenerator

generator = BuilderGenerator()
generator.generate_to_file(template, "my_template_builder.py")
```

**Command-line tool:**
```bash
python examples/generate_builder_from_opt.py path/to/template.opt
```

This eliminates the need to manually code builders - just provide your OPT file and get a fully type-safe builder class with methods for each observation type.

### Canonical JSON Serialization

```python
from openehr_sdk.rm import DV_QUANTITY, CODE_PHRASE, TERMINOLOGY_ID
from openehr_sdk.serialization import to_canonical, from_canonical

# Serialize to canonical JSON (with _type fields)
quantity = DV_QUANTITY(magnitude=120.0, units="mm[Hg]", ...)
canonical = to_canonical(quantity)
# {"_type": "DV_QUANTITY", "magnitude": 120.0, "units": "mm[Hg]", ...}

# Deserialize back to Python object
restored = from_canonical(canonical, expected_type=DV_QUANTITY)
```

### FLAT Format Builder

```python
from openehr_sdk.serialization import FlatBuilder

# For EHRBase 2.26.0+, use composition tree ID as prefix
builder = FlatBuilder(composition_prefix="vital_signs_observations")
builder.context(language="en", territory="US", composer_name="Dr. Smith")
builder.set_quantity("vital_signs_observations/vital_signs/blood_pressure/systolic", 120.0, "mm[Hg]")
builder.set_coded_text("vital_signs_observations/vital_signs/blood_pressure/position", "Sitting", "at0001")

flat_data = builder.build()
# Automatically includes required fields: category, context/start_time, context/setting
```

### EHRBase REST Client

```python
from openehr_sdk.client import EHRBaseClient

async with EHRBaseClient(
    base_url="http://localhost:8080/ehrbase",
    username="admin",
    password="admin",
) as client:
    # Create an EHR
    ehr = await client.create_ehr()
    print(f"Created EHR: {ehr.ehr_id}")

    # Create a composition
    result = await client.create_composition(
        ehr_id=ehr.ehr_id,
        template_id="IDCR - Vital Signs Encounter.v1",
        composition=flat_data,
        format="FLAT",
    )
    print(f"Created composition: {result.uid}")

    # Query compositions
    query_result = await client.query(
        "SELECT c FROM EHR e CONTAINS COMPOSITION c WHERE e/ehr_id/value = :ehr_id",
        query_parameters={"ehr_id": ehr.ehr_id},
    )
```

### AQL Query Builder

```python
from openehr_sdk.aql import AQLBuilder

# Build complex queries with a fluent API
query = (
    AQLBuilder()
    .select("c/uid/value", alias="composition_id")
    .select("c/context/start_time/value", alias="time")
    .from_ehr()
    .contains_composition()
    .contains_observation(archetype_id="openEHR-EHR-OBSERVATION.blood_pressure.v1")
    .where_ehr_id()
    .order_by_time(descending=True)
    .limit(100)
    .build()
)

print(query.to_string())
# SELECT c/uid/value AS composition_id, c/context/start_time/value AS time
# FROM EHR e CONTAINS COMPOSITION c CONTAINS OBSERVATION o[...]
# WHERE e/ehr_id/value = :ehr_id
# ORDER BY c/context/start_time/value DESC
# LIMIT 100
```

## Available RM Types

The SDK includes all major openEHR RM 1.1.0 types:

**Data Types:**
- `DV_TEXT`, `DV_CODED_TEXT`, `CODE_PHRASE`
- `DV_QUANTITY`, `DV_COUNT`, `DV_PROPORTION`, `DV_SCALE` *(new in 1.1.0)*
- `DV_ORDINAL` *(integer values only - use DV_SCALE for decimal scale values)*
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

### New in RM 1.1.0

- **DV_SCALE**: Data type for scales/scores with decimal values (extends DV_ORDINAL for non-integer scales)
- **preferred_term**: New optional field in DV_CODED_TEXT for terminology mapping
- **Enhanced Folder support**: Archetypeable meta-data in EHR folders

For details, see [ADR-0001: Support RM 1.1.0](docs/adr/0001-odin-parsing-and-rm-1.1.0-support.md).

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

```text
oehrpy/
├── src/openehr_sdk/       # Main package
│   ├── rm/                # Generated RM + BASE classes (134 types)
│   ├── serialization/     # JSON serialization (canonical + FLAT)
│   ├── client/            # EHRBase REST client
│   ├── templates/         # Template builders (Vital Signs, etc.)
│   └── aql/               # AQL query builder
├── generator/             # Code generation tools
│   ├── bmm_parser.py      # BMM JSON parser
│   ├── pydantic_generator.py  # Pydantic code generator
│   └── bmm/               # BMM specification files
├── tests/                 # Test suite (66 tests)
└── docs/                  # Documentation
```

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to get started.

## License

MIT

## Documentation

- [FLAT Format Versions](docs/FLAT_FORMAT_VERSIONS.md) - Understanding EHRBase 2.0+ FLAT format changes
- [FLAT Format Learnings](docs/flat-format-learnings.md) - Comprehensive FLAT format guide
- [ADR-0001: RM 1.1.0 Support](docs/adr/0001-odin-parsing-and-rm-1.1.0-support.md)
- [ADR-0002: Integration Testing](docs/adr/0002-integration-testing-with-ehrbase.md)
- [PRD-0000: Python openEHR SDK](docs/prd/PRD-0000-python-openehr-sdk.md)

## References

- [openEHR BMM Specifications](https://github.com/openEHR/specifications-ITS-BMM)
- [openEHR RM Specification](https://specifications.openehr.org/releases/RM/latest)
- [EHRBase](https://ehrbase.org/)
- [EHRBase Documentation](https://docs.ehrbase.org/) *(Note: FLAT format docs may be outdated, see our [FLAT Format Versions](docs/FLAT_FORMAT_VERSIONS.md) guide)*
