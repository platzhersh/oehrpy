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

let diagnosticCollection: vscode.DiagnosticCollection;
let statusBar: OehrpyStatusBar;
let templateTreeProvider: WebTemplateTreeProvider;
let outputChannel: vscode.OutputChannel;
let debounceTimer: ReturnType<typeof setTimeout> | undefined;

export function activate(context: vscode.ExtensionContext): void {
  // Initialize template resolver with persistent workspace state
  initTemplateResolver(context.workspaceState);

  // Create diagnostic collection
  diagnosticCollection = vscode.languages.createDiagnosticCollection(
    "oehrpy-flat-validator",
  );
  context.subscriptions.push(diagnosticCollection);

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
    }),
  );

  // Populate the Web Template tree for the current file
  void templateTreeProvider.syncWithActiveEditor();

  // Validate current file if it's a FLAT composition
  const activeEditor = vscode.window.activeTextEditor;
  if (activeEditor && activeEditor.document.languageId === "json") {
    const classification = classifyDocument(activeEditor.document);
    if (classification === "flat_composition") {
      runValidation(false);
    }
  }
}

export function deactivate(): void {
  if (debounceTimer) {
    clearTimeout(debounceTimer);
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
