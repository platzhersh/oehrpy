# ADR-0006: Align Python Import Name with PyPI Package Name

**Date:** 2026-04-11

## Status

Accepted

## Context

The PyPI distribution is named `oehrpy`, but the Python import name is
`openehr_sdk`:

```bash
pip install oehrpy
```

```python
from openehr_sdk.rm import DV_QUANTITY  # unexpected module name
```

This mismatch is a recurring source of confusion. Users who `pip install oehrpy`
will naturally attempt `import oehrpy` and receive a `ModuleNotFoundError`.
While distribution-vs-import mismatches exist in the wider ecosystem
(e.g., `Pillow` / `PIL`, `scikit-learn` / `sklearn`), those cases are
long-established. For a young project this is an avoidable friction point that
hurts discoverability and onboarding.

### Scope of the Problem

The name `openehr_sdk` is embedded deeply:

| Category | Files affected |
|----------|---------------|
| Python source (`src/openehr_sdk/`) | 10 internal modules with absolute imports |
| Unit and integration tests (`tests/`) | 14 test files |
| Documentation (`.md`) | 17 files (README, CLAUDE.md, ADRs, PRDs, guides) |
| Static HTML documentation (`docs/`) | 3 files (`docs.html`, `index.html`, `validator.html`) |
| Configuration (`pyproject.toml`) | Package path, CLI entry point, mypy/ruff overrides, semantic-release version variable |
| CI workflow (`.github/workflows/ci.yml`) | mypy target path, coverage path |
| Generator scripts (`generator/`) | 2 files with hard-coded output paths |
| Example scripts (`examples/`) | 1 file |

### Backwards Compatibility Concern

The package has been published on PyPI. Existing users have code that imports
from `openehr_sdk`. A rename without a compatibility layer would break all
downstream code on upgrade.

## Decision

We will **rename the Python package from `openehr_sdk` to `oehrpy`** so that
the import name matches the PyPI distribution name. This is a **breaking
change** with no backwards-compatible shim.

Since the project is still in `0.x` (pre-1.0), breaking changes are acceptable
without a major version bump per semver conventions. The user base is small
enough that the cost of a clean break is far lower than maintaining a
compatibility shim indefinitely.

### 1. Rename the Package Directory

```
src/openehr_sdk/  -->  src/oehrpy/
```

All internal absolute imports change from `openehr_sdk.*` to `oehrpy.*`.

### 2. No Backwards-Compatible Shim

An earlier draft of this ADR proposed a PEP 562 `__getattr__` shim package
at `src/openehr_sdk/` to provide deprecation warnings. This was rejected in
favour of a clean break because:

- The project is pre-1.0 with a small user base.
- Shims risk becoming a "definitive provisorium" -- temporary solutions that
  persist indefinitely.
- A clean break is simpler to maintain and reason about.
- Users upgrading can do a straightforward find-and-replace:
  `openehr_sdk` -> `oehrpy`.

### 3. Documentation Updates Required

All of the following files contain `openehr_sdk` import examples, path
references, or configuration that must be updated to `oehrpy`:

**Root-level documentation:**

- `README.md` -- all import examples, quick-start guide
- `CLAUDE.md` -- architecture docs, command examples, import references
- `CONTRIBUTING.md` -- test commands, module references
- `INTEGRATION_TEST_STATUS.md` -- module path references

**Architecture Decision Records (`docs/adr/`):**

- `0001-odin-parsing-and-rm-1.1.0-support.md` -- import examples
- `0002-integration-testing-with-ehrbase.md` -- client/template imports
- `0003-pre-commit-hooks-for-code-quality.md` -- `src/openehr_sdk/` paths
- `0005-web-template-as-primary-source-of-truth-for-flat-paths.md` -- path
  references

**Product Requirement Documents (`docs/prd/`):**

- `PRD-0000-python-openehr-sdk.md`
- `PRD-0001-odin-parser.md`
- `PRD-0004-dynamic-composition-builders.md`
- `PRD-0006-flat-format-validator.md`
- `PRD-0007-pyodide-integration.md`
- `PRD-0008-opt-validator.md`

**Other documentation (`docs/`):**

- `FLAT_FORMAT_VERSIONS.md`
- `ehrbase-issues/001-flat-format-documentation-gap.md`
- `integration-testing-journey.md`

**Static HTML docs (`docs/`):**

- `docs.html`
- `index.html`
- `validator.html`

### 4. Configuration Updates Required

**`pyproject.toml`:**

- `[tool.hatch.build.targets.wheel]` -- update `packages` to `["src/oehrpy"]`
- `[project.scripts]` -- update `oehrpy-validate-opt` entry point module path
- `[tool.mypy]` -- update `openehr_sdk.rm.rm_types` override
- `[tool.ruff.lint.per-file-ignores]` -- update `src/openehr_sdk/...` paths
- `[tool.semantic_release]` -- update `version_variables` path
- `[tool.pytest.ini_options]` -- update `--cov=src/openehr_sdk` if present

**`.github/workflows/ci.yml`:**

- `mypy src/openehr_sdk` -> `mypy src/oehrpy`
- `--cov=src/openehr_sdk` -> `--cov=src/oehrpy`

### 5. Source Code Updates Required

**Internal imports (all files under `src/oehrpy/`):**

All `from openehr_sdk.x import y` statements become `from oehrpy.x import y`.
This affects every module with cross-package imports (serialization, client,
templates, validation, aql).

**Generator scripts (`generator/`):**

- `pydantic_generator.py` -- output path `src/openehr_sdk/rm` -> `src/oehrpy/rm`
- `generate_rm_1_1_0.py` -- output path `src/openehr_sdk/rm/rm_types.py` -> `src/oehrpy/rm/rm_types.py`

**Example scripts (`examples/`):**

- `generate_builder_from_opt.py` -- update imports

**Test files (`tests/`):**

All 14 test files that `from openehr_sdk import ...` must update to
`from oehrpy import ...`.

## Consequences

### Positive

- **Eliminates naming confusion**: `pip install oehrpy` and `import oehrpy`
  just work.
- **Better discoverability**: Users searching PyPI for "oehrpy" can immediately
  know the import name.
- **Industry convention**: Most modern Python packages use matching
  distribution and import names.
- **No shim maintenance**: Clean break means no compatibility code to carry.
- **Simpler codebase**: Only one package directory, one import name to reason
  about.

### Negative

- **Breaking change**: Existing code using `from openehr_sdk import ...` will
  fail on upgrade with `ModuleNotFoundError`.
  - *Mitigation*: Simple find-and-replace migration (`openehr_sdk` -> `oehrpy`).
    Project is pre-1.0 with small user base.
- **Large-scale rename**: Touching 40+ files across source, tests, docs, and
  config. Risk of missed references.
  - *Mitigation*: Mechanical find-and-replace across the entire repo, followed
    by full CI validation (lint, type check, unit tests, integration tests).
- **Documentation churn**: Historical ADRs and PRDs contain old import names.
  - *Mitigation*: Update docs as part of the rename PR. ADRs that discuss
    historical decisions can note the rename without rewriting history.

## Alternatives Considered

### Alternative 1: Rename the PyPI Package to `openehr-sdk`

Change the distribution name to match the existing import name.

**Rejected** because:
- The name `oehrpy` is already established on PyPI and in documentation.
- Would require a new PyPI package (can't rename existing ones), abandoning
  the current package and its download history.
- `openehr-sdk` is a more generic name that could conflict with other openEHR
  projects.

### Alternative 2: Keep the Mismatch, Document It

Add a note in the README explaining the discrepancy.

**Rejected** because:
- Documentation doesn't prevent `ModuleNotFoundError` frustration.
- Every new user will hit this confusion at least once.
- The project is young enough that fixing it now is far cheaper than later.

### Alternative 3: Publish a Separate `openehr-sdk` Compatibility Package

Publish a thin `openehr-sdk` package on PyPI that depends on `oehrpy`.

**Rejected** because:
- Adds PyPI package management overhead (two packages to release).
- Users might install the wrong package.
- Same result achievable by including the shim in the main distribution.

### Alternative 4: Backwards-Compatible Shim via PEP 562

Keep a thin `src/openehr_sdk/` shim package using `__getattr__` to redirect
imports with `DeprecationWarning`.

**Rejected** because:
- Risk of the shim becoming permanent ("definitive provisorium").
- Extra code to maintain with no clear removal timeline.
- Pre-1.0 status makes a clean break acceptable and simpler.

## References

- [Hatchling Build Configuration -- packages](https://hatch.pypa.io/latest/config/build/#packages)
