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

## Features

- **Type-safe RM Classes**: 110+ Pydantic models for openEHR Reference Model 1.0.4 types
- **Template Builders**: Pre-built composition builders for common templates (Vital Signs)
- **FLAT Format**: Full support for EHRBase FLAT format serialization
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
#   "ctx/language": "en",
#   "ctx/territory": "US",
#   "ctx/composer_name": "Dr. Smith",
#   "vital_signs/blood_pressure:0/any_event:0/systolic|magnitude": 120,
#   "vital_signs/blood_pressure:0/any_event:0/systolic|unit": "mm[Hg]",
#   ...
# }
```

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

builder = FlatBuilder()
builder.context(language="en", territory="US", composer_name="Dr. Smith")
builder.set_quantity("vital_signs/bp/systolic", 120.0, "mm[Hg]")
builder.set_coded_text("vital_signs/status", "Normal", "at0001")

flat_data = builder.build()
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
│   ├── rm/                # Generated RM classes (110+ types)
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

Contributions are welcome! Please see the documentation for guidelines.

## License

MIT

## References

- [openEHR BMM Specifications](https://github.com/openEHR/specifications-ITS-BMM)
- [openEHR RM Specification](https://specifications.openehr.org/releases/RM/latest)
- [EHRBase](https://ehrbase.org/)
- [PRD-0000: Python openEHR SDK](docs/prd/PRD-0000-python-openehr-sdk.md)
