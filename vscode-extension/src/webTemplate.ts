/**
 * Shared, VS Code-free Web Template parsing utilities.
 *
 * Both the FLAT path autocomplete and the Web Template tree view need to
 * understand the structure of a Web Template `tree`. Keeping the parsing
 * logic here (with no `vscode` import) avoids duplication and lets the unit
 * tests exercise it without the VS Code API.
 */

/** A raw node as it appears in the Web Template JSON `tree`. */
export interface WebTemplateTreeNode {
  id: string;
  name?: string;
  localizedName?: string;
  rmType?: string;
  rm_type?: string;
  min?: number;
  max?: number;
  children?: WebTemplateTreeNode[];
}

/** A single autocomplete entry derived from a leaf (data) node. */
export interface FlatPathEntry {
  fullPath: string;
  nodeName: string;
  rmType: string;
  min: number;
  max: number;
  suffix: string | null;
}

/** A fully resolved tree node with its accumulated FLAT path. */
export interface TemplateTreeNode {
  /** The node's local id (the FLAT path segment). */
  id: string;
  /** Human-readable name (falls back to id). */
  name: string;
  /** openEHR RM type, e.g. `DV_QUANTITY`. */
  rmType: string;
  /** Accumulated FLAT path of ids from the root, without any `|suffix`. */
  flatPath: string;
  min: number;
  /** Maximum cardinality; `-1` means unbounded (`*`). */
  max: number;
  /** True for container/structural RM types that are not addressable leaves. */
  isStructural: boolean;
  /** Valid `|suffix` attributes for this node's RM type. */
  validSuffixes: string[];
  children: TemplateTreeNode[];
}

/**
 * RM types that represent containers/structure rather than addressable
 * leaf data values. These are skipped when enumerating FLAT data paths.
 */
export const STRUCTURAL_RM_TYPES = new Set([
  "COMPOSITION",
  "SECTION",
  "OBSERVATION",
  "EVALUATION",
  "INSTRUCTION",
  "ACTION",
  "ADMIN_ENTRY",
  "CLUSTER",
  "HISTORY",
  "EVENT",
  "POINT_EVENT",
  "INTERVAL_EVENT",
  "ITEM_TREE",
  "ITEM_LIST",
  "ITEM_SINGLE",
  "ITEM_TABLE",
  "ELEMENT",
  "EVENT_CONTEXT",
  "ACTIVITY",
  "ISM_TRANSITION",
  "INSTRUCTION_DETAILS",
]);

/** Valid `|suffix` attributes per RM data type. */
export const VALID_SUFFIXES: Record<string, string[]> = {
  DV_QUANTITY: ["|magnitude", "|unit", "|precision", "|normal_range", "|normal_status"],
  DV_CODED_TEXT: ["|value", "|code", "|terminology", "|preferred_term"],
  DV_TEXT: ["|value"],
  DV_DATE_TIME: [],
  DV_DATE: [],
  DV_TIME: [],
  DV_BOOLEAN: [],
  DV_COUNT: ["|magnitude", "|accuracy", "|accuracy_is_percent"],
  DV_ORDINAL: ["|value", "|code", "|terminology", "|ordinal"],
  DV_SCALE: ["|value", "|code", "|terminology", "|symbol_value"],
  DV_PROPORTION: ["|numerator", "|denominator", "|type", "|precision"],
  DV_DURATION: [],
  DV_IDENTIFIER: ["|id", "|type", "|issuer", "|assigner"],
  DV_URI: [],
  DV_EHR_URI: [],
  DV_MULTIMEDIA: ["|mediatype", "|alternatetext", "|uri", "|size"],
  DV_PARSABLE: ["|value", "|formalism"],
  CODE_PHRASE: ["|code", "|terminology"],
  PARTY_IDENTIFIED: ["|name", "|id"],
  PARTY_RELATED: ["|name", "|id", "|relationship"],
  PARTY_SELF: [],
};

function rmTypeOf(node: WebTemplateTreeNode): string {
  return node.rmType || node.rm_type || "";
}

/**
 * Enumerate all valid FLAT data paths (with and without suffixes) from a
 * Web Template tree. Structural container nodes are skipped, but their ids
 * still contribute to the accumulated path of their descendants.
 */
export function enumeratePathsFromTree(tree: WebTemplateTreeNode): FlatPathEntry[] {
  const entries: FlatPathEntry[] = [];

  function traverse(node: WebTemplateTreeNode, prefix: string): void {
    const nodeId = node.id || "";
    const currentPath = prefix ? `${prefix}/${nodeId}` : nodeId;
    const rmType = rmTypeOf(node);
    const nodeName = node.name || nodeId;
    const min = node.min ?? 0;
    const max = node.max ?? 1;

    if (!STRUCTURAL_RM_TYPES.has(rmType)) {
      entries.push({
        fullPath: currentPath,
        nodeName,
        rmType,
        min,
        max,
        suffix: null,
      });

      const suffixes = VALID_SUFFIXES[rmType];
      if (suffixes) {
        for (const suffix of suffixes) {
          entries.push({
            fullPath: currentPath + suffix,
            nodeName,
            rmType,
            min,
            max,
            suffix,
          });
        }
      }
    }

    if (node.children) {
      for (const child of node.children) {
        traverse(child, currentPath);
      }
    }
  }

  traverse(tree, "");
  entries.sort((a, b) => a.fullPath.localeCompare(b.fullPath));
  return entries;
}

/**
 * Parse a Web Template tree into a navigable {@link TemplateTreeNode}
 * structure, preserving the original hierarchy and computing the
 * accumulated FLAT path for every node.
 */
export function parseTemplateTree(root: WebTemplateTreeNode): TemplateTreeNode {
  function build(node: WebTemplateTreeNode, prefix: string): TemplateTreeNode {
    const id = node.id || "";
    const flatPath = prefix ? `${prefix}/${id}` : id;
    const rmType = rmTypeOf(node);
    const name = node.name || node.localizedName || id;
    const min = node.min ?? 0;
    const max = node.max ?? 1;
    const children = (node.children ?? []).map((child) => build(child, flatPath));

    return {
      id,
      name,
      rmType,
      flatPath,
      min,
      max,
      isStructural: STRUCTURAL_RM_TYPES.has(rmType),
      validSuffixes: VALID_SUFFIXES[rmType] ?? [],
      children,
    };
  }

  return build(root, "");
}

/** Render a node's cardinality as `min..max` (with `*` for unbounded). */
export function formatCardinality(min: number, max: number): string {
  const maxStr = max === -1 ? "*" : String(max);
  return `${min}..${maxStr}`;
}
