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
├── public/                static files served as-is (logo, og/*.png share images, apple-touch-icon, robots.txt, .nojekyll)
├── scripts/               generate-og-images.mjs — renders public/og/*.png and the apple-touch-icon
├── src/
│   ├── components/        SiteHeader.astro (the one nav), ToolTitle/ToolAbout (tool pages), Logo, GithubIcon
│   ├── layouts/           Layout.astro — shared <head>: SEO / Open Graph / Twitter tags, JSON-LD, fonts, favicon
│   │                      DocsLayout.astro — docs sidebar, mobile page menu, previous/next links
│   ├── utils/             version.ts (from ../pyproject.toml), site.ts, docs-nav.ts (docs page list), structured-data.ts
│   ├── pages/             one .astro file per page; docs/ holds the docs topic pages; sitemap.xml.ts generates the sitemap
│   └── styles/pages/      each page's stylesheet
└── astro.config.mjs
```

- Pages build to flat files (`docs.html`, `docs/aql.html`, …), so existing links keep working — see `build.format` in `astro.config.mjs`.
- Link between pages with **root-absolute** hrefs (`/`, `/docs.html`, `/assets/logo.svg`): the docs topic pages live in `docs/`, and GitHub Pages serves `404.html` at whatever URL was requested. Link to the home page as `/`, never `/index.html`.
- The interactive tools' JavaScript lives in `<script is:inline>` blocks inside each page because the markup calls those functions from `onclick=` attributes; `astro check` still type-checks it as JavaScript.
- The header version badge comes from `pyproject.toml` — don't hardcode versions in pages.

## SEO

Every page passes `title`, `description` and `path` to `Layout.astro`, which emits the canonical URL, Open Graph/Twitter tags and JSON-LD. Conventions:

- **Titles** lead with what people search for and end with ` | oehrpy`, e.g. `openEHR AQL Query Builder for Python | oehrpy`.
- **Share images** are 1200×630 PNGs in `public/og/` (pass `image="og/<name>.png"`; the default is `og/default.png`). They are committed; after changing their texts in `scripts/generate-og-images.mjs`, regenerate them with `npm install --no-save playwright && node scripts/generate-og-images.mjs`.
- **Structured data**: `breadcrumbs` adds a BreadcrumbList; `jsonLd` takes extra schema.org objects (see `src/utils/structured-data.ts`).
- **`noindex`** keeps a page out of search results; also add it to `EXCLUDED` in `src/pages/sitemap.xml.ts`. New pages are added to the sitemap automatically.
- **Docs pages** use `DocsLayout.astro` and must be listed in `src/utils/docs-nav.ts`.

### Google Search Console

The site is verified with an HTML meta tag. Set the repository variable `GOOGLE_SITE_VERIFICATION` (Settings → Secrets and variables → Actions → Variables) to the `content` value Search Console gives you. `pages.yml` passes it to the build as `PUBLIC_GOOGLE_SITE_VERIFICATION`, and the tag is omitted while the variable is unset. After deploying, click *Verify* in Search Console and submit `https://oehrpy.dev/sitemap.xml` under *Sitemaps*. (Alternatively, verify the whole domain with a DNS TXT record, which needs no code.)

## Deployment

`.github/workflows/pages.yml` builds this project on every PR that touches it, and on `main` publishes `dist/` via `actions/deploy-pages` (requires Settings → Pages → Source = "GitHub Actions").
