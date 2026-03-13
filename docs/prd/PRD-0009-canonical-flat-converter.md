# PRD-0009: Canonical JSON ↔ FLAT Format Converter Web GUI

**Status:** Draft
**Version:** 0.1
**Target Release:** oehrpy v0.3.0
**Author:** Chregi
**Date:** 2026-03-13

---

## 1. Overview

### 1.1 Background

oehrpy already implements two serialization formats for openEHR compositions:

- **Canonical JSON** (`serialization/canonical.py`): The standard openEHR JSON format with `_type` fields for polymorphic type identification and a fully nested hierarchical structure.
- **FLAT Format** (`serialization/flat.py`): EHRBase's simplified key-value representation where the hierarchy is collapsed into dot-separated paths (e.g., `vital_signs/blood_pressure:0/systolic|magnitude`).

Both formats represent the same clinical data. Developers regularly need to convert between them — for example, to debug a FLAT composition by viewing its canonical structure, or to construct a FLAT payload from a canonical JSON example returned by the CDR.

### 1.2 The Problem in Practice

Converting between canonical and FLAT is tedious and error-prone when done manually:

| Scenario | Pain |
|----------|------|
| EHRBase returns canonical JSON but your app submits FLAT | Manual path reconstruction from nested structure |
| Debugging a FLAT composition | Impossible to see the tree structure; paths are opaque without context |
| Migrating from Better (canonical) to EHRBase (FLAT) | No tool to preview the FLAT output before submitting |
| Onboarding new developers | "What does this FLAT path actually mean in the composition tree?" |
| Building test fixtures | Hand-translating between formats for integration tests |

There is no existing tool in the openEHR ecosystem that converts between these formats in a browser. EHRBase's `/composition?format=FLAT` endpoint requires a running server and an uploaded template.

### 1.3 Relationship to Existing Tools

This converter complements the existing **validator** (`docs/validator.html`):

```
Validator:   "Is my FLAT composition valid against this Web Template?"
Converter:   "Show me what this canonical JSON looks like in FLAT format (and vice versa)."
```

Both tools share the same audience (openEHR developers) and will share the same UI design system and navigation.

---

## 2. Goals

| Goal | Priority |
|------|----------|
| Convert Canonical JSON → FLAT format in the browser | P0 |
| Convert FLAT format → nested hierarchical JSON (unflattened) | P0 |
| Real-time conversion as the user types/pastes | P0 |
| Side-by-side input/output panels | P0 |
| Syntax-highlighted JSON display with line numbers | P1 |
| Copy-to-clipboard for output | P1 |
| Load example data (Vital Signs composition) | P1 |
| Show path mapping: click a FLAT key to highlight the corresponding canonical node | P2 |
| Support EHRBase 2.x FLAT format (composition tree ID prefix, no `:0` indexing) | P0 |
| Support Better/simSDT FLAT format (`:0` indexing, `ctx/` prefix) | P1 |
| Platform selector (EHRBase vs Better) affects conversion rules | P1 |
| Web Template-aware conversion (use Web Template to resolve node names) | P2 |

### Out of Scope (v0.3.0)

- Round-trip fidelity guarantee (canonical → FLAT → canonical producing identical output) — this requires full RM schema knowledge and is inherently lossy without a template
- ECISFLAT format (archetype-path-based FLAT variant)
- Server-side conversion (all conversion runs client-side in JS or Pyodide)
- STRUCTURED format (EHRBase's tree-based JSON variant)
- Validating the composition content — use the Validator for that

---

## 3. User Stories

### Developer debugging a failing FLAT submission

> *"EHRBase rejected my FLAT composition with 'Could not consume Parts'. I want to paste the FLAT JSON, see it as a tree, and visually verify which paths are malformed versus which are structurally correct."*

### Developer building FLAT payloads from canonical examples

> *"I used the /composition endpoint to fetch a canonical JSON example. Now I need to convert it to FLAT format for my app's submission logic. I want to paste the canonical JSON and get the FLAT key-value pairs."*

### openEHR newcomer learning the formats

> *"I'm new to openEHR and confused by the two formats. I want to paste an example in one format and see the other format side-by-side so I can understand the mapping."*

### QA engineer comparing CDR responses

> *"I submitted a FLAT composition and retrieved it as canonical. I want to convert my original FLAT payload to canonical and diff them to see what the CDR added or changed."*

---

## 4. Functional Requirements

### 4.1 Conversion Modes

#### Mode 1: Canonical → FLAT

**Input:** Canonical JSON (nested object with `_type` fields)

**Processing:**
1. Parse JSON and validate it is a valid object
2. Walk the nested structure depth-first
3. Build FLAT paths from the tree hierarchy:
   - Object keys become path segments separated by `/`
   - Array elements get index notation (`:0`, `:1`) — or no index for EHRBase 2.x single-occurrence nodes
   - Leaf values with data type attributes get `|` suffix notation (`|magnitude`, `|unit`, `|code`, `|value`, `|terminology`)
4. Handle `_type` fields: strip from output paths but use them to determine attribute suffixes
5. Apply platform-specific rules (EHRBase vs Better)

**Output:** FLAT JSON dictionary (key-value pairs)

**Data type attribute mapping:**

| `_type` | FLAT suffixes |
|---------|--------------|
| `DV_QUANTITY` | `\|magnitude`, `\|unit`, `\|precision` |
| `DV_CODED_TEXT` | `\|value`, `\|code`, `\|terminology` |
| `DV_TEXT` | `\|value` (or bare path) |
| `DV_DATE_TIME` | bare path |
| `DV_BOOLEAN` | bare path |
| `DV_COUNT` | `\|magnitude` |
| `DV_PROPORTION` | `\|numerator`, `\|denominator`, `\|type` |
| `DV_ORDINAL` | `\|value`, `\|code`, `\|ordinal`, `\|terminology` |
| `DV_DURATION` | `\|value` (ISO 8601 duration) |
| `DV_IDENTIFIER` | `\|id`, `\|type`, `\|issuer`, `\|assigner` |
| `DV_MULTIMEDIA` | `\|mediatype`, `\|size`, `\|url` |
| `DV_URI` | `\|url` |
| `DV_PARSABLE` | `\|value`, `\|formalism` |
| `CODE_PHRASE` | `\|code`, `\|terminology` |

#### Mode 2: FLAT → Hierarchical (Unflatten)

**Input:** FLAT JSON dictionary (key-value pairs)

**Processing:**
1. Parse JSON and validate it is a flat key-value object (no nested structures)
2. Split each key on `/` to recover path segments
3. Parse index notation (`:0`, `:1`) to reconstruct arrays
4. Parse attribute notation (`|magnitude`, `|code`) to reconstruct data type objects
5. Build nested dictionary from paths

**Output:** Nested JSON (hierarchical tree structure)

Note: This mode produces a *structural unflatten* — the output is a nested dictionary reconstructed from the FLAT paths. It does **not** reconstruct full canonical JSON with `_type` fields, since that requires RM schema knowledge beyond what the FLAT keys alone provide.

### 4.2 Platform-Specific Rules

| Behaviour | EHRBase 2.x | Better / simSDT |
|-----------|-------------|-----------------|
| Index notation on single-occurrence nodes | Omitted (no `:0`) | Required (`:0` on all multi-valued nodes) |
| Context prefix | Composition tree ID (e.g., `vital_signs/`) | `ctx/` |
| `any_event` in paths | Omitted | Present |
| `_type` fields in canonical | Present | Present |

The platform selector controls which rules apply during conversion.

### 4.3 UI Layout

```
┌──────────────────────────────────────────────────────────────────┐
│  oehrpy · Converter                             [GitHub] [Docs] │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [Canonical → FLAT]  [FLAT → Tree]     Platform: [EHRBase ▾]    │
│                                                                  │
│  ┌────────────── Input ──────────────┐ ┌────── Output ─────────┐│
│  │                                   │ │                        ││
│  │  {                                │ │  {                     ││
│  │    "_type": "COMPOSITION",        │ │    "vital_signs/...":  ││
│  │    "name": { ... },               │ │    120,                ││
│  │    "content": [ ... ]             │ │    ...                 ││
│  │  }                                │ │  }                     ││
│  │                                   │ │                        ││
│  │                                   │ │             [Copy]     ││
│  └───────────────────────────────────┘ └────────────────────────┘│
│                                                                  │
│  [Load Example]  [Clear]  [Swap ⇄]              0 errors        │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

**Key UI elements:**
- **Mode tabs**: Toggle between Canonical → FLAT and FLAT → Tree
- **Platform selector**: EHRBase 2.x / Better (same selector as validator)
- **Input panel**: Editable textarea with line count and JSON syntax validation
- **Output panel**: Read-only display with syntax highlighting
- **Swap button**: Exchange input and output (useful for round-trip exploration)
- **Load Example**: Pre-fills a Vital Signs composition in the selected format
- **Copy button**: Copy output to clipboard
- **Error bar**: Shows JSON parse errors or conversion warnings

### 4.4 Error Handling

| Error | Display |
|-------|---------|
| Invalid JSON in input | Red border on input, error message below: "Invalid JSON at line N: ..." |
| Empty input | Grey placeholder text: "Paste canonical JSON here..." |
| Non-object JSON (array, string, number) | Warning: "Expected a JSON object, got [type]" |
| Canonical JSON missing `_type` | Info: "No _type field found — converting structurally without type-aware attribute mapping" |
| FLAT input with nested values | Warning: "Key 'x' has a nested object value — expected flat key-value pairs" |

### 4.5 Example Data

**Canonical JSON example** (Vital Signs — blood pressure + pulse):
```json
{
  "_type": "COMPOSITION",
  "name": { "_type": "DV_TEXT", "value": "Vital Signs" },
  "archetype_details": {
    "archetype_id": { "value": "openEHR-EHR-COMPOSITION.encounter.v1" },
    "template_id": { "value": "Vital Signs" }
  },
  "content": [
    {
      "_type": "OBSERVATION",
      "name": { "value": "Blood pressure" },
      "data": {
        "events": [
          {
            "_type": "POINT_EVENT",
            "data": {
              "items": [
                {
                  "_type": "ELEMENT",
                  "name": { "value": "Systolic" },
                  "value": { "_type": "DV_QUANTITY", "magnitude": 120, "units": "mm[Hg]" }
                }
              ]
            }
          }
        ]
      }
    }
  ]
}
```

**FLAT example** (matching composition):
```json
{
  "vital_signs/language|code": "en",
  "vital_signs/language|terminology": "ISO_639-1",
  "vital_signs/territory|code": "CH",
  "vital_signs/territory|terminology": "ISO_3166-1",
  "vital_signs/composer|name": "Dr. Chregi",
  "vital_signs/context/start_time": "2026-03-13T10:00:00Z",
  "vital_signs/blood_pressure/any_event/systolic|magnitude": 120,
  "vital_signs/blood_pressure/any_event/systolic|unit": "mm[Hg]"
}
```

---

## 5. Technical Design

### 5.1 Implementation Approach

**Pure JavaScript** for the core conversion logic. Unlike the OPT validator which requires Python (Pyodide) for XML parsing and RM validation, the format converter operates on JSON structures and can be implemented entirely in JS:

- `canonicalToFlat(obj, platform)` → flat dictionary
- `flatToTree(flat)` → nested dictionary
- No Pyodide dependency → faster page load, no 10MB runtime download

### 5.2 Conversion Algorithm: Canonical → FLAT

```
function canonicalToFlat(obj, path = "", platform = "ehrbase"):
    result = {}

    for each [key, value] in obj:
        if key == "_type": continue

        currentPath = path ? path + "/" + key : key

        if value is array:
            for i, item in value:
                indexedPath = platform == "better" ? currentPath + ":" + i : currentPath
                if item is object:
                    result.merge(canonicalToFlat(item, indexedPath, platform))
                else:
                    result[indexedPath] = item

        else if value is object:
            type = value["_type"]
            if type in DV_TYPE_MAP:
                // Expand data type into |suffix paths
                for each [attr, suffix] in DV_TYPE_MAP[type]:
                    if attr in value:
                        result[currentPath + "|" + suffix] = value[attr]
            else:
                result.merge(canonicalToFlat(value, currentPath, platform))

        else:
            result[currentPath] = value

    return result
```

### 5.3 Conversion Algorithm: FLAT → Tree

Reuses the same logic as oehrpy's `unflatten_dict()` from `serialization/flat.py`:

1. Split each key on `/`
2. Parse `:N` index notation on segments
3. Parse `|attr` suffix on final segment
4. Build nested dict/array structure

### 5.4 File Structure

```
docs/
├── converter.html         # New: standalone converter page
├── validator.html         # Existing
├── index.html             # Landing page (add link to converter)
└── ...
```

Single HTML file matching the pattern of `validator.html` — all CSS, JS, and HTML in one file. Shared design system (CSS variables, header, navigation) consistent with the validator.

### 5.5 Navigation Integration (shared across all tools)

All pages use a shared "Tools" dropdown in the navigation bar, replacing the previous single "Validators" link:

```html
<nav>
  <a href="index.html">Home</a>
  <a href="docs.html">Docs</a>
  <div class="nav-dropdown">
    <button class="nav-dropdown-btn">Tools <span class="dropdown-arrow">▾</span></button>
    <div class="nav-dropdown-menu">
      <a href="validator.html">Validator</a>
      <a href="converter.html" class="active">Converter</a>
      <a href="explorer.html">Explorer</a>
    </div>
  </div>
  <a href="brand-kit.html">Brand Kit</a>
  <a href="https://github.com/platzhersh/oehrpy" class="github-link">GitHub</a>
</nav>
```

The dropdown appears on hover and lists all three tools. The `class="active"` marker moves to whichever tool is currently active. This pattern is consistent across:
- `index.html` (no active tool)
- `docs.html` (no active tool)
- `validator.html` (Validator active)
- `converter.html` (Converter active)
- `explorer.html` (Explorer active)
- `brand-kit.html` (no active tool)

---

## 6. Implementation Plan

| Task | Effort |
|------|--------|
| HTML/CSS scaffold matching validator design system | 0.5 day |
| Canonical → FLAT conversion (JS, with DV type mapping) | 1 day |
| FLAT → Tree conversion (JS, unflatten algorithm) | 0.5 day |
| Platform-specific rules (EHRBase vs Better) | 0.5 day |
| Example data (Vital Signs canonical + FLAT) | 0.5 day |
| Input validation and error display | 0.5 day |
| Copy-to-clipboard, Swap, Clear buttons | 0.25 day |
| Navigation updates (index.html, validator.html) | 0.25 day |
| Manual testing with real EHRBase compositions | 0.5 day |
| **Total** | **~4.5 days** |

### Future Enhancements (post v0.3.0)

| Enhancement | Effort |
|-------------|--------|
| Path mapping: click FLAT key to highlight canonical node | 2 days |
| Web Template-aware conversion (resolve node names from template) | 3 days |
| STRUCTURED format support | 2 days |
| Diff view: compare two FLAT compositions side-by-side | 1.5 days |
| URL-shareable state (encode input in URL hash) | 0.5 day |

---

## 7. Open Questions

| Question | Decision needed by |
|----------|--------------------|
| Should canonical → FLAT require a Web Template for accurate node name resolution, or is structural conversion (using JSON keys as path segments) sufficient for v1? | Design start |
| Should the converter attempt to reconstruct `_type` fields during FLAT → canonical if common patterns are detected (e.g., `\|magnitude` + `\|unit` → `DV_QUANTITY`)? | Implementation |
| Should conversion stats be shown (e.g., "42 FLAT paths generated from 156 canonical nodes")? | UI review |
