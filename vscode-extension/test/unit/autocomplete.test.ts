/**
 * Unit tests for the FLAT path autocomplete module.
 *
 * Tests the Web Template path enumeration and JSON key context detection
 * by importing the production functions from src/flatPaths.ts.
 */

import {
  enumeratePathsFromTree,
  findJsonKeyBounds,
  type WebTemplateTreeNode,
} from "../../src/flatPaths";

export {};

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

// === Web Template Path Enumeration Tests ===

console.log("\n--- Web Template Path Enumeration Tests ---");

const simpleTree: WebTemplateTreeNode = {
  id: "vital_signs",
  rmType: "COMPOSITION",
  name: "Vital Signs",
  children: [
    {
      id: "blood_pressure",
      rmType: "OBSERVATION",
      name: "Blood Pressure",
      children: [
        {
          id: "any_event",
          rmType: "EVENT",
          name: "Any event",
          children: [
            {
              id: "systolic",
              rmType: "DV_QUANTITY",
              name: "Systolic",
              min: 0,
              max: 1,
            },
            {
              id: "diastolic",
              rmType: "DV_QUANTITY",
              name: "Diastolic",
              min: 0,
              max: 1,
            },
          ],
        },
      ],
    },
  ],
};

const paths = enumeratePathsFromTree(simpleTree);
const pathStrings = paths.map((p) => p.fullPath);

assert(
  pathStrings.includes(
    "vital_signs/blood_pressure/any_event/systolic",
  ),
  "includes bare systolic path",
);
assert(
  pathStrings.includes(
    "vital_signs/blood_pressure/any_event/systolic|magnitude",
  ),
  "includes systolic|magnitude",
);
assert(
  pathStrings.includes(
    "vital_signs/blood_pressure/any_event/systolic|unit",
  ),
  "includes systolic|unit",
);
assert(
  pathStrings.includes(
    "vital_signs/blood_pressure/any_event/diastolic",
  ),
  "includes bare diastolic path",
);
assert(
  pathStrings.includes(
    "vital_signs/blood_pressure/any_event/diastolic|magnitude",
  ),
  "includes diastolic|magnitude",
);

assert(
  !pathStrings.includes("vital_signs"),
  "excludes COMPOSITION root",
);
assert(
  !pathStrings.includes("vital_signs/blood_pressure"),
  "excludes OBSERVATION node",
);
assert(
  !pathStrings.includes("vital_signs/blood_pressure/any_event"),
  "excludes EVENT node",
);

// Check DV_QUANTITY generates correct number of suffixes (base + 5)
const systolicPaths = paths.filter((p) =>
  p.fullPath.startsWith(
    "vital_signs/blood_pressure/any_event/systolic",
  ),
);
assertEqual(
  systolicPaths.length,
  6,
  "DV_QUANTITY generates 6 entries (base + 5 suffixes)",
);

// --- rmType alias support ---
console.log("\n--- rmType Alias Tests ---");

const treeWithAlias: WebTemplateTreeNode = {
  id: "test",
  rm_type: "COMPOSITION",
  children: [
    {
      id: "value",
      rm_type: "DV_TEXT",
      name: "Value",
    },
  ],
};

const aliasPaths = enumeratePathsFromTree(treeWithAlias);
const aliasPathStrings = aliasPaths.map((p) => p.fullPath);
assert(
  aliasPathStrings.includes("test/value"),
  "supports rm_type alias (snake_case)",
);
assert(
  aliasPathStrings.includes("test/value|value"),
  "generates suffixes with rm_type alias",
);

// --- Empty tree ---
console.log("\n--- Edge Case Tests ---");

const emptyTree: WebTemplateTreeNode = {
  id: "empty",
  rmType: "COMPOSITION",
};
const emptyPaths = enumeratePathsFromTree(emptyTree);
assertEqual(
  emptyPaths.length,
  0,
  "COMPOSITION with no children produces no paths",
);

// --- Unknown RM type ---
const unknownTree: WebTemplateTreeNode = {
  id: "root",
  rmType: "COMPOSITION",
  children: [
    {
      id: "custom",
      rmType: "CUSTOM_TYPE",
      name: "Custom",
    },
  ],
};
const unknownPaths = enumeratePathsFromTree(unknownTree);
assertEqual(
  unknownPaths.length,
  1,
  "unknown RM type gets bare path only",
);
assertEqual(
  unknownPaths[0].fullPath,
  "root/custom",
  "unknown RM type path is correct",
);
assertEqual(
  unknownPaths[0].suffix,
  null,
  "unknown RM type has no suffix",
);

// --- Node metadata ---
console.log("\n--- Node Metadata Tests ---");

const metaTree: WebTemplateTreeNode = {
  id: "root",
  rmType: "COMPOSITION",
  children: [
    {
      id: "temperature",
      rmType: "DV_QUANTITY",
      name: "Body Temperature",
      min: 1,
      max: 1,
    },
  ],
};
const metaPaths = enumeratePathsFromTree(metaTree);
const tempEntry = metaPaths.find((p) => p.suffix === null);
assert(tempEntry !== undefined, "bare path entry exists");
assertEqual(
  tempEntry!.nodeName,
  "Body Temperature",
  "node name preserved",
);
assertEqual(tempEntry!.rmType, "DV_QUANTITY", "RM type preserved");
assertEqual(tempEntry!.min, 1, "min cardinality preserved");
assertEqual(tempEntry!.max, 1, "max cardinality preserved");

// --- Sorted output ---
console.log("\n--- Sort Order Tests ---");

const sortTree: WebTemplateTreeNode = {
  id: "root",
  rmType: "COMPOSITION",
  children: [
    {
      id: "zebra",
      rmType: "DV_BOOLEAN",
      name: "Zebra",
    },
    {
      id: "alpha",
      rmType: "DV_BOOLEAN",
      name: "Alpha",
    },
  ],
};
const sortedPaths = enumeratePathsFromTree(sortTree);
assert(
  sortedPaths[0].fullPath === "root/alpha" &&
    sortedPaths[1].fullPath === "root/zebra",
  "paths are sorted alphabetically",
);

// === JSON Key Context Detection Tests ===

console.log("\n--- JSON Key Context Detection Tests ---");

// Cursor inside a key (before colon)
const keyLine1 = '  "vital_signs/blood_pressure/systolic|magnitude": 120,';
const range1 = findJsonKeyBounds(keyLine1, 20);
assert(range1 !== undefined, "detects cursor inside a JSON key");
assertEqual(range1!.startChar, 3, "key range starts after opening quote");
assertEqual(range1!.endChar, 48, "key range ends at closing quote");

// Cursor inside a value (after colon) — should return undefined
const valueLine = '  "key": "some_value"';
const range2 = findJsonKeyBounds(valueLine, 15);
assert(range2 === undefined, "rejects cursor inside a JSON value");

// Cursor at start of key (just after opening quote)
const freshKey = '  "';
const range3 = findJsonKeyBounds(freshKey, 3);
assert(range3 !== undefined, "detects cursor at fresh key start");
assertEqual(range3!.startChar, 3, "fresh key range starts after quote");
assertEqual(range3!.endChar, 3, "fresh key range ends at cursor (no close quote)");

// Cursor outside any string
const outsideLine = "  { }";
const range4 = findJsonKeyBounds(outsideLine, 3);
assert(range4 === undefined, "rejects cursor outside any string");

// Cursor inside a key with partial text typed
const partialKey = '  "vital_signs/blo';
const range5 = findJsonKeyBounds(partialKey, 18);
assert(range5 !== undefined, "detects cursor in partial key");
assertEqual(range5!.startChar, 3, "partial key range starts after quote");
assertEqual(range5!.endChar, 18, "partial key range ends at cursor");

// Cursor at value position after colon and space
const afterColon = '  "key": "val';
const range6 = findJsonKeyBounds(afterColon, 12);
assert(range6 === undefined, "rejects cursor in value after colon+space+quote");

// Key on line with only opening brace before
const firstKey = '{"first_key": 1}';
const range7 = findJsonKeyBounds(firstKey, 5);
assert(range7 !== undefined, "detects key after opening brace");

// Cursor after colon (not in string)
const afterColonNoStr = '  "key": ';
const range8 = findJsonKeyBounds(afterColonNoStr, 9);
assert(range8 === undefined, "rejects cursor after colon outside string");

// --- Summary ---

console.log(`\n--- Results: ${passed} passed, ${failed} failed ---\n`);

if (failed > 0) {
  process.exit(1);
}
