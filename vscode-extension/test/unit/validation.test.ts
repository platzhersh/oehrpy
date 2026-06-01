/**
 * Unit tests for the in-process FLAT validator (validation.ts).
 *
 * Mirrors the behaviour of the Python `oehrpy.validation` validator so the
 * extension and the `python -m oehrpy.validation` CLI stay consistent. This
 * module is free of any `vscode` dependency.
 */

import {
  enumerateValidPaths,
  inspectPath,
  parseWebTemplate,
  validateComposition,
  type ParsedWebTemplate,
} from "../../src/validation";

let passed = 0;
let failed = 0;

function assert(condition: boolean, message: string): asserts condition {
  if (condition) {
    passed++;
    console.log(`  PASS: ${message}`);
  } else {
    failed++;
    throw new Error(`FAIL: ${message}`);
  }
}

function assertEqual<T>(actual: T, expected: T, message: string): void {
  assert(
    actual === expected,
    `${message} (expected ${String(expected)}, got ${String(actual)})`,
  );
}

function makeWebTemplate(): Record<string, unknown> {
  return {
    templateId: "IDCR - Adverse Reaction List.v1",
    tree: {
      id: "adverse_reaction_list",
      name: "Adverse Reaction List",
      rmType: "COMPOSITION",
      min: 1,
      max: 1,
      children: [
        { id: "category", name: "category", rmType: "DV_CODED_TEXT", children: [] },
        { id: "language", name: "language", rmType: "CODE_PHRASE", children: [] },
        { id: "territory", name: "territory", rmType: "CODE_PHRASE", children: [] },
        { id: "composer", name: "composer", rmType: "PARTY_IDENTIFIED", children: [] },
        {
          id: "context",
          name: "context",
          rmType: "EVENT_CONTEXT",
          children: [
            { id: "start_time", name: "start_time", rmType: "DV_DATE_TIME", children: [] },
            { id: "setting", name: "setting", rmType: "DV_CODED_TEXT", children: [] },
          ],
        },
        {
          id: "adverse_reaction",
          name: "Adverse Reaction Risk",
          rmType: "EVALUATION",
          min: 0,
          max: -1,
          children: [
            {
              id: "causative_agent",
              name: "Causative agent",
              rmType: "DV_CODED_TEXT",
              // localizedName differs from id "causative_agent"? No — same slug.
              children: [],
            },
            { id: "temperature", name: "Temperature", rmType: "DV_QUANTITY", children: [] },
          ],
        },
      ],
    },
  };
}

function makeValidFlat(): Record<string, unknown> {
  return {
    "adverse_reaction_list/category|code": "433",
    "adverse_reaction_list/language|code": "en",
    "adverse_reaction_list/territory|code": "CH",
    "adverse_reaction_list/composer|name": "Dr. Chregi",
    "adverse_reaction_list/context/start_time": "2026-03-12T10:00:00Z",
    "adverse_reaction_list/context/setting|code": "238",
    "adverse_reaction_list/adverse_reaction/causative_agent|value": "Penicillin",
  };
}

const parsed: ParsedWebTemplate = parseWebTemplate(makeWebTemplate());

console.log("\nparseWebTemplate:");
assertEqual(parsed.treeId, "adverse_reaction_list", "tree id parsed");
assertEqual(parsed.templateId, "IDCR - Adverse Reaction List.v1", "template id parsed");
assert(
  parsed.nodes.has("adverse_reaction_list/adverse_reaction/temperature"),
  "node map keyed by accumulated flat path",
);

console.log("\nenumerateValidPaths:");
const ehrbasePaths = enumerateValidPaths(parsed, "ehrbase");
assert(
  ehrbasePaths.includes("adverse_reaction_list/adverse_reaction/temperature|magnitude"),
  "ehrbase paths include DV_QUANTITY |magnitude",
);
assert(
  ehrbasePaths.includes("adverse_reaction_list/adverse_reaction/temperature"),
  "ehrbase paths include bare leaf path",
);
assert(
  !ehrbasePaths.includes("adverse_reaction_list"),
  "structural COMPOSITION not enumerated",
);
assert(
  !ehrbasePaths.some((p) => p.includes(":0")),
  "ehrbase paths have no :0 index notation",
);

const betterPaths = enumerateValidPaths(parsed, "better");
assert(
  betterPaths.some((p) => p.includes(":0")),
  "better paths include :0 indexed variants",
);

console.log("\nvalidateComposition — valid composition:");
const validResult = validateComposition(makeValidFlat(), parsed, "ehrbase");
assert(validResult.is_valid, "valid composition reports is_valid");
assertEqual(validResult.errors.length, 0, "valid composition has no errors");
assertEqual(validResult.template_id, "IDCR - Adverse Reaction List.v1", "result carries template id");
assert(validResult.valid_path_count > 0, "result reports valid_path_count");

console.log("\nvalidateComposition — unknown path + suggestion:");
const typoResult = validateComposition(
  { "adverse_reaction_list/adverse_reaction/causative_agnt|value": "Penicillin" },
  parsed,
  "ehrbase",
);
assert(!typoResult.is_valid, "typo composition is invalid");
const typoErr = typoResult.errors.find((e) => e.path.includes("causative_agnt"));
assert(typoErr !== undefined, "typo produces an error");
assertEqual(typoErr!.error_type, "unknown_path", "typo error type is unknown_path");
assert(
  typoErr!.suggestion !== null && typoErr!.suggestion.includes("causative_agent"),
  "typo suggests causative_agent (fuzzy match)",
);

console.log("\nvalidateComposition — wrong suffix:");
const suffixResult = validateComposition(
  { "adverse_reaction_list/adverse_reaction/temperature|bogus": 37.5 },
  parsed,
  "ehrbase",
);
const suffixErr = suffixResult.errors.find((e) => e.error_type === "wrong_suffix");
assert(suffixErr !== undefined, "bogus suffix produces wrong_suffix error");
assert(
  suffixErr!.valid_alternatives.some((a) => a.endsWith("|magnitude")),
  "wrong_suffix offers |magnitude alternative",
);

console.log("\nvalidateComposition — index mismatch (ehrbase):");
const indexResult = validateComposition(
  { "adverse_reaction_list/adverse_reaction:0/temperature|magnitude": 37.5 },
  parsed,
  "ehrbase",
);
const indexErr = indexResult.errors.find((e) => e.error_type === "index_mismatch");
assert(indexErr !== undefined, "ehrbase flags :0 index as index_mismatch");
assert(
  indexErr!.suggestion === "adverse_reaction_list/adverse_reaction/temperature|magnitude",
  "index_mismatch suggests the de-indexed path",
);

console.log("\nvalidateComposition — required field warnings:");
const emptyResult = validateComposition({}, parsed, "ehrbase");
assert(
  emptyResult.warnings.some((w) => w.error_type === "missing_required"),
  "missing required fields produce warnings",
);
assert(emptyResult.is_valid, "missing required fields are warnings, not errors");

console.log("\nvalidateComposition — ctx handling:");
const ctxResult = validateComposition(
  {
    "ctx/language": "en",
    "ctx/bogus_key": "x",
    "adverse_reaction_list/category|code": "433",
  },
  parsed,
  "ehrbase",
);
assert(
  ctxResult.warnings.some((w) => w.path === "ctx/bogus_key"),
  "unknown ctx/ key warns",
);
assert(
  !ctxResult.warnings.some((w) => w.path === "ctx/language"),
  "known ctx/ key does not warn",
);
assert(ctxResult.info.length > 0, "ctx keys add an informational note");

console.log("\nvalidateComposition — rename detection:");
const renamedWt = makeWebTemplate();
// Make causative_agent look renamed from an original archetype name.
const tree = renamedWt.tree as { children: { id: string; children: unknown[] }[] };
const evaluation = tree.children.find((c) => c.id === "adverse_reaction") as {
  children: Record<string, unknown>[];
};
const agentNode = evaluation.children.find((c) => c.id === "causative_agent");
if (agentNode) {
  agentNode.localizedNames = { en: "Substance" };
}
const renamedParsed = parseWebTemplate(renamedWt);
const renameResult = validateComposition(
  { "adverse_reaction_list/adverse_reaction/substance|value": "Penicillin" },
  renamedParsed,
  "ehrbase",
);
const renameErr = renameResult.errors.find((e) => e.path.includes("substance"));
assert(renameErr !== undefined, "renamed segment produces an error");
assert(
  renameErr!.message.includes("renamed"),
  "rename error message mentions the rename",
);
assert(
  renameErr!.suggestion === "adverse_reaction_list/adverse_reaction/causative_agent|value",
  "rename error suggests the current node id",
);

console.log("\ninspectPath:");
const inspectKnown = inspectPath(parsed, "adverse_reaction_list/adverse_reaction/temperature");
assert(inspectKnown !== undefined, "known path inspected");
assertEqual(inspectKnown!.rm_type, "DV_QUANTITY", "inspect returns rm type");
assert(inspectKnown!.valid_suffixes.includes("|magnitude"), "inspect returns valid suffixes");

const inspectWithSuffix = inspectPath(
  parsed,
  "adverse_reaction_list/adverse_reaction/temperature|magnitude",
);
assert(inspectWithSuffix !== undefined, "inspect strips |suffix before lookup");

const inspectUnknown = inspectPath(parsed, "adverse_reaction_list/nope");
assert(inspectUnknown === undefined, "unknown path returns undefined");

// --- Summary ---

console.log(`\n--- Results: ${passed} passed, ${failed} failed ---\n`);

if (failed > 0) {
  process.exit(1);
}
