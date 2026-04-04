# PRD-0012: oehrpy's Role in the openEHR Workflow — Docs Diagram Page

**Version:** 1.0
**Date:** 2026-04-04
**Status:** Draft
**Owner:** oehrpy (github.com/platzhersh/oehrpy)
**Milestone:** v0.2.0 docs

---

## Executive Summary

Add a "Workflow" or "Concepts" page to the oehrpy GitHub Pages documentation site that visually explains where oehrpy sits within the broader openEHR data lifecycle — from clinical modelling through CDR upload, app development, composition writing, and querying. The page centres a single interactive HTML diagram that maps each phase of the workflow, highlights which steps oehrpy is responsible for, and links anchor sections to relevant API reference pages.

The goal is to give new users a mental model *before* they read any API docs, reducing the most common onboarding friction: not understanding why the library is structured the way it is.

---

## Problem Statement

### Current State

The oehrpy README and API reference assume readers already understand the openEHR template lifecycle — how an `.opt` file relates to a Web Template, why FLAT paths come from `tree.id` values, and what role a builder class plays. This context is absent from the docs.

### Pain Points

- New users don't know *why* they need to fetch the Web Template before constructing a FLAT composition
- The relationship between `TemplateBuilder`, `FlatValidator`, and `AqlBuilder` is not obvious without ecosystem context
- oehrpy's scope boundary (what it does vs. what the CDR or modelling tool does) is unclear
- There is no "start here" conceptual page — the README jumps straight to installation

### Who This Is For

- **Developers new to openEHR** picking up oehrpy as their first contact with the ecosystem
- **FHIR developers** evaluating openEHR who need a workflow comparison point
- **Community members** linking to the oehrpy docs from the openEHR Discourse forum or the "Building Open CIS" article series

---

## Goals

1. Provide a single visual that answers "where does oehrpy fit?" in under 30 seconds
2. Clearly distinguish the phases oehrpy owns (app dev, write, query) from those it does not (modelling, CDR ops)
3. Serve as the canonical anchor reference for all other oehrpy docs pages
4. Support light and dark themes to match user system preferences

---

## Non-Goals

- This is not a tutorial or how-to guide — prose content is minimal
- This is not a FHIR-vs-openEHR comparison page (though it can coexist with one)
- This does not replace the API reference

---

## Technical Design

### Page Location

```
docs/
└── workflow.html    ← Standalone HTML page matching existing site structure
```

The diagram HTML is a standalone page consistent with the existing oehrpy docs site (static HTML with Inter font, brand colours).

### Diagram Architecture

A single self-contained HTML page (`workflow.html`) with:

- **Five workflow phases**, laid out vertically with left-side phase labels:
  1. Modelling *(out of oehrpy scope — dimmed)*
  2. CDR Upload *(out of oehrpy scope — dimmed)*
  3. App Development *(oehrpy primary)*
  4. Write Composition *(oehrpy primary)*
  5. Read / Query *(oehrpy primary)*

- **oehrpy highlight treatment**: phases 3–5 use the oehrpy brand colours (Blue `#3b82f6`, Orange `#f97316`) and full opacity; phases 1–2 are visually dimmed with a clear "outside oehrpy scope" label

- **Anchor IDs** on each phase section (`#modelling`, `#upload`, `#app-dev`, `#write`, `#read`) so API reference pages can deep-link to the relevant phase for contextual explanation

- **Format reference legend** below the diagram explaining `.opt`, Web Template, FLAT, Canonical, and AQL in one line each

- **`prefers-color-scheme` media query** providing a light theme variant; CSS custom properties used throughout so the switch requires only a variable override block

### Anchor Link Usage (examples)

```markdown
<!-- In FlatValidator API reference -->
> The `FlatValidator` catches path errors during [App Development](#app-dev)
> before a composition is submitted. See the [workflow overview](workflow.html#app-dev).

<!-- In TemplateBuilder API reference -->
> Builder classes produce compositions ready for the [Write phase](workflow.html#write).
```

### Dark / Light Theme Implementation

```css
:root {
  --bg: #1a1a2e;
  --text: #f3f4f6;
  --card-bg: #252540;
  /* ... */
}

@media (prefers-color-scheme: light) {
  :root {
    --bg: #F8FAFB;
    --text: #1A202C;
    --card-bg: #FFFFFF;
    /* ... */
  }
}
```

Brand colours (`#3b82f6`, `#f97316`) remain constant across both themes.

---

## Implementation Plan

### Phase 1 — Diagram (P0)

- [ ] Create workflow diagram HTML page with oehrpy-scoped framing
  - Dim phases 1–2 (Modelling, CDR Upload) with "outside oehrpy scope" badge
  - Highlight phases 3–5 with oehrpy brand treatment and SDK-specific node labels (`TemplateBuilder`, `FlatValidator`, `AqlBuilder`, builder classes)
  - Add anchor IDs to each phase wrapper
- [ ] Add `prefers-color-scheme` light theme CSS block
- [ ] Verify diagram renders correctly in GitHub Pages preview

### Phase 2 — Docs Integration (P0)

- [ ] Create `docs/workflow.html` with the diagram embedded
- [ ] Add "Workflow" to the docs site navigation across all pages
- [ ] Add anchor deep-links from docs page to the relevant phases

### Phase 3 — Cross-linking (P1)

- [ ] Reference the workflow page from the README ("New to openEHR? Start with the [workflow overview](docs/workflow.html)")

---

## Acceptance Criteria

- [ ] The diagram page loads correctly on the oehrpy GitHub Pages site in both light and dark system themes
- [ ] Phases 1–2 are visually distinct (dimmed) from phases 3–5 (oehrpy scope)
- [ ] Each phase has a working HTML anchor (`#modelling`, `#upload`, `#app-dev`, `#write`, `#read`)
- [ ] The diagram is navigable on mobile (horizontal scroll acceptable, no content clipping)
- [ ] The README includes a link to the workflow page

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Raw HTML consistency with site | Medium | Follow existing brand-kit.html and docs.html patterns exactly |
| Diagram becomes stale as oehrpy API evolves | Low | Anchor links and node labels are generic enough to survive minor API changes; review at each minor version bump |

---

## Related

- PRD-0006: `FlatValidator` module (the "App Development" phase node)
- PRD-0004: Dynamic Composition Builders (a concrete example of the "Write" phase)
- oehrpy GitHub: github.com/platzhersh/oehrpy
