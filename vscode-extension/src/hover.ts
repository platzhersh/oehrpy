import * as vscode from "vscode";
import { getConfig } from "./config";
import { resolveWebTemplate } from "./templateResolver";
import { discoverPythonPath, inspectPathWithCli } from "./validator";

/**
 * FLAT path pattern to detect hoverable keys in JSON.
 * Matches strings that look like FLAT paths: word/word (with optional :N and |suffix).
 */
const FLAT_PATH_PATTERN = /^[a-z][a-z0-9_]*(?::\d+)?(?:\/[a-z][a-z0-9_]*(?::\d+)?)+(?:\|[a-z_]+)?$/;

/**
 * Hover provider that shows FLAT path documentation when hovering over
 * a FLAT key in a JSON file.
 */
export class FlatPathHoverProvider implements vscode.HoverProvider {
  async provideHover(
    document: vscode.TextDocument,
    position: vscode.Position,
  ): Promise<vscode.Hover | undefined> {
    const config = getConfig();
    if (!config.enableHover) {
      return undefined;
    }

    // Get the word range at the cursor position, extended to cover FLAT paths
    const range = getFlatPathRangeAtPosition(document, position);
    if (!range) {
      return undefined;
    }

    const text = document.getText(range);
    if (!FLAT_PATH_PATTERN.test(text)) {
      return undefined;
    }

    // Strip |suffix for path lookup
    const basePath = text.split("|")[0];

    // Resolve the web template
    const webTemplatePath = await resolveWebTemplate(document.uri);
    if (!webTemplatePath) {
      return undefined;
    }

    // Get path info from CLI
    const pythonPath = await discoverPythonPath();
    const inspectResult = await inspectPathWithCli(
      pythonPath,
      webTemplatePath,
      basePath,
      config.validationTimeout,
    );

    if (!inspectResult) {
      return undefined;
    }

    // Build hover markdown
    const maxStr = inspectResult.max === -1 ? "*" : String(inspectResult.max);
    const requiredStr = inspectResult.min > 0 ? "Yes" : "No";

    const md = new vscode.MarkdownString();
    md.isTrusted = true;
    md.appendCodeblock(text, "text");
    md.appendMarkdown("\n\n");
    md.appendMarkdown(`**Node:** \`${inspectResult.id}\`\n\n`);
    md.appendMarkdown(`**Name:** ${inspectResult.name}\n\n`);
    md.appendMarkdown(`**RM Type:** \`${inspectResult.rm_type}\`\n\n`);
    md.appendMarkdown(
      `**Required:** ${requiredStr} (min: ${inspectResult.min}, max: ${maxStr})\n\n`,
    );

    if (inspectResult.valid_suffixes.length > 0) {
      md.appendMarkdown("**Valid suffixes:**\n\n");
      for (const suffix of inspectResult.valid_suffixes) {
        md.appendMarkdown(`- \`${suffix}\`\n`);
      }
    }

    return new vscode.Hover(md, range);
  }
}

/**
 * Get the range of a FLAT path string at the given position.
 * This handles the fact that FLAT paths contain `/` and `|` characters
 * which are not part of the default word pattern.
 */
function getFlatPathRangeAtPosition(
  document: vscode.TextDocument,
  position: vscode.Position,
): vscode.Range | undefined {
  const line = document.lineAt(position.line).text;

  // Find the quoted string containing the position
  let inString = false;
  let stringStart = -1;

  for (let i = 0; i < line.length; i++) {
    if (line[i] === '"' && (i === 0 || line[i - 1] !== "\\")) {
      if (inString) {
        // End of string
        if (position.character > stringStart && position.character <= i) {
          // Position is within this string
          const start = new vscode.Position(position.line, stringStart + 1);
          const end = new vscode.Position(position.line, i);
          return new vscode.Range(start, end);
        }
        inString = false;
      } else {
        // Start of string
        inString = true;
        stringStart = i;
      }
    }
  }

  return undefined;
}
