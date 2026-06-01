/**
 * File-loading wrappers around the in-process FLAT validator.
 *
 * Validation runs entirely in TypeScript (see `validation.ts`) — no Python
 * interpreter is required. Parsed Web Templates are cached by path + mtime so
 * repeated validations of the same template are cheap.
 */

import * as fs from "fs";
import {
  enumerateValidPaths,
  inspectPath,
  parseWebTemplate,
  validateComposition,
  type FlatValidationResult,
  type ParsedWebTemplate,
  type PathInspection,
  type Platform,
} from "./validation";

export type {
  FlatValidationError,
  FlatValidationResult,
  PathInspection,
  Platform,
} from "./validation";

const templateCache = new Map<string, { parsed: ParsedWebTemplate; mtime: number }>();

/**
 * Load and parse a Web Template from disk, caching by file mtime.
 *
 * @throws if the file cannot be read or is not a valid Web Template.
 */
function loadParsedTemplate(webTemplatePath: string): ParsedWebTemplate {
  const stat = fs.statSync(webTemplatePath);
  const cached = templateCache.get(webTemplatePath);
  if (cached && cached.mtime === stat.mtimeMs) {
    return cached.parsed;
  }

  const content = fs.readFileSync(webTemplatePath, "utf-8");
  const json = JSON.parse(content) as Record<string, unknown>;
  const parsed = parseWebTemplate(json);
  templateCache.set(webTemplatePath, { parsed, mtime: stat.mtimeMs });
  return parsed;
}

/**
 * Validate a FLAT composition (as raw JSON text) against a Web Template.
 *
 * @throws if either the Web Template or the composition cannot be parsed, or
 *   if the composition is not a JSON object of FLAT paths to values.
 */
export function validateFlatComposition(
  webTemplatePath: string,
  compositionText: string,
  platform: Platform,
): FlatValidationResult {
  const parsed = loadParsedTemplate(webTemplatePath);

  let composition: unknown;
  try {
    composition = JSON.parse(compositionText);
  } catch (error) {
    const detail = error instanceof Error ? error.message : "invalid JSON";
    throw new Error(`Composition is not valid JSON: ${detail}`);
  }

  if (
    typeof composition !== "object" ||
    composition === null ||
    Array.isArray(composition)
  ) {
    throw new Error("Composition must be a JSON object of FLAT paths to values.");
  }

  return validateComposition(
    composition as Record<string, unknown>,
    parsed,
    platform,
  );
}

/**
 * Inspect a single FLAT path's node metadata (for hover documentation).
 *
 * Returns `undefined` if the template cannot be loaded or the path is unknown.
 */
export function inspectFlatPath(
  webTemplatePath: string,
  flatPath: string,
): PathInspection | undefined {
  try {
    const parsed = loadParsedTemplate(webTemplatePath);
    return inspectPath(parsed, flatPath);
  } catch {
    return undefined;
  }
}

/**
 * Enumerate all valid FLAT paths for a Web Template and platform.
 *
 * Returns `undefined` if the template cannot be loaded.
 */
export function enumerateValidPathStrings(
  webTemplatePath: string,
  platform: Platform,
): string[] | undefined {
  try {
    const parsed = loadParsedTemplate(webTemplatePath);
    return enumerateValidPaths(parsed, platform);
  } catch {
    return undefined;
  }
}
