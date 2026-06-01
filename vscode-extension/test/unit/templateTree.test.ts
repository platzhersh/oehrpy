/**
 * Unit tests for the Web Template tree parsing (webTemplate.ts).
 *
 * These exercise the real `parseTemplateTree` / `enumeratePathsFromTree`
 * implementation, which is intentionally free of any `vscode` dependency.
 */

import {
  enumeratePathsFromTree,
  formatCardinality,
  parseTemplateTree,
  type TemplateTreeNode,
  type WebTemplateTreeNode,
} from "../../src/webTemplate";

let passed = 0;
let failed = 0;

function assert(condition: boolean, message: string): void {
  if (condition) {
    passed++;
    console.log(`  PASS: ${message}`);
  } else {
    failed++;
    console.error(`  FAIL: ${message}`);
  }
}

function assertEqual<T>(actual: T, expected: T, message: string): void {
  if (actual === expected) {
    passed++;
    console.log(`  PASS: ${message}`);
  } else {
    failed++;
    console.error(
      `  FAIL: ${message} (expected ${String(expected)}, got ${String(actual)})`,
    );
  }
}

/** Find a node by its flat path in a parsed tree. */
function findByPath(
  node: TemplateTreeNode,
  flatPath: string,
): TemplateTreeNode | undefined {
  if (node.flatPath === flatPath) {
    return node;
  }
  for (const child of node.children) {
    const found = findByPath(child, flatPath);
    if (found) {
      return found;
    }
  }
  return undefined;
}

// A small but representative Web Template tree.
const sampleTree: WebTemplateTreeNode = {
  id: "vital_signs",
  name: "Vital signs",
  rmType: "COMPOSITION",
  min: 1,
  max: 1,
  children: [
    {
      id: "blood_pressure",
      name: "Blood pressure",
      rmType: "OBSERVATION",
      min: 0,
      max: -1,
      children: [
        {
          id: "systolic",
          name: "Systolic",
          rmType: "DV_QUANTITY",
          min: 1,
          max: 1,
        },
        {
          id: "diastolic",
          name: "Diastolic",
          // Use snake_case key to confirm rm_type fallback works.
          rm_type: "DV_QUANTITY",
          min: 0,
          max: 1,
        },
      ],
    },
  ],
};

console.log("\nparseTemplateTree:");

const root = parseTemplateTree(sampleTree);

assertEqual(root.id, "vital_signs", "root id parsed");
assertEqual(root.name, "Vital signs", "root name parsed");
assertEqual(root.flatPath, "vital_signs", "root flat path is the id");
assert(root.isStructural, "COMPOSITION is structural");
assertEqual(root.children.length, 1, "root has one child");

const bp = root.children[0];
assertEqual(bp.flatPath, "vital_signs/blood_pressure", "child flat path accumulates");
assert(bp.isStructural, "OBSERVATION is structural");
assertEqual(formatCardinality(bp.min, bp.max), "0..*", "unbounded max renders as *");

const systolic = findByPath(root, "vital_signs/blood_pressure/systolic");
assert(systolic !== undefined, "leaf node found by flat path");
assert(!systolic!.isStructural, "DV_QUANTITY is a leaf (not structural)");
assertEqual(systolic!.rmType, "DV_QUANTITY", "leaf rm type parsed");
assert(
  systolic!.validSuffixes.includes("|magnitude"),
  "DV_QUANTITY exposes |magnitude suffix",
);
assertEqual(formatCardinality(systolic!.min, systolic!.max), "1..1", "required leaf cardinality");

const diastolic = findByPath(root, "vital_signs/blood_pressure/diastolic");
assert(diastolic !== undefined, "rm_type fallback node found");
assertEqual(diastolic!.rmType, "DV_QUANTITY", "rm_type fallback resolves rm type");

// A node missing an explicit name should fall back to its id.
const unnamed = parseTemplateTree({ id: "lonely", rmType: "DV_TEXT" });
assertEqual(unnamed.name, "lonely", "name falls back to id");
assertEqual(formatCardinality(unnamed.min, unnamed.max), "0..1", "default cardinality 0..1");

console.log("\nenumeratePathsFromTree (consistency with tree):");

const entries = enumeratePathsFromTree(sampleTree);
const baseEntry = entries.find(
  (e) => e.fullPath === "vital_signs/blood_pressure/systolic",
);
assert(baseEntry !== undefined, "enumerated paths include systolic base path");
assert(
  entries.some(
    (e) => e.fullPath === "vital_signs/blood_pressure/systolic|magnitude",
  ),
  "enumerated paths include systolic|magnitude",
);
assert(
  !entries.some((e) => e.fullPath === "vital_signs"),
  "structural COMPOSITION node is not emitted as a data path",
);

// --- Summary ---

console.log(`\n--- Results: ${passed} passed, ${failed} failed ---\n`);

if (failed > 0) {
  process.exit(1);
}
