# PRD-0004: Dynamic Composition Builders

**Version:** 1.0
**Date:** 2026-01-31
**Status:** Partially Superseded
**Owner:** Open CIS Project
**Priority:** P1 (High)

> **ADR-0005 Impact (2026-04-04):** This PRD assumes that FLAT paths can be
> derived from OPT XML at build time or runtime. ADR-0005 established that
> FLAT paths **must** come from the Web Template JSON provided by the CDR, not
> from OPT XML. The following requirements are affected:
>
> - **FR-1 (Runtime Builder Factory):** `from_opt()` cannot produce correct
>   FLAT paths. A future implementation should accept a Web Template JSON
>   instead, e.g. `CompositionBuilder.from_web_template(wt_json)`.
> - **FR-2 (CLI Generation):** The generator now produces metadata-only
>   skeletons. FLAT paths are not included in generated code.
> - **FR-3 (Pre-built Builders):** VitalSignsBuilder already sources paths
>   from the Web Template. Future builders should follow the same pattern.
> - **FR-4 (Constraint Validation):** Constraints should be derived from
>   the Web Template tree (`min`, `max`, `inputs`), not from OPT XML.
>
> The goals of this PRD remain valid; only the **input source** changes from
> OPT XML to Web Template JSON for any FLAT-path-related functionality.

---

## Executive Summary

Unlock oehrpy's existing OPT parser and template generator so that developers can generate type-safe composition builders from any OPT file — at build time or at runtime. Ship a small set of pre-built builders for common clinical document types alongside the generic capability.

---

## Problem Statement

oehrpy ships a single hand-crafted `VitalSignsBuilder`. The OPT parser (`opt_parser.py`) and builder generator (`builder_generator.py`) exist in the codebase and can already produce builder classes from OPT files, but:

1. **The capability is undiscoverable** — There is no public API or CLI command to generate a builder from an OPT file. The only example is a script in `examples/`.
2. **No runtime generation** — Developers must run a script, capture the output, and paste it into their project. There is no way to load a template and get a builder object at runtime.
3. **Only one pre-built builder** — `VitalSignsBuilder` covers one template. Common clinical document types (medications, problem lists, lab results) have no builder support.
4. **No validation against template constraints** — Generated builders set FLAT paths but do not enforce cardinality, mandatory fields, or terminology bindings from the OPT.

---

## Requirements

### Functional Requirements

#### FR-1: Runtime Builder Factory

```python
from oehrpy.templates import CompositionBuilder

# Load from a local OPT file
builder = CompositionBuilder.from_opt("path/to/medication_order.opt")

# Use the builder with FLAT format
composition = (
    builder
    .set("medication/order:0/medication_item|value", "Amoxicillin")
    .set("medication/order:0/dose|magnitude", 500)
    .set("medication/order:0/dose|unit", "mg")
    .build()
)
```

- Parse the OPT at runtime and return a builder instance with template-aware path helpers
- Builder must produce valid FLAT format output

#### FR-2: CLI / Script Generation (improve existing)

```bash
# Generate a builder module from an OPT file
python -m oehrpy.templates.generate path/to/template.opt --output my_builder.py
```

- Wrap the existing `builder_generator.py` in a proper CLI entry point
- Generated code should be a self-contained Python module that can be imported

#### FR-3: Pre-built Builders

Ship builders for commonly used openEHR templates:

| Builder | Template |
|---|---|
| `VitalSignsBuilder` | (already exists) |
| `MedicationOrderBuilder` | Medication order / prescription |
| `ProblemListBuilder` | Problem / diagnosis list |
| `LabResultBuilder` | Laboratory result report |

Pre-built builders should be generated from OPT files included in the repository under `templates/`.

#### FR-4: Template Constraint Validation (optional / stretch)

Builders optionally validate values against OPT constraints:
- Required fields raise an error on `build()` if missing
- Cardinality constraints (max occurrences) enforced on indexed paths
- Terminology bindings validated for coded fields

### Non-Functional Requirements

- **NFR-1**: Runtime builder creation from an OPT file must complete in under 500ms for typical templates
- **NFR-2**: Generated builder code must pass ruff and mypy checks
- **NFR-3**: Pre-built builders must be importable from `oehrpy.templates.builders`

---

## Testing Strategy

- **Unit tests**:
  - `from_opt()` produces a builder with correct paths for the Vital Signs OPT (already in repo)
  - CLI generation produces importable, lint-clean Python code
  - Pre-built builders produce valid FLAT output
- **Integration tests**: Compositions built with generated builders are accepted by EHRBase 2.0
- **Round-trip**: Generate builder → build composition → upload → retrieve → verify content

---

## Success Criteria

1. `CompositionBuilder.from_opt()` works for any valid OPT 1.4 file
2. CLI entry point generates importable builder modules
3. At least 3 pre-built builders ship alongside `VitalSignsBuilder`
4. All generated compositions pass EHRBase validation in integration tests
