import * as vscode from "vscode";
import * as path from "path";
import * as fs from "fs";
import { getConfig } from "./config";

/**
 * File-to-template mapping stored in workspace state.
 */
const templateAssociations = new Map<string, string>();

/**
 * Resolve the Web Template file path for a given FLAT composition file.
 *
 * Resolution order:
 * 1. Explicit config (oehrpy.webTemplatePaths)
 * 2. Same directory (web_template.json or *.wt.json)
 * 3. Project root (web_templates/ or templates/ directory)
 * 4. Stored association from previous user selection
 */
export async function resolveWebTemplate(
  compositionUri: vscode.Uri,
): Promise<string | undefined> {
  // 1. Check explicit config
  const configResult = resolveFromConfig();
  if (configResult) {
    return configResult;
  }

  // 2. Check same directory
  const dirResult = await resolveFromSameDirectory(compositionUri);
  if (dirResult) {
    return dirResult;
  }

  // 3. Check project root directories
  const rootResult = await resolveFromProjectRoot();
  if (rootResult) {
    return rootResult;
  }

  // 4. Check stored associations
  const stored = templateAssociations.get(compositionUri.fsPath);
  if (stored && fs.existsSync(stored)) {
    return stored;
  }

  return undefined;
}

/**
 * Prompt the user to select a Web Template file and remember the choice.
 */
export async function promptForWebTemplate(
  compositionUri: vscode.Uri,
): Promise<string | undefined> {
  const result = await vscode.window.showInformationMessage(
    "No Web Template found for this FLAT composition. Select one?",
    "Choose Web Template",
    "Cancel",
  );

  if (result !== "Choose Web Template") {
    return undefined;
  }

  const files = await vscode.window.showOpenDialog({
    canSelectFiles: true,
    canSelectMany: false,
    filters: {
      "Web Template": ["json"],
    },
    title: "Select Web Template JSON file",
  });

  if (!files || files.length === 0) {
    return undefined;
  }

  const templatePath = files[0].fsPath;
  templateAssociations.set(compositionUri.fsPath, templatePath);
  return templatePath;
}

/**
 * Set a template association for a composition file.
 */
export function setTemplateAssociation(
  compositionPath: string,
  templatePath: string,
): void {
  templateAssociations.set(compositionPath, templatePath);
}

function resolveFromConfig(): string | undefined {
  const config = getConfig();
  const paths = config.webTemplatePaths;

  // Return the first configured path that exists
  for (const templateId of Object.keys(paths)) {
    const templatePath = paths[templateId];
    const resolved = resolveWorkspacePath(templatePath);
    if (resolved && fs.existsSync(resolved)) {
      return resolved;
    }
  }

  return undefined;
}

async function resolveFromSameDirectory(
  compositionUri: vscode.Uri,
): Promise<string | undefined> {
  const dir = path.dirname(compositionUri.fsPath);

  // Check for web_template.json
  const webTemplatePath = path.join(dir, "web_template.json");
  if (fs.existsSync(webTemplatePath)) {
    return webTemplatePath;
  }

  // Check for *.wt.json files
  try {
    const files = fs.readdirSync(dir);
    for (const file of files) {
      if (file.endsWith(".wt.json")) {
        return path.join(dir, file);
      }
    }
  } catch {
    // Directory not readable
  }

  return undefined;
}

async function resolveFromProjectRoot(): Promise<string | undefined> {
  const workspaceFolders = vscode.workspace.workspaceFolders;
  if (!workspaceFolders || workspaceFolders.length === 0) {
    return undefined;
  }

  const rootPath = workspaceFolders[0].uri.fsPath;

  // Check web_templates/ directory
  for (const dirName of ["web_templates", "templates"]) {
    const templatesDir = path.join(rootPath, dirName);
    if (!fs.existsSync(templatesDir)) {
      continue;
    }

    try {
      const files = fs.readdirSync(templatesDir);
      for (const file of files) {
        if (file.endsWith(".wt.json") || file === "web_template.json") {
          return path.join(templatesDir, file);
        }
      }
      // Also check for any .json file in the templates directory
      for (const file of files) {
        if (file.endsWith(".json")) {
          const fullPath = path.join(templatesDir, file);
          try {
            const content = fs.readFileSync(fullPath, "utf-8");
            const parsed = JSON.parse(content);
            if (
              parsed &&
              typeof parsed === "object" &&
              parsed.tree &&
              typeof parsed.tree === "object" &&
              "id" in parsed.tree
            ) {
              return fullPath;
            }
          } catch {
            // Not valid JSON or not a web template
          }
        }
      }
    } catch {
      // Directory not readable
    }
  }

  return undefined;
}

function resolveWorkspacePath(filePath: string): string | undefined {
  if (path.isAbsolute(filePath)) {
    return filePath;
  }

  const workspaceFolders = vscode.workspace.workspaceFolders;
  if (!workspaceFolders || workspaceFolders.length === 0) {
    return undefined;
  }

  return path.join(workspaceFolders[0].uri.fsPath, filePath);
}
