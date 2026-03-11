# Architecture Overview

oehrpy is organized into five core components, each addressing a specific layer of the openEHR integration stack.

## Component Diagram

```
┌─────────────────────────────────────────────────────┐
│                    Your Application                  │
├─────────────┬─────────────┬─────────────────────────┤
│  Template   │    AQL      │      EHRBase            │
│  Builders   │   Builder   │      Client             │
│             │             │                         │
│  OPT → Code │  Fluent API │  Async REST (httpx)     │
├─────────────┴─────────────┴─────────────────────────┤
│              Serialization Layer                     │
│  Canonical JSON  ←→  RM Objects  ←→  FLAT Format    │
├─────────────────────────────────────────────────────┤
│           Reference Model (134 Pydantic classes)     │
│              openEHR RM 1.1.0 + BASE types           │
└─────────────────────────────────────────────────────┘
```

## 1. Reference Model (`openehr_sdk.rm`)

134 Pydantic v2 models generated from the openEHR RM 1.1.0 JSON Schema specification. All classes live in a single `rm_types.py` module to avoid circular imports.

**Key design decisions:**

- UPPERCASE class names (`DV_QUANTITY`, `CODE_PHRASE`) match the openEHR specification
- Generated code — do not edit manually; regenerate with `python -m generator.pydantic_generator`
- Special ruff ignore rules for generated naming conventions (N801, N817)

## 2. Serialization (`openehr_sdk.serialization`)

Two serialization formats for converting between RM objects and wire formats:

- **Canonical JSON** (`canonical.py`) — openEHR standard format with `_type` discriminator fields
- **FLAT Format** (`flat.py`) — EHRBase-specific format that flattens hierarchical compositions into dot-separated key-value pairs

**FLAT path structure:**

```
template_id/section/observation:index/event:index/element|attribute
```

Example: `vital_signs_observations/vital_signs/blood_pressure:0/any_event:0/systolic|magnitude`

## 3. Template System (`openehr_sdk.templates`)

- **OPT Parser** — Parses OPT 1.4 XML files using `defusedxml`
- **Builder Generator** — Auto-generates type-safe Python builder classes from parsed templates
- **Pre-built Builders** — Ships with `VitalSignsBuilder` for common use cases

**Workflow:** OPT XML → Parser → Template Definition → Builder Generator → Python Builder Class

## 4. EHRBase Client (`openehr_sdk.client`)

Async REST client using `httpx` for EHRBase CDR operations:

- EHR creation and retrieval
- Composition CRUD (CANONICAL, FLAT, STRUCTURED formats)
- AQL query execution with parameterized queries

## 5. AQL Query Builder (`openehr_sdk.aql`)

Fluent API for building AQL queries without string concatenation. Supports SELECT, FROM, WHERE, ORDER BY, and LIMIT clauses with archetype containment paths.

## Code Generation

The `generator/` package (not part of the runtime SDK) contains:

- **BMM Parser** — Parses BMM JSON specifications from `specifications-ITS-BMM`
- **JSON Schema Parser** — Parses JSON Schema files from `specifications-ITS-JSON`
- **Pydantic Generator** — Renders Pydantic v2 model code from parsed schemas

All 134 RM classes are generated into the single `rm_types.py` module.
