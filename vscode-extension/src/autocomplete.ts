import * as vscode from "vscode";
import * as fs from "fs";
import { getConfig } from "./config";
import { classifyDocument } from "./detector";
import { resolveWebTemplate } from "./templateResolver";

interface WebTemplateTreeNode {
  id: string;
  name?: string;
  rmType?: string;
  rm_type?: string;
  min?: number;
  max?: number;
  children?: WebTemplateTreeNode[];
}

export interface FlatPathEntry {
  fullPath: string;
  nodeName: string;
  rmType: string;
  min: number;
  max: number;
  suffix: string | null;
}

const STRUCTURAL_RM_TYPES = new Set([
  "COMPOSITION",
  "SECTION",
  "OBSERVATION",
  "EVALUATION",
  "INSTRUCTION",
  "ACTION",
  "ADMIN_ENTRY",
  "CLUSTER",
  "HISTORY",
  "EVENT",
  "POINT_EVENT",
  "INTERVAL_EVENT",
  "ITEM_TREE",
  "ITEM_LIST",
  "ITEM_SINGLE",
  "ITEM_TABLE",
  "ELEMENT",
  "EVENT_CONTEXT",
  "ACTIVITY",
  "ISM_TRANSITION",
  "INSTRUCTION_DETAILS",
]);

const VALID_SUFFIXES: Record<string, string[]> = {
  DV_QUANTITY: ["|magnitude", "|unit", "|precision", "|normal_range", "|normal_status"],
  DV_CODED_TEXT: ["|value", "|code", "|terminology", "|preferred_term"],
  DV_TEXT: ["|value"],
  DV_DATE_TIME: [],
  DV_DATE: [],
  DV_TIME: [],
  DV_BOOLEAN: [],
  DV_COUNT: ["|magnitude", "|accuracy", "|accuracy_is_percent"],
  DV_ORDINAL: ["|value", "|code", "|terminology", "|ordinal"],
  DV_SCALE: ["|value", "|code", "|terminology", "|symbol_value"],
  DV_PROPORTION: ["|numerator", "|denominator", "|type", "|precision"],
  DV_DURATION: [],
  DV_IDENTIFIER: ["|id", "|type", "|issuer", "|assigner"],
  DV_URI: [],
  DV_EHR_URI: [],
  DV_MULTIMEDIA: ["|mediatype", "|alternatetext", "|uri", "|size"],
  DV_PARSABLE: ["|value", "|formalism"],
  CODE_PHRASE: ["|code", "|terminology"],
  PARTY_IDENTIFIED: ["|name", "|id"],
  PARTY_RELATED: ["|name", "|id", "|relationship"],
  PARTY_SELF: [],
};

const pathsCache = new Map<string, { paths: FlatPathEntry[]; mtime: number }>();

export function enumeratePathsFromTree(
  tree: WebTemplateTreeNode,
): FlatPathEntry[] {
  const entries: FlatPathEntry[] = [];

  function traverse(node: WebTemplateTreeNode, prefix: string): void {
    const nodeId = node.id || "";
    const currentPath = prefix ? `${prefix}/${nodeId}` : nodeId;
    const rmType = node.rmType || node.rm_type || "";
    const nodeName = node.name || nodeId;
    const min = node.min ?? 0;
    const max = node.max ?? 1;

    if (!STRUCTURAL_RM_TYPES.has(rmType)) {
      entries.push({
        fullPath: currentPath,
        nodeName,
        rmType,
        min,
        max,
        suffix: null,
      });

      const suffixes = VALID_SUFFIXES[rmType];
      if (suffixes) {
        for (const suffix of suffixes) {
          entries.push({
            fullPath: currentPath + suffix,
            nodeName,
            rmType,
            min,
            max,
            suffix,
          });
        }
      }
    }

    if (node.children) {
      for (const child of node.children) {
        traverse(child, currentPath);
      }
    }
  }

  traverse(tree, "");
  entries.sort((a, b) => a.fullPath.localeCompare(b.fullPath));
  return entries;
}

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

interface KeyContext {
  replaceRange: vscode.Range;
}

function isPrecededByOddBackslashes(str: string, index: number): boolean {
  let count = 0;
  for (let i = index - 1; i >= 0 && str[i] === "\\"; i--) {
    count++;
  }
  return count % 2 === 1;
}

export function getJsonKeyRange(
  lineText: string,
  lineNumber: number,
  charIndex: number,
): KeyContext | undefined {
  let openQuote = -1;
  for (let i = charIndex - 1; i >= 0; i--) {
    if (lineText[i] === '"' && !isPrecededByOddBackslashes(lineText, i)) {
      openQuote = i;
      break;
    }
    if (lineText[i] === ":" || lineText[i] === "}" || lineText[i] === "]") {
      return undefined;
    }
  }

  if (openQuote === -1) {
    return undefined;
  }

  const beforeQuote = lineText.slice(0, openQuote).trimEnd();
  if (beforeQuote.endsWith(":")) {
    return undefined;
  }

  let closeQuote = -1;
  for (let i = charIndex; i < lineText.length; i++) {
    if (lineText[i] === '"' && !isPrecededByOddBackslashes(lineText, i)) {
      closeQuote = i;
      break;
    }
  }

  const start = { line: lineNumber, char: openQuote + 1 };
  const end =
    closeQuote !== -1
      ? { line: lineNumber, char: closeQuote }
      : { line: lineNumber, char: charIndex };

  return {
    replaceRange: new vscode.Range(
      new vscode.Position(start.line, start.char),
      new vscode.Position(end.line, end.char),
    ),
  };
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
    const keyCtx = getJsonKeyRange(line, position.line, position.character);
    if (!keyCtx) {
      return undefined;
    }

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

      item.range = keyCtx.replaceRange;
      item.filterText = entry.fullPath;
      return item;
    });
  }
}
