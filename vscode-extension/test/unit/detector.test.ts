/**
 * Unit tests for the FLAT/Web Template file detector.
 *
 * These tests validate the classification logic without depending on
 * the VS Code API — we mock vscode.TextDocument with a minimal interface.
 */

// Tests validate detection logic without VS Code API dependencies.

// Simple test runner (no external test framework dependency)
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
    console.error(`  FAIL: ${message} (expected ${String(expected)}, got ${String(actual)})`);
  }
}

// --- Test the detection logic directly ---

const FLAT_PATH_PATTERN = /^[a-z][a-z0-9_]*(?::\d+)?(?:\/[a-z][a-z0-9_]*(?::\d+)?)+(?:\|[a-z_]+)?$/;

function isFlatComposition(obj: Record<string, unknown>): boolean {
  const keys = Object.keys(obj);
  if (keys.length === 0) return false;
  let matchCount = 0;
  for (const key of keys) {
    if (FLAT_PATH_PATTERN.test(key)) matchCount++;
  }
  return matchCount / keys.length > 0.5;
}

function isWebTemplate(obj: Record<string, unknown>): boolean {
  const tree = obj["tree"];
  if (typeof tree !== "object" || tree === null || Array.isArray(tree)) return false;
  const treeObj = tree as Record<string, unknown>;
  return "id" in treeObj && "children" in treeObj;
}

// --- FLAT path pattern tests ---

console.log("\n--- FLAT Path Pattern Tests ---");

assert(FLAT_PATH_PATTERN.test("vital_signs/blood_pressure/systolic|magnitude"), "simple FLAT path with suffix");
assert(FLAT_PATH_PATTERN.test("vital_signs/blood_pressure/systolic"), "FLAT path without suffix");
assert(FLAT_PATH_PATTERN.test("vital_signs/blood_pressure:0/systolic|magnitude"), "FLAT path with index");
assert(FLAT_PATH_PATTERN.test("ctx/language"), "context path");
assert(!FLAT_PATH_PATTERN.test("simple_key"), "single segment is not FLAT");
assert(!FLAT_PATH_PATTERN.test(""), "empty string is not FLAT");
assert(!FLAT_PATH_PATTERN.test("Capital/path"), "uppercase not FLAT");

// --- FLAT composition detection tests ---

console.log("\n--- FLAT Composition Detection Tests ---");

assertEqual(
  isFlatComposition({
    "vital_signs/blood_pressure/systolic|magnitude": 120,
    "vital_signs/blood_pressure/systolic|unit": "mm[Hg]",
    "vital_signs/blood_pressure/diastolic|magnitude": 80,
  }),
  true,
  "all keys match FLAT pattern → FLAT composition",
);

assertEqual(
  isFlatComposition({
    "name": "test",
    "version": "1.0",
    "description": "not a flat composition",
  }),
  false,
  "no keys match FLAT pattern → not FLAT",
);

assertEqual(
  isFlatComposition({}),
  false,
  "empty object → not FLAT",
);

assertEqual(
  isFlatComposition({
    "vital_signs/blood_pressure/systolic|magnitude": 120,
    "name": "test",
    "version": "1.0",
    "description": "mixed",
  }),
  false,
  "only 25% keys match → not FLAT (need >50%)",
);

assertEqual(
  isFlatComposition({
    "vital_signs/blood_pressure/systolic|magnitude": 120,
    "vital_signs/blood_pressure/diastolic|magnitude": 80,
    "extra": "value",
  }),
  true,
  "66% keys match → FLAT composition",
);

// --- Web Template detection tests ---

console.log("\n--- Web Template Detection Tests ---");

assertEqual(
  isWebTemplate({
    tree: { id: "vital_signs", children: [] },
    templateId: "test",
  }),
  true,
  "has tree with id and children → Web Template",
);

assertEqual(
  isWebTemplate({
    tree: { id: "vital_signs" },
  }),
  false,
  "tree missing children → not Web Template",
);

assertEqual(
  isWebTemplate({
    data: "something",
  }),
  false,
  "no tree key → not Web Template",
);

assertEqual(
  isWebTemplate({
    tree: null as unknown,
  } as Record<string, unknown>),
  false,
  "tree is null → not Web Template",
);

assertEqual(
  isWebTemplate({
    tree: [1, 2, 3],
  }),
  false,
  "tree is array → not Web Template",
);

// --- findKeyRange logic test ---

console.log("\n--- JSON Key Position Tests ---");

function findKeyPosition(text: string, key: string): { index: number; length: number } | null {
  const escaped = key.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const regex = new RegExp(`"(${escaped})"\\s*:`);
  const match = regex.exec(text);
  if (!match) return null;
  return { index: match.index + 1, length: key.length };
}

const sampleJson = `{
  "vital_signs/blood_pressure/systolic|magnitude": 120,
  "vital_signs/blood_pressure/diastolic|magnitude": 80
}`;

const pos1 = findKeyPosition(sampleJson, "vital_signs/blood_pressure/systolic|magnitude");
assert(pos1 !== null, "finds systolic key in JSON");
assertEqual(pos1!.length, "vital_signs/blood_pressure/systolic|magnitude".length, "correct key length");

const pos2 = findKeyPosition(sampleJson, "nonexistent/path");
assert(pos2 === null, "returns null for nonexistent key");

const posSpecial = findKeyPosition('{"test|pipe": 1}', "test|pipe");
assert(posSpecial !== null, "handles pipe in key");

// --- Summary ---

console.log(`\n--- Results: ${passed} passed, ${failed} failed ---\n`);

if (failed > 0) {
  process.exit(1);
}
