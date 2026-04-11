# PRD: OPT (Operational Template) Validator for oehrpy

**Status:** Draft
**Version:** 0.1
**Target Release:** oehrpy v0.2.0 (alongside FLAT validator)
**Author:** Chregi
**Date:** 2026-03-12

---

## 1. Overview

### 1.1 Background

oehrpy already includes an `OPTParser` that reads OPT 1.4 XML files into a `TemplateDefinition` object. This parser is used today to **generate builder classes** from templates. What it does not do is tell you whether the OPT itself is well-formed, internally consistent, and likely to be accepted by EHRBase.

Uploading a broken OPT to EHRBase produces terse, unhelpful errors — or worse, it silently accepts the file and then rejects compositions against it later with no clear traceability back to the template defect. There is currently no offline pre-flight check for OPT files.

### 1.2 The Problem in Practice

OPT files are authored in tools like **Archetype Designer** (CKM) and exported as XML. Common failure modes before a template even reaches the CDR:

| Failure | How it manifests |
|---------|-----------------|
| Missing required XML elements (`template_id`, `concept`, `language`) | EHRBase returns HTTP 400 with a Java stack trace |
| Archetype reference uses wrong format or missing version | Template uploads but compositions fail at runtime |
| Mandatory node (`occurrences min=1`) with no `name` in ontology | Builder generation silently produces broken code |
| Terminology binding references a code that doesn't exist in the ontology section | FLAT paths with `\|code` suffix silently map to nothing |
| Duplicate `node_id` values within the same archetype scope | Ambiguous path resolution; CDR behaviour is undefined |
| Cardinality contradictions (`min > max`, `min=1 max=0`) | Parser may silently ignore the constraint |
| `rm_type_name` on a node that doesn't exist in the openEHR RM | Template uploads but AQL queries return nothing |
| UTF-8 encoding issues in term definitions (accented characters, em-dashes) | Terminology display breaks in forms |

These issues are time-consuming to debug because the feedback loop runs through EHRBase. An offline validator short-circuits that loop.

### 1.3 Relationship to the FLAT Validator

The **FLAT validator** (PRD `flat-validator`) checks whether a *composition* matches a template. The **OPT validator** checks whether the *template itself* is structurally sound. They are complementary:

```
OPT file → [OPT Validator] → Upload to EHRBase → Web Template
FLAT composition → [FLAT Validator] → Submit to EHRBase
```

Both validators share the `oehrpy.validation` module namespace and the same CLI entry point (`oehrpy validate`).

---

## 2. Goals

| Goal | Priority |
|------|----------|
| Validate required top-level OPT fields are present and non-empty | P0 |
| Validate `template_id` format and naming conventions | P0 |
| Validate all referenced archetype IDs follow `openEHR-RM-CLASS.concept.vN` format | P0 |
| Detect duplicate `node_id` values within scope | P0 |
| Validate occurrences constraints (min ≤ max, no negative values) | P0 |
| Validate every `node_id` has a corresponding ontology term definition | P1 |
| Validate terminology bindings reference codes present in the ontology | P1 |
| Validate `rm_type_name` values are known openEHR RM types | P1 |
| Detect missing mandatory names that would break FLAT path generation | P1 |
| Validate XML encoding (UTF-8, no null bytes, well-formed) | P1 |
| Report structural warnings (suspicious patterns that may cause issues) | P2 |
| CLI: `oehrpy validate-opt` command | P0 |
| Python API: `OPTValidator` class | P0 |

### Out of Scope (v0.2.0)

- Full AOM 2 constraint semantics (interval logic, regular expressions on C_STRING)
- Cross-archetype consistency (checking that referenced archetypes in slots actually exist in CKM)
- ADL 1.4 / ADL 2 source file validation (only compiled OPT XML)
- OPT 2.0 (JSON format) — validate OPT 1.4 XML only
- Validation of `ARCHETYPE_SLOT` include/exclude expressions beyond basic XML well-formedness

---

## 3. User Stories

### Modeler uploading a new template

> *"I exported an OPT from Archetype Designer and want to make sure it's clean before uploading to EHRBase. I want a single command that tells me if there are any issues — before I waste 20 minutes debugging a cryptic server error."*

### Developer running CI on a clinical knowledge repository

> *"We store our OPT files in Git. I want `oehrpy validate-opt` to run in our CI pipeline on every PR that touches a `.opt` file, so broken templates never reach our staging environment."*

### oehrpy builder generator user

> *"When I run `generate_builder_from_opt('my_template.opt')`, I want the generator to first validate the OPT and fail fast with a clear message if the template has issues that would produce broken Python code."*

---

## 4. Functional Requirements

### 4.1 Validation Categories

#### Category A — Well-formedness (errors)

These checks must all pass for the OPT to be considered valid. Failures block upload to any CDR.

**A1. XML Integrity**
- File is valid, well-formed XML
- Root element is `template` with the correct namespace (`http://schemas.openehr.org/v1`)
- Encoding declaration is UTF-8 (or compatible); no null bytes or invalid code points in text nodes

**A2. Required Top-Level Fields**

| Field (XPath) | Requirement |
|---------------|-------------|
| `template_id/value` | Present, non-empty, matches allowed character set `[a-zA-Z0-9 ._\-]` |
| `concept` | Present, non-empty |
| `language/code_string` | Present, valid ISO 639-1 two-letter code |
| `language/terminology_id/value` | Present, must be `ISO_639-1` |
| `description/lifecycle_state` | Present (warn if not `published`) |
| `definition/rm_type_name` | Present, must be `COMPOSITION` for a template root |
| `definition/archetype_id/value` | Present, must match `openEHR-EHR-COMPOSITION.*` |

**A3. Archetype ID Format**

All `archetype_id/value` elements in the tree must match:
```
openEHR-<rm_originator>-<rm_class>.<concept_name>.<version>
```
Where:
- `rm_originator` is typically `EHR`
- `rm_class` is a known RM class (see A5)
- `concept_name` is snake_case
- `version` is `v` followed by a positive integer (e.g., `v1`, `v2`)

Invalid examples that must be caught:
```
openEHR-EHR-OBSERVATION.blood_pressure   ← missing version
openEHR-EHR-Observation.blood_pressure.v1 ← wrong case on RM class
blood_pressure.v1                          ← missing namespace
```

**A4. Duplicate node_id Detection**

Within each archetype's scope (bounded by `archetype_id/value`), all `node_id` values must be unique. Duplicate `node_id` values within the same archetype scope are an error. Duplicates across different archetypes are expected and allowed.

**A5. RM Type Name Validation**

All `rm_type_name` elements must be known openEHR RM 1.1.0 types. Unknown types are errors. The valid set includes all types from oehrpy's existing RM class registry (134 types).

Critical structural types that are commonly misspelled:
- `COMPOSITION`, `SECTION`, `OBSERVATION`, `EVALUATION`, `INSTRUCTION`, `ACTION`
- `ITEM_TREE`, `ITEM_LIST`, `ITEM_SINGLE`, `ITEM_TABLE`
- `CLUSTER`, `ELEMENT`
- `HISTORY`, `POINT_EVENT`, `INTERVAL_EVENT`
- `DV_QUANTITY`, `DV_CODED_TEXT`, `DV_TEXT`, `DV_DATE_TIME`, etc.

**A6. Occurrences Constraint Validity**

For every `occurrences` element:
- `lower` must be a non-negative integer
- `upper` must be >= `lower` (unless `upper_unbounded` is `true`)
- If `upper_unbounded` is `false`, `upper` must be present
- `lower_unbounded` should always be `false` for occurrences (warn if `true`)

#### Category B — Semantic Integrity (errors)

**B1. Ontology Completeness**

Every `node_id` value appearing in the `definition` tree must have a corresponding `term_definition` entry in the `ontology/term_definitions` section for the template's primary language.

Missing term definitions cause:
- FLAT paths to use `node_id` instead of human-readable names (breaking path construction)
- Builder generator to emit `None` names for fields
- Forms to display raw codes instead of labels

**B2. Terminology Binding Consistency**

Every `term_binding` in the ontology must:
- Reference a `node_id` that exists in the `definition` tree
- Reference a `terminology_id` that is declared in `terminologies_available`

Orphan terminology bindings (binding for a node that no longer exists in the tree) are errors — they indicate the template was edited without updating the bindings.

**B3. Mandatory Node Name Coverage**

Any node with `occurrences/lower >= 1` (mandatory) must have:
- A non-empty `name` or a term definition that resolves to a non-empty name
- A consistent `rm_type_name` that is valid for its position in the RM hierarchy

Mandatory nodes missing names will produce builder methods that cannot be called, breaking code generation.

#### Category C — Structural Warnings

These patterns are not necessarily errors but are worth flagging:

| Warning | Condition |
|---------|-----------|
| `lifecycle_state` is not `published` | Template marked as `draft` or `in_development` |
| Archetype version is `v0` | Experimental/unstable archetype reference |
| Node has `max=0` (prohibited) | Node exists in tree but is prohibited — likely an accidental inclusion |
| `ARCHETYPE_SLOT` with no include/exclude expressions | Unconstrained slot accepts any archetype — may be intentional but worth noting |
| Template concept contains spaces that will affect FLAT path prefix | The concept name converts to the composition tree ID; spaces become underscores |
| No `description/details` provided | Missing documentation |
| Same archetype used more than 3 times in one template | May indicate over-specialization of a generic archetype |
| Node name contains special characters that complicate FLAT paths | `/`, `\`, `|`, `:` in term definitions |

#### Category D — FLAT Path Impact Analysis

> **ADR-0005 Note (2026-04-04):** FLAT paths cannot be reliably derived from
> OPT XML. The CDR applies undocumented normalisation rules when converting
> OPT to Web Template, so any OPT-based FLAT path preview is **illustrative
> only**. The authoritative FLAT paths come from the Web Template JSON
> (fetched via `EHRBaseClient.get_web_template()` or the CDR's
> `/example?format=FLAT` endpoint after upload).

This category connects OPT validation to FLAT format usage. It provides
**informational hints** about potential FLAT path implications, not
authoritative path derivation:

**D1. Name-to-path mapping preview (informational)**

Show how each top-level concept *might* appear in FLAT paths, with an
explicit caveat that the CDR's normalisation rules may produce different
results:

```
Template concept: "IDCR - Adverse Reaction List.v1"
  -> Possible composition tree ID: "idcr___adverse_reaction_list_v1" (illustrative)
  Note: The actual FLAT path prefix is determined by the CDR when the OPT
    is uploaded. Verify against the Web Template or /example?format=FLAT.
```

**D2. Renamed nodes (informational)**

Flag any node where the ontology term name differs significantly from the `node_id`. At the OPT level, this is detectable when:

- `node_id` is `at0002` and the term definition is `"Causative agent"` — the Web Template may use `causative_agent` instead of the original archetype name

Report these as informational hints. The actual FLAT path segment is
determined by the Web Template `id` field, not by OPT analysis.

---

### 4.2 Validation Result Model

```python
@dataclass
class OPTValidationIssue:
    severity: Literal["error", "warning", "info"]
    category: Literal["wellformedness", "semantic", "structural", "flat_impact"]
    code: str                    # e.g., "MISSING_TEMPLATE_ID", "DUPLICATE_NODE_ID"
    message: str
    xpath: str | None = None     # XPath to the offending element in the OPT XML
    node_id: str | None = None   # The at-code involved, if applicable
    archetype_id: str | None = None
    suggestion: str | None = None

@dataclass
class OPTValidationResult:
    is_valid: bool               # True only if zero errors
    template_id: str | None
    concept: str | None
    issues: list[OPTValidationIssue]
    node_count: int              # Total number of nodes parsed
    archetype_count: int         # Number of distinct archetypes referenced
    error_count: int
    warning_count: int
```

### 4.3 Python API

```python
from oehrpy.validation import OPTValidator

# From file path
validator = OPTValidator()
result = validator.validate_file("path/to/adverse_reaction.opt")

# From XML string
result = validator.validate_string(xml_content)

# From already-parsed TemplateDefinition (integrates with existing parser)
from oehrpy.templates import parse_opt
template = parse_opt("adverse_reaction.opt")
result = validator.validate_template(template)

# Check results
if not result.is_valid:
    for issue in result.issues:
        if issue.severity == "error":
            print(f"[{issue.code}] {issue.message}")
            if issue.xpath:
                print(f"  at: {issue.xpath}")
            if issue.suggestion:
                print(f"  -> {issue.suggestion}")

for issue in result.issues:
    if issue.severity == "warning":
        print(f"Warning: {issue.message}")
```

### 4.4 CLI Interface

```bash
# Validate a single OPT file
oehrpy validate-opt path/to/template.opt

# Validate multiple files (glob)
oehrpy validate-opt templates/*.opt

# JSON output (for CI/CD integration)
oehrpy validate-opt template.opt --output json

# Strict mode: treat warnings as errors
oehrpy validate-opt template.opt --strict

# Show FLAT path impact analysis
oehrpy validate-opt template.opt --show-flat-paths

# Validate and then generate builder (fail fast pattern)
oehrpy validate-opt template.opt && python -m oehrpy.templates.generate template.opt
```

---

## 5. Module Structure

The OPT validator lives alongside the FLAT validator in `oehrpy.validation`:

```
src/oehrpy/
└── validation/
    ├── __init__.py             # Public API: FlatValidator, OPTValidator, results
    ├── path_checker.py         # FLAT validation (existing)
    ├── web_template.py         # FLAT validation (existing)
    └── opt/
        ├── __init__.py         # OPTValidator class
        ├── xml_checks.py       # Category A: Well-formedness checks
        ├── semantic_checks.py  # Category B: Semantic integrity checks
        ├── structural_checks.py # Category C: Structural warnings
        ├── flat_impact.py      # Category D: FLAT path impact analysis
        ├── rm_types.py         # Known RM type registry (reused from oehrpy.rm)
        └── issue_codes.py      # All OPT_* error/warning code constants
```

---

## 6. Integration with Existing oehrpy Code

### 6.1 OPTParser Integration

The existing `OPTParser.parse_file()` and `parse_string()` methods will gain an optional `validate: bool = False` parameter:

```python
# Current behaviour (unchanged)
template = parse_opt("template.opt")

# New opt-in validation
template = parse_opt("template.opt", validate=True)
# Raises OPTValidationError if errors found
# OPTValidationError.result contains the full OPTValidationResult
```

### 6.2 Builder Generator Integration

`generate_builder_from_opt()` will validate by default (can be disabled with `validate=False`):

```python
# Will validate the OPT before generating — raises OPTValidationError on errors
code = generate_builder_from_opt("template.opt")

# Skip validation (not recommended)
code = generate_builder_from_opt("template.opt", validate=False)
```

### 6.3 Shared RM Type Registry

Category A5 requires a list of all valid RM type names. This list already effectively exists in `oehrpy.rm` (134 Pydantic models). The validator will import the model registry directly rather than maintaining a separate list, ensuring the validator and the SDK stay in sync automatically.

---

## 7. Error Code Reference

All validation issues use namespaced codes for programmatic handling:

| Code | Category | Severity | Description |
|------|----------|----------|-------------|
| `XML_INVALID` | A | Error | File is not valid XML |
| `XML_WRONG_NAMESPACE` | A | Error | Root element has wrong namespace |
| `XML_ENCODING_ISSUE` | A | Error | Invalid characters in text nodes |
| `MISSING_TEMPLATE_ID` | A | Error | `template_id/value` absent or empty |
| `INVALID_TEMPLATE_ID_FORMAT` | A | Error | Template ID contains invalid characters |
| `MISSING_CONCEPT` | A | Error | `concept` element absent or empty |
| `MISSING_LANGUAGE` | A | Error | `language` element absent |
| `INVALID_LANGUAGE_CODE` | A | Error | Not a valid ISO 639-1 code |
| `INVALID_ROOT_RM_TYPE` | A | Error | Root `rm_type_name` is not `COMPOSITION` |
| `INVALID_ARCHETYPE_ID_FORMAT` | A | Error | Archetype ID does not match required pattern |
| `DUPLICATE_NODE_ID` | A | Error | Duplicate `node_id` within archetype scope |
| `INVALID_RM_TYPE` | A | Error | `rm_type_name` not in RM 1.1.0 type registry |
| `INVALID_OCCURRENCES` | A | Error | Occurrences `min > max` or negative values |
| `MISSING_TERM_DEF` | B | Error | `node_id` has no ontology term definition |
| `ORPHAN_TERMINOLOGY_BINDING` | B | Error | Binding references non-existent `node_id` |
| `MANDATORY_NODE_NO_NAME` | B | Error | Required node (min>=1) has no resolvable name |
| `DRAFT_LIFECYCLE` | C | Warning | Template not in `published` state |
| `UNSTABLE_ARCHETYPE_VERSION` | C | Warning | Archetype reference uses `v0` |
| `PROHIBITED_NODE_IN_TREE` | C | Warning | Node with `max=0` is included in the tree |
| `UNCONSTRAINED_ARCHETYPE_SLOT` | C | Warning | Slot with no include/exclude |
| `CONCEPT_SPECIAL_CHARS` | C | Warning | Concept name has chars that complicate FLAT prefix |
| `RENAMED_NODE_DETECTED` | D | Info | Node renamed in template; FLAT path differs from archetype default |
| `FLAT_PATH_COLLISION` | D | Warning | Two nodes produce the same FLAT path segment |

---

## 8. Implementation Plan

### Phase 1 — Core Validator (v0.2.0, alongside FLAT validator)

| Task | Effort |
|------|--------|
| Module scaffold (`opt/` directory, `OPTValidator` class) | 0.5 day |
| Category A: XML well-formedness + required fields | 1 day |
| Category A: Archetype ID format validation | 0.5 day |
| Category A: Duplicate node_id detection | 0.5 day |
| Category A: RM type name validation (reuse RM registry) | 0.5 day |
| Category A: Occurrences constraint validity | 0.5 day |
| Category B: Ontology completeness check | 1 day |
| Category B: Terminology binding consistency | 1 day |
| Category B: Mandatory node name coverage | 0.5 day |
| Category C: Structural warnings | 1 day |
| Category D: FLAT path impact analysis + renamed node detection | 1 day |
| `OPTValidationResult` dataclasses + issue codes | 0.5 day |
| OPTParser integration (`validate` parameter) | 0.5 day |
| Builder generator integration (validate by default) | 0.5 day |
| CLI (`oehrpy validate-opt`) | 1 day |
| Unit tests (one test file per check category) | 2 days |
| **Total** | **~12 days** |

### Phase 2 — Enhanced Checks (v0.3.0)

| Task | Effort |
|------|--------|
| C_STRING pattern validation (regex syntax checking) | 1 day |
| Interval constraint logic validation (C_REAL, C_INTEGER bounds) | 1.5 days |
| ARCHETYPE_SLOT include/exclude expression validation | 2 days |
| Cross-archetype slot resolution (check CKM or local archetype library) | 3 days |
| OPT 2.0 (JSON format) support | 3 days |
| **Total** | **~10.5 days** |

---

## 9. Open Questions

| Question | Decision needed by |
|----------|--------------------|
| Should `validate=True` be the default in `parse_opt()` or opt-in? Changing default is a breaking change for current users. | v0.2.0 start |
| Should the OPT validator also try to upload the template to a local EHRBase instance as a final integration check, if `--ehrbase-url` is provided? | Phase 2 |
| The CaboLabs openEHR-SDK (Java) has a more complete OPT validator. Should we cross-reference their check list and adopt any missing rules? | Phase 1 end |
| For Category D (FLAT path impact), should we generate the full expected FLAT path set and output it as a reference file alongside the OPT? | Phase 1 end |
