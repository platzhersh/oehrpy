import * as vscode from "vscode";
import { getConfig } from "./config";
import { FLAT_PATH_PATTERN } from "./patterns";
import { resolveWebTemplate } from "./templateResolver";
import { inspectFlatPath } from "./validator";

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

    // Inspect the path in-process (parsed templates are cached by mtime).
    const inspectResult = inspectFlatPath(webTemplatePath, basePath);
    if (!inspectResult) {
      return undefined;
    }

    // Build hover markdown
    const maxStr = inspectResult.max === -1 ? "*" : String(inspectResult.max);
    const requiredStr = inspectResult.min > 0 ? "Yes" : "No";

    const md = new vscode.MarkdownString();
    md.isTrusted = false;
    md.supportHtml = false;
    md.appendCodeblock(text, "text");
    md.appendMarkdown("\n\n");
    md.appendMarkdown(`**Node:** \`${escapeMarkdown(inspectResult.id)}\`\n\n`);
    md.appendMarkdown(`**Name:** ${escapeMarkdown(inspectResult.name)}\n\n`);
    md.appendMarkdown(`**RM Type:** \`${escapeMarkdown(inspectResult.rm_type)}\`\n\n`);
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
    if (line[i] === '"' && !isPrecededByOddBackslashes(line, i)) {
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

function isPrecededByOddBackslashes(str: string, index: number): boolean {
  let count = 0;
  for (let i = index - 1; i >= 0 && str[i] === "\\"; i--) {
    count++;
  }
  return count % 2 === 1;
}

function escapeMarkdown(text: string): string {
  return text.replace(/[\\`*_{}[\]()#+\-.!|]/g, "\\$&");
}
