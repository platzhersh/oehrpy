# Releasing oehrpy

Releases are cut **on demand**. Merging to `main` does not release anything by
itself: changes accumulate on `main` until a maintainer runs the Release
workflow, so several features and fixes ship together. The rationale is in
[ADR-0010](docs/adr/0010-on-demand-releases.md).

## TL;DR

1. Go to **Actions → Release → Run workflow**, branch `main`.
2. Optional: tick **Dry run** first to see which version would be released.
3. Leave **bump** on `auto` and run it.

That's it. The workflow bumps the version, updates `CHANGELOG.md`, tags,
creates the GitHub Release, and the Release triggers the PyPI upload.

## What happens

`.github/workflows/release.yml` runs
[python-semantic-release](https://python-semantic-release.readthedocs.io/)
(config in `[tool.semantic_release]` in `pyproject.toml`), which:

1. Reads every commit on `main` since the last `v*` tag.
2. Picks the bump from the [Conventional Commits](https://www.conventionalcommits.org/)
   types: `fix`/`perf` → patch, `feat` → minor. While on `0.x`
   (`major_on_zero = false`) breaking changes also bump minor.
   `docs`, `ci`, `chore`, `build`, `test`, `refactor`, `style` don't cause a
   release on their own but are listed in the changelog. The same goes for
   anything scoped `website`, e.g. `feat(website)` (see
   `.github/release/commit_parser.py`).
3. Writes the new version to `pyproject.toml` and `src/oehrpy/__init__.py`, and
   adds a section to `CHANGELOG.md`.
4. Commits `chore(release): X.Y.Z`, tags `vX.Y.Z` and pushes to `main`.
5. Creates the GitHub Release with the generated notes.

The published GitHub Release then triggers `.github/workflows/publish.yml`,
which builds the sdist/wheel and uploads to PyPI via trusted publishing.

## Workflow inputs

| Input | Default | Meaning |
|---|---|---|
| `bump` | `auto` | `auto` derives the bump from commits. `patch`/`minor`/`major` forces that bump, e.g. to release when only non-releasing commit types landed, or to go to `1.0.0`. |
| `dry_run` | off | Runs with `--noop`: logs the version it would release, changes nothing. |

If `auto` finds no `feat`/`fix`/`perf`/breaking commits since the last tag, the
run succeeds without releasing and says so in the job summary.

## When to release

- Release when `main` has SDK changes users should get: new features, bug fixes,
  dependency or security updates that affect the installed package.
- Website changes (`website/`, deployed by `pages.yml`) never need a release,
  and `(website)`-scoped commits don't count toward the bump. Docs, CI or VS
  Code extension changes don't need one either; they ride along with the next
  SDK release.

## Commit messages still matter

PR titles (squash-merged into `main`) must follow Conventional Commits; see
`CLAUDE.md`. They decide the version number and become the changelog, even
though they no longer trigger a release.

## Testing a build without releasing

`publish.yml` can also be run manually (**Actions → Publish to PyPI → Run
workflow**) with target `testpypi` to upload the current `main` to TestPyPI.
