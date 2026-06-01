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
  STRUCTURAL_RM_TYPES,
  VALID_SUFFIXES,
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

// ---------------------------------------------------------------------------
// formatCardinality — additional edge cases
// ---------------------------------------------------------------------------

console.log("\nformatCardinality — additional cases:");

assertEqual(formatCardinality(0, 0), "0..0", "zero..zero cardinality");
assertEqual(formatCardinality(1, 1), "1..1", "required singleton");
assertEqual(formatCardinality(0, 5), "0..5", "optional bounded (0..5)");
assertEqual(formatCardinality(2, 10), "2..10", "min > 1 bounded");
assertEqual(formatCardinality(0, -1), "0..*", "optional unbounded (0..-1)");
assertEqual(formatCardinality(1, -1), "1..*", "required unbounded (1..-1)");
assertEqual(formatCardinality(3, -1), "3..*", "min=3 unbounded");

// ---------------------------------------------------------------------------
// parseTemplateTree — localizedName fallback
// ---------------------------------------------------------------------------

console.log("\nparseTemplateTree — name resolution priority:");

// localizedName used when name is absent
const localizedOnly = parseTemplateTree({
  id: "local_node",
  localizedName: "Localized Name",
  rmType: "DV_TEXT",
});
assertEqual(localizedOnly.name, "Localized Name", "localizedName used when name is absent");

// name takes priority over localizedName
const bothNames = parseTemplateTree({
  id: "both_node",
  name: "Explicit Name",
  localizedName: "Localized Name",
  rmType: "DV_TEXT",
});
assertEqual(bothNames.name, "Explicit Name", "name preferred over localizedName");

// id used as last resort when both name and localizedName are absent
const noName = parseTemplateTree({ id: "fallback_id", rmType: "DV_TEXT" });
assertEqual(noName.name, "fallback_id", "id is the final name fallback");

// ---------------------------------------------------------------------------
// parseTemplateTree — deep nesting (3+ levels)
// ---------------------------------------------------------------------------

console.log("\nparseTemplateTree — deep nesting:");

const deepTree: WebTemplateTreeNode = {
  id: "composition",
  rmType: "COMPOSITION",
  children: [
    {
      id: "section",
      rmType: "SECTION",
      children: [
        {
          id: "observation",
          rmType: "OBSERVATION",
          children: [
            {
              id: "history",
              rmType: "HISTORY",
              children: [
                {
                  id: "event",
                  rmType: "POINT_EVENT",
                  children: [
                    {
                      id: "temperature",
                      name: "Temperature",
                      rmType: "DV_QUANTITY",
                      min: 1,
                      max: 1,
                    },
                  ],
                },
              ],
            },
          ],
        },
      ],
    },
  ],
};

const deepRoot = parseTemplateTree(deepTree);
const tempNode = findByPath(
  deepRoot,
  "composition/section/observation/history/event/temperature",
);
assert(tempNode !== undefined, "deep leaf found by accumulated flat path");
assertEqual(
  tempNode!.flatPath,
  "composition/section/observation/history/event/temperature",
  "deep leaf flat path includes all ancestor ids",
);
assert(!tempNode!.isStructural, "DV_QUANTITY leaf is not structural at depth 5");
assertEqual(tempNode!.rmType, "DV_QUANTITY", "deep leaf rm type correct");
assertEqual(tempNode!.name, "Temperature", "deep leaf name correct");

// Intermediate structural nodes at each level
const sectionNode = findByPath(deepRoot, "composition/section");
assert(sectionNode !== undefined, "SECTION node found");
assert(sectionNode!.isStructural, "SECTION is structural");

const historyNode = findByPath(deepRoot, "composition/section/observation/history");
assert(historyNode !== undefined, "HISTORY node found");
assert(historyNode!.isStructural, "HISTORY is structural");

const pointEventNode = findByPath(
  deepRoot,
  "composition/section/observation/history/event",
);
assert(pointEventNode !== undefined, "POINT_EVENT node found");
assert(pointEventNode!.isStructural, "POINT_EVENT is structural");

// ---------------------------------------------------------------------------
// parseTemplateTree — children array handling
// ---------------------------------------------------------------------------

console.log("\nparseTemplateTree — children handling:");

// Explicit empty children array → no children
const emptyChildren = parseTemplateTree({
  id: "leaf",
  rmType: "DV_TEXT",
  children: [],
});
assertEqual(emptyChildren.children.length, 0, "empty children array produces no children");

// Missing children property → no children
const noChildren = parseTemplateTree({ id: "leaf2", rmType: "DV_TEXT" });
assertEqual(noChildren.children.length, 0, "absent children property produces no children");

// ---------------------------------------------------------------------------
// parseTemplateTree — validSuffixes for various RM types
// ---------------------------------------------------------------------------

console.log("\nparseTemplateTree — validSuffixes by RM type:");

const dvCodedText = parseTemplateTree({ id: "n", rmType: "DV_CODED_TEXT" });
assert(dvCodedText.validSuffixes.includes("|value"), "DV_CODED_TEXT has |value suffix");
assert(dvCodedText.validSuffixes.includes("|code"), "DV_CODED_TEXT has |code suffix");
assert(dvCodedText.validSuffixes.includes("|terminology"), "DV_CODED_TEXT has |terminology suffix");
assert(dvCodedText.validSuffixes.includes("|preferred_term"), "DV_CODED_TEXT has |preferred_term suffix");

const dvCount = parseTemplateTree({ id: "n", rmType: "DV_COUNT" });
assert(dvCount.validSuffixes.includes("|magnitude"), "DV_COUNT has |magnitude suffix");
assert(dvCount.validSuffixes.includes("|accuracy"), "DV_COUNT has |accuracy suffix");
assert(dvCount.validSuffixes.includes("|accuracy_is_percent"), "DV_COUNT has |accuracy_is_percent suffix");

const dvOrdinal = parseTemplateTree({ id: "n", rmType: "DV_ORDINAL" });
assert(dvOrdinal.validSuffixes.includes("|ordinal"), "DV_ORDINAL has |ordinal suffix");
assert(dvOrdinal.validSuffixes.includes("|value"), "DV_ORDINAL has |value suffix");
assert(dvOrdinal.validSuffixes.includes("|code"), "DV_ORDINAL has |code suffix");

const dvIdentifier = parseTemplateTree({ id: "n", rmType: "DV_IDENTIFIER" });
assert(dvIdentifier.validSuffixes.includes("|id"), "DV_IDENTIFIER has |id suffix");
assert(dvIdentifier.validSuffixes.includes("|type"), "DV_IDENTIFIER has |type suffix");
assert(dvIdentifier.validSuffixes.includes("|issuer"), "DV_IDENTIFIER has |issuer suffix");
assert(dvIdentifier.validSuffixes.includes("|assigner"), "DV_IDENTIFIER has |assigner suffix");

const dvMultimedia = parseTemplateTree({ id: "n", rmType: "DV_MULTIMEDIA" });
assert(dvMultimedia.validSuffixes.includes("|mediatype"), "DV_MULTIMEDIA has |mediatype suffix");
assert(dvMultimedia.validSuffixes.includes("|uri"), "DV_MULTIMEDIA has |uri suffix");

// RM types with empty suffix lists
const dvDateTime = parseTemplateTree({ id: "n", rmType: "DV_DATE_TIME" });
assertEqual(dvDateTime.validSuffixes.length, 0, "DV_DATE_TIME has no suffixes");
assert(!dvDateTime.isStructural, "DV_DATE_TIME is not structural");

const dvBoolean = parseTemplateTree({ id: "n", rmType: "DV_BOOLEAN" });
assertEqual(dvBoolean.validSuffixes.length, 0, "DV_BOOLEAN has no suffixes");

const dvDuration = parseTemplateTree({ id: "n", rmType: "DV_DURATION" });
assertEqual(dvDuration.validSuffixes.length, 0, "DV_DURATION has no suffixes");

const dvUri = parseTemplateTree({ id: "n", rmType: "DV_URI" });
assertEqual(dvUri.validSuffixes.length, 0, "DV_URI has no suffixes");

// Unknown RM type → empty validSuffixes, not structural
const unknownRm = parseTemplateTree({ id: "n", rmType: "UNKNOWN_TYPE" });
assertEqual(unknownRm.validSuffixes.length, 0, "unknown RM type gets empty validSuffixes");
assert(!unknownRm.isStructural, "unknown RM type is not structural");

// No rmType at all → empty validSuffixes, not structural
const noRm = parseTemplateTree({ id: "n" });
assertEqual(noRm.validSuffixes.length, 0, "absent rmType gets empty validSuffixes");
assert(!noRm.isStructural, "absent rmType is not structural");

// ---------------------------------------------------------------------------
// STRUCTURAL_RM_TYPES — verify all expected members
// ---------------------------------------------------------------------------

console.log("\nSTRUCTURAL_RM_TYPES — membership:");

const expectedStructural = [
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
];
for (const rmType of expectedStructural) {
  assert(STRUCTURAL_RM_TYPES.has(rmType), `${rmType} is in STRUCTURAL_RM_TYPES`);
}

// Data types should NOT be structural
const expectedDataTypes = ["DV_QUANTITY", "DV_CODED_TEXT", "DV_TEXT", "DV_BOOLEAN", "DV_COUNT"];
for (const rmType of expectedDataTypes) {
  assert(!STRUCTURAL_RM_TYPES.has(rmType), `${rmType} is NOT in STRUCTURAL_RM_TYPES`);
}

// ---------------------------------------------------------------------------
// VALID_SUFFIXES — spot-check exported map contents
// ---------------------------------------------------------------------------

console.log("\nVALID_SUFFIXES — exported map:");

assert(Array.isArray(VALID_SUFFIXES["DV_QUANTITY"]), "VALID_SUFFIXES has DV_QUANTITY entry");
assertEqual(VALID_SUFFIXES["DV_QUANTITY"].length, 5, "DV_QUANTITY has 5 suffixes");
assert(Array.isArray(VALID_SUFFIXES["DV_PARSABLE"]), "VALID_SUFFIXES has DV_PARSABLE entry");
assert(VALID_SUFFIXES["DV_PARSABLE"].includes("|formalism"), "DV_PARSABLE has |formalism suffix");
assert(Array.isArray(VALID_SUFFIXES["CODE_PHRASE"]), "VALID_SUFFIXES has CODE_PHRASE entry");
assert(VALID_SUFFIXES["CODE_PHRASE"].includes("|code"), "CODE_PHRASE has |code suffix");
assert(VALID_SUFFIXES["CODE_PHRASE"].includes("|terminology"), "CODE_PHRASE has |terminology suffix");
assert(Array.isArray(VALID_SUFFIXES["PARTY_RELATED"]), "VALID_SUFFIXES has PARTY_RELATED entry");
assert(VALID_SUFFIXES["PARTY_RELATED"].includes("|relationship"), "PARTY_RELATED has |relationship suffix");
assert(Array.isArray(VALID_SUFFIXES["DV_SCALE"]), "VALID_SUFFIXES has DV_SCALE entry");
assert(VALID_SUFFIXES["DV_SCALE"].includes("|symbol_value"), "DV_SCALE has |symbol_value suffix");

// ---------------------------------------------------------------------------
// enumeratePathsFromTree — additional edge cases
// ---------------------------------------------------------------------------

console.log("\nenumeratePathsFromTree — additional edge cases:");

// DV_DATE_TIME leaf: only base path, no suffix entries
const dateTimeTree: WebTemplateTreeNode = {
  id: "comp",
  rmType: "COMPOSITION",
  children: [
    { id: "start_time", name: "Start Time", rmType: "DV_DATE_TIME", min: 0, max: 1 },
  ],
};
const dateTimeEntries = enumeratePathsFromTree(dateTimeTree);
assertEqual(dateTimeEntries.length, 1, "DV_DATE_TIME produces only one entry (no suffixes)");
assertEqual(dateTimeEntries[0].fullPath, "comp/start_time", "DV_DATE_TIME base path correct");
assertEqual(dateTimeEntries[0].suffix, null, "DV_DATE_TIME base entry has null suffix");

// DV_BOOLEAN leaf: only base path, no suffix entries
const boolTree: WebTemplateTreeNode = {
  id: "comp",
  rmType: "COMPOSITION",
  children: [
    { id: "active", name: "Active", rmType: "DV_BOOLEAN", min: 0, max: 1 },
  ],
};
const boolEntries = enumeratePathsFromTree(boolTree);
assertEqual(boolEntries.length, 1, "DV_BOOLEAN produces only one entry (no suffixes)");

// nodeName falls back to id when name is absent
const noNameLeafTree: WebTemplateTreeNode = {
  id: "comp",
  rmType: "COMPOSITION",
  children: [
    { id: "measurement", rmType: "DV_TEXT" },
  ],
};
const noNameEntries = enumeratePathsFromTree(noNameLeafTree);
assertEqual(noNameEntries.length, 2, "DV_TEXT with no name produces base + 1 suffix");
const noNameBase = noNameEntries.find((e) => e.suffix === null);
assertEqual(noNameBase!.nodeName, "measurement", "nodeName falls back to id when name absent");

// base entry has suffix=null; suffix entries have the correct suffix string
const suffixTree: WebTemplateTreeNode = {
  id: "root",
  rmType: "COMPOSITION",
  children: [
    { id: "code", name: "Code", rmType: "DV_CODED_TEXT", min: 0, max: 1 },
  ],
};
const suffixEntries = enumeratePathsFromTree(suffixTree);
const suffixBase = suffixEntries.find((e) => e.fullPath === "root/code");
assert(suffixBase !== undefined, "DV_CODED_TEXT base entry present");
assertEqual(suffixBase!.suffix, null, "base entry suffix field is null");
const codeEntry = suffixEntries.find((e) => e.fullPath === "root/code|code");
assert(codeEntry !== undefined, "DV_CODED_TEXT |code entry present");
assertEqual(codeEntry!.suffix, "|code", "suffix entry has correct suffix field value");

// min/max on enumerated entries matches source node
const cardinalityTree: WebTemplateTreeNode = {
  id: "root",
  rmType: "COMPOSITION",
  children: [
    { id: "qty", name: "Qty", rmType: "DV_QUANTITY", min: 2, max: 5 },
  ],
};
const cardEntries = enumeratePathsFromTree(cardinalityTree);
const cardBase = cardEntries.find((e) => e.suffix === null);
assert(cardBase !== undefined, "cardinality base entry present");
assertEqual(cardBase!.min, 2, "entry min matches source node min");
assertEqual(cardBase!.max, 5, "entry max matches source node max");

// Structural node deep in tree still excluded from entries
const deepStructuralTree: WebTemplateTreeNode = {
  id: "root",
  rmType: "COMPOSITION",
  children: [
    {
      id: "cluster",
      rmType: "CLUSTER",
      children: [
        { id: "value", name: "Value", rmType: "DV_TEXT", min: 0, max: 1 },
      ],
    },
  ],
};
const deepStructEntries = enumeratePathsFromTree(deepStructuralTree);
assert(
  !deepStructEntries.some((e) => e.fullPath === "root/cluster"),
  "CLUSTER structural node not emitted as data path",
);
assert(
  deepStructEntries.some((e) => e.fullPath === "root/cluster/value"),
  "child of CLUSTER still emitted with accumulated path",
);

// Output is sorted alphabetically across all paths including suffixes
const multiLeafTree: WebTemplateTreeNode = {
  id: "root",
  rmType: "COMPOSITION",
  children: [
    { id: "z_field", rmType: "DV_BOOLEAN" },
    { id: "a_field", rmType: "DV_BOOLEAN" },
    { id: "m_field", rmType: "DV_BOOLEAN" },
  ],
};
const sortedEntries = enumeratePathsFromTree(multiLeafTree);
const sortedPaths = sortedEntries.map((e) => e.fullPath);
const expectedOrder = ["root/a_field", "root/m_field", "root/z_field"];
assert(
  sortedPaths[0] === expectedOrder[0] &&
    sortedPaths[1] === expectedOrder[1] &&
    sortedPaths[2] === expectedOrder[2],
  "enumerated paths are sorted alphabetically",
);

// Flat tree with a single leaf node (no nesting)
const singleLeaf: WebTemplateTreeNode = {
  id: "weight",
  name: "Weight",
  rmType: "DV_QUANTITY",
  min: 0,
  max: 1,
};
const singleLeafEntries = enumeratePathsFromTree(singleLeaf);
const singleBase = singleLeafEntries.find((e) => e.suffix === null);
assert(singleBase !== undefined, "single leaf tree produces base entry");
assertEqual(singleBase!.fullPath, "weight", "single leaf base path has no prefix slash");
assert(
  singleLeafEntries.some((e) => e.fullPath === "weight|magnitude"),
  "single leaf tree produces suffix entry",
);

// rm_type (snake_case) on leaf node correctly treated as non-structural
const snakeCaseLeafTree: WebTemplateTreeNode = {
  id: "root",
  rmType: "COMPOSITION",
  children: [
    { id: "obs_date", rm_type: "DV_DATE_TIME", min: 1, max: 1 },
  ],
};
const snakeCaseEntries = enumeratePathsFromTree(snakeCaseLeafTree);
assertEqual(snakeCaseEntries.length, 1, "snake_case rm_type leaf treated correctly");
assertEqual(snakeCaseEntries[0].fullPath, "root/obs_date", "snake_case rm_type path correct");
assertEqual(snakeCaseEntries[0].rmType, "DV_DATE_TIME", "snake_case rm_type value preserved in entry");

// OBSERVATION structural node (not COMPOSITION) also excluded at root
const obsTree: WebTemplateTreeNode = {
  id: "obs",
  rmType: "OBSERVATION",
};
const obsEntries = enumeratePathsFromTree(obsTree);
assertEqual(obsEntries.length, 0, "bare OBSERVATION root produces no data paths");

// --- Summary ---

console.log(`\n--- Results: ${passed} passed, ${failed} failed ---\n`);

if (failed > 0) {
  process.exit(1);
}
