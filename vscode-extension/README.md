# oehrpy FLAT Validator — VS Code Extension

Validate openEHR FLAT format compositions against Web Templates, directly in VS Code. Catch invalid paths, wrong suffixes, and missing required fields before they reach EHRBase.

## Features

- **Inline diagnostics** — red/yellow squiggles on invalid FLAT paths with detailed error messages
- **Validate on save** — automatic validation when you save a `.json` file detected as a FLAT composition
- **FLAT path autocomplete** — IntelliSense completions for all valid FLAT paths derived from the Web Template
- **Hover documentation** — hover over a FLAT key to see RM type, cardinality, and valid suffixes
- **Quick Fix** — lightbulb suggestions to replace invalid paths with "did you mean?" corrections
- **Web Template tree view** — browse the template structure in the Explorer sidebar; click a node to copy its FLAT path
- **OPT template validation** — inline diagnostics for `.opt` / openEHR `<template>` XML files (well-formedness, semantic, structural, and FLAT-path-impact checks)
- **Status bar** — shows validation state (valid, errors, no template) in the bottom bar
- **Web Template auto-detection** — finds templates from workspace config, same directory, or `templates/` folder
- **Manual command** — `oehrpy: Validate FLAT Composition` (Ctrl+Shift+F10 / Cmd+Shift+F10)

## Requirements

- **VS Code 1.85+**
- A Web Template JSON file for the template you're validating against

FLAT validation runs entirely in-process — **no Python interpreter is required**. (The same logic is also available as a Python CLI, `python -m oehrpy.validation`, for CI and scripting.)

**OPT validation is optional and Python-backed:** validating `.opt` / `<template>` XML files reuses the Python `oehrpy` package (`pip install oehrpy`), which exposes the full `OPTValidator`. If Python or `oehrpy` isn't available, OPT validation simply stays off (with a one-time hint) — FLAT validation is unaffected. See [ADR-0008](../docs/adr/0008-opt-validation-via-python-cli-in-vscode.md).

## Getting Started

1. Install the extension
2. Open a FLAT composition JSON file (keys like `vital_signs/blood_pressure/systolic|magnitude`)
3. Place a Web Template file in the same directory (`web_template.json` or `*.wt.json`), or configure paths in settings
4. Save the file — diagnostics appear automatically

### Web Template Resolution

The extension finds the Web Template for a composition in this order:

1. **Explicit config** — `oehrpy.webTemplatePaths` in workspace settings
2. **Same directory** — `web_template.json` or `*.wt.json` next to the composition
3. **Project root** — `web_templates/` or `templates/` directory in the workspace
4. **User prompt** — asks you to pick a file and remembers the choice

## Commands

| Command | Keybinding | Description |
|---------|------------|-------------|
| `oehrpy: Validate FLAT Composition` | Ctrl+Shift+F10 | Validate the active JSON file |
| `oehrpy: Validate OPT Template` | — | Validate the active `.opt` / `<template>` XML file |
| `oehrpy: Select Web Template for This File` | — | Pick a Web Template for the current file |
| `oehrpy: Show Valid Paths for Template` | — | List all valid FLAT paths in the output panel |
| `oehrpy: Refresh Web Template Tree` | — | Reload the Web Template tree view from disk |
| `oehrpy: Copy FLAT Path` | — | Copy the selected tree node's FLAT path to the clipboard |

## Web Template Tree View

When the active editor is a Web Template (or a FLAT composition with a resolvable template), an **openEHR Web Template** view appears in the Explorer sidebar. It mirrors the template `tree` as a collapsible structure:

- Each node shows its **name**, **RM type**, and **cardinality** (`min..max`, with `*` for unbounded)
- Container nodes (`COMPOSITION`, `SECTION`, `OBSERVATION`, …) use a namespace icon; addressable data nodes use a field icon
- **Hover** a node for the full FLAT path, required flag, and valid `|suffix` attributes
- **Click** a node (or use the inline copy button) to copy its FLAT path to the clipboard — handy for building compositions
- The tree follows the active editor and reloads automatically when the template file is saved; use the title-bar refresh button to reload manually

The view is parsed entirely from the Web Template JSON and needs no Python interpreter. Disable it with `oehrpy.enableTemplateExplorer: false`.

## Settings

All settings are under the `oehrpy` namespace. Add them to `.vscode/settings.json`:

```jsonc
{
  // CDR platform dialect
  "oehrpy.platform": "ehrbase",  // "ehrbase" | "better"

  // Validate automatically on save
  "oehrpy.validateOnSave": true,

  // Map template IDs to Web Template file paths
  "oehrpy.webTemplatePaths": {
    "IDCR - Adverse Reaction List.v1": "./templates/adverse_reaction_wt.json"
  },

  // Glob patterns for FLAT composition files (overrides auto-detection)
  "oehrpy.flatCompositionPatterns": ["**/*.flat.json"],

  // Glob patterns for Web Template files
  "oehrpy.webTemplatePatterns": ["**/*.wt.json", "**/web_template.json"],

  // Enable hover documentation
  "oehrpy.enableHover": true,

  // Enable Quick Fix suggestions
  "oehrpy.enableQuickFix": true,

  // Enable FLAT path autocomplete
  "oehrpy.enableAutocomplete": true,

  // Show the Web Template structure as a tree view in the Explorer sidebar
  "oehrpy.enableTemplateExplorer": true,

  // Validate OPT templates (.opt / <template> XML) via the Python oehrpy CLI
  "oehrpy.enableOptValidation": true,

  // Python interpreter for OPT validation (empty = auto-detect). Not used for
  // FLAT validation, which runs in-process.
  "oehrpy.pythonPath": "",

  // Max time (ms) to wait for the OPT validation CLI
  "oehrpy.optValidationTimeout": 15000
}
```

## How Detection Works

The extension classifies JSON files automatically:

- **FLAT composition** — root object where >50% of keys match the FLAT path pattern (`word/word|suffix`)
- **Web Template** — root object with a `tree` key containing `id` and `children`
- Files matching `*.flat.json` or `*.wt.json` globs are classified without content inspection

## Development

```bash
cd vscode-extension

# Install dependencies
npm install

# Compile
npm run compile

# Run linter
npm run lint

# Run tests
npm test
```

### Manual Installation

```bash
npm run compile
npx vsce package
code --install-extension oehrpy-validator-0.4.0.vsix
```

### CI & Publishing

- **CI** — every push/PR that touches `vscode-extension/**` runs the
  [VS Code Extension CI](../.github/workflows/vscode-extension-ci.yml) workflow:
  `npm ci`, lint, compile, unit tests, and a `vsce package` smoke test (the
  built `.vsix` is uploaded as an artifact).
- **Icon** — `icon.png` is generated from the project logo by
  `python scripts/generate-icon.py` (pure stdlib, no image libraries).
- **Publishing** — run the
  [Publish VS Code Extension](../.github/workflows/vscode-extension-publish.yml)
  workflow manually after bumping `version` in `package.json`. It publishes to
  the VS Code Marketplace when the `VSCE_PAT` secret is set, and to Open VSX
  when `OVSX_PAT` is set; use the **dry_run** input to package without
  publishing. Publisher: `platzhersh`.

## License

MIT — see [LICENSE](../LICENSE) in the repository root.
