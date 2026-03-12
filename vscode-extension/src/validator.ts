import * as vscode from "vscode";
import { execFile } from "child_process";
import { promisify } from "util";
import * as fs from "fs";
import * as os from "os";
import * as path from "path";
import { getConfig, type Platform } from "./config";

const execFileAsync = promisify(execFile);

export interface CliValidationError {
  path: string;
  error_type: "unknown_path" | "wrong_suffix" | "missing_required" | "index_mismatch";
  message: string;
  suggestion: string | null;
  valid_alternatives: string[];
}

export interface CliValidationResult {
  is_valid: boolean;
  errors: CliValidationError[];
  warnings: CliValidationError[];
  platform: string;
  template_id: string;
  valid_path_count: number;
  checked_path_count: number;
}

export interface CliInspectResult {
  id: string;
  name: string;
  rm_type: string;
  path: string;
  min: number;
  max: number;
  valid_suffixes: string[];
}

/**
 * Discover the Python interpreter path.
 *
 * Resolution order:
 * 1. VS Code Python extension API
 * 2. oehrpy.pythonPath setting
 * 3. python3 on PATH
 */
export async function discoverPythonPath(): Promise<string> {
  // 1. Try VS Code Python extension
  const pythonExt = vscode.extensions.getExtension("ms-python.python");
  if (pythonExt) {
    if (!pythonExt.isActive) {
      try {
        await pythonExt.activate();
      } catch {
        // Activation failed, try other methods
      }
    }
    try {
      const api = pythonExt.exports as {
        settings?: { getExecutionDetails?: (resource?: vscode.Uri) => { execCommand?: string[] } };
      };
      const details = api?.settings?.getExecutionDetails?.();
      if (details?.execCommand && details.execCommand.length > 0) {
        return details.execCommand[0];
      }
    } catch {
      // API not available, try other methods
    }
  }

  // 2. Check oehrpy.pythonPath setting
  const config = getConfig();
  if (config.pythonPath) {
    return config.pythonPath;
  }

  // 3. Fall back to python3
  return "python3";
}

/**
 * Check if oehrpy is installed in the discovered Python environment.
 */
export async function checkOehrpyInstalled(pythonPath: string): Promise<boolean> {
  try {
    await execFileAsync(pythonPath, ["-m", "openehr_sdk.validation", "--version"], {
      timeout: 10000,
    });
    return true;
  } catch {
    return false;
  }
}

/**
 * Offer to install oehrpy via pip in the VS Code terminal.
 */
export async function offerInstallOehrpy(): Promise<void> {
  const result = await vscode.window.showWarningMessage(
    "oehrpy is not installed in your Python environment. Install it?",
    "Install via pip",
    "Cancel",
  );

  if (result === "Install via pip") {
    const terminal = vscode.window.createTerminal("oehrpy install");
    terminal.sendText("pip install oehrpy");
    terminal.show();
  }
}

/**
 * Run FLAT composition validation via the oehrpy CLI.
 */
export async function validateWithCli(
  pythonPath: string,
  webTemplatePath: string,
  compositionContent: string,
  platform: Platform,
  timeoutMs: number,
): Promise<CliValidationResult> {
  // Write composition content to a temp file
  const tmpDir = os.tmpdir();
  const tmpFile = path.join(tmpDir, `oehrpy-validate-${Date.now()}.json`);

  try {
    fs.writeFileSync(tmpFile, compositionContent, "utf-8");

    const { stdout } = await execFileAsync(
      pythonPath,
      [
        "-m",
        "openehr_sdk.validation",
        "validate-flat",
        "--web-template",
        webTemplatePath,
        "--composition",
        tmpFile,
        "--platform",
        platform,
        "--output",
        "json",
      ],
      { timeout: timeoutMs },
    );

    return JSON.parse(stdout) as CliValidationResult;
  } finally {
    // Clean up temp file
    try {
      fs.unlinkSync(tmpFile);
    } catch {
      // Ignore cleanup errors
    }
  }
}

/**
 * Inspect a FLAT path to get node documentation via the oehrpy CLI.
 */
export async function inspectPathWithCli(
  pythonPath: string,
  webTemplatePath: string,
  flatPath: string,
  timeoutMs: number,
): Promise<CliInspectResult | undefined> {
  try {
    const { stdout } = await execFileAsync(
      pythonPath,
      [
        "-m",
        "openehr_sdk.validation",
        "web-template",
        "inspect",
        "--web-template",
        webTemplatePath,
        "--path",
        flatPath,
      ],
      { timeout: timeoutMs },
    );

    return JSON.parse(stdout) as CliInspectResult;
  } catch {
    return undefined;
  }
}
