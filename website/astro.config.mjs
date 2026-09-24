import { defineConfig } from "astro/config";

// Published as a GitHub Pages *project* site at
// https://platzhersh.github.io/oehrpy/, hence `base: "/oehrpy"`.
// `build.format: "file"` keeps the historical flat URLs (`docs.html`,
// `validator.html`, …) instead of Astro's default `/docs/` directory
// style, so the README links, the sitemap, and search engine indexing
// keep working. Pages link to each other with relative hrefs, which
// resolve correctly under the base path because every page is emitted
// at the site root. See docs/adr/0009-astro-for-github-pages-site.md.
export default defineConfig({
  site: "https://platzhersh.github.io",
  base: "/oehrpy",
  outDir: "./dist",
  build: {
    format: "file",
  },
});
