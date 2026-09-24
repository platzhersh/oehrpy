// schema.org JSON-LD builders shared by several pages. Layout.astro adds
// the BreadcrumbList itself; these cover the page-type specific objects.
import { AUTHOR, GITHUB_URL } from "./site";

const SITE = "https://oehrpy.dev/";
const abs = (path: string) => new URL(path, SITE).href;

/** An in-browser tool (Validator, Converter, Explorer). */
export function toolJsonLd(opts: {
  name: string;
  path: string;
  description: string;
  features: string[];
}): Record<string, unknown> {
  return {
    "@context": "https://schema.org",
    "@type": "WebApplication",
    name: opts.name,
    url: abs(opts.path),
    description: opts.description,
    applicationCategory: "DeveloperApplication",
    operatingSystem: "Any (runs in the browser)",
    browserRequirements: "Requires JavaScript",
    featureList: opts.features,
    isAccessibleForFree: true,
    offers: { "@type": "Offer", price: "0", priceCurrency: "USD" },
    author: AUTHOR,
    isPartOf: { "@type": "WebSite", name: "oehrpy", url: SITE },
  };
}

/** A documentation page. */
export function docsJsonLd(opts: {
  title: string;
  path: string;
  description: string;
}): Record<string, unknown> {
  return {
    "@context": "https://schema.org",
    "@type": "TechArticle",
    headline: opts.title,
    url: abs(opts.path),
    description: opts.description,
    inLanguage: "en",
    proficiencyLevel: "Beginner",
    author: AUTHOR,
    publisher: AUTHOR,
    about: [
      { "@type": "Thing", name: "openEHR", sameAs: "https://en.wikipedia.org/wiki/OpenEHR" },
      { "@type": "SoftwareSourceCode", name: "oehrpy", codeRepository: GITHUB_URL, programmingLanguage: "Python" },
    ],
    isPartOf: { "@type": "WebSite", name: "oehrpy", url: SITE },
  };
}
