# 3. Pre-commit Hooks for Code Quality

Date: 2026-01-09

## Status

Proposed

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

We will investigate and implement pre-commit hooks using the `pre-commit` framework (https://pre-commit.com/) to automatically run code quality checks before allowing commits.

### Proposed Configuration

Create `.pre-commit-config.yaml` with the following hooks:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9  # Use latest stable version
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0  # Use latest stable version
    hooks:
      - id: mypy
        additional_dependencies: [pydantic>=2.0, httpx>=0.25]
        args: [--config-file=pyproject.toml]
        files: ^src/openehr_sdk/
```

### Implementation Plan

1. Add `pre-commit` to development dependencies in `pyproject.toml`:
   ```toml
   [project.optional-dependencies]
   dev = [
       "pytest>=7.4",
       "pytest-asyncio>=0.21",
       "mypy>=1.7",
       "ruff>=0.1.9",
       "pre-commit>=3.5.0",  # Add this
   ]
   ```

2. Document in README.md:
   ```markdown
   ## Development Setup

   ```bash
   # Install with development dependencies
   pip install -e ".[dev]"

   # Install pre-commit hooks (one-time setup)
   pre-commit install
   ```

   Pre-commit hooks will automatically run on `git commit` to:
   - Format code with ruff
   - Check linting with ruff
   - Run type checking with mypy on SDK code

   To skip hooks temporarily (not recommended):
   ```bash
   git commit --no-verify
   ```
   ```

3. Add CI check to ensure hooks are up-to-date:
   ```yaml
   - name: Check pre-commit hooks
     run: pre-commit run --all-files
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

## Implementation Timeline

1. **Research phase** (This ADR): Document decision and rationale
2. **Proof of concept**: Test pre-commit configuration with current codebase
3. **Team review**: Get feedback from other contributors (if any)
4. **Implementation**: Add configuration files and documentation
5. **Rollout**: Add to README, mention in CONTRIBUTING.md

## References

- [pre-commit framework](https://pre-commit.com/)
- [Ruff pre-commit hooks](https://github.com/astral-sh/ruff-pre-commit)
- [mypy pre-commit hook](https://github.com/pre-commit/mirrors-mypy)
- [GitHub discussion on pre-commit best practices](https://github.com/pre-commit/pre-commit/issues)

## Notes

- This ADR documents the intent to investigate and implement pre-commit hooks
- Implementation details may change based on testing and team feedback
- Status will be updated to "Accepted" once implementation is complete
