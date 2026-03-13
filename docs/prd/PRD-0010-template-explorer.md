# PRD-0010: Template Explorer / OPT Viewer Web GUI

**Status:** Draft
**Version:** 0.1
**Target Release:** oehrpy v0.3.0
**Author:** Chregi
**Date:** 2026-03-13

---

## 1. Overview

### 1.1 Background

openEHR templates (OPT 1.4 XML files) define the clinical data structures used by CDRs like EHRBase and Better. They are the central artifact in any openEHR deployment: they constrain the Reference Model, define which archetypes are used, rename nodes, bind terminology codes, and determine the valid FLAT paths for composition submission.

Despite their importance, templates are opaque. OPT XML files are verbose (often 500–5,000+ lines), deeply nested, and difficult to read. The only current ways to inspect a template are:

1. **Open the raw XML** in a text editor — overwhelming and not navigable
2. **Upload to a CDR** and use `/template/{id}/example?format=FLAT` — requires a running server
3. **Use Archetype Designer** — requires the original modeling project, not just the exported OPT
4. **oehrpy's OPT Parser** — Python API only, no visual output

### 1.2 The Problem in Practice

| Scenario | Pain |
|----------|------|
| "What FLAT paths does this template accept?" | Must upload to CDR and hit the example endpoint |
| "Which archetypes does this template use?" | Grep through XML or read the full tree |
| "What RM type is the node at this path?" | Navigate deeply nested XML `<children>` elements |
| "This node was renamed — what was it called in the archetype?" | Compare OPT `ontology/term_definitions` with archetype source |
| "What are the valid coded values for this field?" | Find the `C_CODE_PHRASE` constraint buried in the XML |
| "How many mandatory fields does this template have?" | Count all `occurrences` elements with `lower >= 1` |

These are daily questions for openEHR developers. Each requires either a running CDR, deep XML knowledge, or both.

### 1.3 Relationship to Existing Tools

The **Validator** (`docs/validator.html`) already parses OPT files and runs checks. The **Template Explorer** is complementary:

```
Validator:  "Is this OPT well-formed and semantically correct?"
Explorer:   "Show me what's inside this OPT — its structure, paths, constraints, and terminology."
```

The Explorer reuses the same Pyodide + `OPTParser` infrastructure that the validator already loads. Both tools benefit from shared investment in browser-based OPT parsing.

---

## 2. Goals

| Goal | Priority |
|------|----------|
| Parse and display an OPT file as an interactive tree | P0 |
| Show node metadata: RM type, node_id, occurrences, archetype_id | P0 |
| Enumerate and list all valid FLAT paths for the template | P0 |
| Search/filter the tree and path list | P0 |
| Show terminology bindings and coded value constraints per node | P1 |
| Highlight mandatory vs optional nodes visually | P1 |
| Show renamed nodes (template name vs archetype default name) | P1 |
| Support both OPT 1.4 XML input and Web Template JSON input | P1 |
| Export path list as CSV or JSON | P1 |
| Collapsible tree with expand/collapse all controls | P1 |
| Click a tree node to see its FLAT path, RM type, and constraints | P0 |
| Platform-aware path display (EHRBase vs Better) | P1 |
| Show template statistics (node count, archetype count, mandatory count) | P2 |

### Out of Scope (v0.3.0)

- Editing the template (this is a read-only explorer)
- ADL 2 / OPT 2.0 (JSON format) input
- Cross-referencing with CKM or archetype repositories
- Visual diagram / graph rendering of the template (e.g., D3.js force graph)
- Comparing two templates side-by-side (diff view)

---

## 3. User Stories

### Developer integrating a new template

> *"I received an OPT file from our clinical modeler. Before writing any code, I want to understand its structure — what observations it contains, what FLAT paths I'll need to use, and which fields are mandatory."*

### Clinical modeler reviewing their template

> *"I exported an OPT from Archetype Designer. I want a quick visual check that the structure matches my intent — correct archetypes, correct renames, correct constraints — without uploading to a CDR."*

### Developer debugging FLAT path issues

> *"My FLAT composition is being rejected. I want to browse the template tree, find the correct path for each field, and see what RM type and valid codes are expected at each node."*

### Team lead assessing template complexity

> *"We're planning sprint work for a new template integration. I want to quickly see how many nodes, archetypes, and mandatory fields this template has to estimate development effort."*

---

## 4. Functional Requirements

### 4.1 Input Handling

#### OPT 1.4 XML Input

- Textarea for pasting OPT XML (same as validator's OPT mode)
- File upload button (drag-and-drop or file picker)
- Parse using Pyodide + oehrpy's `OPTParser` (already loaded in the browser from validator infrastructure)
- Show parse errors if XML is malformed

#### Web Template JSON Input

- Textarea for pasting Web Template JSON (fetched from CDR's `/template/{id}` endpoint)
- Parse the `tree` structure to build the node hierarchy
- Extract: `id`, `name`, `rmType`, `min`, `max`, `aqlPath`, `inputs` (coded values)

### 4.2 Tree View

The primary view is an interactive collapsible tree showing the template's archetype structure.

```
┌─────────────────────────────────────────────────────────────────────┐
│ Template: Vital Signs  ·  12 nodes  ·  3 archetypes  ·  4 required │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  🔍 [Search nodes...]                    [Expand All] [Collapse All]│
│                                                                     │
│  ▼ COMPOSITION · Vital Signs                              required  │
│    ├── context                                                      │
│    │   └── start_time · DV_DATE_TIME                      required  │
│    ▼ OBSERVATION · Blood pressure (v2)                    optional  │
│    │ ├── any_event                                                  │
│    │ │   ├── Systolic · DV_QUANTITY [mm[Hg]]              required  │
│    │ │   ├── Diastolic · DV_QUANTITY [mm[Hg]]             optional  │
│    │ │   └── Comment · DV_TEXT                             optional  │
│    │ └── method · DV_CODED_TEXT [at0011, at0012]          optional  │
│    ▼ OBSERVATION · Pulse/Heart beat (v2)                  optional  │
│      └── any_event                                                  │
│          ├── Rate · DV_QUANTITY [/min]                     optional  │
│          └── Regularity · DV_CODED_TEXT                   optional  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Tree node display:**
- **Icon/colour**: RM type indicator (COMPOSITION, OBSERVATION, SECTION, CLUSTER, ELEMENT — each with a distinct colour or icon)
- **Label**: Human-readable name from term definition (with rename indicator if different from archetype default)
- **RM Type badge**: Small tag showing `DV_QUANTITY`, `DV_CODED_TEXT`, etc.
- **Occurrences badge**: "required" (red/orange) or "optional" (grey) or "0..*" for unbounded
- **Archetype ID**: Shown on archetype root nodes (e.g., `openEHR-EHR-OBSERVATION.blood_pressure.v2`)

### 4.3 Node Detail Panel

Clicking a tree node opens a detail panel (right side or below) showing:

```
┌─────────────────── Node Detail ────────────────────────┐
│                                                         │
│  Name:         Systolic                                 │
│  Node ID:      at0004                                   │
│  RM Type:      DV_QUANTITY                              │
│  Archetype:    openEHR-EHR-OBSERVATION.blood_pressure.v2│
│  Occurrences:  1..1 (mandatory)                         │
│                                                         │
│  FLAT Path (EHRBase):                                   │
│  vital_signs/blood_pressure/any_event/systolic          │
│                                      [Copy path]       │
│                                                         │
│  FLAT Path (Better):                                    │
│  vital_signs/blood_pressure:0/any_event:0/systolic      │
│                                      [Copy path]       │
│                                                         │
│  Data Type Attributes:                                  │
│  ├── |magnitude  (number)                               │
│  ├── |unit       (string: "mm[Hg]")                     │
│  └── |precision  (integer, optional)                    │
│                                                         │
│  Constraints:                                           │
│  └── Unit: mm[Hg] (fixed)                               │
│                                                         │
│  Terminology Bindings:                                  │
│  └── SNOMED-CT: 271649006 (Systolic blood pressure)     │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 4.4 FLAT Path List

A searchable, sortable list of all valid FLAT paths derived from the template:

```
┌──────────────────── FLAT Paths ────────────────────────────────────┐
│  🔍 [Filter paths...]        Platform: [EHRBase ▾]  [Export CSV]  │
│                                                                    │
│  PATH                                        RM TYPE    REQUIRED   │
│  ─────────────────────────────────────────────────────────────────  │
│  vital_signs/category|code                   CODE_PHR.  ✓          │
│  vital_signs/category|value                  CODE_PHR.  ✓          │
│  vital_signs/language|code                   CODE_PHR.  ✓          │
│  vital_signs/composer|name                   DV_TEXT    ✓          │
│  vital_signs/context/start_time              DV_DATE_T  ✓          │
│  vital_signs/blood_pressure/systolic|magnit  DV_QUANT.  ✓          │
│  vital_signs/blood_pressure/systolic|unit    DV_QUANT.  ✓          │
│  vital_signs/blood_pressure/diastolic|magni  DV_QUANT.             │
│  vital_signs/blood_pressure/diastolic|unit   DV_QUANT.             │
│  vital_signs/blood_pressure/comment          DV_TEXT               │
│  vital_signs/pulse_heart_beat/rate|magnitude DV_QUANT.             │
│  vital_signs/pulse_heart_beat/rate|unit      DV_QUANT.             │
│  ...                                                               │
│                                                                    │
│  Showing 24 of 24 paths                                            │
└────────────────────────────────────────────────────────────────────┘
```

**Path list features:**
- Click a path to highlight the corresponding node in the tree view
- Filter by RM type, required/optional, or text search
- Copy individual paths or export all paths
- Platform toggle changes paths between EHRBase and Better format
- Sort by path, RM type, or required status

### 4.5 Template Statistics Bar

A summary bar shown above the tree:

```
Template: Vital Signs  ·  v1  ·  Language: en
Nodes: 24  ·  Archetypes: 3  ·  Required fields: 8  ·  Coded values: 5
```

### 4.6 Export Options

| Export | Format | Contents |
|--------|--------|----------|
| FLAT path list | CSV | path, rm_type, required, min, max |
| FLAT path list | JSON | Array of path objects with metadata |
| Template summary | JSON | Statistics + archetype list + path list |
| Node detail | Clipboard | Individual FLAT path for copy-paste |

---

## 5. Technical Design

### 5.1 Implementation Approach

**Hybrid: JavaScript + Pyodide (Python)**

- **OPT XML parsing**: Pyodide + oehrpy's `OPTParser` (reuse from validator — already proven)
- **Web Template JSON parsing**: Pure JavaScript (JSON structure, no XML needed)
- **Tree rendering**: JavaScript DOM manipulation
- **Path enumeration**: JavaScript (from parsed template structure)

This matches the validator's architecture and avoids duplicating the OPT parsing logic in JavaScript.

### 5.2 Data Flow

```
OPT XML input                    Web Template JSON input
      │                                    │
      ▼                                    ▼
  [Pyodide]                          [JS parser]
  OPTParser.parse_string()      parseWebTemplate(json)
      │                                    │
      ▼                                    ▼
  TemplateDefinition              ParsedTemplate (JS)
      │                                    │
      └────────────┬───────────────────────┘
                   ▼
            Unified Node Tree (JS)
                   │
          ┌────────┼────────┐
          ▼        ▼        ▼
      Tree View  Path List  Statistics
```

### 5.3 Unified Node Model (JavaScript)

Both OPT and Web Template inputs are normalized into a common JS object model:

```javascript
{
  id: "at0004",
  name: "Systolic",
  rmType: "DV_QUANTITY",
  archetypeId: "openEHR-EHR-OBSERVATION.blood_pressure.v2",
  min: 1,
  max: 1,
  flatPath: "vital_signs/blood_pressure/any_event/systolic",
  renamedFrom: null,       // or "Substance/Agent" if template renamed
  constraints: {
    unit: ["mm[Hg]"],
    range: { min: 0, max: 1000 }
  },
  terminologyBindings: [
    { terminology: "SNOMED-CT", code: "271649006", text: "Systolic blood pressure" }
  ],
  codedValues: [
    { code: "at0011", text: "Auscultation" },
    { code: "at0012", text: "Palpation" }
  ],
  children: [ ... ]
}
```

### 5.4 File Structure

```
docs/
├── explorer.html          # New: template explorer page
├── converter.html         # New (PRD-0009)
├── validator.html         # Existing
├── index.html             # Landing page (add link)
└── ...
```

Single HTML file. Shares Pyodide loading infrastructure with the validator (if both are open in the same browser session, Pyodide is cached by the CDN).

### 5.5 Pyodide Integration

Reuse the same Pyodide bootstrapping pattern from `validator.html`:

1. Load Pyodide CDN script
2. Install `defusedxml` micropip package
3. Load oehrpy's `OPTParser` source into the Python runtime
4. Call `parse_string(xml_content)` and serialize the result to JSON for JavaScript consumption
5. Fallback: if Pyodide fails to load, show a message that only Web Template JSON input is available (no OPT XML support without Python)

---

## 6. Implementation Plan

| Task | Effort |
|------|--------|
| HTML/CSS scaffold: tree view layout, detail panel, path list | 1 day |
| Web Template JSON parser (JS) — extract tree, paths, constraints | 1 day |
| Tree rendering with collapsible nodes and RM type badges | 1.5 days |
| Node detail panel with FLAT path generation | 1 day |
| FLAT path enumeration and searchable list | 1 day |
| OPT XML input via Pyodide (reuse validator infrastructure) | 1 day |
| Platform-aware path display (EHRBase vs Better) | 0.5 day |
| Export (CSV, JSON, clipboard) | 0.5 day |
| Statistics bar | 0.25 day |
| Navigation updates (index.html, validator.html, converter.html) | 0.25 day |
| Example templates (built-in Vital Signs OPT + Web Template) | 0.5 day |
| Manual testing with production OPT files | 1 day |
| **Total** | **~9.5 days** |

### Future Enhancements (post v0.3.0)

| Enhancement | Effort |
|-------------|--------|
| Template diff: compare two OPTs side-by-side | 3 days |
| AQL path display alongside FLAT paths | 1 day |
| D3.js force-directed graph visualization | 3 days |
| OPT 2.0 (JSON format) support | 2 days |
| Deep-link to specific node (URL hash) | 0.5 day |
| Auto-generate FlatBuilder code snippet per node | 1.5 days |

---

## 7. Open Questions

| Question | Decision needed by |
|----------|--------------------|
| Should the tree view default to fully expanded or collapsed? For large templates (100+ nodes), fully expanded is overwhelming. Suggest: expand first two levels by default. | UI review |
| Should the explorer support drag-and-drop file upload, or is paste + file picker sufficient? | Design start |
| Should the path list show the full FLAT path including all `\|suffix` variants, or group them under the base path? E.g., show `systolic\|magnitude` and `systolic\|unit` as separate rows or as sub-items under `systolic`? | UI review |
| For Web Template JSON input, should we support fetching directly from a CDR URL (CORS allowing), or is paste-only sufficient for v1? | Implementation |
