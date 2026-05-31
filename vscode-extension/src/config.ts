import * as vscode from "vscode";

export type Platform = "ehrbase" | "better";

export interface OehrpyConfig {
  pythonPath: string;
  platform: Platform;
  validateOnSave: boolean;
  webTemplatePaths: Record<string, string>;
  flatCompositionPatterns: string[];
  webTemplatePatterns: string[];
  validationTimeout: number;
  enableHover: boolean;
  enableQuickFix: boolean;
}

export function getConfig(): OehrpyConfig {
  const config = vscode.workspace.getConfiguration("oehrpy");
  return {
    pythonPath: config.get<string>("pythonPath", ""),
    platform: config.get<Platform>("platform", "ehrbase"),
    validateOnSave: config.get<boolean>("validateOnSave", true),
    webTemplatePaths: config.get<Record<string, string>>("webTemplatePaths", {}),
    flatCompositionPatterns: config.get<string[]>("flatCompositionPatterns", [
      "**/*.flat.json",
    ]),
    webTemplatePatterns: config.get<string[]>("webTemplatePatterns", [
      "**/*.wt.json",
      "**/web_template.json",
    ]),
    validationTimeout: config.get<number>("validationTimeout", 5000),
    enableHover: config.get<boolean>("enableHover", true),
    enableQuickFix: config.get<boolean>("enableQuickFix", true),
  };
}
