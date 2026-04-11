# ADR-0006: Align Python Import Name with PyPI Package Name

**Date:** 2026-04-11

## Status

Proposed

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
the import name matches the PyPI distribution name, and provide a
**backwards-compatible shim** using PEP 562 module-level `__getattr__` so that
existing `from openehr_sdk import ...` code continues to work with a
deprecation warning.

### 1. Rename the Package Directory

```
src/openehr_sdk/  -->  src/oehrpy/
```

All internal absolute imports change from `openehr_sdk.*` to `oehrpy.*`.

### 2. Create a Backwards-Compatible Shim

A thin `src/openehr_sdk/` package remains, included in the same wheel via
hatchling:

```toml
# pyproject.toml
[tool.hatch.build.targets.wheel]
packages = ["src/oehrpy", "src/openehr_sdk"]
```

The shim package uses PEP 562 (`__getattr__`) to transparently redirect all
attribute access and submodule imports to `oehrpy`, emitting a
`DeprecationWarning` on first use:

```python
# src/openehr_sdk/__init__.py
import importlib
import warnings

def __getattr__(name):
    warnings.warn(
        "The 'openehr_sdk' module has been renamed to 'oehrpy'. "
        "Please update your imports: "
        "'from oehrpy import ...' instead of 'from openehr_sdk import ...'. "
        "The 'openehr_sdk' name will be removed in a future release.",
        DeprecationWarning,
        stacklevel=2,
    )
    return getattr(importlib.import_module("oehrpy"), name)
```

Each submodule (`openehr_sdk.rm`, `openehr_sdk.client`, etc.) gets a similar
one-file shim that redirects to the corresponding `oehrpy.*` submodule.
The submodules that need shims:

- `openehr_sdk.aql` -> `oehrpy.aql`
- `openehr_sdk.client` -> `oehrpy.client`
- `openehr_sdk.client.ehrbase` -> `oehrpy.client.ehrbase`
- `openehr_sdk.rm` -> `oehrpy.rm`
- `openehr_sdk.serialization` -> `oehrpy.serialization`
- `openehr_sdk.templates` -> `oehrpy.templates`
- `openehr_sdk.validation` -> `oehrpy.validation`
- `openehr_sdk.validation.opt` -> `oehrpy.validation.opt`

### 3. Deprecation Timeline

- **v0.9.0**: Introduce the rename. `openehr_sdk` shim emits
  `DeprecationWarning`. Both import names work.
- **v1.0.0** (or later): Remove the `openehr_sdk` shim package entirely.
  Only `oehrpy` imports work.

This follows PEP 387 guidance on providing at least one major release cycle
of deprecation.

### 4. Documentation Updates Required

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

### 5. Configuration Updates Required

**`pyproject.toml`:**

- `[tool.hatch.build.targets.wheel]` -- update `packages` to include both
- `[project.scripts]` -- update `oehrpy-validate-opt` entry point module path
- `[tool.mypy]` -- update `openehr_sdk.rm.rm_types` override
- `[tool.ruff.lint.per-file-ignores]` -- update `src/openehr_sdk/...` paths
- `[tool.semantic_release]` -- update `version_variables` path
- `[tool.pytest.ini_options]` -- update `--cov=src/openehr_sdk` if present

**`.github/workflows/ci.yml`:**

- `mypy src/openehr_sdk` -> `mypy src/oehrpy`
- `--cov=src/openehr_sdk` -> `--cov=src/oehrpy`

### 6. Source Code Updates Required

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
- **Backwards compatible**: Existing code continues to work with a deprecation
  warning, giving users time to migrate.

### Negative

- **Large-scale rename**: Touching 40+ files across source, tests, docs, and
  config. Risk of missed references.
  - *Mitigation*: Mechanical find-and-replace across the entire repo, followed
    by full CI validation (lint, type check, unit tests, integration tests).
- **Documentation churn**: Historical ADRs and PRDs contain old import names.
  - *Mitigation*: Update docs as part of the rename PR. ADRs that discuss
    historical decisions can note the rename without rewriting history.
- **Shim maintenance**: The `openehr_sdk` compatibility package must be
  maintained until removal.
  - *Mitigation*: Shims are thin (one `__getattr__` function per module) and
    require no ongoing changes.
- **Breaking change on shim removal**: When `openehr_sdk` is eventually
  removed, any code that hasn't migrated will break.
  - *Mitigation*: Clear deprecation warnings, multi-release timeline, migration
    guide in changelog.

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

## References

- [PEP 562 -- Module `__getattr__` and `__dir__`](https://peps.python.org/pep-0562/)
- [PEP 387 -- Backwards Compatibility Policy](https://peps.python.org/pep-0387/)
- [Hatchling Build Configuration -- packages](https://hatch.pypa.io/latest/config/build/#packages)
