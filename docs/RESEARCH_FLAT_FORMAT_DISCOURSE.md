# Research: FLAT Format Documentation Gap

**Date:** 2026-01-09
**Research Question:** Why does EHRBase documentation describe a different FLAT format than what EHRBase 2.26.0 actually uses?

## TL;DR

**Finding:** There is NO public documentation, discourse discussion, or GitHub issue that explains the FLAT format changes between EHRBase 1.x → 2.x. The format change appears to be **undocumented**.

---

## Research Conducted

### 1. openEHR Discourse Forum ✅

**Searched:** https://discourse.openehr.org/tag/ehrbase

**Found:**
- General FLAT format discussions (pre-2023)
- Issue #1117 (May 2023) showing OLD format with `:0` indices
- No discussions about format changes in EHRBase 2.0+

**Example from Issue #1117 (May 2023):**
```
generic_laboratory_report/laboratory_test_result:0/specimen:0/specimen_type|value
```
Still uses `:0` indexing!

**Conclusion:** No discourse threads about FLAT format version differences.

---

### 2. EHRBase GitHub Releases ✅

**Searched:** https://github.com/ehrbase/ehrbase/releases (2.0.0 - 2.26.0)

**Found:**
- v2.0.0: "Completely overhauled data structure" (requires migration tool)
- v2.5.0: "Add simplified JSON-based web template format support"
- v2.10.0: Composition validation changes
- **NO mention of FLAT format structure changes**

**Key Quote from v2.0.0:**
> "EHRbase 2.0.0 comes with a completely overhauled data structure that is not automatically migrated"

But no details about FLAT format!

**Conclusion:** Release notes don't document FLAT format changes.

---

### 3. EHRBase UPDATING.md ✅

**Searched:** Migration guide for 1.x → 2.0

**Found:**
- Data structure migration required
- ehrscape API deprecated
- Validation rule changes
- **NO mention of FLAT format changes**

**Conclusion:** Migration guide silent on FLAT format.

---

### 4. EHRBase GitHub Issues ✅

**Searched:** Issues tagged with "flat format"

**Found (Recent):**
- #1520 (2025): Terminology validation config
- #1391 (2024): compositionUid not returned (FLAT format)
- #1381 (2024): UID handling in FLAT format
- #1368 (2024): Posting composition with ID
- #1164 (2023): Language code handling
- **#1117 (2023): Shows OLD format with `:0` indices!**

**Conclusion:** No issues discussing format structure changes.

---

### 5. EHRBase GitHub Pull Requests ✅

**Searched:** PRs about FLAT format

**Found:**
- All PRs are from **2021-2022**
- #825 (May 2022): compositionUid consistency
- #801 (Apr 2022): Example generator
- #750 (Feb 2022): Round trip test
- #744, #731, #673, #646, #639, #511: Various FLAT format tests/fixes

**Conclusion:** FLAT format work was done in 2021-2022. Nothing since then about structure changes.

---

## What We Did Find

### Evidence the Old Format Was Used (2021-2023)

From GitHub Issue #1117 (May 2023):
```json
{
  "generic_laboratory_report/laboratory_test_result:0/specimen:0/specimen_type|value": "...",
  "generic_laboratory_report/laboratory_test_result:0/specimen:0/specimen_type|code": "...",
  "generic_laboratory_report/laboratory_test_result:0/specimen:0/specimen_type|terminology": "..."
}
```

This matches the **documentation format**:
- Template ID prefix
- `:0` indexing
- Hierarchical path structure

### Evidence the New Format Is Used (2026)

From EHRBase 2.26.0 `/example?format=FLAT` endpoint:
```json
{
  "vital_signs_observations/vital_signs/blood_pressure/systolic|magnitude": 120,
  "vital_signs_observations/vital_signs/body_temperature/temperature|unit": "°C"
}
```

This is **completely different**:
- Composition tree ID prefix (not template ID)
- NO `:0` indexing
- Direct observation → element paths

---

## Timeline (Inferred)

| Period | FLAT Format | Evidence |
|--------|-------------|----------|
| **2021-2022** | Development phase | Multiple PRs adding FLAT format support |
| **May 2023** | Old format (`:0` indices) | Issue #1117 shows old format |
| **2.0.0 (2023?)** | **UNDOCUMENTED CHANGE** | "Overhauled data structure" mentioned but not detailed |
| **2.26.0 (2024+)** | New format (tree IDs) | `/example` endpoint shows new format |

---

## Why the Documentation Is Wrong

### Theory 1: Documentation Frozen at 1.x
The docs.ehrbase.org documentation was written during the 1.x era (2021-2022) and **never updated** for 2.0+.

### Theory 2: Silent Breaking Change
EHRBase 2.0.0's "completely overhauled data structure" included changing the FLAT format, but this was:
- Not announced in release notes
- Not documented in migration guide
- Not discussed in community forums
- Not mentioned in GitHub issues

### Theory 3: Internal Knowledge
The EHRBase team knows about the format change but:
- Considers it an "internal" implementation detail
- Relies on WebTemplate + `/example` endpoint for format discovery
- Hasn't prioritized updating public documentation

---

## Impact on Users

### ❌ Following Documentation = Broken Code
Users who follow docs.ehrbase.org will:
1. Implement old format with `:0` indices
2. Get HTTP 422 "Could not consume Parts" errors
3. Have no idea why it's failing
4. Find no help in forums or GitHub

### ✅ Using `/example` Endpoint = Working Code
Users who discover `/example?format=FLAT` will:
1. See the actual format EHRBase expects
2. Implement correct format
3. Succeed
4. Never know the docs were wrong

---

## Recommendations

### For EHRBase Project

1. **Update Documentation Urgently** 📝
   - docs.ehrbase.org needs complete rewrite for 2.0+ format
   - Add "FLAT Format v1 vs v2" migration guide
   - Mark old format as deprecated

2. **Document Breaking Changes** 📋
   - Add FLAT format changes to release notes retroactively
   - Update UPDATING.md with format migration info
   - Create GitHub issue acknowledging the documentation gap

3. **Version the Format** 🏷️
   - Explicitly version FLAT format (v1 = old, v2 = new)
   - Include format version in web template JSON
   - Add deprecation warnings if old format is submitted

4. **Community Communication** 💬
   - Post to Discourse about the format change
   - Explain migration path
   - Apologize for documentation gap

### For SDK Developers (Us)

1. ✅ **Trust the API, Not the Docs**
   - Always fetch `/example?format=FLAT` to verify format
   - Use WebTemplate `tree.id` values for path construction
   - Test against real EHRBase instance

2. ✅ **Document Our Findings**
   - Our FLAT_FORMAT_VERSIONS.md fills the documentation gap
   - Share with community via blog post or discourse
   - Help other developers avoid this trap

3. ✅ **Version-Aware Implementation**
   - Clearly state we support EHRBase 2.26.0+
   - Don't try to support old format (not worth complexity)
   - Link to our documentation explaining differences

---

## Evidence of the Gap

### What We Expected to Find:
- ❌ GitHub issue: "Breaking: FLAT format changed in 2.0"
- ❌ Release note: "FLAT format now uses composition tree IDs"
- ❌ Migration guide: "Update FLAT paths from X to Y"
- ❌ Discourse discussion: "How to migrate FLAT format to 2.0"
- ❌ Documentation: "FLAT Format v1 vs v2"

### What We Actually Found:
- ✅ Silence on GitHub
- ✅ Silence in release notes
- ✅ Silence in migration guide
- ✅ Silence on Discourse
- ✅ Outdated documentation still showing old format

---

## Conclusion

The FLAT format change in EHRBase 2.0 is **completely undocumented**. There is:
- No announcement
- No migration guide
- No discussion
- No GitHub issue
- No updated documentation

This is a **significant documentation gap** that affects all EHRBase users working with FLAT format.

**Our contribution:** We've documented this gap and provided the missing migration information in our SDK documentation. We should consider sharing this with the EHRBase community to help others.

---

## Next Steps

### For This PR:
1. ✅ Document the format differences (done)
2. ✅ Implement correct format (done)
3. ✅ Test against EHRBase 2.26.0 (done)
4. Consider filing GitHub issue with EHRBase documenting this gap

### For Community:
1. Post our findings to openEHR Discourse
2. Link to our FLAT_FORMAT_VERSIONS.md documentation
3. Help other developers avoid this trap
4. Pressure EHRBase to update docs

---

## Research Sources

- ✅ openEHR Discourse: https://discourse.openehr.org/tag/ehrbase
- ✅ EHRBase Releases: https://github.com/ehrbase/ehrbase/releases
- ✅ EHRBase UPDATING.md: https://github.com/ehrbase/ehrbase/blob/develop/UPDATING.md
- ✅ EHRBase Issues: https://github.com/ehrbase/ehrbase/issues?q=flat+format
- ✅ EHRBase PRs: https://github.com/ehrbase/ehrbase/pulls?q=flat+format
- ✅ EHRBase Docs: https://docs.ehrbase.org/
- ✅ EHRBase API: `/rest/openehr/v1/definition/template/adl1.4/{id}/example?format=FLAT`

**Research Date:** 2026-01-09
**Researcher:** Claude Code (via oehrpy SDK development)
