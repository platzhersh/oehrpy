import * as vscode from "vscode";
import { getConfig } from "./config";

export type FileClassification = "flat_composition" | "web_template" | "unknown";

/**
 * FLAT path pattern: segments separated by `/`, optional `:N` indices,
 * optional `|suffix` at the end.
 */
const FLAT_PATH_PATTERN = /^[a-z][a-z0-9_]*(?::\d+)?(?:\/[a-z][a-z0-9_]*(?::\d+)?)+(?:\|[a-z_]+)?$/;

/**
 * Classify a JSON document as a FLAT composition, Web Template, or unknown.
 */
export function classifyDocument(document: vscode.TextDocument): FileClassification {
  const fileName = document.fileName;

  // Check configured glob patterns first
  const config = getConfig();

  for (const pattern of config.flatCompositionPatterns) {
    if (matchesGlobSimple(fileName, pattern)) {
      return "flat_composition";
    }
  }

  for (const pattern of config.webTemplatePatterns) {
    if (matchesGlobSimple(fileName, pattern)) {
      return "web_template";
    }
  }

  // Parse JSON content for heuristic detection
  const text = document.getText();
  let parsed: unknown;
  try {
    parsed = JSON.parse(text);
  } catch {
    return "unknown";
  }

  if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
    return "unknown";
  }

  const obj = parsed as Record<string, unknown>;

  // Check for Web Template structure: has "tree" with "id" and "children"
  if (isWebTemplate(obj)) {
    return "web_template";
  }

  // Check for FLAT composition: >50% of keys match FLAT path pattern
  if (isFlatComposition(obj)) {
    return "flat_composition";
  }

  return "unknown";
}

/**
 * Check if a parsed JSON object looks like a Web Template.
 */
function isWebTemplate(obj: Record<string, unknown>): boolean {
  const tree = obj["tree"];
  if (typeof tree !== "object" || tree === null || Array.isArray(tree)) {
    return false;
  }
  const treeObj = tree as Record<string, unknown>;
  return "id" in treeObj && "children" in treeObj;
}

/**
 * Check if a parsed JSON object looks like a FLAT composition.
 * Returns true if >50% of root keys match the FLAT path pattern.
 */
function isFlatComposition(obj: Record<string, unknown>): boolean {
  const keys = Object.keys(obj);
  if (keys.length === 0) {
    return false;
  }

  let matchCount = 0;
  for (const key of keys) {
    if (FLAT_PATH_PATTERN.test(key)) {
      matchCount++;
    }
  }

  return matchCount / keys.length > 0.5;
}

/**
 * Simple glob matching for file name patterns.
 * Supports `**` for any directory depth and `*` for any characters within a segment.
 */
function matchesGlobSimple(filePath: string, pattern: string): boolean {
  // Normalize path separators
  const normalized = filePath.replace(/\\/g, "/");

  // Convert glob to regex
  const regexStr = pattern
    .replace(/\./g, "\\.")
    .replace(/\*\*/g, "{{GLOBSTAR}}")
    .replace(/\*/g, "[^/]*")
    .replace(/\{\{GLOBSTAR\}\}/g, ".*");

  const regex = new RegExp(`(^|/)${regexStr}$`);
  return regex.test(normalized);
}
