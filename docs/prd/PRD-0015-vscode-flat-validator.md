# PRD: VS Code Extension — oehrpy FLAT Format Validator

**Status:** Draft
**Version:** 0.1
**Target Release:** oehrpy-vscode v0.1.0
**Depends on:** PRD `flat-validator` (oehrpy v0.2.0) — the Python CLI must exist and be installable
**Author:** Chregi
**Date:** 2026-03-12

---

## 1. Overview

### 1.1 Problem Statement

FLAT format errors are currently discovered in one of two ways:

1. **At runtime** — submit to EHRBase, get a cryptic `Could not consume Parts` error, debug manually
2. **With the web tool** — copy/paste JSON into the browser validator, switch back to the editor

Neither is good. A developer writing FLAT compositions or Web Template integration code in VS Code gets no feedback until they leave the editor. There's no syntax awareness, no red squiggles, no hover documentation for FLAT paths.

The VS Code extension closes this loop: **validate on save, validate on command, see errors inline** — without leaving the editor.

### 1.2 Proposed Solution

A VS Code extension (`oehrpy-validator`) that:

1. Detects JSON files that look like FLAT compositions or Web Templates
2. Validates them against a configured or auto-detected Web Template using the oehrpy Python CLI
3. Shows errors and warnings as VS Code diagnostics (red/yellow squiggles) with hover messages
4. Provides an `oehrpy: Validate FLAT Composition` command
5. Optionally validates automatically on save

### 1.3 Scope

This is a developer tooling extension. Target users are clinical system developers writing Python or TypeScript backends that produce FLAT compositions — specifically users of oehrpy and the Open CIS stack. It is not a general-purpose openEHR IDE.

---

## 2. Goals

| Goal | Priority |
|------|----------|
| Show FLAT validation errors as inline diagnostics (squiggles) | P0 |
| `oehrpy: Validate FLAT Composition` command | P0 |
| Hover messages explaining each error with "did you mean?" | P0 |
| Validate on save (configurable) | P1 |
| Auto-detect Web Template from project context | P1 |
| Path autocomplete for FLAT keys based on Web Template | P2 |
| Quick Fix: replace invalid path with suggestion | P2 |
| Tree view showing the Web Template structure | P3 |

### Non-Goals

- Support for editors other than VS Code (JetBrains, Neovim, etc.) in v0.1.0
- Validating canonical JSON compositions
- Archetype/OPT authoring support
- Language Server Protocol (LSP) implementation (use VS Code extension API directly)

---

## 3. User Stories

### Developer writing FLAT compositions inline

> *"I'm writing integration tests for our FHIR-to-openEHR pipeline. The test fixtures are FLAT JSON files. I want to see red squiggles on invalid paths immediately when I save, so I catch renames before they reach CI."*

### New team member learning oehrpy

> *"I don't know the FLAT path structure for this template. I want to hover over a key and see what RM type it maps to, whether it's required, and what valid suffixes it accepts."*

### Developer debugging an EHRBase rejection

> *"EHRBase just returned a `Could not consume Parts` error. I want to paste the response into VS Code and run a command that tells me exactly which keys in my payload are wrong."*

---

## 4. Functional Requirements

### 4.1 Extension Activation

The extension activates when:

- A `.json` file is opened that contains a root object with keys matching the pattern `{word}/{word}` (FLAT composition heuristic)
- A file named `web_template.json` or matching `*.wt.json` is opened
- The user runs any `oehrpy:` command

Activation is lazy — the extension does not load until one of these conditions is true.

### 4.2 FLAT Composition Detection

The extension must classify open JSON files as one of:

| Classification | Detection heuristic |
|---------------|---------------------|
| **FLAT composition** | Root object; >50% of keys match `^[a-z_]+/[a-z_/\|]+$` |
| **Web Template** | Root object with `"tree"` key containing `"id"` and `"children"` |
| **Unknown** | Anything else — extension is silent |

Classification runs once when the file is opened or its content changes significantly.

### 4.3 Web Template Resolution

To validate a FLAT composition, the extension needs the corresponding Web Template. Resolution order:

1. **Explicit config** — `oehrpy.webTemplatePaths` workspace setting (map of template ID → file path)
2. **Same directory** — look for `web_template.json` or `*.wt.json` in the same directory as the composition
3. **Project root** — look for `web_templates/` or `templates/` directory in the workspace root
4. **Prompt user** — if no template found, show an information message with a "Choose Web Template" button that opens a file picker; remember the choice per-composition-file in workspace state

If no Web Template can be resolved, the extension shows a warning in the status bar but does not error.

### 4.4 Validation Engine: oehrpy CLI

The extension calls the oehrpy CLI as a subprocess to perform validation:

```
oehrpy validate-flat \
  --web-template <path> \
  --composition <path_or_stdin> \
  --platform <ehrbase|better> \
  --output json
```

The JSON output from the CLI is parsed and mapped to VS Code diagnostics.

**Python interpreter discovery**: The extension must find the correct Python interpreter:

1. Use VS Code's Python extension API (`vscode.extensions.getExtension('ms-python.python')`) to get the active interpreter path
2. Fall back to the `oehrpy.pythonPath` setting
3. Fall back to `python3` on PATH
4. If none found, show an actionable error: "Python not found. Configure `oehrpy.pythonPath` or install the Python extension."

**oehrpy installation check**: On first activation, run `python -m openehr_sdk.validation --version`. If it fails, offer to run `pip install oehrpy` via a VS Code terminal.

### 4.5 Diagnostics

Map `ValidationResult` to VS Code `Diagnostic` objects:

| ValidationError.error_type | VS Code severity | Color |
|---------------------------|-----------------|-------|
| `unknown_path` | Error | Red |
| `wrong_suffix` | Error | Red |
| `missing_required` | Warning | Yellow |
| `index_mismatch` | Error | Red |

Each diagnostic must:

- Point to the **key** in the JSON (the FLAT path string), not the whole line
- Include the full error message in the diagnostic tooltip
- Include the suggestion (if any) in the tooltip: `"Did you mean: adverse_reaction_list/adverse_reaction/causative_agent|value?"`

Example diagnostic tooltip:

```
Unknown path segment: 'substance' under 'adverse_reaction'
Node was renamed in this template.

→ Did you mean:
  adverse_reaction_list/adverse_reaction/causative_agent|value
```

Diagnostics are published to a `oehrpy-flat-validator` diagnostic collection (not merged with other linters).

### 4.6 Validate on Save

When the active file is a classified FLAT composition and `oehrpy.validateOnSave` is `true` (default: `true`), trigger validation automatically after every save.

Debounce: do not trigger more often than once every 500ms. Cancel in-flight validation if a new save arrives before it completes.

### 4.7 Manual Validation Command

Command: `oehrpy: Validate FLAT Composition`
Keybinding: `Ctrl+Shift+V` / `Cmd+Shift+V` (configurable)
Available when: active file is a JSON file

Runs validation on the currently active file regardless of classification heuristic (useful for edge cases the auto-detect misses).

### 4.8 Hover Documentation

When the cursor hovers over a FLAT key string, show a hover card:

```
adverse_reaction_list/adverse_reaction/causative_agent|value

  Node:     causative_agent
  Name:     Causative agent
  RM Type:  DV_CODED_TEXT
  Required: No (min: 0, max: *)

  Valid suffixes:
    |value  — The display text
    |code   — The code string
    |terminology — The terminology ID
```

Hover data is fetched from the Python CLI:

```
oehrpy web-template inspect \
  --web-template <path> \
  --path "adverse_reaction_list/adverse_reaction/causative_agent"
```

### 4.9 Quick Fix: Apply Suggestion

When a diagnostic has a `suggestion`, expose a VS Code Quick Fix (lightbulb) that replaces the invalid key with the suggested one. The fix must update the JSON key in-place, preserving the value and surrounding whitespace.

### 4.10 Status Bar Item

Show a persistent status bar item (bottom-left) when a FLAT composition is the active file:

- Loading: `$(sync~spin) oehrpy: validating...`
- Valid: `$(check) oehrpy: valid`
- Invalid: `$(error) oehrpy: 3 errors`
- No template: `$(warning) oehrpy: no template`

Clicking the status bar item opens the Problems panel filtered to `oehrpy-flat-validator`.

### 4.11 Web Template Tree View (P3)

An optional sidebar tree view panel (`oehrpy.templateExplorer`) that shows the Web Template `tree` structure as a collapsible tree with node names, RM types, and cardinality. Clicking a node copies its FLAT path to the clipboard.

---

## 5. Configuration

All settings are under the `oehrpy` namespace:

```jsonc
{
  // Path to Python interpreter with oehrpy installed
  "oehrpy.pythonPath": "",

  // Platform dialect for FLAT path validation
  "oehrpy.platform": "ehrbase",  // "ehrbase" | "better"

  // Validate automatically on file save
  "oehrpy.validateOnSave": true,

  // Map of template IDs to web template file paths
  // Example: { "IDCR - Adverse Reaction List.v1": "./templates/adverse_reaction_wt.json" }
  "oehrpy.webTemplatePaths": {},

  // Glob patterns of files to always treat as FLAT compositions
  // (overrides auto-detection)
  "oehrpy.flatCompositionPatterns": ["**/*.flat.json"],

  // Glob patterns of files to always treat as Web Templates
  "oehrpy.webTemplatePatterns": ["**/*.wt.json", "**/web_template.json"],

  // Maximum time (ms) to wait for CLI validation before timeout
  "oehrpy.validationTimeout": 5000,

  // Show hover documentation for FLAT paths
  "oehrpy.enableHover": true,

  // Show Quick Fix suggestions
  "oehrpy.enableQuickFix": true
}
```

---

## 6. Technical Design

### 6.1 Architecture

```
oehrpy-vscode/
├── package.json              # Extension manifest, commands, config schema
├── src/
│   ├── extension.ts          # Activation, command registration
│   ├── detector.ts           # FLAT / Web Template file classifier
│   ├── templateResolver.ts   # Web Template discovery logic
│   ├── validator.ts          # CLI subprocess runner + result parser
│   ├── diagnostics.ts        # Diagnostic collection + position mapping
│   ├── hover.ts              # Hover provider
│   ├── quickfix.ts           # Code action provider
│   ├── statusBar.ts          # Status bar item
│   └── config.ts             # Settings access
├── test/
│   ├── unit/                 # Unit tests (detector, resolver, etc.)
│   └── integration/          # VS Code integration tests
└── .vscodeignore
```

### 6.2 JSON Key Position Mapping

VS Code diagnostics require a `Range` (line/column). Given the raw text of a JSON file, find the exact range of a specific key string:

```typescript
function findKeyRange(document: vscode.TextDocument, key: string): vscode.Range {
  const text = document.getText();
  // Find the key surrounded by quotes: "adverse_reaction_list/..."
  const escaped = key.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const regex = new RegExp(`"(${escaped})"\\s*:`);
  const match = regex.exec(text);
  if (!match) return new vscode.Range(0, 0, 0, 0);
  const start = document.positionAt(match.index + 1); // skip opening quote
  const end = document.positionAt(match.index + match[1].length + 1);
  return new vscode.Range(start, end);
}
```

### 6.3 CLI Subprocess Execution

```typescript
import { execFile } from 'child_process';
import { promisify } from 'util';
const execFileAsync = promisify(execFile);

async function validateWithCli(
  pythonPath: string,
  wtPath: string,
  compositionPath: string,
  platform: string,
  timeoutMs: number
): Promise<ValidationResult> {
  const { stdout } = await execFileAsync(
    pythonPath,
    ['-m', 'openehr_sdk.validation', 'validate-flat',
     '--web-template', wtPath,
     '--composition', compositionPath,
     '--platform', platform,
     '--output', 'json'],
    { timeout: timeoutMs }
  );
  return JSON.parse(stdout) as ValidationResult;
}
```

For in-memory validation (unsaved files), write the current document text to a temp file before calling the CLI.

### 6.4 Extension Manifest Highlights

```json
{
  "name": "oehrpy-validator",
  "displayName": "oehrpy FLAT Validator",
  "description": "Validate openEHR FLAT format compositions against Web Templates",
  "publisher": "platzhersh",
  "version": "0.1.0",
  "engines": { "vscode": "^1.85.0" },
  "categories": ["Linters", "Other"],
  "keywords": ["openEHR", "FLAT", "EHRBase", "clinical", "oehrpy"],
  "icon": "assets/icon.png",
  "activationEvents": ["onLanguage:json"],
  "contributes": {
    "commands": [
      {
        "command": "oehrpy.validateFlat",
        "title": "oehrpy: Validate FLAT Composition"
      },
      {
        "command": "oehrpy.selectWebTemplate",
        "title": "oehrpy: Select Web Template for This File"
      },
      {
        "command": "oehrpy.showValidPaths",
        "title": "oehrpy: Show Valid Paths for Template"
      }
    ],
    "configuration": { /* see Section 5 */ },
    "views": {
      "explorer": [
        {
          "id": "oehrpy.templateExplorer",
          "name": "Web Template",
          "when": "oehrpy.hasWebTemplate"
        }
      ]
    }
  }
}
```

---

## 7. Implementation Plan

### Phase 3C — Core Extension (v0.1.0)

| Task | Effort | Notes |
|------|--------|-------|
| Project scaffold (TypeScript, esbuild, VS Code test runner) | 0.5 day | |
| File classifier (FLAT / Web Template detection) | 0.5 day | |
| CLI subprocess runner + result parser | 1 day | |
| JSON key position mapper (find Range for each error) | 1 day | Tricky; test thoroughly |
| Diagnostic collection publisher | 0.5 day | |
| `validate-flat` command | 0.5 day | |
| Validate-on-save with debounce | 0.5 day | |
| Status bar item | 0.5 day | |
| Web Template resolver (4 strategies) | 1 day | |
| Python interpreter discovery | 0.5 day | |
| Settings schema + configuration access | 0.5 day | |
| Unit tests (classifier, resolver, position mapper) | 1 day | |
| Integration tests (mock CLI) | 1 day | |
| **Subtotal** | **~9 days** | |

### Phase 3D — Enhanced UX (v0.2.0)

| Task | Effort |
|------|--------|
| Hover provider (path documentation) | 1.5 days |
| Quick Fix code action (apply suggestion) | 1 day |
| Web Template tree view (sidebar) | 2 days |
| Path autocomplete (CompletionItemProvider) | 3 days |
| VS Code Marketplace publication | 0.5 day |
| **Subtotal** | **~8 days** |

---

## 8. Distribution

### VS Code Marketplace

Publish to the [VS Code Marketplace](https://marketplace.visualstudio.com/vscode) under publisher `platzhersh`:

```bash
npm install -g @vscode/vsce
vsce package
vsce publish
```

The extension will be listed at: `https://marketplace.visualstudio.com/items?itemName=platzhersh.oehrpy-validator`

### Manual Installation (until marketplace approval)

Include a `.vsix` file in each GitHub release. Users install via:

```
Extensions panel → ··· → Install from VSIX
```

Or:
```bash
code --install-extension oehrpy-validator-0.1.0.vsix
```

### Repository Structure

The extension lives in the oehrpy monorepo:

```
oehrpy/
├── src/openehr_sdk/        # Python package (existing)
├── validator/              # GitHub Pages web tool (v0.2.0)
└── vscode-extension/       # VS Code extension (Phase 3)
    ├── package.json
    ├── src/
    └── test/
```

---

## 9. Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Python not found / wrong environment in VS Code | High | High | Clear error messages; auto-detect via Python extension API; setup guide in README |
| CLI subprocess too slow for validate-on-save | Medium | Medium | Debounce 500ms; show spinner; cancel in-flight; consider in-process validation via embedded Python in future |
| JSON key position mapping fails for complex nested JSON | Medium | Medium | Thorough unit tests; fall back to line-level diagnostics if exact range not found |
| oehrpy not installed in user's Python env | High | Medium | On activation, check and offer `pip install oehrpy` via integrated terminal |
| VS Code Marketplace review delay | Low | Low | Provide .vsix download as immediate alternative |

---

## 10. Success Metrics

- A developer catches the `substance` → `causative_agent` rename within 1 second of saving, without leaving VS Code
- Zero configuration needed for projects that follow the standard directory layout (`templates/` at project root)
- Extension published to VS Code Marketplace with 4+ star average rating
- Used in Open CIS development workflow (dogfooding signal)

---

## Appendix: Example Workflow

**Setup** (once per project):
```jsonc
// .vscode/settings.json
{
  "oehrpy.platform": "ehrbase",
  "oehrpy.webTemplatePaths": {
    "IDCR - Adverse Reaction List.v1": "./api/templates/adverse_reaction_wt.json"
  }
}
```

**Developer workflow**:
1. Open `tests/fixtures/adverse_reaction.flat.json` in VS Code
2. Edit a FLAT path — accidentally use `substance` instead of `causative_agent`
3. Save the file
4. Red squiggle appears on `"adverse_reaction_list/adverse_reaction/substance|value"` immediately
5. Hover over squiggle → tooltip shows: `"Did you mean: causative_agent?"`
6. Click lightbulb → Quick Fix → `Replace with 'causative_agent'`
7. Error disappears. Composition is valid before it ever touches EHRBase.
