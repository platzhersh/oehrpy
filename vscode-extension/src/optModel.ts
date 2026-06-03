/**
 * VS Code-free types and helpers for OPT (Operational Template) validation.
 *
 * Kept free of the `vscode` API so detection and position-finding can be
 * unit-tested directly. The `vscode`-dependent pieces (Python discovery, CLI
 * execution, diagnostic publishing) live in `optValidator.ts` /
 * `optDiagnostics.ts`.
 */

export type OptSeverity = "error" | "warning" | "info";
export type OptCategory = "wellformedness" | "semantic" | "structural" | "flat_impact";

export interface OptIssue {
  severity: OptSeverity;
  category: OptCategory;
  code: string;
  message: string;
  xpath: string | null;
  node_id: string | null;
  archetype_id: string | null;
  suggestion: string | null;
}

export interface OptValidationResult {
  is_valid: boolean;
  template_id: string | null;
  concept: string | null;
  node_count: number;
  archetype_count: number;
  error_count: number;
  warning_count: number;
  issues: OptIssue[];
}

/** Outcome of an OPT validation attempt. */
export type OptValidationOutcome =
  | { kind: "ok"; result: OptValidationResult }
  | { kind: "unavailable"; detail: string }
  | { kind: "error"; detail: string };

/**
 * Classify a document as an OPT 1.4 template.
 *
 * `.opt` files are always treated as OPT. Other files (e.g. `.xml`) are
 * treated as OPT only if their content has a `<template>` root in the openEHR
 * namespace.
 */
export function classifyOptDocument(fileName: string, text: string): boolean {
  if (fileName.toLowerCase().endsWith(".opt")) {
    return true;
  }

  // Scan a bounded prefix for a <template> element declaring the openEHR
  // namespace, to stay cheap on large files.
  const head = text.slice(0, 4000);
  const templateMatch = /<(?:[\w.-]+:)?template\b[^>]*>/i.exec(head);
  if (!templateMatch) {
    return false;
  }
  // Require the openEHR namespace on an xmlns of the <template> tag itself, so
  // the namespace string appearing elsewhere in the prefix can't false-positive.
  return /\bxmlns(?::\w+)?=["'][^"']*schemas\.openehr\.org[^"']*["']/i.test(
    templateMatch[0],
  );
}

/**
 * Find the character offset range of the text most relevant to an issue.
 *
 * OPT issues carry no line numbers, only identifiers. We locate the issue by
 * searching for its `node_id` (e.g. `at0001`) or `archetype_id`, returning the
 * first occurrence. Returns `null` when no anchor is found, in which case the
 * caller should fall back to a file-level diagnostic.
 */
export function locateOptIssue(
  text: string,
  issue: OptIssue,
): { start: number; end: number } | null {
  const anchors = [issue.node_id, issue.archetype_id].filter(
    (a): a is string => typeof a === "string" && a.length > 0,
  );

  for (const anchor of anchors) {
    const idx = text.indexOf(anchor);
    if (idx !== -1) {
      return { start: idx, end: idx + anchor.length };
    }
  }

  return null;
}

/** Render an issue's message, appending its suggestion when present. */
export function formatOptMessage(issue: OptIssue): string {
  return issue.suggestion ? `${issue.message}\n\n→ ${issue.suggestion}` : issue.message;
}
