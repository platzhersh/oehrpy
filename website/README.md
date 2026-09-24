# oehrpy — Website

The public site (<https://oehrpy.dev>, served by GitHub Pages): landing page, documentation, the in-browser Validator / Converter / Explorer tools, the workflow diagram, the VS Code extension page and the brand kit. Built with [Astro](https://astro.build). See [`docs/adr/0009-astro-for-github-pages-site.md`](../docs/adr/0009-astro-for-github-pages-site.md) for why it exists and how it is structured.

This is a separate npm project (its own `package.json`, `node_modules`, lockfile) — it is not part of the Python package build.

## Commands

Run from this directory (`website/`), with Node.js ≥ 22.12:

```bash
npm install       # install dependencies
npm run dev       # local dev server at http://localhost:4321/
npm run build     # type-check (astro check) + build to dist/
npm run preview   # preview the production build locally
npm run check     # type-check only
```

## Structure

```
website/
├── public/                static files served as-is (logo, robots.txt, sitemap.xml, .nojekyll)
├── src/
│   ├── components/        SiteHeader.astro (the one nav), Logo.astro, GithubIcon.astro
│   ├── layouts/           Layout.astro — shared <head>: SEO / Open Graph / Twitter tags, fonts, favicon
│   ├── utils/version.ts     package version, read from ../pyproject.toml at build time
│   ├── pages/             one .astro file per page (index, docs, validator, converter, …)
│   └── styles/pages/      each page's stylesheet
└── astro.config.mjs
```

- Pages build to flat files (`docs.html`, `validator.html`, …) at the site root, so existing links and the sitemap keep working — see `build.format` and `base` in `astro.config.mjs`.
- Link between pages with **relative** hrefs (`docs.html`, `assets/logo.svg`); every page is emitted at the site root.
- The interactive tools' JavaScript lives in `<script is:inline>` blocks inside each page because the markup calls those functions from `onclick=` attributes; `astro check` still type-checks it as JavaScript.
- The header version badge comes from `pyproject.toml` — don't hardcode versions in pages.

## Deployment

`.github/workflows/pages.yml` builds this project on every PR that touches it, and on `main` publishes `dist/` via `actions/deploy-pages` (requires Settings → Pages → Source = "GitHub Actions").
