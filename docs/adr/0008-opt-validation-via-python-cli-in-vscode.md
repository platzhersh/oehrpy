# ADR-0008: OPT Validation in the VS Code Extension via the Python CLI

**Date:** 2026-06-01

## Status

Accepted

## Context

ADR-0007 established that the VS Code extension validates **FLAT compositions
in-process** (a TypeScript port), with the Python `oehrpy.validation` CLI kept
as a parallel backend for CI/scripting. A deliberate property of that decision
was that the extension needs **no Python interpreter** for its core, on-every-
save workflow.

PRD-0015 Phase 3E extends the extension to validate **OPT 1.4 templates**
(`.opt` files and openEHR `<template>` XML). oehrpy already ships a
comprehensive `OPTValidator` (`src/oehrpy/validation/opt/`) covering four
categories — well-formedness, semantic, structural, and FLAT-path impact —
across 25 issue codes, exposed by the `oehrpy-validate-opt` CLI
(`python -m oehrpy.validate_opt_cli ... --output json`).

The question: how should the extension obtain OPT diagnostics?

Unlike the FLAT validator (a few hundred lines of string/tree logic that ported
cleanly to TypeScript), the OPT validator parses OPT 1.4 XML with `defusedxml`,
walks archetype structure, checks RM types against the RM 1.1.0 model, validates
terminology bindings, and analyses FLAT-path impact. Re-implementing that
faithfully in TypeScript would be a large, high-risk effort that would
inevitably drift from the Python reference.

A further constraint surfaced from the data model: `OPTValidationIssue` carries
no line/column information — only `xpath`, `node_id`, and `archetype_id`. So
inline positioning is best-effort regardless of backend.

## Decision

For OPT validation, the extension **shells out to the Python CLI**
(`python -m oehrpy.validate_opt_cli <file> --output json`) and **degrades
gracefully** when Python or `oehrpy` is unavailable.

Concretely:

1. **Detection.** `.opt` files are always treated as OPT; other files are
   treated as OPT only when their content has a `<template>` root in the
   openEHR namespace. A dedicated `opt` language is contributed for `.opt`.
2. **CLI backend.** On open/save of an OPT document (and via the
   `oehrpy: Validate OPT Template` command), run the CLI and map its JSON
   issues to diagnostics in a separate `oehrpy-opt-validator` collection.
3. **Best-effort positioning.** Each issue is anchored to the first occurrence
   of its `node_id` (preferred) or `archetype_id` in the document text; issues
   with no anchor fall back to a file-level diagnostic on line 1. In practice
   this positions the large majority of issues (≈74/90 on the sample template).
4. **Graceful degradation.** If the interpreter can't be found or `oehrpy`
   isn't importable, OPT validation silently no-ops and shows a **one-time**
   hint offering to `pip install oehrpy` or set `oehrpy.pythonPath`. FLAT
   validation is entirely unaffected and continues to need no Python.
5. **Scope of the Python dependency.** Python is **optional and only for OPT**.
   The common FLAT-on-save path remains in-process per ADR-0007.

New settings: `oehrpy.enableOptValidation` (default `true`),
`oehrpy.pythonPath` (reintroduced, scoped to OPT), and
`oehrpy.optValidationTimeout`.

## Consequences

### Positive

- Reuses the full, battle-tested `OPTValidator` (25 codes, four categories)
  with zero duplication and no risk of TS/Python drift.
- Single source of truth for OPT validation stays in Python, where the RM
  model, archetype, and terminology logic already lives.
- FLAT validation's zero-config, no-Python property (ADR-0007) is preserved;
  the Python requirement is opt-in and confined to template-authoring files.
- Graceful degradation means users without Python see no errors — just an
  unobtrusive, dismissible hint.

### Negative

- **Partially walks back ADR-0007's "no Python" property** for OPT files: users
  who want OPT diagnostics must have Python + `oehrpy` installed. This is an
  accepted, scoped exception, not a reversal of the FLAT decision.
- **Subprocess cost and latency** on save for OPT files (mitigated by debounce
  and a configurable timeout), versus the synchronous in-process FLAT path.
- **Best-effort, identifier-based positioning.** Because issues lack line
  numbers, some diagnostics land on the first matching `node_id` rather than the
  exact element, and anchor-less issues fall back to file level. Improving this
  would require either richer position data from the Python validator or an
  in-TS XML position index — deferred.

### Neutral

- A future enhancement could have the Python `OPTValidationIssue` carry source
  line/column (e.g. via `lxml` `sourceline`), which both the CLI and the
  extension would benefit from; tracked separately.

## Alternatives Considered

### Alternative A: Port the OPTValidator to TypeScript

Re-implement well-formedness, semantic, structural, and FLAT-impact checks in
TS for a fully Python-free extension. Rejected: disproportionate effort and
ongoing drift risk for a complex, RM-model-aware validator — the opposite of
the clean port that justified the FLAT decision in ADR-0007.

### Alternative B: TypeScript well-formedness only

Catch XML syntax errors and a couple of structural checks in TS, skipping the
semantic/terminology/FLAT-impact diagnostics. Rejected: those richer checks are
the `OPTValidator`'s real value; a syntax-only check adds little over VS Code's
built-in XML support.

### Alternative C: Defer OPT validation; ship a TS OPT outline instead

Provide `.opt` detection plus a structural outline/tree without validation.
Rejected for this phase as lower value, though it remains a reasonable
complementary feature later.

## References

- ADR-0007 — Dual-backend FLAT validation (the no-Python property this scopes)
- ADR-0005 — Web Template as the source of truth for FLAT paths
- PRD-0015 — VS Code extension, Phase 3E (Template Format Validation)
- `src/oehrpy/validation/opt/` — the Python `OPTValidator`
- `src/oehrpy/validate_opt_cli.py` — the `oehrpy-validate-opt` CLI
- `vscode-extension/src/optValidator.ts` / `optDiagnostics.ts` / `optModel.ts`
