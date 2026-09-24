import { defineConfig } from "astro/config";

// Published by GitHub Pages under the custom domain https://oehrpy.dev,
// so the site is served from the domain root (no project-site base path).
// `build.format: "file"` keeps the historical flat URLs (`docs.html`,
// `validator.html`, …) instead of Astro's default `/docs/` directory
// style, so existing links and the sitemap keep working. Pages link to
// each other with relative hrefs. See
// docs/adr/0009-astro-for-github-pages-site.md.
export default defineConfig({
  site: "https://oehrpy.dev",
  outDir: "./dist",
  build: {
    format: "file",
  },
});
