// Site-wide constants shared by the layout, structured data and sitemap.
export const SITE_NAME = "oehrpy";
export const GITHUB_URL = "https://github.com/platzhersh/oehrpy";
export const PYPI_URL = "https://pypi.org/project/oehrpy/";
export const AUTHOR = { "@type": "Organization", name: "Open CIS Project" } as const;

/** Default Open Graph image (1200×630 PNG in public/og/). */
export const DEFAULT_OG_IMAGE = "og/default.png";

/** A crumb in the BreadcrumbList; `path` is relative to the site root. */
export interface Crumb {
  name: string;
  path: string;
}
