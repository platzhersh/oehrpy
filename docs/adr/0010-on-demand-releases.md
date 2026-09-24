# ADR-0010: On-Demand Releases Instead of Release-on-Every-Push

**Date:** 2026-09-24

## Status

Accepted

**Amends:** [ADR-0004](0004-python-semantic-release-for-release-automation.md)
(only the release trigger; the choice of python-semantic-release stands).
**Related:** openEHR Explorer's `RELEASING.md`, whose on-demand release model
this mirrors.

## Context

ADR-0004 wired python-semantic-release to run on every push to `main`. Every
merged `fix:` or `feat:` commit therefore produced a new version, tag, GitHub
Release and PyPI upload on its own.

In practice this released far more often than the SDK actually changed:

- Website-only changes (the Astro site in `website/`, deployed separately by
  `pages.yml`) carry scopes like `fix(website): …` or `feat(website): …`, so
  they bumped the package version even though the published wheel was
  byte-for-byte the same apart from the version string — e.g. `0.16.0`
  (`feat(website): migrate github pages site to astro`) and `0.16.1`
  (`fix(website): serve from oehrpy.dev root …`).
- Related fixes and features landing over a few days went out as a string of
  separate patch/minor releases instead of one coherent release.
- There was no point at which a maintainer decided "this is ready to ship".

## Decision

Releases are cut **on demand**. `.github/workflows/release.yml` is triggered
only by `workflow_dispatch` (Actions → Release → Run workflow, on `main`), not
by pushes.

python-semantic-release is kept for everything it did before: when run, it
looks at all conventional commits since the last tag, derives the bump
(`fix`/`perf` → patch, `feat` → minor, breaking → minor while on 0.x because
`major_on_zero = false`), updates `pyproject.toml`, `__init__.py` and
`CHANGELOG.md`, commits `chore(release): X.Y.Z`, tags, and creates the GitHub
Release, which in turn triggers `publish.yml` to upload to PyPI.

The workflow takes two inputs:

- **`bump`** — `auto` (default, derive from commits) or an explicit
  `patch`/`minor`/`major` override.
- **`dry_run`** — run with `--noop` to preview the next version without
  committing, tagging or publishing.

Commits scoped to `website` (e.g. `fix(website): …`) never cause a version
bump. A small custom parser, `.github/release/commit_parser.py`, wraps
python-semantic-release's built-in `conventional` parser and downgrades those
commits to "no release". It is configured through `commit_parser` in
`pyproject.toml`. The commits are still parsed normally, so they are listed in
the changelog of the next real release. More scopes can be added to
`NON_RELEASING_SCOPES` if other unpackaged parts of the repo need the same
treatment.

Conventional commit messages remain required: they still drive the version
number and the changelog, they just no longer trigger a release by themselves.

## Consequences

### Positive

- Several features and fixes ship together as one release with one changelog
  entry.
- Website, docs and CI-only changes no longer produce PyPI releases unless a
  maintainer chooses to release.
- A dry run makes the next version visible before committing to it.
- Same mental model as openEHR Explorer: merge freely, release deliberately.

### Negative

- Releasing is a manual step; fixes wait on `main` until someone runs the
  workflow.
  - *Mitigation*: the step is one click, documented in `RELEASING.md`.
- The custom parser depends on python-semantic-release's internal parser
  classes (`ConventionalCommitParser`, `ParsedCommit`), which may change in a
  major version (v10).
  - *Mitigation*: the workflow pins the action to `@v9`; revisit the parser
    when upgrading.
