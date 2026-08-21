# ADR-0009: Adopt the Language Server Protocol as the Target Architecture

**Date:** 2026-08-21

## Status

Proposed

## Context

oehrpy's editor tooling today is a **VS Code-only extension**
(`vscode-extension/`) built directly against the VS Code Extension API, per
PRD-0015 §1.2/§2 ("Non-Goals: Language Server Protocol (LSP) implementation —
use VS Code extension API directly"). Two ADRs since then have each chipped
at that boundary:

- **ADR-0007** ported FLAT validation from Python (`FlatValidator`,
  `web_template.py`, `path_checker.py`) into a parallel TypeScript
  implementation (`vscode-extension/src/validation.ts`) so the extension
  needs no Python interpreter for its on-every-save path. It named the
  resulting duplication "the central cost of the decision": *"validation
  rules now live in both Python and TypeScript... or they drift."*
- **ADR-0008** took the opposite path for OPT validation — shelling out to
  the Python `oehrpy-validate-opt` CLI per file, accepting per-invocation
  subprocess latency and best-effort diagnostic positioning, because porting
  the RM-aware `OPTValidator` to TypeScript was judged disproportionate.

So the extension already straddles two inconsistent integration strategies
(in-process TS port vs. subprocess-per-validation CLI) for what is
conceptually one job: turn openEHR artifacts (FLAT compositions, Web
Templates, OPT files) into diagnostics, hovers, completions, and code
actions. Every feature is also locked to VS Code — none of `detector.ts`,
`validation.ts`, `hover.ts`, `autocomplete.ts`, `quickfix.ts`,
`optValidator.ts`, or `templateTree.ts` is reachable from Neovim, JetBrains,
Emacs, or any other LSP-capable editor without a from-scratch reimplementation
in that editor's native extension model.

Projects such as [`nedap/archetype-languageserver`](https://github.com/nedap/archetype-languageserver)
demonstrate the alternative: implement the openEHR-aware logic once, behind
the Language Server Protocol, and get every LSP client editor for free
through a thin, largely boilerplate client shim.

The question this ADR settles: should oehrpy's target architecture for
editor tooling be **LSP**, and if so, how does that interact with the
decisions already recorded in ADR-0007/0008?

## Decision

Adopt the **Language Server Protocol as the target architecture** for
oehrpy's editor integrations, built incrementally, without an immediate
rewrite:

1. **New component: `oehrpy-lsp`.** A standalone Python LSP server (using
   [`pygls`](https://github.com/openlawlibrary/pygls)) that wraps the
   *existing, canonical* validation modules — `FlatValidator`,
   `web_template.py`, `path_checker.py`, and `OPTValidator`
   (`src/oehrpy/validation/`) — with **no new validation logic**, mirroring
   how ADR-0007's Python CLI was "a thin wrapper... no new validation logic."
   It lives under `src/oehrpy/lsp/` and ships as the `oehrpy[lsp]` optional
   dependency (or a separate `oehrpy-lsp` distribution if the `pygls`
   dependency proves too heavy for the core SDK install).
2. **Feature parity, one server.** `textDocument/didOpen|didChange|didSave`
   drives unified FLAT + OPT diagnostics via `publishDiagnostics`;
   `textDocument/hover`, `textDocument/completion`, and
   `textDocument/codeAction` replace `hover.ts`, `autocomplete.ts`, and
   `quickfix.ts` respectively. This retires the TS/Python parity problem
   ADR-0007 flagged as its central cost: there is one implementation again,
   in the language that already holds the canonical model.
3. **The VS Code extension becomes a thin LSP client.** It stops
   reimplementing validation and instead starts `oehrpy-lsp` as a
   long-lived subprocess via `vscode-languageclient`, wiring editor-native
   pieces (status bar, the Web Template tree view, Python interpreter
   discovery) around it. This also resolves ADR-0008's "subprocess cost and
   latency on save": one long-running process replaces a spawn-per-save CLI
   invocation.
4. **Phased rollout, not a rewrite.** The TypeScript FLAT validator and the
   OPT CLI subprocess path are **not** deleted until `oehrpy-lsp` reaches
   verified parity (reusing ADR-0007's parity-testing approach, extended to
   the LSP surface). See PRD-0016 for the phase breakdown.
5. **Cross-editor is the payoff, not a v1 requirement.** Once the server
   exists, publishing minimal client configs for Neovim (`nvim-lspconfig`),
   JetBrains (via `LSP4IJ` or similar), and other LSP hosts is comparatively
   cheap and can follow after VS Code parity, not block it.

## Consequences

### Positive

- **Ends the "two implementations" problem.** ADR-0007's explicit downside
  — validation logic living in both Python and TypeScript — disappears once
  the extension consumes a Python server instead of a TS port. The Python
  implementation, already the documented "canonical reference," becomes the
  *only* implementation.
- **Cross-editor reach for the cost of one server.** The same investment
  that fixes the VS Code architecture's inconsistency also unlocks Neovim,
  JetBrains, Emacs, etc. — the exact value proposition
  `nedap/archetype-languageserver` demonstrates for ADL2 tooling.
- **Fixes ADR-0008's latency and positioning concerns as a side effect.** A
  long-lived server process avoids per-save subprocess spawn cost, and an
  in-process XML/AST model (rather than shelling out per file) opens the
  door to real line/column positions instead of best-effort `node_id`
  anchoring.
- **One validation surface for FLAT, OPT, and future AQL/ADL support**,
  instead of feature-by-feature ad hoc integration choices.

### Negative

- **Reintroduces the Python dependency ADR-0007 deliberately removed** for
  the FLAT-on-save path. That ADR's "zero-config editor UX... no Python
  interpreter, no `pip install`" property is walked back, not just scoped
  (as ADR-0008 already did for OPT) — it now applies to *all* validation.
  This is the central tension of this decision and must be mitigated (see
  PRD-0016 §Distribution) via bundled per-platform binaries so VS Code users
  still see zero-config behavior even though the underlying mechanism
  changed.
- **New moving part.** A long-running subprocess (crash recovery, restart
  policy, version skew between the server and the client extension) is
  operational surface the current architecture doesn't have.
- **Migration cost.** `vscode-extension/src/validation.ts` and the OPT CLI
  subprocess plumbing must be kept alive until `oehrpy-lsp` is proven at
  parity, meaning three validation paths exist simultaneously during the
  transition (Python core, TS port, LSP server) before two can be retired.
- **`pygls` becomes a new runtime dependency** for whichever package hosts
  the server, with its own pinning and CVE-exposure obligations (per this
  repo's "all dependencies pinned to exact versions" policy).

### Neutral

- This does not obsolete ADR-0007 or ADR-0008; it supersedes their
  *architecture*, not their reasoning. Both remain valid records of why the
  extension looked the way it did at the time, and the parity-testing
  discipline ADR-0007 established is reused here rather than replaced.
- The Web Template tree view and status bar remain VS Code-native — LSP has
  no standard notion of a sidebar tree, so that piece of the extension stays
  a thin client-side feature regardless of this decision.

## Alternatives Considered

### Alternative A: Keep the status quo (VS Code extension only, per ADR-0007/0008)

Leave FLAT validation as a TS port and OPT validation as a CLI subprocess,
accepting the parity risk and VS Code lock-in as permanent costs. Rejected
because it leaves both named downsides (drift risk, editor lock-in)
unaddressed indefinitely, and every future language feature would repeat the
same "port to TS, or shell out to Python" decision from scratch.

### Alternative B: Port everything to TypeScript, no LSP

Extend ADR-0007's approach and port `OPTValidator` to TypeScript too,
eliminating the Python dependency entirely from the extension. Rejected for
the same reason ADR-0008 rejected it: the OPT validator is RM-model-aware,
terminology-aware, and non-trivial; a faithful port is high-effort and
high-drift-risk, and this path still never reaches non-VS-Code editors.

### Alternative C: Full LSP rewrite, delete the TS port and CLI immediately

Skip the phased approach and cut over in one release. Rejected as too risky
for a validator developers depend on for correctness feedback — ADR-0007's
own history (issue #56, a silently broken subprocess call going unnoticed)
is a caution against replacing a working path before the replacement is
proven at parity.

### Alternative D: Embed the Python validator via Pyodide/WASM instead of LSP

Already considered and rejected in ADR-0007 (Alternative C) for FLAT
validation alone, for being "disproportionate: a multi-megabyte runtime...
for a few hundred lines of pure string/tree logic." It fares worse here: it
solves *none* of the cross-editor problem, since Pyodide only runs inside a
JS host (i.e., still VS Code-only), and doesn't reach the OPT validator's
XML/RM-model dependencies cleanly either.

## References

- ADR-0007 — Dual-backend FLAT validation (the parity cost this decision
  resolves)
- ADR-0008 — OPT validation via the Python CLI (the latency/positioning
  cost this decision resolves)
- ADR-0005 — Web Template as the source of truth for FLAT paths
- PRD-0015 — VS Code extension (the "no LSP" non-goal this ADR revisits)
- PRD-0016 — Language server support (the implementation plan for this
  decision)
- [`nedap/archetype-languageserver`](https://github.com/nedap/archetype-languageserver)
  — prior art: an LSP server for ADL2 archetypes/templates
- [`pygls`](https://github.com/openlawlibrary/pygls) — the proposed Python
  LSP server framework
- [Language Server Protocol specification](https://microsoft.github.io/language-server-protocol/)
