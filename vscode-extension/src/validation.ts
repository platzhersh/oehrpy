/**
 * In-process FLAT composition validation.
 *
 * This is a faithful TypeScript port of the oehrpy Python validator
 * (`oehrpy/validation/path_checker.py` + `web_template.py`). It lets the
 * extension validate FLAT compositions and inspect paths without spawning a
 * Python interpreter — matching how autocomplete and the tree view already
 * work. The Python `python -m oehrpy.validation` CLI remains available for
 * CI/scripting and produces the same JSON shapes.
 */

import { STRUCTURAL_RM_TYPES, VALID_SUFFIXES } from "./webTemplate";

export type Platform = "ehrbase" | "better";

export type ErrorType =
  | "unknown_path"
  | "wrong_suffix"
  | "missing_required"
  | "index_mismatch";

export interface FlatValidationError {
  path: string;
  error_type: ErrorType;
  message: string;
  suggestion: string | null;
  valid_alternatives: string[];
}

export interface FlatValidationResult {
  is_valid: boolean;
  errors: FlatValidationError[];
  warnings: FlatValidationError[];
  info: string[];
  platform: Platform;
  template_id: string;
  valid_path_count: number;
  checked_path_count: number;
}

export interface PathInspection {
  id: string;
  name: string;
  rm_type: string;
  path: string;
  min: number;
  max: number;
  valid_suffixes: string[];
}

interface RawNode {
  id?: string;
  name?: string;
  rmType?: string;
  rm_type?: string;
  min?: number;
  max?: number;
  originalName?: string;
  localizedNames?: Record<string, string>;
  children?: RawNode[];
}

interface ParsedNode {
  id: string;
  name: string;
  rmType: string;
  path: string;
  min: number;
  max: number;
  originalName: string | null;
  childrenIds: string[];
}

export interface ParsedWebTemplate {
  treeId: string;
  templateId: string;
  nodes: Map<string, ParsedNode>;
}

// ── Required composition-level fields (mirrors required_fields.py) ──────────

const REQUIRED_FIELD_GROUPS: string[][] = [
  ["category|code"],
  ["category|value"],
  ["category|terminology"],
  ["language|code"],
  ["language|terminology"],
  ["territory|code"],
  ["territory|terminology"],
  ["composer|name"],
  ["context/start_time"],
  ["context/setting|code"],
  ["context/setting|value"],
  ["context/setting|terminology"],
];

const CTX_ALLOWED_BASES = new Set<string>([
  "ctx/language",
  "ctx/territory",
  "ctx/composer_name",
  "ctx/composer_id",
  "ctx/id_scheme",
  "ctx/id_namespace",
  "ctx/time",
  "ctx/end_time",
  "ctx/history_origin",
  "ctx/health_care_facility",
  "ctx/participation_name",
  "ctx/participation_function",
  "ctx/participation_mode",
  "ctx/participation_id",
  "ctx/setting",
]);

const SIMSDT_SPEC_URL =
  "https://specifications.openehr.org/releases/ITS-REST/latest/simplified_data_template.html";

// ── String helpers ──────────────────────────────────────────────────────────

function stripIndices(path: string): string {
  return path.replace(/:\d+/g, "");
}

function slugify(name: string): string {
  let slug = name.toLowerCase().trim();
  slug = slug.replace(/[\s/]+/g, "_");
  slug = slug.replace(/[^a-z0-9_]/g, "");
  return slug;
}

function rmTypeOf(node: RawNode): string {
  return node.rmType || node.rm_type || "";
}

// ── difflib.get_close_matches port (SequenceMatcher ratio) ───────────────────

/** Longest contiguous matching block between two strings (difflib core). */
function longestMatchSize(a: string, b: string): [number, number, number] {
  let besti = 0;
  let bestj = 0;
  let bestsize = 0;
  let j2len = new Map<number, number>();

  for (let i = 0; i < a.length; i++) {
    const newJ2len = new Map<number, number>();
    for (let j = 0; j < b.length; j++) {
      if (a[i] === b[j]) {
        const k = (j > 0 ? j2len.get(j - 1) ?? 0 : 0) + 1;
        newJ2len.set(j, k);
        if (k > bestsize) {
          besti = i - k + 1;
          bestj = j - k + 1;
          bestsize = k;
        }
      }
    }
    j2len = newJ2len;
  }
  return [besti, bestj, bestsize];
}

function matchingBlocksSize(a: string, b: string): number {
  if (a.length === 0 || b.length === 0) {
    return 0;
  }
  const [i, j, k] = longestMatchSize(a, b);
  if (k === 0) {
    return 0;
  }
  return (
    k +
    matchingBlocksSize(a.slice(0, i), b.slice(0, j)) +
    matchingBlocksSize(a.slice(i + k), b.slice(j + k))
  );
}

/** SequenceMatcher.ratio() — 2*M / T (Ratcliff/Obershelp). */
function ratio(a: string, b: string): number {
  const t = a.length + b.length;
  if (t === 0) {
    return 1;
  }
  return (2 * matchingBlocksSize(a, b)) / t;
}

/** Port of difflib.get_close_matches. */
function getCloseMatches(
  word: string,
  possibilities: string[],
  n = 3,
  cutoff = 0.6,
): string[] {
  const scored: { score: number; index: number; value: string }[] = [];
  possibilities.forEach((value, index) => {
    const score = ratio(word, value);
    if (score >= cutoff) {
      scored.push({ score, index, value });
    }
  });
  // Highest score first; stable on ties (preserve input order).
  scored.sort((x, y) => y.score - x.score || x.index - y.index);
  return scored.slice(0, n).map((s) => s.value);
}

function suggestPath(invalidPath: string, validPaths: string[]): string[] {
  return getCloseMatches(invalidPath, validPaths, 3, 0.4);
}

function suggestSegment(invalidSegment: string, validSegments: string[]): string[] {
  return getCloseMatches(invalidSegment, validSegments, 3, 0.3);
}

// ── Web Template parsing ─────────────────────────────────────────────────────

function detectRename(node: RawNode, nodeId: string): string | null {
  const localizedNames = node.localizedNames ?? {};
  const localizedValues = Object.values(localizedNames);
  if (localizedValues.length > 0) {
    const localized = localizedNames["en"] ?? localizedValues[0];
    if (localized && slugify(localized) !== nodeId) {
      return localized;
    }
  }

  const originalName = node.originalName;
  if (originalName && slugify(originalName) !== nodeId) {
    return originalName;
  }

  return null;
}

export function parseWebTemplate(webTemplate: Record<string, unknown>): ParsedWebTemplate {
  const tree = webTemplate.tree as RawNode | undefined;
  if (!tree || typeof tree !== "object") {
    throw new Error("Web Template JSON must contain a 'tree' key");
  }

  const treeId = tree.id ?? "";
  const templateId =
    (typeof webTemplate.templateId === "string" && webTemplate.templateId) ||
    (typeof webTemplate.template_id === "string" && webTemplate.template_id) ||
    treeId;

  const nodes = new Map<string, ParsedNode>();

  function traverse(node: RawNode, prefix: string): void {
    const nodeId = node.id ?? "";
    const currentPath = prefix ? `${prefix}/${nodeId}` : nodeId;
    const children = node.children ?? [];

    nodes.set(currentPath, {
      id: nodeId,
      name: node.name || nodeId,
      rmType: rmTypeOf(node),
      path: currentPath,
      min: node.min ?? 0,
      max: node.max ?? 1,
      originalName: detectRename(node, nodeId),
      childrenIds: children.map((c) => c.id ?? ""),
    });

    for (const child of children) {
      traverse(child, currentPath);
    }
  }

  traverse(tree, "");
  return { treeId, templateId, nodes };
}

function addIndexToPath(path: string): string {
  const idx = path.lastIndexOf("/");
  if (idx === -1) {
    return `${path}:0`;
  }
  return `${path.slice(0, idx)}/${path.slice(idx + 1)}:0`;
}

export function enumerateValidPaths(
  parsed: ParsedWebTemplate,
  platform: Platform,
): string[] {
  const indexSingleOccurrence = platform === "better";
  const paths: string[] = [];

  for (const node of parsed.nodes.values()) {
    if (STRUCTURAL_RM_TYPES.has(node.rmType)) {
      continue;
    }

    const suffixes = VALID_SUFFIXES[node.rmType];
    if (suffixes === undefined) {
      // Unknown RM type — accept the bare path only.
      paths.push(node.path);
      continue;
    }

    paths.push(node.path);
    for (const suffix of suffixes) {
      paths.push(node.path + suffix);
    }

    if (indexSingleOccurrence) {
      const indexedPath = addIndexToPath(node.path);
      if (indexedPath !== node.path) {
        paths.push(indexedPath);
        for (const suffix of suffixes) {
          paths.push(indexedPath + suffix);
        }
      }
    }
  }

  paths.sort();
  return paths;
}

// ── Individual diagnosis checks (mirror path_checker.py) ─────────────────────

function isValidCtxPath(path: string): boolean {
  return CTX_ALLOWED_BASES.has(path.split("|")[0]);
}

function checkIndexIssue(
  path: string,
  platform: Platform,
  validPathSet: Set<string>,
): FlatValidationError | null {
  if (platform === "ehrbase" && /:\d+/.test(path)) {
    const stripped = stripIndices(path);
    if (validPathSet.has(stripped)) {
      return {
        path,
        error_type: "index_mismatch",
        message:
          "EHRBase 2.x does not use index notation (:0) for single-occurrence " +
          "items. Remove the index.",
        suggestion: stripped,
        valid_alternatives: [],
      };
    }
  }

  if (platform === "better" && !/:\d+/.test(path)) {
    const parts = path.split("|");
    const base = parts[0];
    const suffix = parts.length > 1 ? "|" + parts[1] : "";
    const segments = base.split("/");
    for (let i = segments.length - 1; i > 0; i--) {
      const indexed = segments.slice();
      indexed[i] = indexed[i] + ":0";
      const candidate = indexed.join("/") + suffix;
      if (validPathSet.has(candidate)) {
        return {
          path,
          error_type: "index_mismatch",
          message: "Better platform requires :0 index notation on array paths.",
          suggestion: candidate,
          valid_alternatives: [],
        };
      }
    }
  }

  return null;
}

function checkAnyEventIssue(path: string, platform: Platform): string | null {
  if (platform === "ehrbase" && path.includes("/any_event")) {
    return "EHRBase 2.x does not include /any_event/ in FLAT paths. Use direct paths.";
  }
  return null;
}

function checkSuffixIssue(
  path: string,
  parsed: ParsedWebTemplate,
): FlatValidationError | null {
  if (!path.includes("|")) {
    return null;
  }

  const pipeIdx = path.lastIndexOf("|");
  const basePath = path.slice(0, pipeIdx);
  const suffix = path.slice(pipeIdx + 1);
  const suffixWithPipe = "|" + suffix;

  const node =
    parsed.nodes.get(stripIndices(basePath)) ?? parsed.nodes.get(basePath);
  if (node === undefined) {
    return null;
  }

  const valid = VALID_SUFFIXES[node.rmType];
  if (valid === undefined) {
    return null;
  }

  if (valid.length === 0) {
    return {
      path,
      error_type: "wrong_suffix",
      message: `${node.rmType} does not accept any suffix. Use the bare path.`,
      suggestion: basePath,
      valid_alternatives: [basePath],
    };
  }

  if (!valid.includes(suffixWithPipe)) {
    const alternatives = valid.map((s) => basePath + s);
    return {
      path,
      error_type: "wrong_suffix",
      message: `Invalid suffix '|${suffix}' for ${node.rmType}. Valid suffixes: ${valid.join(", ")}`,
      suggestion: alternatives.length > 0 ? alternatives[0] : null,
      valid_alternatives: alternatives,
    };
  }

  return null;
}

function checkRenamedSegment(
  path: string,
  parsed: ParsedWebTemplate,
): [string | null, string | null] {
  const basePath = path.split("|")[0];
  const segments = stripIndices(basePath).split("/");
  const suffixPart = path.includes("|") ? "|" + path.split("|")[1] : "";

  for (const node of parsed.nodes.values()) {
    if (node.originalName === null) {
      continue;
    }
    const originalSlug = slugify(node.originalName);
    const originalWords = node.originalName
      .split(/[\s/]+/)
      .filter((w) => w.length > 0)
      .map((w) => slugify(w));

    for (let i = 0; i < segments.length; i++) {
      const segment = segments[i];
      if (segment === originalSlug || originalWords.includes(segment)) {
        const message =
          `Node was renamed in this template. ` +
          `Original name "${node.originalName}" is now "${node.id}".`;
        const fixedSegments = segments.slice();
        fixedSegments[i] = node.id;
        return [message, fixedSegments.join("/") + suffixPart];
      }
    }
  }

  return [null, null];
}

// ── Public API ───────────────────────────────────────────────────────────────

export function validateComposition(
  flatComposition: Record<string, unknown>,
  parsed: ParsedWebTemplate,
  platform: Platform,
): FlatValidationResult {
  const validPaths = enumerateValidPaths(parsed, platform);
  const validPathSet = new Set(validPaths);

  const errors: FlatValidationError[] = [];
  const warnings: FlatValidationError[] = [];
  const info: string[] = [];
  let checkedCount = 0;
  let hasCtxKeys = false;

  for (const path of Object.keys(flatComposition)) {
    checkedCount++;

    if (path.startsWith("ctx/")) {
      hasCtxKeys = true;
      if (!isValidCtxPath(path)) {
        warnings.push({
          path,
          error_type: "unknown_path",
          message: "Unknown ctx/ shorthand",
          suggestion: null,
          valid_alternatives: [],
        });
      }
      continue;
    }

    if (validPathSet.has(path)) {
      continue;
    }

    const indexError = checkIndexIssue(path, platform, validPathSet);
    if (indexError !== null) {
      errors.push(indexError);
      continue;
    }

    const anyEventMsg = checkAnyEventIssue(path, platform);
    if (anyEventMsg !== null) {
      const suggestions = suggestPath(path, validPaths);
      errors.push({
        path,
        error_type: "unknown_path",
        message: anyEventMsg,
        suggestion: suggestions.length > 0 ? suggestions[0] : null,
        valid_alternatives: [],
      });
      continue;
    }

    const suffixError = checkSuffixIssue(path, parsed);
    if (suffixError !== null) {
      errors.push(suffixError);
      continue;
    }

    const [renameMsg, renameFix] = checkRenamedSegment(path, parsed);
    const message = renameMsg ?? "Path not found in Web Template.";

    let suggestions: string[] = [];
    if (renameFix) {
      suggestions = [renameFix];
    } else {
      const base = stripIndices(path.split("|")[0]);
      const segments = base.split("/");
      const suffixPart = path.includes("|") ? "|" + path.split("|")[1] : "";

      if (segments.length > 1) {
        const parentPath = segments.slice(0, -1).join("/");
        const parentNode = parsed.nodes.get(parentPath);
        const validChildren = parentNode ? parentNode.childrenIds : [];
        if (validChildren.length > 0) {
          const segSuggestions = suggestSegment(segments[segments.length - 1], validChildren);
          if (segSuggestions.length > 0) {
            suggestions = segSuggestions.map(
              (s) => parentPath + "/" + s + suffixPart,
            );
          }
        }
      }

      if (suggestions.length === 0) {
        suggestions = suggestPath(path, validPaths);
      }
    }

    errors.push({
      path,
      error_type: "unknown_path",
      message,
      suggestion: suggestions.length > 0 ? suggestions[0] : null,
      valid_alternatives: suggestions,
    });
  }

  const flatKeys = new Set(Object.keys(flatComposition));
  for (const group of REQUIRED_FIELD_GROUPS) {
    const found = group.some((f) => flatKeys.has(`${parsed.treeId}/${f}`));
    if (!found) {
      warnings.push({
        path: `${parsed.treeId}/${group[0]}`,
        error_type: "missing_required",
        message: "Required composition field is missing.",
        suggestion: null,
        valid_alternatives: [],
      });
    }
  }

  if (hasCtxKeys) {
    info.push(
      "Composition contains ctx/ shorthand keys defined by the openEHR " +
        `simSDT specification: ${SIMSDT_SPEC_URL}`,
    );
  }

  return {
    is_valid: errors.length === 0,
    errors,
    warnings,
    info,
    platform,
    template_id: parsed.templateId,
    valid_path_count: validPaths.length,
    checked_path_count: checkedCount,
  };
}

export function inspectPath(
  parsed: ParsedWebTemplate,
  flatPath: string,
): PathInspection | undefined {
  const basePath = flatPath.split("|")[0];
  const node = parsed.nodes.get(basePath) ?? parsed.nodes.get(stripIndices(basePath));
  if (node === undefined) {
    return undefined;
  }

  return {
    id: node.id,
    name: node.name,
    rm_type: node.rmType,
    path: node.path,
    min: node.min,
    max: node.max,
    valid_suffixes: [...(VALID_SUFFIXES[node.rmType] ?? [])],
  };
}
