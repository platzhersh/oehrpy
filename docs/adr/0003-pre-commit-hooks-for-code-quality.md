# 3. Pre-commit Hooks for Code Quality

Date: 2026-01-09

## Status

Accepted

## Context

During development, we've encountered recurring CI failures due to code quality issues that could have been caught earlier:

1. **Formatting issues**: Ruff format checks failing because code wasn't formatted before commit
2. **Linting errors**: Line-too-long errors and other style violations discovered only in CI
3. **Development friction**: Pushing code, waiting for CI, discovering formatting issues, fixing, re-pushing
4. **Wasted CI resources**: Running full CI pipelines for easily preventable formatting/linting issues

The current workflow requires developers to manually run:
```bash
ruff format .
ruff check .
mypy src/openehr_sdk
```

This is error-prone and often forgotten, leading to failed CI runs and additional commits just for formatting fixes.

## Decision

We implemented pre-commit hooks using the `pre-commit` framework (https://pre-commit.com/) to automatically run code quality checks before allowing commits.

### Configuration

The `.pre-commit-config.yaml` file configures the following hooks:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.6
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.14.1
    hooks:
      - id: mypy
        additional_dependencies: [pydantic>=2.0, httpx>=0.25, types-defusedxml>=0.7]
        args: [--config-file=pyproject.toml]
        files: ^src/openehr_sdk/
```

### Implementation

1. Added `pre-commit>=3.5.0` to development dependencies in `pyproject.toml`

2. Documented setup in README.md:
   ```bash
   # Install with development dependencies
   pip install -e ".[dev]"

   # Install pre-commit hooks (one-time setup)
   pre-commit install
   ```

   Pre-commit hooks automatically run on `git commit` to:
   - Format code with ruff
   - Check linting with ruff
   - Run type checking with mypy on SDK code

3. Added CI job in `.github/workflows/ci.yml` to run hooks on all files:
   ```yaml
   pre-commit:
     name: Pre-commit Hooks
     runs-on: ubuntu-latest
     steps:
       - uses: actions/checkout@v4
       - uses: actions/setup-python@v5
         with:
           python-version: "3.12"
       - run: pip install pre-commit
       - run: pre-commit run --all-files
   ```

### Benefits

1. **Catch issues early**: Formatting and linting errors caught before commit, not in CI
2. **Faster feedback**: Developers see issues immediately, not after pushing and waiting for CI
3. **Consistent code style**: All commits automatically formatted, reducing style inconsistencies
4. **Reduced CI load**: Fewer failed CI runs due to trivial formatting issues
5. **Better commit history**: Fewer "fix lint" or "format code" commits
6. **Developer experience**: Automatic fixes for many issues (ruff --fix)

### Potential Concerns

1. **Slower commits**: Hooks add ~5-10 seconds to commit time
   - Mitigation: Only run on staged files, use caching, allow `--no-verify` for emergencies

2. **Developer friction**: Some developers may not like automatic changes
   - Mitigation: Clear documentation, hooks are opt-in (need manual `pre-commit install`)

3. **CI/local divergence**: Different versions of tools between local and CI
   - Mitigation: Pin exact versions in `.pre-commit-config.yaml`, keep in sync with `pyproject.toml`

## Alternatives Considered

### 1. Manual Checks Only
- Status quo: Rely on developers remembering to run checks
- Rejected: Has proven error-prone, wastes CI resources

### 2. Git Aliases
- Create git aliases like `git cm` that run checks before commit
- Rejected: Still requires manual adoption, easy to bypass

### 3. IDE Integration Only
- Rely on IDE plugins (VS Code, PyCharm) to run checks
- Rejected: Not all developers use the same IDE, inconsistent enforcement

### 4. GitHub Actions Workflow Dispatch
- Run checks on-demand before commit
- Rejected: Slower feedback than local hooks, requires internet connection

## References

- [pre-commit framework](https://pre-commit.com/)
- [Ruff pre-commit hooks](https://github.com/astral-sh/ruff-pre-commit)
- [mypy pre-commit hook](https://github.com/pre-commit/mirrors-mypy)
