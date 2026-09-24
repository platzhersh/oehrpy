// The package version shown in the site header badge. Imported from the
// root pyproject.toml at build time (python-semantic-release bumps it there
// on every release) so the site can no longer drift behind the published
// package the way the hand-written "v0.4.0" badges did.
import pyproject from "../../../pyproject.toml?raw";

const match = pyproject.match(/^version\s*=\s*"([^"]+)"/m);
if (!match) {
  throw new Error("Could not find [project] version in pyproject.toml");
}

export const packageVersion: string = match[1];
