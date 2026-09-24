// Generates /sitemap.xml from the pages in src/pages at build time, so it
// can't drift from the site. <lastmod> is the date of the last commit that
// touched the page's source file (pages.yml checks out full history for
// this); it is omitted when git history is unavailable.
import type { APIRoute } from "astro";
import { execFileSync } from "node:child_process";

/** Pages kept out of search results (they also carry a noindex tag). */
const EXCLUDED = new Set(["404.html", "brand-kit.html"]);

const pageFiles = Object.keys(import.meta.glob("./**/*.astro"));

function lastModified(file: string): string | undefined {
  try {
    const date = execFileSync("git", ["log", "-1", "--format=%cs", "--", `src/pages/${file}`], {
      encoding: "utf8",
    }).trim();
    return date || undefined;
  } catch {
    return undefined;
  }
}

export const GET: APIRoute = ({ site }) => {
  const entries = pageFiles
    .map((key) => {
      const file = key.replace(/^\.\//, "");
      const path = file === "index.astro" ? "" : file.replace(/\.astro$/, ".html");
      return { file, path };
    })
    .filter(({ path }) => !EXCLUDED.has(path))
    .sort((a, b) => a.path.localeCompare(b.path))
    .map(({ file, path }) => {
      const lastmod = lastModified(file);
      return [
        "  <url>",
        `    <loc>${new URL(path, site).href}</loc>`,
        ...(lastmod ? [`    <lastmod>${lastmod}</lastmod>`] : []),
        "  </url>",
      ].join("\n");
    });

  const xml = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ...entries,
    "</urlset>",
    "",
  ].join("\n");
  return new Response(xml, { headers: { "Content-Type": "application/xml; charset=utf-8" } });
};
