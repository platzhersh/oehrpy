import * as vscode from "vscode";
import { getConfig } from "./config";
import type { DiagnosticWithData } from "./diagnostics";

/**
 * Code action provider that offers quick fixes for FLAT validation errors.
 *
 * When a diagnostic has a suggestion, it provides a "Replace with ..." fix
 * that updates the JSON key in-place.
 */
export class FlatPathQuickFixProvider implements vscode.CodeActionProvider {
  public static readonly providedCodeActionKinds = [
    vscode.CodeActionKind.QuickFix,
  ];

  provideCodeActions(
    document: vscode.TextDocument,
    range: vscode.Range,
    context: vscode.CodeActionContext,
  ): vscode.CodeAction[] {
    const config = getConfig();
    if (!config.enableQuickFix) {
      return [];
    }

    const actions: vscode.CodeAction[] = [];

    for (const diagnostic of context.diagnostics) {
      if (diagnostic.source !== "oehrpy") {
        continue;
      }

      const data = (diagnostic as DiagnosticWithData).data;
      if (!data?.suggestion) {
        continue;
      }

      // Create the primary quick fix
      const fix = new vscode.CodeAction(
        `Replace with '${data.suggestion}'`,
        vscode.CodeActionKind.QuickFix,
      );

      fix.edit = new vscode.WorkspaceEdit();
      fix.edit.replace(document.uri, diagnostic.range, data.suggestion);
      fix.isPreferred = true;
      fix.diagnostics = [diagnostic];

      actions.push(fix);

      // Add alternative suggestions if available
      if (data.validAlternatives && data.validAlternatives.length > 1) {
        for (const alt of data.validAlternatives.slice(1, 4)) {
          if (alt === data.suggestion) {
            continue;
          }

          const altFix = new vscode.CodeAction(
            `Replace with '${alt}'`,
            vscode.CodeActionKind.QuickFix,
          );

          altFix.edit = new vscode.WorkspaceEdit();
          altFix.edit.replace(document.uri, diagnostic.range, alt);
          altFix.diagnostics = [diagnostic];

          actions.push(altFix);
        }
      }
    }

    return actions;
  }
}
