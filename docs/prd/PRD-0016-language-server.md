# PRD: oehrpy Language Server (`oehrpy-lsp`)

**Status:** Draft
**Version:** 0.1
**Depends on:** ADR-0009 (LSP adoption decision); `oehrpy.validation` (ADR-0007) and `OPTValidator` (ADR-0008) as the wrapped engines
**Author:** Chregi
**Date:** 2026-08-21

---

## 1. Overview

### 1.1 Problem Statement

oehrpy's editor tooling (`vscode-extension/`) only exists for VS Code, and
internally it is two inconsistent integrations glued together: FLAT
validation is a hand-ported TypeScript copy of the Python validator
(ADR-0007), and OPT validation shells out to a Python CLI per file
(ADR-0008). Neither generalizes: a developer using Neovim, JetBrains, Emacs,
Helix, or any other [LSP](https://microsoft.github.io/language-server-protocol/)-capable
editor gets nothing, and every future language feature (AQL, ADL syntax)
means re-deciding "port to TS or shell out to Python" from scratch.

Prior art exists in the openEHR ecosystem —
[`nedap/archetype-languageserver`](https://github.com/nedap/archetype-languageserver)
implements ADL2 archetype/template language support once, behind LSP, and
gets every LSP client editor for free. oehrpy has no equivalent.

### 1.2 Proposed Solution

Build **`oehrpy-lsp`**, a Python [LSP](https://microsoft.github.io/language-server-protocol/)
server (via [`pygls`](https://github.com/openlawlibrary/pygls)) that wraps
oehrpy's existing, canonical validation engines — no new validation logic —
and exposes them as diagnostics, hover, completion, and code actions to
**any** LSP client. The VS Code extension is refactored into a thin LSP
client on top of it, and the same server becomes installable for other
editors with a small, mostly boilerplate client config.

### 1.3 Scope

Same target users as PRD-0015 (clinical system developers using oehrpy /
Open CIS), but no longer VS Code-only. In scope: FLAT compositions, Web
Templates, and OPT 1.4 XML — the same three artifact types the VS Code
extension already handles. Not in scope for v1: AQL and ADL 1.4/2 language
support (tracked as future work, same as PRD-0015 Phase 3F/future).

---

## 2. Goals

| Goal | Priority |
|------|----------|
| One server implementing FLAT + OPT diagnostics, hover, completion, code actions | P0 |
| VS Code extension consumes the server via `vscode-languageclient` instead of the TS port / CLI subprocess | P0 |
| Verified parity with the current TS FLAT validator and Python OPT CLI before either is retired | P0 |
| `pip install oehrpy[lsp]` (or `pipx install oehrpy-lsp`) works standalone, editor-agnostic | P0 |
| Bundled per-platform binary so VS Code users keep zero-config UX despite the new Python dependency | P1 |
| Minimal Neovim (`nvim-lspconfig`) client config published and documented | P1 |
| Real line/column diagnostic positions for OPT issues (vs. best-effort `node_id` anchoring today) | P2 |
| JetBrains client config (e.g. via a generic LSP plugin) documented | P2 |
| Web Template tree view equivalent via a custom LSP request/notification | P3 |
| AQL / ADL language support on the same server | Future |

### Non-Goals

- Rewriting the FLAT/OPT validation *rules* — the server wraps
  `FlatValidator`/`OPTValidator` verbatim; behavior changes are out of scope.
- Dropping VS Code-native UX pieces that LSP has no standard concept for
  (status bar item, Web Template sidebar tree) — these stay client-side.
- Supporting editors with no LSP client story at all.
- A rewrite of `oehrpy.validation`'s public Python API; the server is an
  additional consumer, not a replacement for the CLI (ADR-0007's
  `python -m oehrpy.validation` remains for CI/scripting).

---

## 3. User Stories

### Developer using Neovim / JetBrains / Emacs

> *"I write FHIR-to-openEHR pipelines in Neovim. Today oehrpy tooling doesn't
> exist outside VS Code. I want the same red squiggles and hover docs my
> VS Code colleagues get, via my editor's normal LSP setup."*

### VS Code user (unchanged experience, different plumbing)

> *"I don't care how it works under the hood — I want validate-on-save,
> hover, and quick fixes to keep working exactly as they do today, without
> having to newly install or configure Python."*

### Maintainer adding a new language feature

> *"I want to add AQL completion once, in one server, instead of deciding
> per editor whether to port the logic or shell out to a CLI."*

---

## 4. Functional Requirements

### 4.1 Server Activation and Transport

`oehrpy-lsp` speaks LSP over **stdio** (the default for editor-spawned
servers) and, for debugging, optionally over TCP. It is a long-lived
process started once per workspace by the client, not spawned per
validation (this is the deliberate contrast with ADR-0008's per-save CLI
subprocess).

### 4.2 Document Classification

Reuses the same classification heuristics `detector.ts` and
`optDiagnostics.ts` already encode (FLAT composition: root object, >50% of
keys match `^[a-z_]+/[a-z_/|]+$`; Web Template: root object with a `tree` /
`id` / `children` shape; OPT: `.opt` extension or `<template>` root in the
openEHR namespace), ported once into the server so every client shares
identical detection — currently this logic exists only in
`vscode-extension/src/detector.ts` and would otherwise need reimplementing
per editor.

### 4.3 Capabilities

| LSP capability | Backing logic | Replaces |
|---|---|---|
| `textDocument/publishDiagnostics` | `FlatValidator` + `OPTValidator`, unified | `diagnostics.ts`, `optDiagnostics.ts` |
| `textDocument/hover` | `web_template.py` node lookup | `hover.ts` |
| `textDocument/completion` | FLAT path enumeration from the Web Template | `autocomplete.ts` |
| `textDocument/codeAction` | "Did you mean?" suggestions from `path_checker.py` | `quickfix.ts` |
| `workspace/didChangeConfiguration` | Platform (`ehrbase`/`better`), Web Template resolution paths | `config.ts` |
| Custom: `oehrpy/webTemplateTree` | Serialized Web Template tree | `templateTree.ts` (client renders it; server just supplies data) |

Diagnostic severity mapping is unchanged from PRD-0015 §4.5 / ADR-0007's
JSON contract (`unknown_path`/`wrong_suffix`/`index_mismatch` → Error,
`missing_required` → Warning) — the server emits LSP diagnostics built from
the same `ValidationResult` shape, not a new schema.

### 4.4 Web Template Resolution

Identical resolution order to PRD-0015 §4.3 (explicit config → same
directory → project root `templates/`/`web_templates/` → prompt), except
"prompt user" becomes a `window/showMessageRequest` LSP call so it renders
correctly in any client, not just VS Code's API.

### 4.5 OPT Diagnostic Positioning (Improvement over ADR-0008)

Because the server holds a persistent in-process XML tree (via
`defusedxml`, as the existing `OPTValidator` already does) rather than
being re-invoked as a stateless CLI call per file, this is the natural point
to close ADR-0008's "Negative: best-effort, identifier-based positioning" gap
— computing exact source line/column via `sourceline`-style tracking during
the existing parse, instead of matching `node_id` text after the fact. This
is P2, not required for parity, since it's a strict improvement over the
current CLI baseline rather than a blocker to shipping v1.

### 4.6 Parity Verification (extends ADR-0007's approach)

Before the TS FLAT validator or OPT CLI subprocess path is removed from the
extension, `oehrpy-lsp`'s diagnostics must match both on the repository's
reference fixtures and Web Template: same `is_valid`, same error/warning
counts, same suggestions. This reuses the parity discipline ADR-0007
established for the Python-CLI-vs-TypeScript-port comparison, now applied to
the-server-vs-both-predecessors.

---

## 5. Technical Design

### 5.1 Architecture

```
oehrpy/
├── src/oehrpy/
│   ├── validation/            # existing — FlatValidator, OPTValidator (unchanged)
│   └── lsp/                   # NEW
│       ├── server.py          # pygls server, capability registration
│       ├── documents.py       # classification (ports detector.ts once, in Python)
│       ├── diagnostics.py     # ValidationResult -> lsp.Diagnostic
│       ├── hover.py
│       ├── completion.py
│       ├── code_actions.py
│       └── __main__.py        # `python -m oehrpy.lsp` entry point
├── vscode-extension/
│   └── src/
│       ├── extension.ts       # now starts oehrpy-lsp via vscode-languageclient
│       ├── serverDiscovery.ts # NEW — finds/bundles the server binary
│       ├── statusBar.ts       # unchanged, client-side
│       └── templateTree.ts    # unchanged rendering; data now via oehrpy/webTemplateTree
└── docs/editors/
    ├── neovim.md              # NEW — nvim-lspconfig snippet
    └── jetbrains.md           # NEW
```

`vscode-extension/src/validation.ts` (the TS FLAT port) and the
`optValidator.ts` CLI-subprocess path are kept, unmodified, behind a
feature flag until §4.6 parity is signed off — see Implementation Plan.

### 5.2 Server Skeleton (`pygls`)

```python
from pygls.server import LanguageServer
from lsprotocol import types

server = LanguageServer("oehrpy-lsp", "v0.1.0")

@server.feature(types.TEXT_DOCUMENT_DID_SAVE)
def on_save(ls: LanguageServer, params: types.DidSaveTextDocumentParams):
    doc = ls.workspace.get_text_document(params.text_document.uri)
    kind = classify(doc.source)          # documents.py
    if kind is DocumentKind.FLAT:
        result = flat_validator.validate(doc.source, resolve_web_template(doc.uri))
    elif kind is DocumentKind.OPT:
        result = opt_validator.validate(doc.source)
    else:
        return
    ls.publish_diagnostics(doc.uri, to_lsp_diagnostics(result))
```

### 5.3 VS Code Client

```typescript
import { LanguageClient } from 'vscode-languageclient/node';

const serverPath = await resolveServerBinary(context); // bundled or discovered
const client = new LanguageClient(
  'oehrpy-lsp',
  { command: serverPath, args: ['--stdio'] },
  { documentSelector: [{ language: 'json' }, { language: 'opt' }, { language: 'xml' }] }
);
await client.start();
```

`serverDiscovery.ts` mirrors PRD-0015 §4.4's interpreter-discovery ladder,
but resolves a *server binary* instead of a bare interpreter: (1) a bundled
per-platform binary shipped in the `.vsix` (see §6.1), (2) `oehrpy.lsp.path`
setting, (3) `python -m oehrpy.lsp` via the same Python-discovery chain
PRD-0015 already documents, (4) an actionable error.

---

## 6. Distribution

### 6.1 Bundled Binary for VS Code (mitigates ADR-0009's "Negative")

To preserve the "zero-config" property ADR-0007 won and this ADR partially
gives back, the `.vsix` bundles a `oehrpy-lsp` binary per platform (built
via [PyInstaller](https://pyinstaller.org/) or
[PyOxidizer](https://pyoxidizer.readthedocs.io/)) for the common triples
(win-x64, macos-x64/arm64, linux-x64). Only users on an unsupported platform
fall back to the `python -m oehrpy.lsp` discovery chain.

### 6.2 Standalone (other editors)

```bash
pip install "oehrpy[lsp]"      # or: pipx install oehrpy-lsp
oehrpy-lsp --stdio
```

`docs/editors/neovim.md` ships a copy-pasteable `nvim-lspconfig` snippet;
`docs/editors/jetbrains.md` documents wiring via a generic LSP plugin.

### 6.3 PyPI / Marketplace

The server ships as part of the `oehrpy` distribution (`oehrpy[lsp]` extra)
so its version stays locked to the validation engine it wraps, avoiding the
version-skew risk ADR-0009 flags. The VS Code extension continues to
publish independently to the Marketplace, per its existing versioning
(ADR-0007 §Neutral).

---

## 7. Implementation Plan

### Phase 1 — Server Core (parity with FLAT-in-TS)

| Task | Notes |
|------|-------|
| `pygls` scaffold, `oehrpy.lsp.__main__` entry point | |
| Document classification port (`documents.py`) | One-time port of `detector.ts`'s heuristics |
| FLAT diagnostics via `FlatValidator` | Reuses `oehrpy.validation` directly — no logic port |
| Hover, completion, code actions for FLAT | |
| Parity test suite vs. `vscode-extension/test/unit/validation.test.ts` fixtures | Extends ADR-0007's parity discipline |

### Phase 2 — OPT on the Server (parity with the CLI path)

| Task | Notes |
|------|-------|
| OPT diagnostics via `OPTValidator`, in-process (no subprocess) | |
| Line/column positioning improvement (§4.5) | P2, can slip past Phase 2 |
| Parity vs. `oehrpy-validate-opt` CLI output on the reference template | |

### Phase 3 — VS Code Cutover

| Task | Notes |
|------|-------|
| `vscode-languageclient` integration, `serverDiscovery.ts` | |
| Bundled per-platform binaries in CI, added to `.vsix` | |
| Feature-flag old TS/CLI paths off by default once parity (Phase 1+2) is signed off | Code stays for one release as a fallback |
| Remove `validation.ts` / CLI subprocess path | Follow-up release, after the flag has been off by default for a full cycle |

### Phase 4 — Cross-Editor

| Task | Notes |
|------|-------|
| Neovim client doc + snippet | |
| JetBrains client doc | |
| Announce standalone `pip install oehrpy[lsp]` usage | |

Future (post v1, tracked separately): AQL and ADL 1.4/2 support on the same
server, superseding PRD-0015 Phase 3F/future as VS Code-specific plans.

---

## 8. Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Bundled binary build (PyInstaller/PyOxidizer) breaks per-platform in CI | Medium | High | Build and smoke-test all target triples in CI before every extension release |
| Parity gaps between server and existing TS/CLI paths delay cutover | Medium | Medium | Phase 3 keeps old paths behind a flag until parity tests pass, not on a deadline |
| `pygls`/`lsprotocol` version churn | Low | Medium | Pin exact versions per repo policy; track upstream releases deliberately |
| Long-lived server process leaks memory/state across a long editing session | Low | Medium | Restart policy in the client; server-side tests for repeated open/close cycles |
| Users on unsupported platforms fall back to a Python-discovery UX regression | Medium | Low | Same discovery ladder and error messaging PRD-0015 already validated |

---

## 9. Success Metrics

- `oehrpy-lsp` diagnostics are byte-for-byte equivalent (error/warning
  counts, suggestions) to the current TS FLAT validator and OPT CLI on the
  reference fixtures before either legacy path is removed
- VS Code users see no change in validate-on-save latency or configuration
  burden after cutover
- At least one non-VS-Code editor (Neovim) documented and confirmed working
  end-to-end against a real Web Template
- `vscode-extension/src/validation.ts` and the OPT CLI subprocess path
  fully removed within two release cycles of Phase 3 shipping

---

## Appendix: Example Cross-Editor Workflow

**VS Code** (unchanged from the user's perspective):
1. Open a FLAT composition, edit an invalid path, save
2. Red squiggle + hover "Did you mean?" appear — now served by
   `oehrpy-lsp` over stdio instead of the in-process TS port

**Neovim** (new):
```lua
-- ~/.config/nvim/lua/lsp/oehrpy.lua
require('lspconfig.configs').oehrpy = {
  default_config = {
    cmd = { 'oehrpy-lsp', '--stdio' },
    filetypes = { 'json', 'xml' },
    root_dir = require('lspconfig.util').root_pattern('web_template.json', '.git'),
  },
}
require('lspconfig').oehrpy.setup{}
```
3. Same FLAT composition, same red squiggle, same hover — no VS Code
   required.
