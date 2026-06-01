import * as vscode from "vscode";

export type Platform = "ehrbase" | "better";

export interface OehrpyConfig {
  platform: Platform;
  validateOnSave: boolean;
  webTemplatePaths: Record<string, string>;
  flatCompositionPatterns: string[];
  webTemplatePatterns: string[];
  enableHover: boolean;
  enableQuickFix: boolean;
  enableAutocomplete: boolean;
  enableTemplateExplorer: boolean;
}

export function getConfig(): OehrpyConfig {
  const config = vscode.workspace.getConfiguration("oehrpy");
  return {
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
    enableHover: config.get<boolean>("enableHover", true),
    enableQuickFix: config.get<boolean>("enableQuickFix", true),
    enableAutocomplete: config.get<boolean>("enableAutocomplete", true),
    enableTemplateExplorer: config.get<boolean>("enableTemplateExplorer", true),
  };
}
