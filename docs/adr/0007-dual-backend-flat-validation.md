# ADR-0007: Dual-Backend FLAT Validation (Python CLI + In-Process TypeScript)

**Date:** 2026-06-01

## Status

Accepted

## Context

oehrpy validates FLAT-format compositions against a Web Template. The core
logic lives in the Python package (`src/oehrpy/validation/`): `FlatValidator`,
the Web Template parser (`web_template.py`), and the path checker
(`path_checker.py`), which together enumerate valid paths and diagnose invalid
ones (unknown paths, wrong suffixes, index/platform mismatches, renamed nodes,
missing required fields) with fuzzy "did you mean?" suggestions.

A second consumer of this logic emerged: the **VS Code extension**
(`vscode-extension/`), which surfaces validation as inline diagnostics, hover
documentation, and a "show valid paths" command.

### The Broken Bridge

The extension was originally wired to shell out to the Python validator as a
subprocess:

```ts
execFile(pythonPath, ["-m", "openehr_sdk.validation", "validate-flat", ...])
```

This was broken on two counts:

1. **The module never existed.** `openehr_sdk` was renamed to `oehrpy` in
   ADR-0006 (#40), so `openehr_sdk.validation` is unresolvable. Even under the
   new name, `oehrpy.validation` had **no CLI entry point** (`__main__.py`) and
   `pyproject.toml` only exposed `oehrpy-validate-opt`. There was no
   `validate-flat`, `web-template inspect`, or `show-paths` command anywhere.
2. **Consequences for users.** Every diagnostic/hover call failed silently, and
   the install check (`python -m openehr_sdk.validation --version`) always
   reported "not installed", so users were perpetually prompted to
   `pip install oehrpy` even when it was present (issue #56).

Meanwhile, two newer extension features — FLAT path autocomplete (#52) and the
Web Template tree view (#55) — had quietly set a precedent: they parse the Web
Template **directly in TypeScript** and never touch Python.

This left a design question: how should the extension obtain validation
results? Two obvious options pulled in opposite directions:

- **Python CLI only** keeps a single source of truth for validation logic but
  forces every extension user to have a correctly-configured Python interpreter
  with `oehrpy` installed — a heavy, fragile dependency for an editor plugin,
  and the original source of the breakage.
- **TypeScript only** gives the best editor UX (zero-config, no Python, no
  subprocess latency) but abandons a reusable CLI that CI pipelines and scripts
  can call, and risks the two diverging.

## Decision

Provide **both**, with a shared, stable JSON contract.

### 1. Python CLI — `python -m oehrpy.validation`

Add `src/oehrpy/validation/__main__.py` exposing the validator as a
machine-readable CLI for CI and scripting:

- `validate-flat --web-template <p> --composition <p> [--platform] [--output json|text]`
- `web-template inspect --web-template <p> --path <flat-path>`
- `show-paths --web-template <p> [--platform] [--output json|text]`
- `--version`

It is a thin wrapper over the existing `FlatValidator` / `enumerate_valid_paths`
/ Web Template parser — **no new validation logic**. Exit codes: `0` valid,
`1` invalid or unknown path, `2` usage error.

### 2. In-Process TypeScript Validator

The extension validates **entirely in the extension host**, with no Python
dependency. `vscode-extension/src/validation.ts` is a faithful port of
`path_checker.py` + `web_template.py`, including a port of
`difflib.get_close_matches` (SequenceMatcher / Ratcliff–Obershelp ratio) so
suggestions match. `validator.ts` is reduced to file-loading wrappers with
mtime-cached parsed templates; all `child_process` / Python-discovery code is
removed.

### 3. Shared JSON Contract

Both backends emit the **same** JSON shape so they stay interchangeable and
verifiable against each other:

```jsonc
// validate-flat
{
  "is_valid": bool,
  "errors":   [{ "path", "error_type", "message", "suggestion", "valid_alternatives" }],
  "warnings": [ ... ],
  "info":     [string],
  "platform": "ehrbase" | "better",
  "template_id": string,
  "valid_path_count": int,
  "checked_path_count": int
}
```

`error_type` is one of `unknown_path | wrong_suffix | missing_required |
index_mismatch`.

### 4. Parity as an Invariant

The TS port and the Python CLI must produce equivalent results. This is checked
during development against the repository's real `web_template.json` (identical
validity, error/warning counts, `valid_path_count`, and suggestions) and guarded
by parallel unit tests on both sides (`tests/test_validation_cli.py` and
`vscode-extension/test/unit/validation.test.ts`).

## Consequences

### Positive

- **Zero-config editor UX.** The extension needs no Python interpreter, no
  `pip install`, and no subprocess spawning — diagnostics and hover are
  synchronous and instant. This fixes #56 and aligns with the existing
  autocomplete/tree-view architecture.
- **CLI for automation.** CI pipelines and scripts get a stable, JSON-emitting
  `python -m oehrpy.validation` command, reusing the canonical Python logic.
- **Cross-checkable.** The shared contract makes it cheap to assert the two
  backends agree, turning "do they match?" into an automatable test.
- Removed the misleading `oehrpy.pythonPath` / `oehrpy.validationTimeout`
  settings and the spurious install prompt.

### Negative

- **Two implementations of the same logic.** The validation rules now live in
  both Python and TypeScript. Any change to path-checking semantics must be made
  (and tested) in both places, or they drift. This is the central cost of the
  decision; the shared JSON contract and paired tests are the mitigation.
- The `difflib.get_close_matches` port is an approximation of CPython's exact
  algorithm. It matches in practice for FLAT paths, but pathological inputs
  could rank suggestions differently between backends.

### Neutral

- The Python package remains the **canonical reference** for validation
  behaviour; the TS port follows it. When in doubt, the Python implementation
  wins and the port is corrected to match.
- The extension and the SDK are versioned independently (extension bumped to
  `0.3.0` for the in-process switch; SDK versioned via semantic-release).

## Alternatives Considered

### Alternative A: Python CLI only (subprocess from the extension)

Fix the module name, add the CLI, and keep the extension shelling out. Rejected
as the *primary* mechanism: it reintroduces the exact dependency that broke —
every editor user must have a discoverable interpreter with `oehrpy` installed,
plus per-keystroke subprocess latency and temp-file juggling for unsaved
buffers. It remains valuable for CI/scripting, hence it is kept as the *second*
backend, not the extension's path.

### Alternative B: TypeScript only

Port to TS and drop the Python CLI entirely. Rejected because CI and scripting
users legitimately want a command-line validator backed by the canonical Python
logic; removing it would push them to reimplement validation or drive the
extension headlessly.

### Alternative C: Compile Python to WASM / embed a Python runtime

Run the real Python validator inside the extension via Pyodide or similar. This
would give a single source of truth with no Python install. Rejected as
disproportionate: a multi-megabyte runtime and significant startup cost for what
is a few hundred lines of pure string/tree logic that ports cleanly to TS.

### Alternative D: Extract a language-neutral spec and generate both

Define the rules once (e.g. as data) and generate/interpret in both languages.
Rejected as over-engineering for the current surface area; revisit if the rule
set grows substantially or a third consumer appears.

## References

- Issue #56 — "CLI-backed validation/hover call non-existent
  `openehr_sdk.validation` module"
- ADR-0005 — Web Template as the primary source of truth for FLAT paths
- ADR-0006 — Align Python import name with the PyPI package name (the
  `openehr_sdk` → `oehrpy` rename)
- `src/oehrpy/validation/__main__.py` — the Python CLI
- `vscode-extension/src/validation.ts` — the in-process TypeScript port
- Python `difflib.get_close_matches` — the suggestion algorithm ported to TS
