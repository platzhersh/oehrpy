# ADR-0009: Astro for the GitHub Pages Site

**Date:** 2026-09-24

## Status

Accepted

**Related:** PRD-0014 (GitHub Pages SEO); openEHR Explorer's ADR-0024
("Astro + Vue for the Marketing/Docs Site"), which this decision mirrors.

## Context

The public site at <https://platzhersh.github.io/oehrpy/> was served by GitHub
Pages' "deploy from a branch" mode straight out of `docs/` on `main`. It
consisted of eight hand-written, fully self-contained HTML files — `index`,
`docs`, `validator`, `converter`, `explorer`, `workflow`, `vscode` and
`brand-kit` — totalling roughly 10,000 lines. Every page repeated its own
copy of:

- the ~20-line SEO `<head>` block (description, canonical URL, Open Graph,
  Twitter card, favicon, Google Fonts);
- the site header: inline SVG logo, the nav with the "Tools" dropdown, and the
  GitHub link;
- the same ~20-line vanilla-JS IIFE that makes the "Tools" dropdown open and
  close;
- a `<style>` block with its own `:root` design tokens.

That duplication had already drifted in ways nobody noticed:

- **Nav order** differed between pages — Workflow came *after* "Tools" on most
  pages but *before* it on `workflow.html` and `vscode.html`.
- **Logo**: `converter.html` had lost the SVG mark from its header entirely;
  `explorer.html` rendered it at a different size.
- **Version badge**: the Validator, Converter and Explorer headers all read a
  hardcoded `v0.4.0` while the package had moved on to `0.15.0` —
  `python-semantic-release` bumps `pyproject.toml` on every release, but
  nothing connected that to the site.
- **Dropdown behavior**: `workflow.html` and `vscode.html` used a different
  dropdown script from the other pages (no Escape-to-close, no focus return).
- **Design tokens** exist in two unrelated naming schemes (`--surface*` /
  `--accent` on the tool pages, `--bg-card` / `--blue` on workflow and vscode).

The sibling project openEHR Explorer hit exactly this problem with its own
hand-written Pages site and solved it by rebuilding it as an Astro project
(its ADR-0024). Using the same approach here keeps the two sites maintainable
the same way.

## Decision

We rebuild the site as an **[Astro](https://astro.build) project in
`website/`**, with its own `package.json` (separate from the Python package),
built and deployed by a GitHub Actions workflow
(`.github/workflows/pages.yml`) using `actions/upload-pages-artifact` +
`actions/deploy-pages`.

- **Astro, not a SPA framework:** the site is content-first and needs to ship
  as static, crawlable HTML (PRD-0014's SEO goals). Astro renders everything
  to static HTML at build time and ships no framework runtime.
- **No UI framework integration (unlike openEHR Explorer):** Explorer uses
  `@astrojs/vue` because its desktop app is written in Vue, so islands can be
  shared between the app and the site. oehrpy has no JavaScript UI of its own
  to share components with (the Python SDK is the product; the VS Code
  extension has no webview UI), so a Vue/React integration would only add
  dependency surface. Astro components cover the shared layout; an
  integration can be added later if an interactive component would benefit
  from it.
- **Same URLs:** `base: "/oehrpy"` (it is a GitHub *project* site) and
  `build.format: "file"` keep every existing URL (`docs.html`,
  `validator.html`, …) working, so the README links, the sitemap, and search
  engine indexing are unaffected.
- **Deploy via Actions, not by committing build output to `docs/`:** avoids
  checking generated files into the repo and matches GitHub's recommended
  Pages setup. The `build` job runs on every PR that touches `website/`, so a
  broken page or type error fails CI before merge.

### What is shared now

- **`Layout.astro`** — one `<head>`: title, description, canonical URL, Open
  Graph and Twitter tags (built from the page path and the configured `site` +
  `base`), favicon and fonts. Pages pass only their title/descriptions.
- **`SiteHeader.astro`** — the one nav, with an `active` prop instead of
  hand-placed `class="active"`, one nav order, one dropdown script (the
  accessible variant, now typed TypeScript), and the logo from `Logo.astro`.
- **`src/lib/version.ts`** — imports the root `pyproject.toml` at build time,
  so the header badge always shows the released version.

### What deliberately did *not* change in this migration

The goal is a **behavior-preserving port** so the diff can be reviewed as
"same site, new tooling":

- Each page's CSS moved verbatim into `src/styles/pages/<page>.css`; the two
  token schemes and per-page footers were **not** unified yet, as that would
  be a visual redesign rather than a migration.
- The tool pages' JavaScript (the Pyodide-backed Validator, the Converter,
  the Explorer, the brand-kit animations) stays as `<script is:inline>`
  blocks, unchanged apart from dropping the duplicated dropdown IIFE. The
  markup calls these functions from `onclick=` attributes, which needs them as
  page globals; Astro's bundled `<script>` modules would scope them away.
  `astro check` still type-checks these blocks as JavaScript.

The port was verified by rendering every old and new page in headless
Chromium: full-page screenshots are pixel-identical apart from the intended
header changes (nav order, converter logo, version number) and running
animations, and the Validator (FLAT, OPT and migration modes), Converter and
Explorer produce identical output on their built-in examples with no new
console errors.

## Consequences

### Positive

- One source of truth for the `<head>` and navigation — adding a page or a
  nav entry is a one-file change, and the drift described above is fixed.
- The version badge can no longer go stale.
- `npm run build` (`astro check && astro build`) fails CI on a broken page or
  type error; the static HTML had no equivalent.
- The same structure and tooling as openEHR Explorer's `website/`.

### Negative

- A Node.js toolchain (`website/package-lock.json`) to keep pinned and
  updated alongside the Python one.
- Contributors editing the site need basic familiarity with `.astro` files,
  e.g. that literal `{`/`}` in page markup must be written as `&#123;` /
  `&#125;` because braces start template expressions.
- The Pages source setting has to be switched manually once (see below).

### Neutral

- The large inline tool scripts are no more modular than before; extracting
  them into typed modules is possible now but left for later.

## Migration Plan

1. **Land `website/` and `pages.yml`** alongside the still-live `docs/` site.
   The workflow builds on PRs and pushes; its deploy job only takes effect
   once step 2 is done.
2. **Cut over:** Settings → Pages → Build and deployment → Source →
   "GitHub Actions", then re-run the "Pages (website)" workflow on `main`
   (or push a change under `website/`).
3. **Retire the old site files** from `docs/` (`*.html`, `assets/`,
   `robots.txt`, `sitemap.xml`). Until then they are frozen: edit
   `website/` only. `docs/adr/`, `docs/prd/` and the Markdown guides stay —
   they are project documentation, not site source. The README's logo
   reference (`docs/assets/logo.svg`) must move to
   `website/public/assets/logo.svg` in the same change.
4. **Follow-ups (out of scope):** unify the two design-token schemes and the
   per-page footers into shared components; generate `sitemap.xml` with
   `@astrojs/sitemap`; move the tool scripts into typed modules.

## Alternatives Considered

### Keep the hand-written HTML and deduplicate with a script / includes

- **Pros:** no new toolchain.
- **Cons:** no build-time validation, no component model, and homemade
  include tooling is a worse version of what a static site generator offers.
- **Verdict:** Rejected — treats the symptom only.

### MkDocs (Material) or Sphinx

- **Pros:** Python-native, the default choice for Python library docs.
- **Cons:** built for Markdown documentation, not for the custom landing page,
  interactive in-browser tools, workflow diagram and brand kit that make up
  most of this site; porting those would mean fighting the theme. It would
  also diverge from openEHR Explorer's setup.
- **Verdict:** Rejected for the site as a whole. It could still make sense
  later for generated API reference docs, published under a sub-path.

### Astro + Vue (identical to openEHR Explorer)

- **Pros:** exactly the same stack as the sibling project.
- **Cons:** the Vue integration exists there to share components with a Vue
  app; oehrpy has none, so it would add a dependency with no current user.
- **Verdict:** Deferred — trivial to add (`@astrojs/vue`) once an
  interactive component warrants it.

## References

- `website/README.md` — local development instructions
- `.github/workflows/pages.yml`
- [Astro documentation](https://docs.astro.build)
- [GitHub Pages: publishing with a custom GitHub Actions workflow](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
- openEHR Explorer ADR-0024: <https://github.com/platzhersh/openehr-explorer/blob/main/docs/adr/ADR-0024-astro-vue-marketing-site.md>
