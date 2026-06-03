/**
 * Map OPT validation issues to VS Code diagnostics. Detection and
 * position-finding live in the vscode-free `optModel.ts`.
 */

import * as vscode from "vscode";
import {
  formatOptMessage,
  locateOptIssue,
  type OptIssue,
  type OptValidationResult,
} from "./optModel";

export { classifyOptDocument } from "./optModel";

function severityOf(issue: OptIssue): vscode.DiagnosticSeverity {
  if (issue.category === "flat_impact") {
    // FLAT-path-impact notes are informational; surface them as Hints so they
    // don't clutter the Problems panel as errors/warnings.
    return vscode.DiagnosticSeverity.Hint;
  }
  switch (issue.severity) {
    case "error":
      return vscode.DiagnosticSeverity.Error;
    case "warning":
      return vscode.DiagnosticSeverity.Warning;
    case "info":
    default:
      return vscode.DiagnosticSeverity.Information;
  }
}

function rangeFor(document: vscode.TextDocument, issue: OptIssue): vscode.Range {
  const located = locateOptIssue(document.getText(), issue);
  if (!located) {
    // File-level fallback: highlight the first line.
    return document.lineAt(0).range;
  }
  return new vscode.Range(
    document.positionAt(located.start),
    document.positionAt(located.end),
  );
}

/**
 * Convert an OPT validation result into diagnostics and publish them.
 */
export function publishOptDiagnostics(
  document: vscode.TextDocument,
  result: OptValidationResult,
  collection: vscode.DiagnosticCollection,
): void {
  const diagnostics: vscode.Diagnostic[] = result.issues.map((issue) => {
    const diagnostic = new vscode.Diagnostic(
      rangeFor(document, issue),
      formatOptMessage(issue),
      severityOf(issue),
    );
    diagnostic.source = "oehrpy";
    diagnostic.code = issue.code;
    return diagnostic;
  });

  collection.set(document.uri, diagnostics);
}
