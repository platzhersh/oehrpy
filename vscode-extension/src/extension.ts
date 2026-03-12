import * as vscode from "vscode";
import { getConfig } from "./config";
import { classifyDocument } from "./detector";
import {
  clearDiagnostics,
  publishDiagnostics,
} from "./diagnostics";
import { FlatPathHoverProvider } from "./hover";
import { FlatPathQuickFixProvider } from "./quickfix";
import { OehrpyStatusBar } from "./statusBar";
import {
  resolveWebTemplate,
  promptForWebTemplate,
  setTemplateAssociation,
} from "./templateResolver";
import {
  discoverPythonPath,
  checkOehrpyInstalled,
  offerInstallOehrpy,
  validateWithCli,
} from "./validator";

let diagnosticCollection: vscode.DiagnosticCollection;
let statusBar: OehrpyStatusBar;
let debounceTimer: ReturnType<typeof setTimeout> | undefined;
let currentValidationAbort: AbortController | undefined;

export function activate(context: vscode.ExtensionContext): void {
  // Create diagnostic collection
  diagnosticCollection = vscode.languages.createDiagnosticCollection(
    "oehrpy-flat-validator",
  );
  context.subscriptions.push(diagnosticCollection);

  // Create status bar
  statusBar = new OehrpyStatusBar();
  context.subscriptions.push(statusBar);

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

  // Validate on save
  context.subscriptions.push(
    vscode.workspace.onDidSaveTextDocument((document) => {
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

  // Check oehrpy installation on activation
  checkInstallation();

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
  if (currentValidationAbort) {
    currentValidationAbort.abort();
  }
}

/**
 * Run validation on the currently active JSON file.
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

  // Cancel any in-flight validation
  if (currentValidationAbort) {
    currentValidationAbort.abort();
  }
  currentValidationAbort = new AbortController();

  statusBar.setState("validating");

  try {
    // Discover Python
    const pythonPath = await discoverPythonPath();

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
    const result = await validateWithCli(
      pythonPath,
      webTemplatePath,
      document.getText(),
      config.platform,
      config.validationTimeout,
    );

    // Check if validation was cancelled
    if (currentValidationAbort.signal.aborted) {
      return;
    }

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
    if (currentValidationAbort.signal.aborted) {
      return;
    }

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

  try {
    const pythonPath = await discoverPythonPath();
    const config = getConfig();

    const { execFile } = await import("child_process");
    const { promisify } = await import("util");
    const execFileAsync = promisify(execFile);

    const { stdout } = await execFileAsync(
      pythonPath,
      [
        "-m",
        "openehr_sdk.validation",
        "show-paths",
        "--web-template",
        webTemplatePath,
        "--platform",
        config.platform,
      ],
      { timeout: config.validationTimeout },
    );

    // Show in output channel
    const channel = vscode.window.createOutputChannel("oehrpy Valid Paths");
    channel.clear();
    channel.appendLine(`Valid FLAT paths for template:\n`);
    channel.appendLine(stdout);
    channel.show();
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown error";
    vscode.window.showErrorMessage(
      `Failed to retrieve valid paths: ${message}`,
    );
  }
}

/**
 * Check if oehrpy is installed and offer to install if not.
 */
async function checkInstallation(): Promise<void> {
  try {
    const pythonPath = await discoverPythonPath();
    const installed = await checkOehrpyInstalled(pythonPath);
    if (!installed) {
      offerInstallOehrpy();
    }
  } catch {
    // Silently ignore — will show error when user tries to validate
  }
}
