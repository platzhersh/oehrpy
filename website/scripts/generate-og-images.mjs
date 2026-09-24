// Renders the social preview images (public/og/*.png, 1200×630) and the
// apple-touch-icon (public/apple-touch-icon.png, 180×180) with headless
// Chromium. The PNGs are committed; re-run this after changing the texts
// below or the logo:
//
//   cd website && npm install --no-save playwright && node scripts/generate-og-images.mjs
//
// (Playwright is deliberately not a dependency: the site build doesn't
// need it.)
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";
import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const font = (weight) =>
  `url("file://${join(root, `node_modules/@fontsource/inter/files/inter-latin-${weight}-normal.woff2`)}") format("woff2")`;

/** Page images: file name, kicker, headline, subline. */
const IMAGES = [
  ["default", "oehrpy", "The Python SDK for openEHR", "Type-safe RM classes · FLAT & canonical JSON · EHRBase client · AQL builder"],
  ["docs", "oehrpy docs", "Build openEHR apps in Python", "Reference Model · templates · serialization · EHRBase · AQL · validation"],
  ["validator", "oehrpy tools", "openEHR FLAT & OPT Validator", "Check compositions against Web Templates, in your browser"],
  ["converter", "oehrpy tools", "Canonical JSON ⇄ FLAT Converter", "Convert openEHR compositions for EHRBase and Better, in your browser"],
  ["explorer", "oehrpy tools", "openEHR Template Explorer", "Browse Web Templates and every FLAT path, in your browser"],
  ["workflow", "oehrpy guide", "How openEHR works", "Archetypes · templates · compositions · CDRs · AQL"],
  ["vscode", "oehrpy for VS Code", "openEHR FLAT Validator", "Inline diagnostics, hover docs and quick fixes in your editor"],
];

const MARK = `
<svg viewBox="30 20 140 160" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="b" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#60a5fa"/><stop offset="100%" stop-color="#3b82f6"/></linearGradient>
    <linearGradient id="o" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#fdba74"/><stop offset="100%" stop-color="#f97316"/></linearGradient>
  </defs>
  <path d="M100 30 C55 30 45 65 45 85 C45 108 70 120 100 120 C130 120 155 108 155 85 C155 65 145 30 100 30" fill="url(#b)"/>
  <circle cx="72" cy="58" r="8" fill="#fff"/>
  <path d="M100 170 C145 170 155 135 155 115 C155 92 130 80 100 80 C70 80 45 92 45 115 C45 135 55 170 100 170" fill="url(#o)"/>
  <circle cx="128" cy="142" r="8" fill="#fff"/>
</svg>`;

const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;");
const base = `
  @font-face { font-family: Inter; font-weight: 400; src: ${font(400)}; }
  @font-face { font-family: Inter; font-weight: 600; src: ${font(600)}; }
  @font-face { font-family: Inter; font-weight: 700; src: ${font(700)}; }
  * { margin: 0; box-sizing: border-box; }
  body { background: #1a1a2e; font-family: Inter, sans-serif; color: #f3f4f6; }`;

const card = (kicker, title, sub) => `<!doctype html><html><head><style>${base}
  .card { width: 1200px; height: 630px; padding: 80px 88px; display: flex; flex-direction: column; justify-content: space-between;
          background: radial-gradient(900px 500px at 100% 0%, rgba(59,130,246,.22), transparent 60%),
                      radial-gradient(700px 420px at 0% 100%, rgba(249,115,22,.16), transparent 60%), #1a1a2e;
          border-bottom: 10px solid #3b82f6; }
  .top { display: flex; align-items: center; gap: 22px; }
  .top svg { width: 64px; height: 73px; }
  .kicker { font-size: 34px; font-weight: 600; color: #9ca3af; }
  h1 { font-size: 76px; font-weight: 700; line-height: 1.08; letter-spacing: -1.5px; max-width: 1000px; }
  p { font-size: 32px; color: #9ca3af; margin-top: 26px; max-width: 1000px; line-height: 1.35; }
  .url { font-size: 28px; font-weight: 600; color: #60a5fa; }
</style></head><body><div class="card">
  <div class="top">${MARK}<span class="kicker">${esc(kicker)}</span></div>
  <div><h1>${esc(title)}</h1><p>${esc(sub)}</p></div>
  <div class="url">oehrpy.dev</div>
</div></body></html>`;

const touchIcon = `<!doctype html><html><head><style>${base}
  .icon { width: 180px; height: 180px; display: flex; align-items: center; justify-content: center; }
  .icon svg { width: 118px; height: 135px; }
</style></head><body><div class="icon">${MARK}</div></body></html>`;

// Pages are loaded from temp files (not setContent) so the file:// font
// URLs are allowed to load.
const tmp = mkdtempSync(join(tmpdir(), "og-"));
const load = async (page, html) => {
  const file = join(tmp, "page.html");
  writeFileSync(file, html);
  await page.goto(`file://${file}`, { waitUntil: "load" });
  await page.evaluate(() => document.fonts.ready);
  // Only text pages use (and so load) the font.
  const ok = !html.includes("<h1") || (await page.evaluate(() => document.fonts.check("700 76px Inter")));
  if (!ok) throw new Error("Inter did not load; run `npm ci` in website/ first");
};

const browser = await chromium.launch();
try {
  const page = await browser.newPage({ viewport: { width: 1200, height: 630 } });
  for (const [name, kicker, title, sub] of IMAGES) {
    await load(page, card(kicker, title, sub));
    await page.screenshot({ path: join(root, `public/og/${name}.png`) });
    console.log(`public/og/${name}.png`);
  }
  await page.setViewportSize({ width: 180, height: 180 });
  await load(page, touchIcon);
  await page.screenshot({ path: join(root, "public/apple-touch-icon.png") });
  console.log("public/apple-touch-icon.png");
} finally {
  await browser.close();
  rmSync(tmp, { recursive: true, force: true });
}
