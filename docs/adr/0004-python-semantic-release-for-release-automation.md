# 4. Use python-semantic-release for Release Automation

Date: 2026-01-31

## Status

Accepted

## Context

The project needs an automated release workflow that:

- Determines version bumps from commit history (following [Conventional Commits](https://www.conventionalcommits.org/))
- Generates changelogs and GitHub release notes automatically
- Tags releases in git
- Integrates with the existing PyPI publishing workflow (`.github/workflows/publish.yml`)

In the JavaScript/Node.js ecosystem, tools like **release-it** and **semantic-release** are the standard for this. We evaluated the Python equivalents.

### Options Evaluated

**1. python-semantic-release** (https://github.com/python-semantic-release/python-semantic-release)
- Parses conventional commits to determine semver bumps (`fix:` = patch, `feat:` = minor, `BREAKING CHANGE` = major)
- Generates `CHANGELOG.md` from commit messages
- Bumps version in `pyproject.toml`, commits, tags, and pushes
- Can create GitHub releases with auto-generated release notes
- Has a well-maintained GitHub Action (`python-semantic-release/python-semantic-release@v9`)
- Active community, 2k+ GitHub stars

**2. commitizen** (https://github.com/commitizen-tools/commitizen)
- Also parses conventional commits for version bumps
- Provides interactive commit prompts (`cz commit`)
- Generates changelogs
- Slightly more opinionated about commit workflow (encourages using `cz commit` instead of `git commit`)
- Smaller ecosystem of CI integrations

**3. towncrier** (https://github.com/twisted/towncrier)
- Uses fragment files (one per change) instead of parsing commits
- Requires contributors to create a news fragment file with each PR
- Used by pip, pytest, and other large projects
- Adds friction to the contribution workflow

### Key Differentiators

| Feature | python-semantic-release | commitizen | towncrier |
|---|---|---|---|
| Version from commits | Yes | Yes | No (fragment files) |
| Changelog generation | Yes | Yes | Yes |
| GitHub releases | Yes (native) | Manual | Manual |
| GitHub Action | Official, maintained | Community | None |
| pyproject.toml bump | Yes | Yes | No |
| Contributor friction | Low | Medium (cz commit) | High (fragment files) |

## Decision

We will use **python-semantic-release** for automated release management because:

1. **Closest to release-it in the JS ecosystem** - familiar mental model for polyglot teams
2. **Official GitHub Action** - simple CI integration with `python-semantic-release/python-semantic-release@v9`
3. **Low contributor friction** - only requires conventional commit messages, no special tooling
4. **Native GitHub release support** - creates releases with generated notes automatically
5. **Clean integration** with our existing `publish.yml` workflow - semantic-release creates the GitHub release, which triggers PyPI publishing

### Release Flow

```
Push to main → semantic-release runs →
  1. Analyzes commits since last tag
  2. Determines version bump (patch/minor/major)
  3. Updates version in pyproject.toml
  4. Updates CHANGELOG.md
  5. Commits, tags, pushes
  6. Creates GitHub Release
       ↓
  GitHub Release triggers publish.yml →
  7. Builds package
  8. Publishes to PyPI (trusted publishing)
```

## Consequences

### Positive

- **Automated, consistent releases** - no manual version bumping or changelog writing
- **Conventional commits enforced by convention** - improves commit history quality
- **Release notes generated automatically** - reduces maintainer burden
- **Integrates with existing publish.yml** - GitHub release event triggers PyPI publish
- **Version single-sourced in pyproject.toml** - python-semantic-release reads and writes it directly

### Negative

- **Requires conventional commit discipline** - contributors must follow the format (`feat:`, `fix:`, `docs:`, etc.)
  - *Mitigation*: Document in CONTRIBUTING.md (already present), can add commitlint in pre-commit hooks later
- **Additional CI dependency** - one more GitHub Action to maintain
  - *Mitigation*: Official action is well-maintained and versioned
- **Less control over changelog prose** - auto-generated from commit messages
  - *Mitigation*: Can manually edit GitHub release notes after creation if needed

## References

- [python-semantic-release documentation](https://python-semantic-release.readthedocs.io/)
- [python-semantic-release GitHub Action](https://github.com/python-semantic-release/python-semantic-release)
- [Conventional Commits specification](https://www.conventionalcommits.org/)
- [Existing publish workflow](.github/workflows/publish.yml)
