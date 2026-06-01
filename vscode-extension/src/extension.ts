import * as vscode from "vscode";
import { FlatPathCompletionProvider } from "./autocomplete";
import { getConfig } from "./config";
import { classifyDocument } from "./detector";
import {
  clearDiagnostics,
  publishDiagnostics,
} from "./diagnostics";
import { FlatPathHoverProvider } from "./hover";
import { FlatPathQuickFixProvider } from "./quickfix";
import { OehrpyStatusBar } from "./statusBar";
import { WebTemplateTreeProvider } from "./templateTree";
import type { TemplateTreeNode } from "./webTemplate";
import {
  initTemplateResolver,
  resolveWebTemplate,
  promptForWebTemplate,
  setTemplateAssociation,
} from "./templateResolver";
import {
  enumerateValidPathStrings,
  validateFlatComposition,
} from "./validator";
import { classifyOptDocument, publishOptDiagnostics } from "./optDiagnostics";
import { discoverPythonPath, validateOptFile } from "./optValidator";

let diagnosticCollection: vscode.DiagnosticCollection;
let optDiagnosticCollection: vscode.DiagnosticCollection;
let statusBar: OehrpyStatusBar;
let templateTreeProvider: WebTemplateTreeProvider;
let outputChannel: vscode.OutputChannel;
let debounceTimer: ReturnType<typeof setTimeout> | undefined;
let optDebounceTimer: ReturnType<typeof setTimeout> | undefined;
let optUnavailableHintShown = false;

export function activate(context: vscode.ExtensionContext): void {
  // Initialize template resolver with persistent workspace state
  initTemplateResolver(context.workspaceState);

  // Create diagnostic collection
  diagnosticCollection = vscode.languages.createDiagnosticCollection(
    "oehrpy-flat-validator",
  );
  context.subscriptions.push(diagnosticCollection);

  // Separate collection for OPT (.opt/.xml) template diagnostics
  optDiagnosticCollection = vscode.languages.createDiagnosticCollection(
    "oehrpy-opt-validator",
  );
  context.subscriptions.push(optDiagnosticCollection);

  // Create status bar
  statusBar = new OehrpyStatusBar();
  context.subscriptions.push(statusBar);

  // Create reusable output channel
  outputChannel = vscode.window.createOutputChannel("oehrpy");
  context.subscriptions.push(outputChannel);

  // Register commands
  context.subscriptions.push(
    vscode.commands.registerCommand("oehrpy.validateFlat", () =>
      runValidation(true),
    ),
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("oehrpy.selectWebTemplate", () =>
      selectWebTemplateCommand(),
    ),
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("oehrpy.showValidPaths", () =>
      showValidPathsCommand(),
    ),
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("oehrpy.validateOpt", () =>
      runOptValidation(true),
    ),
  );

  // Register hover provider
  context.subscriptions.push(
    vscode.languages.registerHoverProvider(
      { language: "json", scheme: "file" },
      new FlatPathHoverProvider(),
    ),
  );

  // Register quick fix provider
  context.subscriptions.push(
    vscode.languages.registerCodeActionsProvider(
      { language: "json", scheme: "file" },
      new FlatPathQuickFixProvider(),
      {
        providedCodeActionKinds: FlatPathQuickFixProvider.providedCodeActionKinds,
      },
    ),
  );

  // Register completion provider for FLAT path autocomplete
  context.subscriptions.push(
    vscode.languages.registerCompletionItemProvider(
      { language: "json", scheme: "file" },
      new FlatPathCompletionProvider(),
      "/",
      "|",
    ),
  );

  // Register the Web Template tree view (explorer sidebar)
  templateTreeProvider = new WebTemplateTreeProvider();
  context.subscriptions.push(
    vscode.window.registerTreeDataProvider(
      "oehrpy.templateExplorer",
      templateTreeProvider,
    ),
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("oehrpy.refreshTemplateTree", () =>
      templateTreeProvider.reload(),
    ),
  );

  context.subscriptions.push(
    vscode.commands.registerCommand(
      "oehrpy.copyFlatPath",
      (node?: TemplateTreeNode) => copyFlatPathCommand(node),
    ),
  );

  // Validate on save
  context.subscriptions.push(
    vscode.workspace.onDidSaveTextDocument((document) => {
      // Refresh the tree if the displayed Web Template file was saved.
      if (document.uri.fsPath === templateTreeProvider.sourcePath) {
        void templateTreeProvider.reload();
      }

      const config = getConfig();
      if (!config.validateOnSave) {
        return;
      }

      // OPT (.opt/.xml) templates validate via the Python CLI.
      if (classifyOptDocument(document.fileName, document.getText())) {
        if (optDebounceTimer) {
          clearTimeout(optDebounceTimer);
        }
        optDebounceTimer = setTimeout(() => runOptValidation(false), 500);
        return;
      }

      if (document.languageId !== "json") {
        return;
      }

      const classification = classifyDocument(document);
      if (classification !== "flat_composition") {
        return;
      }

      // Debounce validation
      if (debounceTimer) {
        clearTimeout(debounceTimer);
      }
      debounceTimer = setTimeout(() => runValidation(false), 500);
    }),
  );

  // Validate OPT templates when opened
  context.subscriptions.push(
    vscode.workspace.onDidOpenTextDocument((document) => {
      if (document.uri.scheme !== "file") {
        return;
      }
      if (classifyOptDocument(document.fileName, document.getText())) {
        void runOptValidationFor(document, false);
      }
    }),
  );

  // Update status bar when active editor changes
  context.subscriptions.push(
    vscode.window.onDidChangeActiveTextEditor((editor) => {
      // Keep the Web Template tree in sync with the active file.
      void templateTreeProvider.syncWithActiveEditor();

      if (!editor || editor.document.languageId !== "json") {
        statusBar.setState("idle");
        return;
      }

      const classification = classifyDocument(editor.document);
      if (classification !== "flat_composition") {
        statusBar.setState("idle");
        return;
      }

      // Show status bar for FLAT compositions
      const existingDiagnostics = diagnosticCollection.get(editor.document.uri);
      if (existingDiagnostics && existingDiagnostics.length > 0) {
        const errorCount = existingDiagnostics.filter(
          (d) => d.severity === vscode.DiagnosticSeverity.Error,
        ).length;
        if (errorCount > 0) {
          statusBar.setState("invalid", errorCount);
        } else {
          statusBar.setState("valid");
        }
      } else {
        statusBar.show();
      }
    }),
  );

  // Clear diagnostics when a document is closed
  context.subscriptions.push(
    vscode.workspace.onDidCloseTextDocument((document) => {
      clearDiagnostics(document, diagnosticCollection);
      optDiagnosticCollection.delete(document.uri);
    }),
  );

  // Populate the Web Template tree for the current file
  void templateTreeProvider.syncWithActiveEditor();

  // Validate the current file on activation
  const activeEditor = vscode.window.activeTextEditor;
  if (activeEditor && activeEditor.document.uri.scheme === "file") {
    const document = activeEditor.document;
    if (
      document.languageId === "json" &&
      classifyDocument(document) === "flat_composition"
    ) {
      runValidation(false);
    } else if (classifyOptDocument(document.fileName, document.getText())) {
      void runOptValidationFor(document, false);
    }
  }
}

export function deactivate(): void {
  if (debounceTimer) {
    clearTimeout(debounceTimer);
  }
  if (optDebounceTimer) {
    clearTimeout(optDebounceTimer);
  }
}

/**
 * Run validation on the currently active JSON file.
 *
 * Validation runs in-process (no Python required); see `validation.ts`.
 */
async function runValidation(isManual: boolean): Promise<void> {
  const editor = vscode.window.activeTextEditor;
  if (!editor) {
    if (isManual) {
      vscode.window.showWarningMessage("No active file to validate.");
    }
    return;
  }

  const document = editor.document;

  if (document.languageId !== "json" && isManual) {
    vscode.window.showWarningMessage(
      "oehrpy validation only works with JSON files.",
    );
    return;
  }

  statusBar.setState("validating");

  try {
    // Resolve Web Template
    let webTemplatePath = await resolveWebTemplate(document.uri);
    if (!webTemplatePath) {
      if (isManual) {
        webTemplatePath = await promptForWebTemplate(document.uri);
      }
      if (!webTemplatePath) {
        statusBar.setState("no_template");
        if (isManual) {
          vscode.window.showWarningMessage(
            "No Web Template found. Use 'oehrpy: Select Web Template' to configure.",
          );
        }
        return;
      }
    }

    // Run validation
    const config = getConfig();
    const result = validateFlatComposition(
      webTemplatePath,
      document.getText(),
      config.platform,
    );

    // Publish diagnostics
    publishDiagnostics(document, result, diagnosticCollection);

    // Update status bar
    const errorCount = result.errors.length;
    if (errorCount > 0) {
      statusBar.setState("invalid", errorCount);
    } else {
      statusBar.setState("valid");
    }
  } catch (error) {
    statusBar.setState("error");

    if (isManual) {
      const message =
        error instanceof Error ? error.message : "Unknown error";
      vscode.window.showErrorMessage(
        `oehrpy validation failed: ${message}`,
      );
    }
  }
}

/**
 * Command to select a Web Template for the current file.
 */
async function selectWebTemplateCommand(): Promise<void> {
  const editor = vscode.window.activeTextEditor;
  if (!editor) {
    vscode.window.showWarningMessage("No active file.");
    return;
  }

  const templatePath = await promptForWebTemplate(editor.document.uri);
  if (templatePath) {
    setTemplateAssociation(editor.document.uri.fsPath, templatePath);
    vscode.window.showInformationMessage(
      `Web Template set to: ${templatePath}`,
    );
    // Re-run validation
    runValidation(false);
  }
}

/**
 * Command to copy a tree node's FLAT path to the clipboard.
 */
async function copyFlatPathCommand(node?: TemplateTreeNode): Promise<void> {
  if (!node) {
    return;
  }
  await vscode.env.clipboard.writeText(node.flatPath);
  vscode.window.setStatusBarMessage(
    `$(clippy) Copied: ${node.flatPath}`,
    3000,
  );
}

/**
 * Command to show all valid FLAT paths for the current template.
 */
async function showValidPathsCommand(): Promise<void> {
  const editor = vscode.window.activeTextEditor;
  if (!editor) {
    vscode.window.showWarningMessage("No active file.");
    return;
  }

  const webTemplatePath = await resolveWebTemplate(editor.document.uri);
  if (!webTemplatePath) {
    vscode.window.showWarningMessage("No Web Template found.");
    return;
  }

  const config = getConfig();
  const paths = enumerateValidPathStrings(webTemplatePath, config.platform);
  if (!paths) {
    vscode.window.showErrorMessage(
      "Failed to retrieve valid paths: could not parse the Web Template.",
    );
    return;
  }

  outputChannel.clear();
  outputChannel.appendLine(
    `Valid FLAT paths (${config.platform}, ${paths.length} total):\n`,
  );
  for (const path of paths) {
    outputChannel.appendLine(path);
  }
  outputChannel.show();
}

/**
 * Run OPT validation on the currently active editor.
 */
async function runOptValidation(isManual: boolean): Promise<void> {
  const editor = vscode.window.activeTextEditor;
  if (!editor) {
    if (isManual) {
      vscode.window.showWarningMessage("No active file to validate.");
    }
    return;
  }
  await runOptValidationFor(editor.document, isManual);
}

/**
 * Validate a specific OPT document via the Python CLI and publish diagnostics.
 *
 * Degrades gracefully: no-ops when OPT validation is disabled, the file isn't
 * an OPT template, it isn't saved to disk, or Python/oehrpy is unavailable
 * (showing a one-time hint in the last case). FLAT validation is unaffected.
 */
async function runOptValidationFor(
  document: vscode.TextDocument,
  isManual: boolean,
): Promise<void> {
  const config = getConfig();
  if (!config.enableOptValidation) {
    if (isManual) {
      vscode.window.showInformationMessage(
        "OPT validation is disabled (oehrpy.enableOptValidation).",
      );
    }
    return;
  }

  if (!classifyOptDocument(document.fileName, document.getText())) {
    if (isManual) {
      vscode.window.showWarningMessage(
        "Active file is not an OPT template (.opt or openEHR <template> XML).",
      );
    }
    return;
  }

  if (document.uri.scheme !== "file") {
    if (isManual) {
      vscode.window.showWarningMessage(
        "OPT validation requires the file to be saved to disk.",
      );
    }
    return;
  }

  // The CLI reads from disk; ensure manual runs validate current content.
  if (isManual && document.isDirty) {
    await document.save();
  }

  try {
    const pythonPath = await discoverPythonPath();
    const outcome = await validateOptFile(
      pythonPath,
      document.uri.fsPath,
      config.optValidationTimeout,
    );

    if (outcome.kind === "ok") {
      publishOptDiagnostics(document, outcome.result, optDiagnosticCollection);
      if (isManual) {
        const { error_count, warning_count, is_valid } = outcome.result;
        vscode.window.showInformationMessage(
          is_valid
            ? `OPT valid (${warning_count} warning(s)).`
            : `OPT invalid: ${error_count} error(s), ${warning_count} warning(s).`,
        );
      }
      return;
    }

    optDiagnosticCollection.delete(document.uri);

    if (outcome.kind === "unavailable") {
      showOptUnavailableHint(isManual);
      return;
    }

    if (isManual) {
      vscode.window.showErrorMessage(`OPT validation failed: ${outcome.detail}`);
    }
  } catch (error) {
    if (isManual) {
      const message = error instanceof Error ? error.message : "Unknown error";
      vscode.window.showErrorMessage(`OPT validation failed: ${message}`);
    }
  }
}

/**
 * Show a one-time hint that OPT validation needs Python + oehrpy. Manual
 * invocations always surface it; automatic ones show it at most once.
 */
function showOptUnavailableHint(isManual: boolean): void {
  if (optUnavailableHintShown && !isManual) {
    return;
  }
  optUnavailableHintShown = true;

  void vscode.window
    .showInformationMessage(
      "OPT (.opt/.xml) validation needs Python with oehrpy installed. " +
        "FLAT validation works without it.",
      "Install oehrpy",
      "Set Python Path",
    )
    .then((choice) => {
      if (choice === "Install oehrpy") {
        const terminal = vscode.window.createTerminal("oehrpy install");
        terminal.sendText("pip install oehrpy");
        terminal.show();
      } else if (choice === "Set Python Path") {
        void vscode.commands.executeCommand(
          "workbench.action.openSettings",
          "oehrpy.pythonPath",
        );
      }
    });
}
