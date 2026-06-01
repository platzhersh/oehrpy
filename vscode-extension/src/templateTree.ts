import * as vscode from "vscode";
import * as fs from "fs";
import * as path from "path";
import { getConfig } from "./config";
import { classifyDocument } from "./detector";
import { resolveWebTemplate } from "./templateResolver";
import {
  formatCardinality,
  parseTemplateTree,
  type TemplateTreeNode,
} from "./webTemplate";

/** Context key toggled to control visibility of the tree view. */
export const HAS_WEB_TEMPLATE_CONTEXT = "oehrpy.hasWebTemplate";

interface LoadedTemplate {
  root: TemplateTreeNode;
  templateId: string;
  sourcePath: string;
}

/**
 * Loads a Web Template from disk and parses its `tree`.
 *
 * Returns `undefined` if the file is missing, unparseable, or does not look
 * like a Web Template.
 */
function loadTemplate(filePath: string): LoadedTemplate | undefined {
  try {
    const content = fs.readFileSync(filePath, "utf-8");
    const parsed = JSON.parse(content) as Record<string, unknown>;
    const tree = parsed?.tree;
    if (!tree || typeof tree !== "object") {
      return undefined;
    }

    const root = parseTemplateTree(tree as Parameters<typeof parseTemplateTree>[0]);
    const templateId =
      (typeof parsed.templateId === "string" && parsed.templateId) ||
      root.id ||
      path.basename(filePath);

    return { root, templateId, sourcePath: filePath };
  } catch {
    return undefined;
  }
}

/**
 * Tree data provider backing the "openEHR Web Template" explorer view.
 *
 * It mirrors the Web Template `tree` structure as a collapsible tree, showing
 * each node's name, RM type, and cardinality. The tree follows whichever
 * Web Template is resolvable for the active editor (a Web Template file shows
 * itself; a FLAT composition shows its resolved template).
 */
export class WebTemplateTreeProvider
  implements vscode.TreeDataProvider<TemplateTreeNode>
{
  private readonly _onDidChangeTreeData = new vscode.EventEmitter<
    TemplateTreeNode | undefined | void
  >();
  readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

  private loaded: LoadedTemplate | undefined;

  /** The path of the Web Template currently displayed, if any. */
  get sourcePath(): string | undefined {
    return this.loaded?.sourcePath;
  }

  /**
   * Resolve and load the Web Template for the active editor, then refresh the
   * tree and update the `oehrpy.hasWebTemplate` context key accordingly.
   */
  async syncWithActiveEditor(): Promise<void> {
    const config = getConfig();
    if (!config.enableTemplateExplorer) {
      this.setTemplate(undefined);
      return;
    }

    const editor = vscode.window.activeTextEditor;
    if (!editor || editor.document.languageId !== "json") {
      // Keep showing the last template so the panel doesn't flicker empty
      // when focus moves to a non-JSON editor or the panel itself.
      return;
    }

    const templatePath = await this.resolveTemplatePath(editor.document);
    if (!templatePath) {
      return;
    }

    if (templatePath === this.loaded?.sourcePath) {
      return;
    }

    this.setTemplate(loadTemplate(templatePath));
  }

  private async resolveTemplatePath(
    document: vscode.TextDocument,
  ): Promise<string | undefined> {
    // A Web Template file shows its own structure.
    if (
      classifyDocument(document) === "web_template" &&
      document.uri.scheme === "file"
    ) {
      return document.uri.fsPath;
    }
    // Otherwise resolve the template associated with the composition.
    return resolveWebTemplate(document.uri);
  }

  /** Reload the currently displayed template from disk (e.g. after a save). */
  reload(): void {
    if (this.loaded) {
      this.setTemplate(loadTemplate(this.loaded.sourcePath));
    } else {
      void this.syncWithActiveEditor();
    }
  }

  private setTemplate(loaded: LoadedTemplate | undefined): void {
    this.loaded = loaded;
    void vscode.commands.executeCommand(
      "setContext",
      HAS_WEB_TEMPLATE_CONTEXT,
      loaded !== undefined,
    );
    this._onDidChangeTreeData.fire();
  }

  getTreeItem(node: TemplateTreeNode): vscode.TreeItem {
    const hasChildren = node.children.length > 0;
    const item = new vscode.TreeItem(
      node.name,
      hasChildren
        ? vscode.TreeItemCollapsibleState.Collapsed
        : vscode.TreeItemCollapsibleState.None,
    );

    const cardinality = formatCardinality(node.min, node.max);
    item.description = node.rmType ? `${node.rmType}  ${cardinality}` : cardinality;
    item.iconPath = new vscode.ThemeIcon(
      node.isStructural ? "symbol-namespace" : "symbol-field",
    );
    item.contextValue = node.isStructural
      ? "oehrpyTemplateContainer"
      : "oehrpyTemplateLeaf";

    const tooltip = new vscode.MarkdownString();
    tooltip.isTrusted = false;
    tooltip.supportHtml = false;
    tooltip.appendCodeblock(node.flatPath, "text");
    tooltip.appendMarkdown("\n\n");
    if (node.rmType) {
      tooltip.appendMarkdown(`**RM Type:** \`${node.rmType}\`\n\n`);
    }
    tooltip.appendMarkdown(`**Required:** ${node.min > 0 ? "Yes" : "No"}  `);
    tooltip.appendMarkdown(`(${cardinality})`);
    if (node.validSuffixes.length > 0) {
      tooltip.appendMarkdown("\n\n**Valid suffixes:** ");
      tooltip.appendMarkdown(
        node.validSuffixes.map((s) => `\`${s}\``).join(", "),
      );
    }
    item.tooltip = tooltip;

    // Single-click copies the FLAT path to the clipboard. Expansion still
    // works via the twistie / Enter key.
    item.command = {
      command: "oehrpy.copyFlatPath",
      title: "Copy FLAT Path",
      arguments: [node],
    };

    return item;
  }

  getChildren(node?: TemplateTreeNode): TemplateTreeNode[] {
    if (!this.loaded) {
      return [];
    }
    if (!node) {
      return [this.loaded.root];
    }
    return node.children;
  }
}
