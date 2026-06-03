/**
 * OPT (Operational Template) validation via the Python `oehrpy` CLI.
 *
 * Unlike FLAT validation — which runs in-process (see `validation.ts`) — OPT
 * 1.4 XML validation reuses the full Python `OPTValidator` (well-formedness,
 * semantic, structural, and FLAT-path-impact checks across 25 issue codes),
 * which is not practical to port to TypeScript. This module shells out to
 * `python -m oehrpy.validate_opt_cli` and degrades gracefully when Python or
 * `oehrpy` is unavailable. See ADR-0008.
 */

import * as vscode from "vscode";
import { execFile } from "child_process";
import { promisify } from "util";
import { getConfig } from "./config";
import type { OptValidationOutcome, OptValidationResult } from "./optModel";

const execFileAsync = promisify(execFile);

/**
 * Discover the Python interpreter to use for OPT validation.
 *
 * Resolution order:
 * 1. VS Code Python extension active interpreter
 * 2. `oehrpy.pythonPath` setting
 * 3. `python3` on PATH
 */
export async function discoverPythonPath(): Promise<string> {
  const pythonExt = vscode.extensions.getExtension("ms-python.python");
  if (pythonExt) {
    if (!pythonExt.isActive) {
      try {
        await pythonExt.activate();
      } catch {
        // Activation failed — fall through to other strategies.
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
      // API shape not as expected — fall through.
    }
  }

  const config = getConfig();
  if (config.pythonPath) {
    return config.pythonPath;
  }

  return "python3";
}

/** True if the error indicates Python or oehrpy is simply not installed. */
function isUnavailable(stderr: string, err: NodeJS.ErrnoException): boolean {
  if (err.code === "ENOENT") {
    return true;
  }
  return (
    /No module named ['"]?oehrpy/i.test(stderr) ||
    /No module named ['"]?oehrpy\.validate_opt_cli/i.test(stderr)
  );
}

/**
 * Validate an OPT file by invoking the Python CLI.
 *
 * Returns a tagged outcome so callers can distinguish a real validation
 * result from "Python/oehrpy not installed" (which should degrade silently)
 * and from genuine errors.
 */
export async function validateOptFile(
  pythonPath: string,
  filePath: string,
  timeoutMs: number,
): Promise<OptValidationOutcome> {
  try {
    const { stdout } = await execFileAsync(
      pythonPath,
      ["-m", "oehrpy.validate_opt_cli", filePath, "--output", "json"],
      { timeout: timeoutMs, maxBuffer: 16 * 1024 * 1024 },
    );
    try {
      const result = JSON.parse(stdout) as OptValidationResult;
      return { kind: "ok", result };
    } catch {
      return {
        kind: "error",
        detail: `OPT validator returned invalid JSON: ${stdout.slice(0, 200)}`,
      };
    }
  } catch (error) {
    const err = error as NodeJS.ErrnoException & { stdout?: string; stderr?: string };
    const stderr = err.stderr ?? "";

    // The CLI exits 1 when a template is *invalid* but still prints JSON.
    if (err.stdout) {
      try {
        const result = JSON.parse(err.stdout) as OptValidationResult;
        return { kind: "ok", result };
      } catch {
        // Not JSON — fall through to error classification.
      }
    }

    if (isUnavailable(stderr, err)) {
      return { kind: "unavailable", detail: stderr || err.message };
    }
    return { kind: "error", detail: stderr || err.message };
  }
}
