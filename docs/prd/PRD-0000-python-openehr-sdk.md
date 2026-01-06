# PRD-0000: Python openEHR SDK Generation

**Version:** 1.0
**Date:** 2026-01-06
**Status:** Draft
**Owner:** Open CIS Project

> **UPDATE (2026-01-06)**: This PRD originally targeted RM 1.0.4. We have since decided to support **RM 1.1.0** using JSON Schema files from the `specifications-ITS-JSON` repository. See [ADR-0001: Support RM 1.1.0](../adr/0001-odin-parsing-and-rm-1.1.0-support.md) for details. References to RM 1.0.4 in this document are preserved for historical context.

---

## Executive Summary

Build or generate a Python SDK for openEHR that provides type-safe Reference Model (RM) classes and template-specific composition builders. This addresses the current gap in the openEHR ecosystem where no comprehensive, actively maintained Python SDK exists, forcing developers to manually construct complex nested JSON structures.

This PRD evaluates three approaches and recommends **Option 3: Build a BMM-to-Python Generator** as the most viable path for the Open CIS project, while documenting Options 1 and 2 as context.

---

## Problem Statement

**Current Pain Points:**

1. **No production-ready Python SDK** - Existing options are either unmaintained (pyEHR, ~7 years stale) or limited to specific functions (openehpy - AQL client only)

2. **Manual composition building is error-prone** - Creating openEHR compositions requires constructing deeply nested JSON with precise paths:
   ```python
   # Current approach - manual FLAT format construction
   composition = {
       "ctx/language": "en",
       "ctx/territory": "US", 
       "vital_signs/blood_pressure:0/any_event:0/systolic|magnitude": 120,
       "vital_signs/blood_pressure:0/any_event:0/systolic|unit": "mm[Hg]",
       # ... 20+ more fields for a simple vital signs entry
   }
   ```

3. **No IDE support** - Without typed classes, developers get no autocomplete, type checking, or documentation hints

4. **Template knowledge required** - Developers must memorize FLAT paths for each template they work with

**User Personas:**
1. **Open CIS Developer** - Needs type-safe composition building for FastAPI backend
2. **openEHR Python Community** - Lacks modern tooling compared to Java ecosystem
3. **Healthcare App Developers** - Want to integrate openEHR without deep domain expertise

---

## Context: Three Approaches Evaluated

### Option 1: Collaborate with Borut Jures (NeoEHR / MapEHR)

**Description:** Work with Borut Jures (NeoEHR) who has offered to generate SDKs from BMM files and OPT templates.

**What Borut Offers:**
- BMM → SDK generation (claims ~1 day for known languages, ~3 days otherwise)
- Template SDK generation from OPT files (136+ classes per template)
- Already has working generators for Dart, JavaScript, TypeScript, Java
- MapEHR synthetic data generator for testing

**Pros:**
- Fastest time to working solution
- Proven approach (used in production by NeoEHR clients)
- Includes template-specific builders, not just RM classes
- Potential for ongoing collaboration

**Cons:**
- Dependency on external party
- Unknown if Python is in his "known languages" category
- Licensing terms unclear (his tools are "source available", not fully open source)
- May not align with Pydantic/FastAPI patterns we prefer

**Effort:** Low (days to weeks, depending on collaboration)

**Recommendation:** Pursue this in parallel - reach out to Borut, but don't block on it.

---

### Option 2: BMM → OpenAPI → Pydantic (Indirect Generation)

**Description:** Use Borut's existing OpenAPI schemas generated from BMM, then use `datamodel-code-generator` to produce Pydantic models.

**Pipeline:**
```
BMM Files → OpenAPI Generator (Borut's) → OpenAPI YAML → datamodel-codegen → Pydantic Models
```

**Available Resources:**
- OpenAPI schemas: https://neoehr.com/openehr/openapi
- Pydantic generator: `datamodel-code-generator` (pip install)

**Pros:**
- Can start immediately with existing artifacts
- Leverages mature tooling (datamodel-codegen is well-maintained)
- Produces native Pydantic v2 models

**Cons:**
- OpenAPI schemas may be incomplete (Sebastian Iancu noted BMM files lack some UML spec details)
- Missing discriminator columns for polymorphism (noted by Pieter Bos)
- No template-specific builders - only RM classes
- Two-stage generation adds complexity and potential for drift

**Effort:** Medium (1-2 weeks for RM classes, no template support)

**Recommendation:** Good for quick RM type definitions, but insufficient for composition building.

---

### Option 3: Build a BMM-to-Python Generator (Recommended)

**Description:** Create a custom generator that parses BMM files and produces Pydantic models tailored to our needs, with optional OPT parsing for template-specific builders.

**Pipeline:**
```
Phase 1: BMM Files → BMM Parser → Pydantic RM Classes (~200 classes)
Phase 2: OPT Files → OPT Parser → Template-specific Builders
```

**Why This Approach:**
1. **Full control** over output format, naming conventions, and Pydantic features
2. **Learn openEHR deeply** - aligns with Open CIS's educational mission
3. **Contribute to ecosystem** - could become the de facto Python SDK
4. **Template builders** - the real value-add that eliminates manual JSON construction
5. **Article content** - excellent material for Medium series

**Pros:**
- Produces exactly what we need for FastAPI/Pydantic stack
- Can add features incrementally (RM first, then templates)
- Publishable as open-source package (PyPI)
- Deep learning opportunity

**Cons:**
- Highest initial effort
- Need to parse BMM format (ODIN or JSON)
- Need to handle openEHR's complex inheritance hierarchy
- Ongoing maintenance responsibility

**Effort:** High (8-12 weeks for comprehensive SDK)

**Recommendation:** This is the recommended approach for Open CIS.

---

## Goals & Success Metrics

### Goals

1. **Eliminate manual JSON construction** for openEHR compositions
2. **Provide type safety** with full IDE autocomplete and validation
3. **Support the vital signs template** used in Open CIS as first milestone
4. **Create reusable open-source package** for the Python/openEHR community
5. **Generate Medium article content** documenting the journey

### Success Metrics

| Metric | Target |
|--------|--------|
| RM classes generated | 200+ (all openEHR RM 1.0.4 types) |
| Template builders | At least 1 (IDCR Vital Signs) |
| Type coverage | 100% of generated code passes mypy strict |
| Serialization | Round-trip JSON canonical format |
| PyPI package | Published and installable |
| Documentation | Full API docs with examples |

---

## Technical Requirements

### Phase 1: BMM Parser & RM Class Generation

**Priority:** P0 (Must Have)

**Scope:** Parse BMM files and generate Pydantic models for all openEHR Reference Model classes.

#### 1.1 BMM Parser

**Input:** BMM files from `github.com/openEHR/specifications-ITS-BMM`

**BMM File Locations:**
```
specifications-ITS-BMM/
├── components/
│   ├── BASE/Release-1.1.0/      # Foundation types
│   ├── RM/Release-1.0.4/        # Reference Model (target)
│   │   ├── openehr_rm_ehr_1.0.4.bmm.json
│   │   ├── openehr_rm_demographic_1.0.4.bmm.json
│   │   └── ...
│   └── PROC/Release-1.5.0/      # Task Planning (future)
```

**BMM Format Options:**
- ODIN format (`.bmm`) - Original format, requires ODIN parser
- JSON format (`.bmm.json`) - Easier to parse, available for most schemas

**Recommendation:** Use JSON format BMM files for simpler parsing.

**Parser Requirements:**
- Load and resolve BMM schema includes (schemas reference each other)
- Extract class definitions with:
  - Class name and documentation
  - Ancestor classes (inheritance)
  - Properties with types, cardinality, mandatory flags
  - Generic type parameters
- Handle BMM primitive type mappings to Python types

**Output:** Internal AST/data structure representing the full RM type hierarchy.

#### 1.2 Pydantic Code Generator

**Input:** Parsed BMM schema

**Output:** Python files with Pydantic models

**Generated Code Structure:**
```python
# openehr_sdk/rm/data_types/quantity.py

from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field

class DvQuantity(DvAmount):
    """
    Quantified type representing a quantity with magnitude and units.
    
    openEHR Reference: https://specifications.openehr.org/releases/RM/latest/data_types.html#_dv_quantity_class
    """
    _type: str = Field(default="DV_QUANTITY", alias="_type")
    magnitude: float = Field(..., description="Numeric magnitude of the quantity")
    units: str = Field(..., description="Units, expressed as a string")
    precision: Optional[int] = Field(None, description="Precision to which magnitude is expressed")
    
    class Config:
        populate_by_name = True  # Allow both 'magnitude' and JSON '_type'
```

**Package Structure:**
```
openehr_sdk/
├── __init__.py
├── rm/
│   ├── __init__.py
│   ├── data_types/
│   │   ├── __init__.py
│   │   ├── basic.py          # DV_BOOLEAN, DV_STATE, DV_IDENTIFIER
│   │   ├── text.py           # DV_TEXT, DV_CODED_TEXT, CODE_PHRASE
│   │   ├── quantity.py       # DV_QUANTITY, DV_COUNT, DV_PROPORTION
│   │   ├── date_time.py      # DV_DATE, DV_TIME, DV_DATE_TIME, DV_DURATION
│   │   ├── encapsulated.py   # DV_PARSABLE, DV_MULTIMEDIA
│   │   └── uri.py            # DV_URI, DV_EHR_URI
│   ├── data_structures/
│   │   ├── __init__.py
│   │   ├── item_structure.py # ITEM_TREE, ITEM_LIST, ITEM_TABLE
│   │   └── history.py        # HISTORY, EVENT, POINT_EVENT, INTERVAL_EVENT
│   ├── common/
│   │   ├── __init__.py
│   │   ├── archetyped.py     # LOCATABLE, ARCHETYPED, LINK
│   │   └── generic.py        # PARTICIPATION, PARTY_PROXY, etc.
│   ├── composition/
│   │   ├── __init__.py
│   │   └── content.py        # COMPOSITION, SECTION, ENTRY, OBSERVATION, etc.
│   └── ehr/
│       ├── __init__.py
│       └── ehr.py            # EHR, EHR_STATUS, EHR_ACCESS
├── serialization/
│   ├── __init__.py
│   ├── canonical.py          # To/from canonical JSON format
│   └── flat.py               # To/from FLAT format (EHRBase)
└── client/
    ├── __init__.py
    └── ehrbase.py            # REST client for EHRBase
```

**Code Generation Features:**
- Proper inheritance hierarchy matching openEHR specs
- `_type` discriminator field for polymorphic deserialization
- Optional fields with `None` defaults
- Field descriptions from BMM documentation
- Type hints for all attributes
- Validators for constrained types (e.g., intervals, patterns)

#### 1.3 Serialization Layer

**JSON Canonical Format:**
```python
from openehr_sdk.rm.data_types import DvQuantity
from openehr_sdk.serialization import to_canonical, from_canonical

# Create instance
bp_systolic = DvQuantity(magnitude=120.0, units="mm[Hg]")

# Serialize to canonical JSON
json_data = to_canonical(bp_systolic)
# {
#   "_type": "DV_QUANTITY",
#   "magnitude": 120.0,
#   "units": "mm[Hg]"
# }

# Deserialize (with polymorphic type resolution)
restored = from_canonical(json_data)
assert isinstance(restored, DvQuantity)
```

**FLAT Format Support:**
```python
from openehr_sdk.serialization.flat import to_flat, from_flat

composition = VitalSignsComposition(...)
flat_data = to_flat(composition, template_id="IDCR - Vital Signs Encounter.v1")
# {
#   "ctx/language": "en",
#   "vital_signs/blood_pressure:0/any_event:0/systolic|magnitude": 120,
#   ...
# }
```

---

### Phase 2: Template-Specific Builders

**Priority:** P1 (Should Have)

**Scope:** Parse OPT files and generate template-specific composition builders with constrained types.

#### 2.1 OPT Parser

**Input:** Operational Template files (OPT 1.4 XML format)

**Example:** `IDCR - Vital Signs Encounter.v1.opt`

**Parser Requirements:**
- Parse OPT XML structure
- Extract template constraints on archetypes
- Map archetype node IDs to FLAT paths
- Extract terminology bindings and value sets

#### 2.2 Template Builder Generator

**Output:** Template-specific Python classes

**Generated Code Example:**
```python
# openehr_sdk/templates/idcr_vital_signs.py

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from openehr_sdk.rm.data_types import DvQuantity, DvDateTime, DvCodedText

class BloodPressureEvent(BaseModel):
    """Single blood pressure measurement event."""
    time: datetime
    systolic: DvQuantity = Field(..., description="Systolic pressure")
    diastolic: DvQuantity = Field(..., description="Diastolic pressure")
    position: Optional[DvCodedText] = None
    
    @classmethod
    def create(
        cls,
        systolic_mmhg: float,
        diastolic_mmhg: float,
        time: Optional[datetime] = None,
    ) -> "BloodPressureEvent":
        """Convenience factory with sensible defaults."""
        return cls(
            time=time or datetime.now(),
            systolic=DvQuantity(magnitude=systolic_mmhg, units="mm[Hg]"),
            diastolic=DvQuantity(magnitude=diastolic_mmhg, units="mm[Hg]"),
        )

class BloodPressureObservation(BaseModel):
    """Blood pressure observation with one or more events."""
    events: List[BloodPressureEvent] = Field(default_factory=list)
    
    def add_reading(self, systolic: float, diastolic: float, time: Optional[datetime] = None):
        """Add a blood pressure reading."""
        self.events.append(BloodPressureEvent.create(systolic, diastolic, time))

class PulseObservation(BaseModel):
    """Pulse/heart rate observation."""
    events: List[PulseEvent] = Field(default_factory=list)
    
    def add_reading(self, rate: float, time: Optional[datetime] = None):
        """Add a pulse reading."""
        self.events.append(PulseEvent.create(rate, time))

class VitalSignsComposition(BaseModel):
    """
    IDCR Vital Signs Encounter composition.
    
    Template: IDCR - Vital Signs Encounter.v1
    Source: RippleOSI/Ripple-openEHR
    """
    template_id: str = "IDCR - Vital Signs Encounter.v1"
    
    # Context
    language: str = "en"
    territory: str = "US"
    composer_name: str = Field(..., description="Name of the clinician recording vitals")
    
    # Observations
    blood_pressure: BloodPressureObservation = Field(default_factory=BloodPressureObservation)
    pulse: PulseObservation = Field(default_factory=PulseObservation)
    body_temperature: Optional[BodyTemperatureObservation] = None
    respiration: Optional[RespirationObservation] = None
    oxygen_saturation: Optional[OxygenSaturationObservation] = None
    
    def to_flat(self) -> dict:
        """Convert to EHRBase FLAT format for API submission."""
        from openehr_sdk.serialization.flat import composition_to_flat
        return composition_to_flat(self)
    
    def to_canonical(self) -> dict:
        """Convert to openEHR canonical JSON format."""
        from openehr_sdk.serialization.canonical import composition_to_canonical
        return composition_to_canonical(self)
```

**Usage in Open CIS:**
```python
# api/src/services/vital_signs.py

from openehr_sdk.templates.idcr_vital_signs import VitalSignsComposition
from openehr_sdk.client import EHRBaseClient

async def record_vital_signs(
    ehr_id: str,
    systolic: float,
    diastolic: float,
    pulse: float,
    composer: str,
) -> str:
    """Record vital signs - clean, type-safe, IDE-friendly."""
    
    composition = VitalSignsComposition(composer_name=composer)
    composition.blood_pressure.add_reading(systolic, diastolic)
    composition.pulse.add_reading(pulse)
    
    client = EHRBaseClient()
    result = await client.create_composition(
        ehr_id=ehr_id,
        composition=composition.to_flat(),
        template_id=composition.template_id,
    )
    return result["uid"]
```

---

### Phase 3: REST Client & Integration

**Priority:** P2 (Nice to Have for SDK, already exists in Open CIS)

**Scope:** Type-safe REST client for EHRBase operations.

This phase can leverage the existing `api/src/ehrbase/client.py` but wrap it with typed request/response models.

```python
from openehr_sdk.client import EHRBaseClient
from openehr_sdk.templates.idcr_vital_signs import VitalSignsComposition

client = EHRBaseClient(base_url="http://localhost:8080/ehrbase")

# Create EHR
ehr = await client.create_ehr()

# Create composition with full type safety
composition = VitalSignsComposition(composer_name="Dr. Smith")
composition.blood_pressure.add_reading(120, 80)

result = await client.create_composition(ehr.ehr_id, composition)

# Query with typed results
results = await client.query_aql(
    "SELECT c FROM COMPOSITION c WHERE c/name/value = 'Vital Signs'",
    result_type=VitalSignsComposition,
)
```

---

## Implementation Plan

### Milestone 1: BMM Parser (Week 1-2)

- [ ] Set up `openehr-sdk` Python package structure
- [ ] Download BMM JSON files from openEHR GitHub
- [ ] Implement BMM JSON parser
- [ ] Handle schema includes/references
- [ ] Build internal type hierarchy representation
- [ ] Write tests with sample BMM classes

**Deliverable:** Working BMM parser that can load full RM schema

### Milestone 2: Pydantic Generator (Week 3-4)

- [ ] Implement code generator from parsed BMM
- [ ] Handle inheritance hierarchy
- [ ] Generate proper type hints
- [ ] Add `_type` discriminators
- [ ] Generate all RM 1.0.4 classes
- [ ] Run mypy strict on generated code

**Deliverable:** ~200 generated Pydantic classes passing type checks

### Milestone 3: Serialization (Week 5-6)

- [ ] Implement canonical JSON serialization
- [ ] Implement canonical JSON deserialization with polymorphism
- [ ] Implement FLAT format serialization
- [ ] Add round-trip tests
- [ ] Validate against EHRBase

**Deliverable:** Working serialization to/from EHRBase formats

### Milestone 4: OPT Parser & Template Builder (Week 7-10)

- [ ] Implement OPT XML parser
- [ ] Extract template constraints
- [ ] Map to FLAT paths
- [ ] Generate template-specific builders
- [ ] Start with IDCR Vital Signs template
- [ ] Integration test with Open CIS

**Deliverable:** `VitalSignsComposition` builder working in Open CIS

### Milestone 5: Package & Publish (Week 11-12)

- [ ] Write comprehensive documentation
- [ ] Add usage examples
- [ ] Set up CI/CD
- [ ] Publish to PyPI as `openehr-sdk`
- [ ] Write Medium article on the journey

**Deliverable:** Published PyPI package with documentation

---

## Technical Decisions

### BMM Format: JSON vs ODIN

**Decision:** Use JSON format (`.bmm.json`)

**Rationale:**
- Python has native JSON parsing
- ODIN requires custom parser or external library
- JSON BMM files are available for RM 1.0.4

### Pydantic Version: v1 vs v2

**Decision:** Pydantic v2

**Rationale:**
- Better performance
- Improved type hints
- Active development
- Aligns with Open CIS stack

### Serialization: Model Methods vs Separate Functions

**Decision:** Both - methods on models + standalone functions

**Rationale:**
- Methods (`composition.to_flat()`) for convenience
- Functions (`to_flat(composition)`) for flexibility and testing

### Package Name

**Decision:** `openehr-sdk`

**Alternatives Considered:**
- `pyopenehr` - Could conflict with abandoned pyEHR
- `openehr-python` - Too generic
- `ehrbase-sdk` - Too specific to one CDR

---

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| BMM files incomplete vs UML specs | Medium | Medium | Cross-reference with Archie Java implementation |
| Complex inheritance breaks Pydantic | High | Low | Test incrementally, use discriminated unions |
| OPT parsing too complex | High | Medium | Start with single template, expand gradually |
| Maintenance burden | Medium | High | Generate code, minimize hand-written logic |
| Borut releases Python SDK first | Low | Low | Collaborate rather than compete |

---

## Dependencies

**External:**
- `github.com/openEHR/specifications-ITS-BMM` - BMM source files
- EHRBase instance for integration testing
- Open CIS templates (IDCR Vital Signs)

**Python Packages:**
- `pydantic>=2.0` - Model definitions
- `httpx` - Async HTTP client
- `jinja2` - Code generation templates
- `lxml` - OPT XML parsing
- `pytest` - Testing
- `mypy` - Type checking

---

## Success Criteria

**Phase 1 Complete When:**
- [ ] All RM 1.0.4 classes generated
- [ ] `mypy --strict` passes
- [ ] Canonical JSON round-trip works

**Phase 2 Complete When:**
- [ ] VitalSignsComposition builder works
- [ ] Open CIS uses SDK instead of manual JSON
- [ ] FLAT format serialization validated against EHRBase

**Project Complete When:**
- [ ] Published on PyPI
- [ ] Documentation site live
- [ ] Medium article published
- [ ] At least one external contributor

---

## Future Considerations

### Additional Templates
- Problem List composition
- Medication Order composition
- Lab Results composition

### Additional Features
- AQL query builder with type safety
- Archetype validation
- Form generation hints (for UI builders)

### Community Building
- openEHR discourse announcement
- Conference talk (openEHR annual conference)
- Integration with other Python health tools (FHIR libraries)

---

## References

- [openEHR BMM Specifications](https://github.com/openEHR/specifications-ITS-BMM)
- [openEHR RM Specification](https://specifications.openehr.org/releases/RM/latest)
- [NeoEHR SDK Approach](https://discourse.openehr.org/t/typescript-library-for-am-rm-opts/5131)
- [OpenAPI from BMM Discussion](https://discourse.openehr.org/t/openapi-schemas-generated-from-bmm-files/2116)
- [MapEHR Documentation](https://mapehr.com/docs/)
- [Archie Java SDK](https://github.com/openEHR/archie) - Reference implementation
- [Open CIS SDK Comparison](./openehr-sdk-comparison.md)

---

## Appendix A: BMM Class Example

**Source:** `openehr_rm_data_types_1.0.4.bmm.json`

```json
{
  "DV_QUANTITY": {
    "name": "DV_QUANTITY",
    "ancestors": ["DV_AMOUNT"],
    "documentation": "Quantitified type representing scientific quantities.",
    "properties": {
      "magnitude": {
        "name": "magnitude",
        "type": "Real",
        "is_mandatory": true
      },
      "precision": {
        "name": "precision", 
        "type": "Integer",
        "is_mandatory": false
      },
      "units": {
        "name": "units",
        "type": "String",
        "is_mandatory": true
      }
    }
  }
}
```

**Generated Pydantic:**

```python
class DvQuantity(DvAmount):
    """Quantitified type representing scientific quantities."""
    
    _type: Literal["DV_QUANTITY"] = Field(default="DV_QUANTITY", alias="_type")
    magnitude: float
    units: str
    precision: Optional[int] = None
```

---

## Appendix B: Template Builder Usage Comparison

**Before (Manual FLAT JSON):**
```python
composition = {
    "ctx/language": "en",
    "ctx/territory": "US",
    "ctx/composer_name": "Dr. Smith",
    "vital_signs/blood_pressure:0/any_event:0/systolic|magnitude": 120,
    "vital_signs/blood_pressure:0/any_event:0/systolic|unit": "mm[Hg]",
    "vital_signs/blood_pressure:0/any_event:0/diastolic|magnitude": 80,
    "vital_signs/blood_pressure:0/any_event:0/diastolic|unit": "mm[Hg]",
    "vital_signs/blood_pressure:0/any_event:0/time": "2026-01-05T10:30:00Z",
    "vital_signs/pulse_heart_beat:0/any_event:0/rate|magnitude": 72,
    "vital_signs/pulse_heart_beat:0/any_event:0/rate|unit": "/min",
    "vital_signs/pulse_heart_beat:0/any_event:0/time": "2026-01-05T10:30:00Z",
}
```

**After (Template Builder):**
```python
from openehr_sdk.templates.idcr_vital_signs import VitalSignsComposition

composition = VitalSignsComposition(composer_name="Dr. Smith")
composition.blood_pressure.add_reading(systolic=120, diastolic=80)
composition.pulse.add_reading(rate=72)

flat_data = composition.to_flat()  # Same output as above
```
