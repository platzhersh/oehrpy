# PRD-0007: GitHub Pages Documentation Site

**Version:** 1.1
**Date:** 2026-03-11
**Status:** Draft
**Owner:** Open CIS Project

---

## Executive Summary

Set up a GitHub Pages documentation site for oehrpy that consolidates project documentation, architecture references, guides, and background context into an accessible, well-organized public site. This makes the project more discoverable, lowers the barrier to adoption, and provides a central hub for developers working with openEHR in Python.

---

## Problem Statement

**Current Pain Points:**

1. **Documentation is scattered** — Guides, ADRs, PRDs, and format references live as raw Markdown files in `docs/`, discoverable only by browsing the repository directly
2. **No landing page for newcomers** — Developers evaluating oehrpy must read the README and then navigate into multiple subdirectories to understand the project's scope
3. **Medium articles are disconnected** — The "Building Open CIS" article series provides important context and motivation but is only linked at the bottom of the README
4. **Architecture decisions are hard to find** — ADRs and PRDs are valuable but buried in subdirectories with no index or navigation
5. **No API reference surface** — There is no rendered documentation for the 134 RM types, builders, or client API

**User Personas:**

1. **New evaluator** — Wants to quickly understand what oehrpy does, how mature it is, and whether it fits their needs
2. **Adopting developer** — Needs guides on FLAT format, template builders, and EHRBase integration
3. **Contributor** — Needs architecture context (ADRs, PRDs) and development setup instructions
4. **openEHR community member** — Looking for a Python SDK and finding the project via search or conference references

---

## Goals

| # | Goal | Success Metric |
|---|------|----------------|
| 1 | Provide a public documentation site at `platzhersh.github.io/oehrpy` | Site is live and indexed by search engines |
| 2 | Consolidate existing docs into a navigable structure | All current `docs/` content is reachable within 2 clicks from the home page |
| 3 | Surface the "Building Open CIS" article series prominently | Articles are linked on the home page and in a dedicated background section |
| 4 | Include architecture documentation (ADRs, PRDs) with an index | Each ADR/PRD is rendered as a page with a listing page |
| 5 | Automate deployment so docs stay in sync with `main` | GitHub Actions workflow deploys on every push to `main` |
| 6 | Apply consistent Open CIS branding across the docs site | Brand colors, logo, favicon, and typography match the Archetype Brick brand kit |

---

## Proposed Solution

### Static Site Generator: MkDocs + Material Theme

Use [MkDocs](https://www.mkdocs.org/) with the [Material for MkDocs](https://squidfundamentals.com/mkdocs-material/) theme. This is the dominant choice for Python project documentation because:

- Markdown-native (reuses existing `docs/*.md` files with minimal changes)
- Excellent search, navigation, and mobile support out of the box
- Built-in support for code syntax highlighting, admonitions, and tabs
- `mkdocstrings` plugin can auto-generate API reference from docstrings
- Widely adopted in the Python ecosystem (FastAPI, Pydantic, httpx all use it)

### Site Structure

```
Home (index.md)
├── Getting Started
│   ├── Installation
│   ├── Quick Start (from README examples)
│   └── Compatibility
│
├── Guides
│   ├── FLAT Format Guide (flat-format-learnings.md)
│   ├── FLAT Format Versions (FLAT_FORMAT_VERSIONS.md)
│   ├── Template Builders — OPT to Builder Workflow
│   ├── EHRBase Client Usage
│   ├── AQL Query Builder
│   └── Integration Testing (integration-testing-journey.md)
│
├── Architecture
│   ├── Overview — Component Diagram & Design Patterns
│   ├── ADR Index
│   │   ├── ADR-0000: Record Architecture Decisions
│   │   ├── ADR-0001: RM 1.1.0 Support
│   │   ├── ADR-0002: Integration Testing
│   │   ├── ADR-0003: Pre-commit Hooks
│   │   └── ADR-0004: Semantic Release
│   └── PRD Index
│       ├── PRD-0000: Python openEHR SDK
│       ├── PRD-0001: ODIN Parser
│       ├── PRD-0002: Composition Lifecycle
│       ├── PRD-0003: Audit & Contributions
│       ├── PRD-0004: Dynamic Composition Builders
│       ├── PRD-0005: EHR Management & Query Extensions
│       └── PRD-0007: GitHub Pages Documentation (this document)
│
├── API Reference (future — via mkdocstrings)
│   ├── RM Types
│   ├── Serialization
│   ├── Templates & Builders
│   ├── AQL Builder
│   └── EHRBase Client
│
├── Background
│   ├── About oehrpy — Pronunciation, Name, Motivation
│   ├── The openEHR Ecosystem
│   ├── Building Open CIS Article Series
│   │   ├── Part 4: The openEHR SDK Landscape
│   │   └── Part 5: oehrpy — A Python SDK for openEHR
│   └── EHRBase Issues & Learnings
│       ├── FLAT Format Documentation Gap
│       └── FLAT Format Discourse Research
│
├── Branding
│   ├── Brand Kit — The Archetype Brick (interactive HTML)
│   └── Logo Suite (interactive HTML)
│
├── Contributing (CONTRIBUTING.md)
└── Changelog (CHANGELOG.md)
```

---

## Content Plan

### Home Page (`index.md`)

- Project name, pronunciation, and one-line description
- Key features list (type-safe RM, template builders, EHRBase client, AQL builder)
- Badges: CI status, PyPI version, Python versions, license
- Quick install command
- Minimal "hello world" code example
- Links to the "Building Open CIS" article series for background context

### Getting Started

Extracted and expanded from the current README:

- **Installation** — pip install, source install, optional extras (`[dev]`, `[generator]`)
- **Quick Start** — Copy-pasteable examples for RM objects, template builders, FLAT format, EHRBase client, and AQL builder
- **Compatibility** — Python version matrix, openEHR RM version, EHRBase version requirements

### Guides

Reuse and lightly adapt existing documentation:

| Source File | Page Title | Adaptation Needed |
|-------------|-----------|-------------------|
| `docs/flat-format-learnings.md` | FLAT Format Guide | Add front matter, minor formatting |
| `docs/FLAT_FORMAT_VERSIONS.md` | FLAT Format Versions | Add front matter |
| `docs/integration-testing-journey.md` | Integration Testing Guide | Add front matter |
| *New content* | Template Builders Guide | Write guide for OPT → builder workflow |
| *New content* | EHRBase Client Guide | Expand README client section into full guide |
| *New content* | AQL Query Builder Guide | Expand README AQL section into full guide |

### Architecture Section

- **Overview page** — Describe the five core components (RM, Serialization, Templates, Client, AQL) with a component diagram, key design patterns (generated code conventions, FLAT path structure, builder pattern)
- **ADR Index** — Listing page with title, status, and date for each ADR, linking to the rendered ADR pages
- **PRD Index** — Same format for PRDs

Existing ADR/PRD Markdown files are used directly with MkDocs `nav` configuration — no content duplication.

### Background Section

This section provides context that helps users understand *why* oehrpy exists and where it fits:

- **About oehrpy** — Name origin, pronunciation (/oʊ.ɛər.paɪ/ "o-air-pie"), project history, and motivation
- **The openEHR Ecosystem** — Brief explainer of openEHR, reference model, archetypes, templates, and CDRs for developers new to the domain
- **Building Open CIS Article Series** — Dedicated page linking to and summarizing the Medium articles:
  - [Part 4: The openEHR SDK Landscape](https://medium.com/@platzh1rsch/building-open-cis-part-4-the-openehr-sdk-landscape-1b93411ec279) — Survey of existing openEHR SDKs and the gap that motivated oehrpy
  - [Part 5: oehrpy — A Python SDK for openEHR](https://medium.com/@platzh1rsch/building-open-cis-part-5-oehrpy-a-python-sdk-for-openehr-c9c90f46d075) — Announcement and walkthrough of oehrpy
- **EHRBase Issues & Learnings** — Renders existing `docs/ehrbase-issues/` content and `RESEARCH_FLAT_FORMAT_DISCOURSE.md`

### Branding Section

The documentation site serves as the canonical reference for Open CIS / oehrpy branding. Two interactive brand kit HTML files are already in the repository:

| File | Description |
|------|-------------|
| `docs/brand-kit-archetype-brick.html` | **The Archetype Brick** — Current brand concept with isometric stacked bricks, animated "snap" hero, color palette, light/dark logo lockups, typography spec, and favicon/scale testing |
| `docs/brand-kit.html` | **Logo Suite** — Earlier logo exploration with multiple variants |

**Brand Guidelines page** (`branding/guidelines.md`) — A Markdown summary of the brand identity for quick reference:

- **Concept:** "The Archetype Brick" — isometric interlocking bricks representing openEHR archetypes as composable building blocks
- **Color Palette:**
  - **Archetype Blue** `#005EB8` (RGB: 0, 94, 184) — Primary, used for top brick and "cis" wordmark
  - **Foundation Orange** `#F39200` (RGB: 243, 146, 0) — Secondary, used for bottom brick (foundation layer)
  - **Clinical Neutrals** — Slate scale (slate-900 through slate-50) for UI scaffolding
- **Typography:** Inter (Light for "open", Black for "cis") — weight contrast represents the transition from open-source foundations to clinical-specific tools
- **Logo Construction:** `open` (Inter Light) + `cis` (Inter Black, Archetype Blue) with brick icon
- **Logo Variants:** Light mode (dark text), dark mode (white text), social icon (white-on-blue), glyph-only ("OC")
- **Favicon:** Simplified two-brick isometric icon without studs, works at 16x16 and 32x32

**Applying brand to MkDocs:**

The Material theme will be customized via `docs/stylesheets/brand.css`:

```css
/* Open CIS Brand Colors — The Archetype Brick */
:root {
  --md-primary-fg-color: #005EB8;        /* Archetype Blue */
  --md-primary-fg-color--light: #3380C8;
  --md-primary-fg-color--dark: #004A93;
  --md-accent-fg-color: #F39200;         /* Foundation Orange */
  --md-accent-fg-color--transparent: rgba(243, 146, 0, 0.1);
}

[data-md-color-scheme="slate"] {
  --md-primary-fg-color: #3380C8;        /* Lighter blue for dark mode */
  --md-accent-fg-color: #F5A623;         /* Slightly lighter orange for dark mode */
}
```

**Assets to extract from the brand kit SVGs:**

| Asset | Source | Target |
|-------|--------|--------|
| `docs/assets/logo.svg` | Two-brick icon with studs from brand kit | MkDocs header logo |
| `docs/assets/favicon.svg` | Simplified brick icon (no studs) | Browser tab icon |
| `docs/assets/social-card.png` | Blue background variant from brand kit | og:image for link previews (Phase 3) |

### API Reference (Phase 2)

- Use `mkdocstrings` with the Python handler to auto-generate reference pages from docstrings
- Requires adding docstrings to key public classes/functions (a separate effort)
- Initial scope: RM types listing, builder API, client API, AQL builder API

---

## Technical Implementation

### Repository Changes

```
oehrpy/
├── mkdocs.yml                    # MkDocs configuration
├── docs/
│   ├── index.md                  # Home page (new)
│   ├── getting-started/
│   │   ├── installation.md       # (new)
│   │   ├── quick-start.md        # (new)
│   │   └── compatibility.md      # (new)
│   ├── guides/
│   │   ├── flat-format.md        # (symlink or copy of flat-format-learnings.md)
│   │   ├── flat-format-versions.md
│   │   ├── template-builders.md  # (new)
│   │   ├── ehrbase-client.md     # (new)
│   │   ├── aql-builder.md        # (new)
│   │   └── integration-testing.md
│   ├── architecture/
│   │   ├── overview.md           # (new)
│   │   ├── adr/                  # (existing — referenced via nav)
│   │   └── prd/                  # (existing — referenced via nav)
│   ├── background/
│   │   ├── about.md              # (new)
│   │   ├── openehr-ecosystem.md  # (new)
│   │   ├── articles.md           # (new — links to Medium series)
│   │   └── ehrbase-issues/       # (existing)
│   ├── assets/
│   │   ├── logo.svg              # Archetype Brick icon (extracted from brand kit SVG)
│   │   └── favicon.svg           # Simplified brick favicon
│   ├── stylesheets/
│   │   └── brand.css             # Open CIS brand color overrides
│   ├── branding/
│   │   ├── guidelines.md         # Brand guidelines summary (new)
│   │   ├── brand-kit-archetype-brick.html  # (existing)
│   │   └── brand-kit.html        # (existing)
│   ├── contributing.md           # (from CONTRIBUTING.md)
│   └── changelog.md              # (from CHANGELOG.md)
│
└── .github/workflows/
    └── docs.yml                  # GitHub Pages deployment workflow (new)
```

### `mkdocs.yml` Configuration

```yaml
site_name: oehrpy
site_description: Python SDK for openEHR — Type-safe RM classes, template builders, EHRBase client, and AQL query builder
site_url: https://platzhersh.github.io/oehrpy
repo_url: https://github.com/platzhersh/oehrpy
repo_name: platzhersh/oehrpy

theme:
  name: material
  logo: assets/logo.svg           # Archetype Brick icon (extracted from brand kit)
  favicon: assets/favicon.svg     # Simplified brick icon for browser tabs
  font:
    text: Inter                   # Brand primary font (per brand kit)
    code: JetBrains Mono
  palette:
    - scheme: default
      primary: custom             # Archetype Blue #005EB8 (via extra.css)
      accent: custom              # Foundation Orange #F39200 (via extra.css)
      toggle:
        icon: material/brightness-7
        name: Switch to dark mode
    - scheme: slate
      primary: custom
      accent: custom
      toggle:
        icon: material/brightness-4
        name: Switch to light mode
  features:
    - navigation.instant
    - navigation.sections
    - navigation.expand
    - navigation.top
    - search.suggest
    - search.highlight
    - content.code.copy
    - content.tabs.link

extra_css:
  - stylesheets/brand.css         # Open CIS brand color overrides

plugins:
  - search
  # Phase 2:
  # - mkdocstrings:
  #     handlers:
  #       python:
  #         paths: [src]

markdown_extensions:
  - admonition
  - pymdownx.highlight
  - pymdownx.superfences
  - pymdownx.tabbed:
      alternate_style: true
  - pymdownx.details
  - toc:
      permalink: true

nav:
  - Home: index.md
  - Getting Started:
      - Installation: getting-started/installation.md
      - Quick Start: getting-started/quick-start.md
      - Compatibility: getting-started/compatibility.md
  - Guides:
      - FLAT Format Guide: guides/flat-format.md
      - FLAT Format Versions: guides/flat-format-versions.md
      - Template Builders: guides/template-builders.md
      - EHRBase Client: guides/ehrbase-client.md
      - AQL Query Builder: guides/aql-builder.md
      - Integration Testing: guides/integration-testing.md
  - Architecture:
      - Overview: architecture/overview.md
      - ADRs:
          - ADR-0000 — Record Architecture Decisions: adr/0000-record-architecture-decisions.md
          - ADR-0001 — RM 1.1.0 Support: adr/0001-odin-parsing-and-rm-1.1.0-support.md
          - ADR-0002 — Integration Testing: adr/0002-integration-testing-with-ehrbase.md
          - ADR-0003 — Pre-commit Hooks: adr/0003-pre-commit-hooks-for-code-quality.md
          - ADR-0004 — Semantic Release: adr/0004-python-semantic-release-for-release-automation.md
      - PRDs:
          - PRD-0000 — Python openEHR SDK: prd/PRD-0000-python-openehr-sdk.md
          - PRD-0001 — ODIN Parser: prd/PRD-0001-odin-parser.md
          - PRD-0002 — Composition Lifecycle: prd/PRD-0002-composition-lifecycle.md
          - PRD-0003 — Audit & Contributions: prd/PRD-0003-audit-and-contributions.md
          - PRD-0004 — Dynamic Builders: prd/PRD-0004-dynamic-composition-builders.md
          - PRD-0005 — EHR Management: prd/PRD-0005-ehr-management-and-query-extensions.md
          - PRD-0007 — GitHub Pages Docs: prd/PRD-0007-github-pages-documentation.md
  - Background:
      - About oehrpy: background/about.md
      - The openEHR Ecosystem: background/openehr-ecosystem.md
      - Article Series: background/articles.md
      - EHRBase Issues: ehrbase-issues/README.md
  - Branding:
      - Brand Guidelines: branding/guidelines.md
      - Brand Kit — Archetype Brick: branding/brand-kit-archetype-brick.html
      - Logo Suite: branding/brand-kit.html
  - Contributing: contributing.md
  - Changelog: changelog.md
```

### GitHub Actions Workflow (`.github/workflows/docs.yml`)

```yaml
name: Deploy Documentation

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: true

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install mkdocs-material
      - run: mkdocs build --strict
      - uses: actions/upload-pages-artifact@v3
        with:
          path: site/

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - id: deployment
        uses: actions/deploy-pages@v4
```

### GitHub Pages Setup

1. Enable GitHub Pages in repository settings → Pages → Source: **GitHub Actions**
2. No `gh-pages` branch needed — the workflow uses the modern `actions/deploy-pages` approach

---

## Phased Rollout

### Phase 1: Foundation (This PRD)

- Set up `mkdocs.yml` with Material theme
- Apply Open CIS branding: Archetype Blue/Foundation Orange colors, Inter font, brick logo and favicon
- Create `docs/stylesheets/brand.css` with brand color overrides
- Extract logo and favicon SVGs from the brand kit
- Create home page (`index.md`) with branded hero
- Wire existing docs into the nav (ADRs, PRDs, FLAT format guides)
- Create "Getting Started" pages from README content
- Create "Background" section with Medium article links
- Create "Branding" section with brand guidelines page and links to interactive brand kits
- Add GitHub Actions deployment workflow
- **Deliverable:** Live site at `platzhersh.github.io/oehrpy` with branded design and all existing content navigable

### Phase 2: Expanded Guides

- Write dedicated guide pages for template builders, EHRBase client, and AQL builder
- Add architecture overview page with component diagram
- Add `mkdocstrings` for auto-generated API reference (requires adding docstrings)

### Phase 3: Polish

- Add versioned docs (for future SDK versions)
- Add branded social cards using the Archetype Brick social icon variant (og:image for link previews)
- Add announcement banner for new releases
- Consider custom domain if desired

---

## Dependencies & Requirements

| Dependency | Purpose | Version |
|-----------|---------|---------|
| `mkdocs` | Static site generator | >=1.5 |
| `mkdocs-material` | Theme | >=9.0 |
| `mkdocstrings[python]` | API reference (Phase 2) | >=0.24 |

These are documentation-only dependencies — they do not affect the runtime SDK package.

---

## Open Questions

1. **Custom domain?** — Should the docs live at a custom domain (e.g., `oehrpy.dev`) or is `platzhersh.github.io/oehrpy` sufficient for now?
2. **Versioned docs?** — Should we set up `mike` for version-specific documentation from the start, or defer to Phase 3?
3. **API reference scope** — Which classes/modules should have auto-generated API docs first? All 134 RM types, or start with builders and client?
4. **Additional Medium articles** — Are there other articles in the "Building Open CIS" series (Parts 1–3, or 6+) that should be referenced?

---

## References

- [MkDocs Documentation](https://www.mkdocs.org/)
- [Material for MkDocs](https://squidfundamentals.com/mkdocs-material/)
- [GitHub Pages with Actions](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site#publishing-with-a-custom-github-actions-workflow)
- [mkdocstrings](https://mkdocstrings.github.io/)
- [Building Open CIS Part 4: The openEHR SDK Landscape](https://medium.com/@platzh1rsch/building-open-cis-part-4-the-openehr-sdk-landscape-1b93411ec279)
- [Building Open CIS Part 5: oehrpy — A Python SDK for openEHR](https://medium.com/@platzh1rsch/building-open-cis-part-5-oehrpy-a-python-sdk-for-openehr-c9c90f46d075)
