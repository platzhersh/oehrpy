# Changelog

For the full changelog, see [CHANGELOG.md on GitHub](https://github.com/platzhersh/oehrpy/blob/main/CHANGELOG.md).

## v0.2.1 (2026-02-04)

### Bug Fixes

- Support EHRBase 2.0 JSON format and improve composition retrieval ([#21](https://github.com/platzhersh/oehrpy/pull/21))

## v0.2.0 (2026-02-04)

### Features

- Add composition versioning and update operations (PRD-0002) ([#20](https://github.com/platzhersh/oehrpy/pull/20))

### Documentation

- Add PRDs for composition lifecycle, audit, builders, and EHR management ([#19](https://github.com/platzhersh/oehrpy/pull/19))

## v0.1.1 (2026-01-31)

### Bug Fixes

- Resolve integration test failures against EHRBase 2.0 ([#18](https://github.com/platzhersh/oehrpy/pull/18))

## v0.1.0 (2026-01-31)

Initial release with:

- 134 type-safe RM classes (openEHR RM 1.1.0)
- Template builders and OPT parser
- FLAT format and canonical JSON serialization
- EHRBase async REST client
- AQL query builder
- CI/CD pipeline with GitHub Actions
- PyPI publishing support
- Integration testing with EHRBase
