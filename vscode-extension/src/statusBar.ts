import * as vscode from "vscode";

export type StatusBarState = "idle" | "validating" | "valid" | "invalid" | "no_template" | "error";

/**
 * Manages the oehrpy status bar item shown in the bottom-left of VS Code.
 */
export class OehrpyStatusBar {
  private readonly statusBarItem: vscode.StatusBarItem;
  private errorCount = 0;

  constructor() {
    this.statusBarItem = vscode.window.createStatusBarItem(
      vscode.StatusBarAlignment.Left,
      100,
    );
    this.statusBarItem.command = "workbench.actions.view.problems";
    this.hide();
  }

  /**
   * Update the status bar to reflect the current state.
   */
  setState(state: StatusBarState, errorCount?: number): void {
    this.errorCount = errorCount ?? this.errorCount;

    switch (state) {
      case "idle":
        this.hide();
        return;
      case "validating":
        this.statusBarItem.text = "$(sync~spin) oehrpy: validating...";
        this.statusBarItem.tooltip = "oehrpy is validating the FLAT composition";
        this.statusBarItem.backgroundColor = undefined;
        break;
      case "valid":
        this.statusBarItem.text = "$(check) oehrpy: valid";
        this.statusBarItem.tooltip = "FLAT composition is valid";
        this.statusBarItem.backgroundColor = undefined;
        break;
      case "invalid":
        this.statusBarItem.text = `$(error) oehrpy: ${this.errorCount} error${this.errorCount !== 1 ? "s" : ""}`;
        this.statusBarItem.tooltip = `FLAT composition has ${this.errorCount} validation error${this.errorCount !== 1 ? "s" : ""}. Click to view.`;
        this.statusBarItem.backgroundColor = new vscode.ThemeColor(
          "statusBarItem.errorBackground",
        );
        break;
      case "no_template":
        this.statusBarItem.text = "$(warning) oehrpy: no template";
        this.statusBarItem.tooltip =
          "No Web Template found. Run 'oehrpy: Select Web Template' to configure.";
        this.statusBarItem.backgroundColor = new vscode.ThemeColor(
          "statusBarItem.warningBackground",
        );
        break;
      case "error":
        this.statusBarItem.text = "$(error) oehrpy: error";
        this.statusBarItem.tooltip = "oehrpy validation encountered an error";
        this.statusBarItem.backgroundColor = new vscode.ThemeColor(
          "statusBarItem.errorBackground",
        );
        break;
    }

    this.statusBarItem.show();
  }

  /**
   * Show the status bar item.
   */
  show(): void {
    this.statusBarItem.show();
  }

  /**
   * Hide the status bar item.
   */
  hide(): void {
    this.statusBarItem.hide();
  }

  /**
   * Dispose of the status bar item.
   */
  dispose(): void {
    this.statusBarItem.dispose();
  }
}
