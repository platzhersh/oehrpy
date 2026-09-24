// The documentation's pages, in reading order. Drives the docs sidebar,
// the mobile page menu and the previous/next links, and maps the section
// anchors of the former single-page docs.html to their new pages.
export interface DocsSection {
  id: string;
  label: string;
}

export interface DocsPage {
  /** URL relative to the site root. */
  path: string;
  /** Short label for navigation. */
  label: string;
  group: string;
  sections: DocsSection[];
}

export const DOCS_PAGES: DocsPage[] = [
  {
    path: "docs.html",
    label: "Getting Started",
    group: "Getting Started",
    sections: [
      { id: "installation", label: "Installation" },
      { id: "quick-start", label: "Quick Start" },
      { id: "overview", label: "Overview" },
    ],
  },
  {
    path: "docs/reference-model.html",
    label: "Reference Model",
    group: "Core Concepts",
    sections: [
      { id: "rm-classes", label: "RM Classes" },
      { id: "data-types", label: "Data Types" },
      { id: "validation", label: "RM Validation" },
      { id: "type-safety", label: "Type Safety" },
    ],
  },
  {
    path: "docs/templates.html",
    label: "Templates & Builders",
    group: "Core Concepts",
    sections: [
      { id: "opt-parser", label: "OPT Parser" },
      { id: "template-builders", label: "Template Builders" },
    ],
  },
  {
    path: "docs/serialization.html",
    label: "Serialization",
    group: "Core Concepts",
    sections: [
      { id: "canonical-json", label: "Canonical JSON" },
      { id: "flat-format", label: "FLAT Format" },
    ],
  },
  {
    path: "docs/ehrbase-client.html",
    label: "EHRBase Client",
    group: "API Reference",
    sections: [
      { id: "basic-operations", label: "Basic Operations" },
      { id: "querying-with-aql", label: "Querying with AQL" },
    ],
  },
  {
    path: "docs/aql.html",
    label: "AQL Query Builder",
    group: "API Reference",
    sections: [
      { id: "basic-queries", label: "Basic Queries" },
      { id: "complex-queries", label: "Complex Queries" },
    ],
  },
  {
    path: "docs/validation.html",
    label: "FLAT & OPT Validation",
    group: "Advanced",
    sections: [
      { id: "flat-validator", label: "FLAT Validator" },
      { id: "opt-validator", label: "OPT Validator" },
    ],
  },
  {
    path: "docs/development.html",
    label: "Development",
    group: "Advanced",
    sections: [
      { id: "setup", label: "Setup" },
      { id: "regenerating-rm-classes", label: "Regenerating RM Classes" },
      { id: "project-structure", label: "Project Structure" },
      { id: "running-tests", label: "Running Tests" },
    ],
  },
];

/**
 * Where each section anchor of the old single-page docs.html now lives,
 * so bookmarked links like docs.html#aql-builder keep working.
 */
export const LEGACY_DOCS_ANCHORS: Record<string, string> = {
  "rm-classes": "docs/reference-model.html#rm-classes",
  "data-types": "docs/reference-model.html#data-types",
  validation: "docs/reference-model.html#validation",
  "type-safety": "docs/reference-model.html#type-safety",
  "opt-parser": "docs/templates.html#opt-parser",
  "web-template": "docs/templates.html#web-template",
  "template-builders": "docs/templates.html#template-builders",
  serialization: "docs/serialization.html",
  "ehrbase-client": "docs/ehrbase-client.html",
  "aql-builder": "docs/aql.html",
  "flat-validator": "docs/validation.html#flat-validator",
  "opt-validator": "docs/validation.html#opt-validator",
  development: "docs/development.html",
};
