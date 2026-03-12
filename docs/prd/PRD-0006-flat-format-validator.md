# PRD-0006: FLAT Format Validator for oehrpy

**Status:** Draft
**Version:** 0.1
**Target Release:** oehrpy v0.2.0
**Author:** Chregi
**Date:** 2026-03-12

---

## 1. Overview

### 1.1 Problem Statement

Developing with openEHR's FLAT format is painful. When you submit an invalid composition to EHRBase or Better, the error messages are cryptic and unhelpful:

```
ValidationError: Could not consume Parts [
    adverse_reaction_list/adverse_reaction/causative_agent|value,
    adverse_reaction_list/adverse_reaction/causative_agent|code
]
```

There is no way to know *why* a path is invalid before hitting the CDR. Common causes include:

- **Template renames**: A template renames `at0002` from "Substance/Agent" to "Causative agent", changing the FLAT path from `substance` to `causative_agent` — with no warning
- **Platform divergence**: EHRBase 2.x dropped `:0` indexing and `/any_event/` nodes; Better still uses them
- **Missing required fields**: `category`, `language`, `territory`, `composer`, `context/start_time` are silently mandatory
- **Wrong data type suffixes**: Using `|value` on a `DV_QUANTITY` instead of `|magnitude`
- **Stale paths**: Paths built from outdated documentation or old web templates

The only current workaround is to submit, fail, read the cryptic error, guess, and repeat.

### 1.2 Proposed Solution

Add a `FlatValidator` module to oehrpy that:

1. Parses a Web Template JSON (fetched from the CDR or provided as a file)
2. Enumerates all valid FLAT paths from the `tree` structure
3. Validates a given FLAT composition against those paths
4. Reports **human-readable errors** with "did you mean?" suggestions for typos and renames
5. Supports both **EHRBase** and **Better** platform dialects

Additionally, ship a **GitHub Pages web app** so the validator is accessible to anyone without Python — just paste your Web Template and FLAT composition and click Validate.

---

## 2. Goals

| Goal | Priority |
|------|----------|
| Catch invalid FLAT paths before submission to CDR | P0 |
| Identify missing required composition fields | P0 |
| Provide "did you mean?" suggestions for invalid paths | P1 |
| Support both EHRBase 2.x and Better platform dialects | P1 |
| Validate data type attribute suffixes (`|magnitude`, `|unit`, etc.) | P1 |
| Zero-dependency web UI on GitHub Pages | P2 |
| CLI tool (`oehrpy validate-flat`) | P2 |
| Python API for programmatic use in Open CIS backend | P0 |

### Out of Scope (v0.2.0)

- Validating *values* (e.g., whether a SNOMED code is valid)
- Full RM constraint validation (occurrences, cardinality)
- Support for ECISFLAT format
- Archetype-level validation beyond the Web Template

---

## 3. User Stories

### Developer integrating a new template

> *"I just modeled a new Adverse Reaction template in the Clinical Knowledge Manager. The designer renamed a node. Now my FLAT payloads are failing with 'Could not consume Parts'. I want to paste my Web Template and my FLAT JSON and immediately see which paths are wrong and what they should be."*

### DevOps / CI pipeline

> *"I want to run `oehrpy validate-flat --template wt.json --composition comp.json` in our CI pipeline so that template renames don't silently break our submissions in production."*

### openEHR newcomer

> *"I'm learning openEHR and don't understand FLAT format yet. I want a tool that explains what fields are required and shows me valid example paths."*

---

## 4. Functional Requirements

### 4.1 Core Validation Engine (`oehrpy.validation`)

#### 4.1.1 Web Template Parser

- Parse the EHRBase Web Template JSON format (`GET /rest/openehr/v1/definition/template/adl1.4/{id}`)
- Traverse the `tree` recursively to enumerate all valid nodes
- Extract per-node metadata: `id`, `name`, `rm_type`, `aql_path`, `children`
- Support the `localizedNames` field for alias detection (renamed nodes)

#### 4.1.2 Path Enumerator

Generate the full set of valid FLAT paths for a given platform:

**EHRBase 2.x mode:**
- Prefix: `tree.id` (composition tree ID, e.g., `adverse_reaction_list`)
- No `:0` index notation for single-occurrence items
- `:N` index only for multi-occurrence items (arrays)
- No `/any_event/` intermediate nodes
- Direct element paths: `adverse_reaction_list/adverse_reaction/causative_agent`

**Better mode:**
- Prefix: Template ID
- `:0` index notation always present
- `/any_event:0/` nodes included
- e.g., `adverse_reaction_list/adverse_reaction:0/causative_agent:0`

#### 4.1.3 Data Type Suffix Validation

For each leaf node, validate that the `|` suffixes used are valid for the node's `rm_type`:

| rm_type | Valid suffixes |
|---------|---------------|
| `DV_QUANTITY` | `|magnitude`, `|unit`, `|precision` |
| `DV_CODED_TEXT` | `|value`, `|code`, `|terminology` |
| `DV_TEXT` | (none, or `|value`) |
| `DV_DATE_TIME` | (none) |
| `DV_ORDINAL` | `|value`, `|code`, `|terminology`, `|ordinal` |
| `DV_BOOLEAN` | (none) |
| `DV_COUNT` | `|magnitude` |

#### 4.1.4 Required Fields Check

Flag missing required composition-level fields:

```
{tree_id}/category|code
{tree_id}/category|value
{tree_id}/category|terminology
{tree_id}/language|code
{tree_id}/language|terminology
{tree_id}/territory|code
{tree_id}/territory|terminology
{tree_id}/composer|name
{tree_id}/context/start_time
{tree_id}/context/setting|code
{tree_id}/context/setting|value
{tree_id}/context/setting|terminology
```

#### 4.1.5 "Did You Mean?" Suggestions

For each invalid path, compute fuzzy similarity against all valid paths and suggest the closest match(es). Use Levenshtein distance or similar. This is the key UX feature — the `substance` → `causative_agent` case should produce:

```
✗ adverse_reaction_list/adverse_reaction/substance|value
  Path segment 'substance' not found under 'adverse_reaction'.
  Did you mean 'causative_agent'? (node renamed in template)
  Valid path: adverse_reaction_list/adverse_reaction/causative_agent|value
```

#### 4.1.6 Validation Result Model

```python
@dataclass
class ValidationError:
    path: str
    error_type: Literal["unknown_path", "wrong_suffix", "missing_required", "index_mismatch"]
    message: str
    suggestion: str | None = None
    valid_alternatives: list[str] = field(default_factory=list)

@dataclass
class ValidationResult:
    is_valid: bool
    errors: list[ValidationError]
    warnings: list[ValidationError]
    platform: Literal["ehrbase", "better"]
    template_id: str
    valid_path_count: int
    checked_path_count: int
```

### 4.2 Python API

```python
from oehrpy.validation import FlatValidator

# Initialize with a Web Template
validator = FlatValidator.from_web_template(web_template_dict, platform="ehrbase")

# Or fetch directly from EHRBase
validator = await FlatValidator.from_ehrbase(
    client=ehrbase_client,
    template_id="IDCR - Adverse Reaction List.v1"
)

# Validate a FLAT composition
result = validator.validate(flat_composition_dict)

if not result.is_valid:
    for error in result.errors:
        print(f"✗ {error.path}: {error.message}")
        if error.suggestion:
            print(f"  → Did you mean: {error.suggestion}?")
```

### 4.3 CLI Interface

```bash
# Validate using a local web template file
oehrpy validate-flat \
  --web-template wt.json \
  --composition comp.json \
  --platform ehrbase

# Validate fetching the web template from EHRBase
oehrpy validate-flat \
  --ehrbase-url http://localhost:8080/ehrbase \
  --template-id "IDCR - Adverse Reaction List.v1" \
  --composition comp.json

# Output formats
oehrpy validate-flat ... --output json   # machine-readable
oehrpy validate-flat ... --output text   # human-readable (default)
oehrpy validate-flat ... --output github # GitHub Actions annotation format
```

Exit codes: `0` = valid, `1` = invalid, `2` = tool error.

### 4.4 GitHub Pages Web Tool

A single-file `index.html` deployable to `platzhersh.github.io/oehrpy/validator`:

- **Left panel**: Paste Web Template JSON
- **Right panel**: Paste FLAT Composition JSON
- **Platform toggle**: EHRBase / Better
- **Validate button**: Runs validation in-browser (pure JS, no backend)
- **Results panel**: Error list with highlighting, "did you mean?" inline
- **Path explorer**: Collapsible tree view of all valid paths derived from the Web Template
- **Example loader**: Pre-load example Web Template + invalid composition to demo the tool

No server required. All validation logic reimplemented in JavaScript (or compiled from Python via Pyodide — see Section 6).

---

## 5. Non-Functional Requirements

| Requirement | Target |
|-------------|--------|
| Validation speed | < 200ms for a 50-field FLAT composition |
| Web Template parse time | < 100ms |
| Zero network requests in web tool | Required (pure client-side) |
| Python 3.10+ compatibility | Required |
| No new mandatory dependencies | Use `difflib` (stdlib) for fuzzy matching |
| Optional dependency for CLI | `click` (already in oehrpy dev deps) |

---

## 6. Technical Design

### 6.1 Module Structure

```
src/openehr_sdk/
└── validation/
    ├── __init__.py          # Public API: FlatValidator, ValidationResult, ValidationError
    ├── web_template.py      # Web Template parser + path enumerator
    ├── path_checker.py      # Path validation logic + suffix checking
    ├── suggestions.py       # Fuzzy matching for "did you mean?"
    ├── required_fields.py   # Required field definitions per platform
    └── platforms.py         # EHRBase vs Better dialect configuration
```

### 6.2 Web Template Tree Traversal

The Web Template `tree` is a recursive structure:

```json
{
  "id": "adverse_reaction_list",
  "name": "Adverse Reaction List",
  "rmType": "COMPOSITION",
  "children": [
    {
      "id": "adverse_reaction",
      "name": "Adverse Reaction",
      "rmType": "EVALUATION",
      "children": [
        {
          "id": "causative_agent",
          "name": "Causative agent",
          "rmType": "DV_CODED_TEXT",
          "localizedNames": { "en": "Causative agent" },
          "originalName": "Substance/Agent"
        }
      ]
    }
  ]
}
```

The traversal builds a flat map of `path → node_metadata` which drives all validation.

### 6.3 Web Tool Implementation Options

**Option A (Recommended): Pure JavaScript reimplementation**
- Port the tree traversal and path validation logic to JS
- No Python runtime needed, instant load, works offline
- Simpler deployment

**Option B: Pyodide**
- Run actual Python oehrpy code in the browser via WebAssembly
- Always in sync with the Python implementation
- ~10MB initial load, slower startup

Recommend Option A for v0.2.0, Option B as future enhancement.

---

## 7. Implementation Plan

### Phase 1 — Core Validator (oehrpy v0.2.0)

| Task | Effort |
|------|--------|
| Web Template parser (`web_template.py`) | 1 day |
| Path enumerator (EHRBase dialect) | 1 day |
| Path enumerator (Better dialect) | 0.5 day |
| Required fields checker | 0.5 day |
| Data type suffix validator | 1 day |
| Fuzzy "did you mean?" suggestions | 0.5 day |
| ValidationResult dataclasses | 0.5 day |
| Python API + unit tests | 1 day |
| **Total** | **~6 days** |

### Phase 2 — CLI + Web Tool (oehrpy v0.2.0)

| Task | Effort |
|------|--------|
| CLI (`oehrpy validate-flat`) | 1 day |
| GitHub Pages HTML tool (JS validation engine) | 2 days |
| Path explorer tree view | 1 day |
| Example compositions + web templates | 0.5 day |
| **Total** | **~4.5 days** |

### Phase 3 — Future (v0.3.0)

- Pyodide integration (run real Python in browser)
- VS Code extension (validate on save)
- OpenAPI spec for hosted validator endpoint
- Integration with Open CIS backend (pre-submission validation)

---

## 8. Success Metrics

- Zero "Could not consume Parts" errors from path issues in Open CIS production
- Validator catches the `substance` → `causative_agent` rename in < 200ms
- Web tool accessible without any installation
- Community adoption: validator linked from oehrpy README and openEHR discourse

---

## 9. Open Questions

| Question | Decision needed by |
|----------|--------------------|
| Should `FlatValidator` be a sync or async class? | Phase 1 start |
| Does the web tool need to support uploading Web Template files (not just paste)? | Phase 2 start |
| Should Better platform support be community-contributed given we primarily use EHRBase? | Phase 1 start |
| Should we add a `--strict` mode that fails on warnings too? | Phase 1 end |

---

## Appendix A: Example Validation Output

```
oehrpy validate-flat --web-template wt.json --composition comp.json

Validating FLAT composition against template: IDCR - Adverse Reaction List.v1
Platform: EHRBase 2.x
Paths checked: 12
Valid paths: 9
Errors: 3
Warnings: 0

ERRORS
──────

✗ adverse_reaction_list/adverse_reaction/substance|value
  Unknown path segment: 'substance' under 'adverse_reaction'
  Node was renamed in this template. Did you mean 'causative_agent'?
  Fix: adverse_reaction_list/adverse_reaction/causative_agent|value

✗ adverse_reaction_list/adverse_reaction/substance|code
  (same issue as above)
  Fix: adverse_reaction_list/adverse_reaction/causative_agent|code

✗ adverse_reaction_list/adverse_reaction/substance|terminology
  (same issue as above)
  Fix: adverse_reaction_list/adverse_reaction/causative_agent|terminology

MISSING REQUIRED FIELDS
────────────────────────
  ⚠  adverse_reaction_list/context/start_time (required)
  ⚠  adverse_reaction_list/context/setting|code (required)

Result: INVALID ✗
```

---

## Appendix B: Related Resources

- [EHRBase Web Template format](https://docs.ehrbase.org/)
- [oehrpy FLAT format learnings](docs/flat-format-learnings.md)
- [FLAT Format Versions documentation](docs/FLAT_FORMAT_VERSIONS.md)
- [simSDT specification](https://specifications.openehr.org/releases/ITS-REST/latest/simplified_data_template.html)
