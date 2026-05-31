# PRD-0014: GitHub Pages SEO Optimization

**Version:** 1.0
**Date:** 2026-05-31
**Status:** In Progress
**Owner:** Open CIS Project
**Priority:** P2 (Should Have)

---

## Executive Summary

The oehrpy project ships a marketing and documentation site via GitHub Pages
(served from the `docs/` folder at `https://platzhersh.github.io/oehrpy/`). The
site consists of hand-written, single-file HTML pages (`index`, `docs`,
`workflow`, `converter`, `explorer`, `validator`, `brand-kit`).

An audit found that while the pages have valid titles, `lang` attributes, and
mobile viewports, they are missing nearly every other discoverability and
social-sharing signal: no meta descriptions, no Open Graph / Twitter Card tags,
no canonical URLs, no favicon links, no structured data, and no `sitemap.xml`
or `robots.txt`. Three tool pages also lack an `<h1>`.

This PRD defines a focused, low-risk set of on-page SEO improvements that can be
applied directly to the existing static HTML without introducing a build step.

---

## Problem Statement

**Current pain points (audit findings):**

1. **No meta descriptions** on any page — search engines synthesize snippets
   from arbitrary page text, producing poor SERP listings.
2. **No Open Graph or Twitter Card tags** — links shared on Slack, LinkedIn,
   X, etc. render as bare URLs with no title, description, or preview image.
3. **No canonical URLs** — risk of duplicate-content dilution.
4. **No `sitemap.xml` / `robots.txt`** — slower and less complete crawling.
5. **No structured data (JSON-LD)** — no eligibility for rich results.
6. **No favicon `<link>`** — generic icon in browser tabs and results.
7. **Missing `<h1>`** on `converter.html`, `explorer.html`, `validator.html`.

---

## Goals

- Every page has a unique, descriptive `<meta name="description">`.
- Every page exposes Open Graph + Twitter Card metadata with a preview image.
- Every page declares a `rel="canonical"` URL and a favicon.
- The site has a valid `sitemap.xml` and `robots.txt`.
- The home page carries `SoftwareApplication` JSON-LD structured data.
- All pages have exactly one `<h1>`.

## Non-Goals

- No migration to a static-site generator (Jekyll, etc.) — out of scope.
- No redesign, copy rewrite, or performance/CSS refactor.
- No analytics or third-party tracking changes.

---

## Requirements

### Functional

| ID | Requirement |
|----|-------------|
| FR-1 | Each HTML page includes `<meta name="description">` (≤160 chars, page-specific). |
| FR-2 | Each page includes `og:type`, `og:site_name`, `og:title`, `og:description`, `og:url`, `og:image`. |
| FR-3 | Each page includes `twitter:card` (`summary`, until a 1200×630 image exists — see Implementation Notes), `twitter:title`, `twitter:description`, `twitter:image`. |
| FR-4 | Each page includes `<link rel="canonical">` with its absolute URL. |
| FR-5 | Each page links a favicon (`assets/logo.svg`) and sets `theme-color`. |
| FR-6 | `docs/sitemap.xml` lists all public pages with absolute URLs. |
| FR-7 | `docs/robots.txt` allows all crawlers and references the sitemap. |
| FR-8 | `index.html` includes a `SoftwareApplication` JSON-LD block. |
| FR-9 | `converter.html`, `explorer.html`, `validator.html` each have one `<h1>`. |

### Non-Functional

- Base URL: `https://platzhersh.github.io/oehrpy/`.
- No new runtime dependencies or build steps; pure static edits.
- Changes must not alter existing page layout or behavior.

---

## Success Metrics

- 7/7 pages pass a meta-tag audit (description + OG + Twitter + canonical).
- Social link previews render a title, description, and image.
- `sitemap.xml` and `robots.txt` resolve at the site root.
- Google Rich Results Test validates the `SoftwareApplication` markup.

---

## Implementation Notes

A shared `<head>` SEO block is inserted into each page immediately after the
`<title>` element. Because the pages are hand-maintained single files, the
block is templated per page with the correct title, description, and canonical
URL. The preview image reuses the existing `assets/logo.svg`. A future
follow-up may add a dedicated rasterized (PNG, 1200×630) social image, since
some platforms do not render SVG `og:image`. Until that image exists, the
`twitter:card` type is `summary` (square/logo-friendly) rather than
`summary_large_image`, which expects a large 1200×630 preview.
