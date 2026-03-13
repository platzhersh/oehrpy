# PRD-0011: Platform Migration Helper (Validator Mode)

**Status:** Draft
**Version:** 0.2
**Target Release:** oehrpy v0.3.0
**Author:** Chregi
**Date:** 2026-03-13

---

## 1. Overview

### 1.1 Background

The openEHR ecosystem has two dominant CDR platforms with incompatible FLAT format dialects:

- **EHRBase 2.x** (Vitasystems/Vitagroup): Open-source, widely adopted in Europe
- **Better Platform** (Better/Marand): Commercial, the original FLAT format creator

Both platforms implement the same openEHR specification, and both accept FLAT format compositions — but the *dialect* differs. Compositions that work on one platform fail silently or with cryptic errors on the other.

oehrpy's validator already detects platform-specific issues and has a platform selector (EHRBase vs Better). The **Platform Migration Helper** takes the next step: it *transforms* FLAT compositions from one platform's dialect to the other, and highlights every change made.

### 1.2 Integration Decision: Third Mode in `validator.html`

The Migration Helper is **integrated into `validator.html`** as a third mode alongside "FLAT Composition" and "OPT Template", rather than being a standalone page. The rationale:

1. **Shared infrastructure**: The validator already has the platform selector (EHRBase vs Better), the same two-panel layout, and the same results area — all of which the Migration Helper needs.
2. **Natural workflow**: A developer who just validated a FLAT composition and found platform-specific errors wants to immediately convert it. Switching modes is faster than switching pages.
3. **No new dependencies**: The Migration Helper is pure JavaScript (string-based path transforms), adding ~400 lines to the existing ~2,200. No Pyodide dependency for this mode.
4. **Consistent UX**: The mode toggle bar (`[FLAT Composition] [OPT Template] [Platform Migration]`) is an established pattern in the validator.

The mode toggle becomes:
```
[FLAT Composition]  [OPT Template]  [Platform Migration]
```

### 1.3 The Problem in Practice

Organizations migrating between platforms (or supporting both) face a systematic path translation problem:

| EHRBase 2.x FLAT Path | Better/simSDT FLAT Path | Difference |
|------------------------|------------------------|------------|
| `vital_signs/blood_pressure/any_event/systolic\|magnitude` | `vital_signs/blood_pressure:0/any_event:0/systolic\|magnitude` | Index notation `:0` |
| `vital_signs/language\|code` | `ctx/language\|code` | Context prefix |
| `vital_signs/blood_pressure/systolic\|magnitude` | `vital_signs/blood_pressure:0/any_event:0/systolic\|magnitude` | Missing `any_event` |
| `vital_signs/category\|code` | `ctx/category` | Category path |
| `vital_signs/composer\|name` | `ctx/composer_name` | Composer path |
| `vital_signs/context/start_time` | `ctx/time` | Context time path |

These differences are systematic but numerous. A typical composition has 20–100 FLAT paths. Manually converting each one is tedious, error-prone, and impossible to verify without submitting to the target platform.

### 1.3 Who Needs This

| User | Scenario |
|------|----------|
| **Organizations migrating CDRs** | Switching from Better to EHRBase (or vice versa) — hundreds of FLAT compositions in app code, test fixtures, and integration scripts |
| **Multi-platform vendors** | Building apps that target both platforms — need to generate FLAT compositions in both dialects from a single source |
| **Developers using EHRBase documentation** | EHRBase docs and community examples often show the old FLAT format or the Better dialect; developers need to translate to the current EHRBase 2.x dialect |
| **oehrpy users** | The SDK targets EHRBase 2.x by default; users migrating from Better need to convert their existing payloads |

### 1.5 Relationship to Other Tools

```
Validator (FLAT mode):       "Is this FLAT composition valid against this Web Template?"
Validator (OPT mode):        "Is this OPT template well-formed and semantically correct?"
Validator (Migration mode):  "Convert this FLAT composition between EHRBase and Better dialects"
Converter (standalone):      "Convert between canonical JSON and FLAT format" (PRD-0009)
Explorer (standalone):       "Browse this template's structure, paths, and constraints" (PRD-0010)
```

The Migration Helper lives inside the validator because it operates on the same input (FLAT compositions) and shares the platform concept. The Converter and Explorer are standalone pages with different UI layouts. All tools are accessible via a shared "Tools" dropdown in the navigation.

---

## 2. Goals

| Goal | Priority |
|------|----------|
| Convert FLAT composition from EHRBase 2.x dialect to Better/simSDT dialect | P0 |
| Convert FLAT composition from Better/simSDT dialect to EHRBase 2.x dialect | P0 |
| Show a diff-style view of every path that changed | P0 |
| Auto-detect source platform from the input | P1 |
| Highlight changes by category (index notation, context prefix, path structure) | P1 |
| Generate a migration report summarizing all transformations applied | P1 |
| Support batch path conversion (paste a list of paths, not just full compositions) | P1 |
| Web Template-aware conversion (use template to resolve ambiguous paths) | P2 |
| Copy converted composition to clipboard | P0 |
| Load example data showing common migration scenarios | P1 |

### Out of Scope (v0.3.0)

- ECISFLAT format (archetype-path-based)
- Value transformation (only paths are converted, values are preserved)
- Automatic CDR submission (user copies the output and submits manually)
- Full round-trip guarantee (some transformations are lossy without template context)
- STRUCTURED format dialect differences
- API or CLI interface (web GUI only for v1; Python API can follow)

---

## 3. User Stories

### Developer migrating from Better to EHRBase

> *"We're switching from Better to EHRBase. I have 50 FLAT composition templates in our backend code. I want to paste each one and immediately see what paths need to change, without reading EHRBase migration docs."*

### Developer migrating from EHRBase to Better

> *"Our organization adopted Better for their managed CDR offering. I need to convert our EHRBase FLAT payloads. The index notation and context paths are different and I keep getting 'Could not consume Parts' errors."*

### Developer troubleshooting cross-platform issues

> *"I found a FLAT composition example online but it doesn't work on my EHRBase instance. I want to paste it, auto-detect that it's in Better format, and convert it to EHRBase format."*

### QA engineer validating migration

> *"We migrated 200 compositions from Better to EHRBase. I want to verify our conversion script didn't miss any path transformations by running each composition through an independent tool."*

---

## 4. Functional Requirements

### 4.1 Transformation Rules

#### Rule 1: Index Notation

| From (Better) | To (EHRBase 2.x) | Rule |
|----------------|-------------------|------|
| `blood_pressure:0/any_event:0/systolic` | `blood_pressure/any_event/systolic` | Remove `:0` from single-occurrence nodes |
| `adverse_reaction:0/reaction_event:0` | `adverse_reaction/reaction_event` | Remove `:0` on first occurrence |
| `adverse_reaction:1/reaction_event:0` | `adverse_reaction:1/reaction_event` | Keep `:N` where N > 0 |

| From (EHRBase 2.x) | To (Better) | Rule |
|---------------------|-------------|------|
| `blood_pressure/any_event/systolic` | `blood_pressure:0/any_event:0/systolic` | Add `:0` to all multi-valued nodes |

**Note:** Without a Web Template, the tool cannot know which nodes are multi-valued. The P0 implementation applies the common heuristic: add `:0` to all non-leaf, non-context path segments when converting to Better. With a Web Template (P2), the tool can be precise about which nodes actually need indexing.

#### Rule 2: Context Prefix

| EHRBase 2.x | Better | Field |
|-------------|--------|-------|
| `{tree_id}/language\|code` | `ctx/language` | Language |
| `{tree_id}/language\|terminology` | *(implicit, not needed)* | Language terminology |
| `{tree_id}/territory\|code` | `ctx/territory` | Territory |
| `{tree_id}/composer\|name` | `ctx/composer_name` | Composer name |
| `{tree_id}/composer\|id` | `ctx/composer_id` | Composer ID |
| `{tree_id}/category\|code` | `ctx/category` | Category code |
| `{tree_id}/category\|value` | *(implicit)* | Category value |
| `{tree_id}/category\|terminology` | *(implicit)* | Category terminology |
| `{tree_id}/context/start_time` | `ctx/time` | Start time |
| `{tree_id}/context/end_time` | `ctx/end_time` | End time |
| `{tree_id}/context/setting\|code` | `ctx/setting\|code` | Setting |
| `{tree_id}/context/health_care_facility\|name` | `ctx/health_care_facility\|name` | Facility |

#### Rule 3: `any_event` Handling

| EHRBase 2.x | Better | Notes |
|-------------|--------|-------|
| `.../blood_pressure/systolic` | `.../blood_pressure:0/any_event:0/systolic` | EHRBase 2.x omits `any_event` |
| `.../pulse_heart_beat/rate` | `.../pulse_heart_beat:0/any_event:0/rate` | Same pattern for all HISTORY-based observations |

**Heuristic for EHRBase → Better:** If a path goes directly from an OBSERVATION-level node to a data element without `any_event`, insert `any_event:0` after the observation node.

**Heuristic for Better → EHRBase:** If a path contains `/any_event:0/`, remove it.

#### Rule 4: Composition Tree ID Detection

EHRBase 2.x uses the composition tree ID (derived from the template concept) as the root prefix instead of `ctx/`:

- Template concept `"Vital Signs"` → tree ID `"vital_signs"`
- Template concept `"IDCR - Adverse Reaction List.v1"` → tree ID `"idcr___adverse_reaction_list_v1"`

The tool auto-detects the tree ID from the input by finding the common prefix of all non-context paths.

### 4.2 Auto-Detection

The tool auto-detects the source platform by examining the input:

| Signal | Detected Platform |
|--------|-------------------|
| Keys start with `ctx/` | Better |
| Keys contain `:0` on most segments | Better |
| Keys contain `/any_event:0/` | Better |
| Keys start with a composition tree ID (no `ctx/`) | EHRBase 2.x |
| Keys have no `:0` on single-occurrence segments | EHRBase 2.x |

Detection is best-effort. The user can override the detected source platform.

### 4.3 UI Layout

```
┌───────────────────────────────────────────────────────────────────┐
│  oehrpy · Migration Helper                      [GitHub] [Docs]  │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Source: [EHRBase 2.x ▾]  →  Target: [Better ▾]   [Auto-detect] │
│                                                                   │
│  ┌──────── Source Composition ───────┐ ┌──── Converted Output ──┐│
│  │                                   │ │                         ││
│  │ {                                 │ │ {                       ││
│  │   "vital_signs/language|code":    │ │   "ctx/language": "en", ││
│  │   "en",                           │ │   ...                   ││
│  │   "vital_signs/blood_pressure/    │ │   "vital_signs/         ││
│  │     systolic|magnitude": 120      │ │     blood_pressure:0/   ││
│  │ }                                 │ │     any_event:0/         ││
│  │                                   │ │     systolic|magnitude": ││
│  │                                   │ │     120                  ││
│  │                                   │ │ }                       ││
│  └───────────────────────────────────┘ └─────────────────────────┘│
│                                                                   │
│  ┌──────────────── Change Report ────────────────────────────────┐│
│  │                                                                ││
│  │  12 paths converted  ·  8 changed  ·  4 unchanged             ││
│  │                                                                ││
│  │  INDEX NOTATION (5 changes)                                    ││
│  │  + blood_pressure:0  ←  blood_pressure                         ││
│  │  + any_event:0       ←  (inserted)                             ││
│  │  + pulse_heart_beat:0 ← pulse_heart_beat                       ││
│  │                                                                ││
│  │  CONTEXT PREFIX (3 changes)                                    ││
│  │  ctx/language       ←  vital_signs/language|code               ││
│  │  ctx/territory      ←  vital_signs/territory|code              ││
│  │  ctx/composer_name  ←  vital_signs/composer|name               ││
│  │                                                                ││
│  │  UNCHANGED (4 paths)                                           ││
│  │  vital_signs/blood_pressure.../systolic|magnitude              ││
│  │  vital_signs/blood_pressure.../systolic|unit                   ││
│  │  ...                                                           ││
│  │                                                     [Copy All] ││
│  └────────────────────────────────────────────────────────────────┘│
│                                                                   │
│  [Load Example]  [Clear]  [Swap Source ↔ Target]                  │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

### 4.4 Change Report

The change report is the core differentiator of this tool. It groups transformations by category:

**Categories:**
1. **Index Notation** — `:0` added or removed
2. **Context Prefix** — `ctx/` ↔ composition tree ID mapping
3. **Path Structure** — `any_event` insertion/removal, other structural changes
4. **Unchanged** — paths that are identical on both platforms

Each change shows:
- The original path (source format)
- The converted path (target format)
- The transformation rule that was applied
- Visual diff highlighting (green for additions, red for removals)

### 4.5 Batch Path Mode

In addition to full composition conversion, support a "paths only" mode:

- Input: a list of FLAT paths (one per line, no values)
- Output: converted paths (one per line)
- Use case: converting path constants in application code

```
Input (one path per line):
vital_signs/blood_pressure/systolic|magnitude
vital_signs/blood_pressure/diastolic|magnitude
vital_signs/pulse_heart_beat/rate|magnitude

Output (converted):
vital_signs/blood_pressure:0/any_event:0/systolic|magnitude
vital_signs/blood_pressure:0/any_event:0/diastolic|magnitude
vital_signs/pulse_heart_beat:0/any_event:0/rate|magnitude
```

### 4.6 Error Handling

| Condition | Behaviour |
|-----------|-----------|
| Invalid JSON input | Red border, error message with line number |
| Empty input | Placeholder text |
| Auto-detection uncertain | Show "Detected: EHRBase 2.x (confidence: medium)" with option to override |
| Ambiguous paths (could be either platform) | Flag in report: "This path is identical on both platforms" |
| Paths that cannot be automatically converted | Flag in report: "Manual review needed — this path structure is platform-specific and may require template context" |

### 4.7 Example Scenarios

**Example 1: EHRBase → Better (Adverse Reaction)**

Source (EHRBase 2.x):
```json
{
  "adverse_reaction_list/language|code": "en",
  "adverse_reaction_list/language|terminology": "ISO_639-1",
  "adverse_reaction_list/territory|code": "CH",
  "adverse_reaction_list/territory|terminology": "ISO_3166-1",
  "adverse_reaction_list/composer|name": "Dr. Chregi",
  "adverse_reaction_list/context/start_time": "2026-03-13T10:00:00Z",
  "adverse_reaction_list/category|code": "433",
  "adverse_reaction_list/category|value": "event",
  "adverse_reaction_list/category|terminology": "openehr",
  "adverse_reaction_list/adverse_reaction/substance|value": "Penicillin",
  "adverse_reaction_list/adverse_reaction/substance|code": "372687004",
  "adverse_reaction_list/adverse_reaction/substance|terminology": "SNOMED-CT"
}
```

Target (Better):
```json
{
  "ctx/language": "en",
  "ctx/territory": "CH",
  "ctx/composer_name": "Dr. Chregi",
  "ctx/time": "2026-03-13T10:00:00Z",
  "ctx/category": "event",
  "adverse_reaction_list/adverse_reaction:0/substance|value": "Penicillin",
  "adverse_reaction_list/adverse_reaction:0/substance|code": "372687004",
  "adverse_reaction_list/adverse_reaction:0/substance|terminology": "SNOMED-CT"
}
```

**Example 2: Better → EHRBase (Vital Signs)**

Source (Better):
```json
{
  "ctx/language": "en",
  "ctx/territory": "CH",
  "ctx/composer_name": "Dr. Chregi",
  "ctx/time": "2026-03-13T10:00:00Z",
  "vital_signs/blood_pressure:0/any_event:0/systolic|magnitude": 120,
  "vital_signs/blood_pressure:0/any_event:0/systolic|unit": "mm[Hg]",
  "vital_signs/blood_pressure:0/any_event:0/diastolic|magnitude": 80,
  "vital_signs/blood_pressure:0/any_event:0/diastolic|unit": "mm[Hg]"
}
```

Target (EHRBase 2.x):
```json
{
  "vital_signs/language|code": "en",
  "vital_signs/language|terminology": "ISO_639-1",
  "vital_signs/territory|code": "CH",
  "vital_signs/territory|terminology": "ISO_3166-1",
  "vital_signs/composer|name": "Dr. Chregi",
  "vital_signs/context/start_time": "2026-03-13T10:00:00Z",
  "vital_signs/category|code": "433",
  "vital_signs/category|value": "event",
  "vital_signs/category|terminology": "openehr",
  "vital_signs/blood_pressure/systolic|magnitude": 120,
  "vital_signs/blood_pressure/systolic|unit": "mm[Hg]",
  "vital_signs/blood_pressure/diastolic|magnitude": 80,
  "vital_signs/blood_pressure/diastolic|unit": "mm[Hg]"
}
```

---

## 5. Technical Design

### 5.1 Implementation Approach

**Pure JavaScript, integrated into `validator.html`.** All transformation rules are string-based path manipulation — no RM knowledge, no XML parsing, no Pyodide dependency. The migration mode loads instantly even if Pyodide hasn't finished initializing (unlike OPT mode which requires it).

### 5.2 Core Algorithm

```
function migrate(flatComposition, sourceFormat, targetFormat):
    if sourceFormat == targetFormat:
        return { output: flatComposition, changes: [] }

    result = {}
    changes = []
    treeId = detectTreeId(flatComposition)

    for each [path, value] in flatComposition:
        converted = convertPath(path, sourceFormat, targetFormat, treeId)
        result[converted.newPath] = converted.newValue ?? value
        if converted.changed:
            changes.push({
                original: path,
                converted: converted.newPath,
                category: converted.category,
                rule: converted.ruleDescription
            })

    return { output: result, changes: changes }
```

### 5.3 Transformation Pipeline

Each path goes through a pipeline of transformation functions:

```
path → contextTransform → indexTransform → anyEventTransform → result
```

1. **contextTransform**: Map between `ctx/*` and `{treeId}/*` prefixed context fields
2. **indexTransform**: Add or remove `:0` index notation
3. **anyEventTransform**: Insert or remove `/any_event:0/` segments

Each transform returns the modified path and a change descriptor.

### 5.4 Context Field Mapping Table

Hardcoded bidirectional mapping:

```javascript
const CONTEXT_MAP = {
  // Better ctx/ field → EHRBase expansion
  "ctx/language":                  { path: "{treeId}/language|code",         extra: {"{treeId}/language|terminology": "ISO_639-1"} },
  "ctx/territory":                 { path: "{treeId}/territory|code",        extra: {"{treeId}/territory|terminology": "ISO_3166-1"} },
  "ctx/composer_name":             { path: "{treeId}/composer|name" },
  "ctx/composer_id":               { path: "{treeId}/composer|id" },
  "ctx/time":                      { path: "{treeId}/context/start_time" },
  "ctx/end_time":                  { path: "{treeId}/context/end_time" },
  "ctx/category":                  { path: "{treeId}/category|code",         extra: {"{treeId}/category|value": "event", "{treeId}/category|terminology": "openehr"} },
  "ctx/id_namespace":              { path: "{treeId}/id_namespace" },
  "ctx/id_scheme":                 { path: "{treeId}/id_scheme" },
  "ctx/health_care_facility|name": { path: "{treeId}/context/health_care_facility|name" },
  "ctx/health_care_facility|id":   { path: "{treeId}/context/health_care_facility|id" },
  "ctx/participation_name:0":      { path: "{treeId}/context/participation:0|name" },
  "ctx/participation_function:0":  { path: "{treeId}/context/participation:0|function" },
  "ctx/participation_mode:0":      { path: "{treeId}/context/participation:0|mode" },
  "ctx/participation_id:0":        { path: "{treeId}/context/participation:0|id" },
};
```

### 5.5 Tree ID Detection

```javascript
function detectTreeId(flatComposition) {
    // Find the most common first path segment (excluding "ctx")
    const prefixes = {};
    for (const path of Object.keys(flatComposition)) {
        if (path.startsWith("ctx/")) continue;
        const firstSegment = path.split("/")[0].split(":")[0];
        prefixes[firstSegment] = (prefixes[firstSegment] || 0) + 1;
    }
    // Return the most frequent prefix
    return Object.entries(prefixes)
        .sort((a, b) => b[1] - a[1])[0]?.[0] || "composition";
}
```

### 5.6 Integration into `validator.html`

No new HTML file — all migration code lives in `validator.html`. The implementation adds ~400 lines of JavaScript for the migration logic, UI mode switching, and change report rendering.

**Mode switching logic:** The existing `setMode()` function is extended to handle a third mode (`'migration'`). When activated:
- Hide FLAT-mode panels and OPT-mode panels
- Show migration-mode panels (Source input + Converted output)
- Swap platform bar to source→target variant
- Change button text from "Validate" to "Convert"
- Wire `runValidation()` to call `runMigrationFlow()` instead

---

## 6. Implementation Plan

| Task | Effort |
|------|--------|
| HTML/CSS scaffold matching existing design system | 0.5 day |
| Context field mapping (bidirectional) | 0.5 day |
| Index notation transformation (add/remove `:0`) | 0.5 day |
| `any_event` insertion/removal | 0.5 day |
| Auto-detection of source platform | 0.5 day |
| Tree ID detection | 0.25 day |
| Change report rendering (grouped by category, diff highlighting) | 1 day |
| Batch path mode (paths-only input) | 0.5 day |
| Example data (EHRBase ↔ Better for Vital Signs + Adverse Reaction) | 0.5 day |
| Copy-to-clipboard, Swap, Clear | 0.25 day |
| Navigation updates across all pages | 0.25 day |
| Manual testing with real compositions from both platforms | 1 day |
| **Total** | **~6 days** |

### Future Enhancements (post v0.3.0)

| Enhancement | Effort |
|-------------|--------|
| Web Template-aware conversion (precise index notation based on cardinality) | 2 days |
| Python API (`FlatMigrator` class) | 1.5 days |
| CLI tool (`oehrpy migrate --from ehrbase --to better composition.json`) | 1 day |
| Regex-based find-and-replace mode for converting paths in source code files | 2 days |
| Support for EHRBase 0.x/1.x legacy FLAT format (pre-2.0 dialect) | 1.5 days |
| Confidence scoring per transformation (how certain is the conversion?) | 1 day |

---

## 7. Open Questions

| Question | Decision needed by |
|----------|--------------------|
| For EHRBase → Better conversion, Better's `ctx/category` is just the value (e.g., `"event"`), while EHRBase has three fields (`\|code`, `\|value`, `\|terminology`). When converting to Better, should we just use the `\|value` field, or warn that category information is being reduced? | Implementation |
| Should the tool attempt to handle EHRBase versions before 2.0 (which used a different FLAT format closer to Better's)? Or strictly EHRBase 2.x only? | Design start |
| For the `any_event` heuristic: without a Web Template, how do we know which path segments represent HISTORY-based observations? Should we maintain a hardcoded list of common archetype patterns, or always insert `any_event` between the observation node and data elements? | Implementation |
| Should the batch path mode also accept paths embedded in Python/JavaScript code strings and extract them automatically? This would help developers migrating application code. | Post-v1 |
| The context field mapping between platforms is not fully standardized. Should we document known gaps and unsupported mappings explicitly in the UI? | UI review |
