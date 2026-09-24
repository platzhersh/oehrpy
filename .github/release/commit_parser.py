"""Commit parser for python-semantic-release used by the Release workflow.

Behaves exactly like the built-in ``conventional`` parser, except that commits
scoped to parts of the repo that are not shipped in the PyPI package (e.g.
``fix(website): ...``) never trigger a version bump. They are still parsed
normally, so they keep appearing in the changelog of the next real release.

Wired up via ``[tool.semantic_release] commit_parser`` in ``pyproject.toml``.
See ADR-0010.
"""

from __future__ import annotations

from semantic_release.commit_parser.conventional import ConventionalCommitParser
from semantic_release.commit_parser.token import ParsedCommit, ParseResult
from semantic_release.enums import LevelBump

# Conventional-commit scopes whose changes don't affect the published package.
NON_RELEASING_SCOPES = frozenset({"website"})


class OehrpyCommitParser(ConventionalCommitParser):
    """Conventional commit parser that ignores non-package scopes for bumps."""

    def parse_commit(self, commit):  # type: ignore[no-untyped-def]
        result: ParseResult = super().parse_commit(commit)
        if (
            isinstance(result, ParsedCommit)
            and result.scope.strip().lower() in NON_RELEASING_SCOPES
        ):
            return result._replace(bump=LevelBump.NO_RELEASE)
        return result
