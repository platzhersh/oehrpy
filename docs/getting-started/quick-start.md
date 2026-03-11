# Quick Start

## Creating RM Objects

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

## Template Builders

Build compositions using type-safe builders without knowing FLAT paths:

```python
from openehr_sdk.templates import VitalSignsBuilder

builder = VitalSignsBuilder(composer_name="Dr. Smith")
builder.add_blood_pressure(systolic=120, diastolic=80)
builder.add_pulse(rate=72)
builder.add_temperature(37.2)
builder.add_respiration(rate=16)
builder.add_oxygen_saturation(spo2=98)

flat_data = builder.build()
```

## Generate Builders from OPT Files

Automatically generate template-specific builder classes from OPT files:

```python
from openehr_sdk.templates import generate_builder_from_opt, parse_opt

# Parse an OPT file
template = parse_opt("path/to/your-template.opt")
print(f"Template: {template.template_id}")
print(f"Observations: {len(template.list_observations())}")

# Generate Python builder code
code = generate_builder_from_opt("path/to/your-template.opt")
print(code)  # Full Python class ready to use
```

Or use the command-line tool:

```bash
python examples/generate_builder_from_opt.py path/to/template.opt
```

## Canonical JSON Serialization

```python
from openehr_sdk.rm import DV_QUANTITY, CODE_PHRASE, TERMINOLOGY_ID
from openehr_sdk.serialization import to_canonical, from_canonical

# Serialize to canonical JSON (with _type fields)
quantity = DV_QUANTITY(magnitude=120.0, units="mm[Hg]")
canonical = to_canonical(quantity)
# {"_type": "DV_QUANTITY", "magnitude": 120.0, "units": "mm[Hg]", ...}

# Deserialize back to Python object
restored = from_canonical(canonical, expected_type=DV_QUANTITY)
```

## FLAT Format Builder

```python
from openehr_sdk.serialization import FlatBuilder

# For EHRBase 2.26.0+, use composition tree ID as prefix
builder = FlatBuilder(composition_prefix="vital_signs_observations")
builder.context(language="en", territory="US", composer_name="Dr. Smith")
builder.set_quantity(
    "vital_signs_observations/vital_signs/blood_pressure/systolic",
    120.0, "mm[Hg]"
)
builder.set_coded_text(
    "vital_signs_observations/vital_signs/blood_pressure/position",
    "Sitting", "at0001"
)

flat_data = builder.build()
```

## EHRBase REST Client

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
        "SELECT c FROM EHR e CONTAINS COMPOSITION c "
        "WHERE e/ehr_id/value = :ehr_id",
        query_parameters={"ehr_id": ehr.ehr_id},
    )
```

## AQL Query Builder

```python
from openehr_sdk.aql import AQLBuilder

query = (
    AQLBuilder()
    .select("c/uid/value", alias="composition_id")
    .select("c/context/start_time/value", alias="time")
    .from_ehr()
    .contains_composition()
    .contains_observation(
        archetype_id="openEHR-EHR-OBSERVATION.blood_pressure.v1"
    )
    .where_ehr_id()
    .order_by_time(descending=True)
    .limit(100)
    .build()
)

print(query.to_string())
```
