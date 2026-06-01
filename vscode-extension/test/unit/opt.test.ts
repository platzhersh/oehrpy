/**
 * Unit tests for OPT detection and issue position-finding (optModel.ts).
 * This module is free of any `vscode` dependency.
 */

import {
  classifyOptDocument,
  formatOptMessage,
  locateOptIssue,
  type OptIssue,
} from "../../src/optModel";

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

function issue(overrides: Partial<OptIssue>): OptIssue {
  return {
    severity: "error",
    category: "semantic",
    code: "TEST",
    message: "test message",
    xpath: null,
    node_id: null,
    archetype_id: null,
    suggestion: null,
    ...overrides,
  };
}

console.log("\nclassifyOptDocument:");

assert(classifyOptDocument("template.opt", ""), ".opt extension is always OPT");
assert(classifyOptDocument("TEMPLATE.OPT", ""), ".opt detection is case-insensitive");

const optXml =
  '<?xml version="1.0"?>\n<template xmlns="http://schemas.openehr.org/v1">\n  <template_id><value>x</value></template_id>\n</template>';
assert(
  classifyOptDocument("vital_signs.xml", optXml),
  "xml with openEHR <template> root is OPT",
);

assert(
  !classifyOptDocument("pom.xml", '<?xml version="1.0"?>\n<project><name>x</name></project>'),
  "unrelated xml is not OPT",
);
assert(
  !classifyOptDocument("data.xml", "<template>missing namespace</template>"),
  "<template> without openEHR namespace is not OPT",
);
assert(
  !classifyOptDocument(
    "decoy.xml",
    "<!-- see schemas.openehr.org/v1 -->\n<template>no xmlns here</template>",
  ),
  "openEHR namespace outside the <template> xmlns does not false-positive",
);
assert(
  classifyOptDocument(
    "prefixed.xml",
    '<oe:template xmlns:oe="http://schemas.openehr.org/v1"></oe:template>',
  ),
  "prefixed xmlns on the template tag is OPT",
);
assert(!classifyOptDocument("notes.txt", "just text"), "plain text is not OPT");

console.log("\nlocateOptIssue:");

const doc =
  '<definition>\n  <rm_type_name>OBSERVATION</rm_type_name>\n  <node_id>at0001</node_id>\n  <archetype_id><value>openEHR-EHR-OBSERVATION.pulse.v1</value></archetype_id>\n</definition>';

const byNode = locateOptIssue(doc, issue({ node_id: "at0001" }));
assert(byNode !== null, "node_id anchor is located");
assertEqual(doc.slice(byNode!.start, byNode!.end), "at0001", "node_id range covers the id");

const byArchetype = locateOptIssue(
  doc,
  issue({ archetype_id: "openEHR-EHR-OBSERVATION.pulse.v1" }),
);
assert(byArchetype !== null, "archetype_id anchor is located");
assertEqual(
  doc.slice(byArchetype!.start, byArchetype!.end),
  "openEHR-EHR-OBSERVATION.pulse.v1",
  "archetype_id range covers the id",
);

// node_id takes priority over archetype_id when both are present.
const both = locateOptIssue(
  doc,
  issue({ node_id: "at0001", archetype_id: "openEHR-EHR-OBSERVATION.pulse.v1" }),
);
assertEqual(doc.slice(both!.start, both!.end), "at0001", "node_id preferred over archetype_id");

const noAnchor = locateOptIssue(doc, issue({ code: "INVALID_RM_TYPE" }));
assert(noAnchor === null, "issue with no anchor returns null (file-level fallback)");

const missing = locateOptIssue(doc, issue({ node_id: "at9999" }));
assert(missing === null, "anchor not present in text returns null");

console.log("\nformatOptMessage:");

assertEqual(
  formatOptMessage(issue({ message: "bad", suggestion: null })),
  "bad",
  "message without suggestion is unchanged",
);
assert(
  formatOptMessage(issue({ message: "bad", suggestion: "fix it" })).includes("→ fix it"),
  "suggestion is appended with an arrow",
);

// --- Summary ---

console.log(`\n--- Results: ${passed} passed, ${failed} failed ---\n`);

if (failed > 0) {
  process.exit(1);
}
