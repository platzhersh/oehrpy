import * as vscode from "vscode";
import * as fs from "fs";
import { getConfig } from "./config";
import { classifyDocument } from "./detector";
import {
  enumeratePathsFromTree,
  findJsonKeyBounds,
  type FlatPathEntry,
  type WebTemplateTreeNode,
} from "./flatPaths";
import { resolveWebTemplate } from "./templateResolver";

export { enumeratePathsFromTree, findJsonKeyBounds, type FlatPathEntry, type WebTemplateTreeNode } from "./flatPaths";

const pathsCache = new Map<string, { paths: FlatPathEntry[]; mtime: number }>();

function loadPaths(webTemplatePath: string): FlatPathEntry[] | undefined {
  try {
    const stat = fs.statSync(webTemplatePath);
    const mtime = stat.mtimeMs;
    const cached = pathsCache.get(webTemplatePath);
    if (cached && cached.mtime === mtime) {
      return cached.paths;
    }

    const content = fs.readFileSync(webTemplatePath, "utf-8");
    const parsed = JSON.parse(content) as Record<string, unknown>;
    if (
      !parsed ||
      typeof parsed !== "object" ||
      !parsed.tree ||
      typeof parsed.tree !== "object"
    ) {
      return undefined;
    }

    const paths = enumeratePathsFromTree(
      parsed.tree as WebTemplateTreeNode,
    );
    pathsCache.set(webTemplatePath, { paths, mtime });
    return paths;
  } catch {
    return undefined;
  }
}

function escapeMarkdown(text: string): string {
  return text.replace(/[\\`*_{}[\]()#+\-.!|]/g, "\\$&");
}

export class FlatPathCompletionProvider
  implements vscode.CompletionItemProvider
{
  async provideCompletionItems(
    document: vscode.TextDocument,
    position: vscode.Position,
    token: vscode.CancellationToken,
  ): Promise<vscode.CompletionItem[] | undefined> {
    const config = getConfig();
    if (!config.enableAutocomplete) {
      return undefined;
    }

    const classification = classifyDocument(document);
    if (classification !== "flat_composition") {
      return undefined;
    }

    const line = document.lineAt(position.line).text;
    const bounds = findJsonKeyBounds(line, position.character);
    if (!bounds) {
      return undefined;
    }

    const replaceRange = new vscode.Range(
      new vscode.Position(position.line, bounds.startChar),
      new vscode.Position(position.line, bounds.endChar),
    );

    const webTemplatePath = await resolveWebTemplate(document.uri);
    if (!webTemplatePath || token.isCancellationRequested) {
      return undefined;
    }

    const paths = loadPaths(webTemplatePath);
    if (!paths || token.isCancellationRequested) {
      return undefined;
    }

    return paths.map((entry, index) => {
      const item = new vscode.CompletionItem(
        entry.fullPath,
        vscode.CompletionItemKind.Field,
      );
      item.sortText = String(index).padStart(6, "0");
      item.detail = entry.rmType;

      const required = entry.min > 0 ? "Yes" : "No";
      const maxStr = entry.max === -1 ? "*" : String(entry.max);
      const doc = new vscode.MarkdownString();
      doc.isTrusted = false;
      doc.supportHtml = false;
      doc.appendMarkdown(
        `**${escapeMarkdown(entry.nodeName)}**\n\n`,
      );
      doc.appendMarkdown(
        `RM Type: \`${escapeMarkdown(entry.rmType)}\`\n\n`,
      );
      doc.appendMarkdown(
        `Required: ${required} (${entry.min}..${maxStr})\n\n`,
      );
      if (entry.suffix) {
        doc.appendMarkdown(`Suffix: \`${entry.suffix}\``);
      }
      item.documentation = doc;

      item.range = replaceRange;
      item.filterText = entry.fullPath;
      return item;
    });
  }
}
