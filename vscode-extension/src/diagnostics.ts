import * as vscode from "vscode";
import type { CliValidationError, CliValidationResult } from "./validator";

/**
 * Find the exact range of a JSON key string in a document.
 *
 * Searches for the key surrounded by quotes followed by a colon.
 * Falls back to line 0 if the key is not found.
 */
export function findKeyRange(
  document: vscode.TextDocument,
  key: string,
): vscode.Range {
  const text = document.getText();
  const escaped = key.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const regex = new RegExp(`"(${escaped})"\\s*:`);
  const match = regex.exec(text);

  if (!match) {
    // Fall back to line-level diagnostic at line 0
    return new vscode.Range(0, 0, 0, 0);
  }

  const start = document.positionAt(match.index + 1); // skip opening quote
  const end = document.positionAt(match.index + 1 + key.length);
  return new vscode.Range(start, end);
}

/**
 * Map a CLI validation error to a VS Code Diagnostic severity.
 */
function errorTypeToSeverity(
  errorType: CliValidationError["error_type"],
): vscode.DiagnosticSeverity {
  switch (errorType) {
    case "unknown_path":
    case "wrong_suffix":
    case "index_mismatch":
      return vscode.DiagnosticSeverity.Error;
    case "missing_required":
      return vscode.DiagnosticSeverity.Warning;
    default:
      return vscode.DiagnosticSeverity.Error;
  }
}

/**
 * Format the diagnostic message including suggestion if available.
 */
function formatDiagnosticMessage(error: CliValidationError): string {
  let message = error.message;

  if (error.suggestion) {
    message += `\n\nDid you mean:\n  ${error.suggestion}`;
  }

  return message;
}

/**
 * Convert CLI validation results to VS Code Diagnostic objects and publish them.
 */
export function publishDiagnostics(
  document: vscode.TextDocument,
  result: CliValidationResult,
  diagnosticCollection: vscode.DiagnosticCollection,
): void {
  const diagnostics: vscode.Diagnostic[] = [];

  // Process errors
  for (const error of result.errors) {
    const range = findKeyRange(document, error.path);
    const diagnostic = new vscode.Diagnostic(
      range,
      formatDiagnosticMessage(error),
      errorTypeToSeverity(error.error_type),
    );
    diagnostic.source = "oehrpy";
    diagnostic.code = error.error_type;

    // Store suggestion and error data for quick fix provider
    if (error.suggestion) {
      diagnostic.relatedInformation = [];
      // Store the suggestion in the diagnostic data for quick fix access
      (diagnostic as DiagnosticWithData).data = {
        suggestion: error.suggestion,
        originalPath: error.path,
        validAlternatives: error.valid_alternatives,
      };
    }

    diagnostics.push(diagnostic);
  }

  // Process warnings
  for (const warning of result.warnings) {
    const range = findKeyRange(document, warning.path);
    const diagnostic = new vscode.Diagnostic(
      range,
      formatDiagnosticMessage(warning),
      errorTypeToSeverity(warning.error_type),
    );
    diagnostic.source = "oehrpy";
    diagnostic.code = warning.error_type;
    diagnostics.push(diagnostic);
  }

  diagnosticCollection.set(document.uri, diagnostics);
}

/**
 * Clear diagnostics for a document.
 */
export function clearDiagnostics(
  document: vscode.TextDocument,
  diagnosticCollection: vscode.DiagnosticCollection,
): void {
  diagnosticCollection.delete(document.uri);
}

/**
 * Extended diagnostic type that carries suggestion data for quick fixes.
 */
export interface DiagnosticData {
  suggestion: string;
  originalPath: string;
  validAlternatives: string[];
}

export interface DiagnosticWithData extends vscode.Diagnostic {
  data?: DiagnosticData;
}
