# Issue 001: FLAT Format Documentation Gap

**Status:** 🔴 Not Reported
**Discovered:** 2026-01-09
**Affects:** EHRBase 2.0.0+
**Severity:** High (blocks new users, causes widespread confusion)

---

## Summary

The official EHRBase documentation (docs.ehrbase.org) describes a FLAT format structure that **does not match** what EHRBase 2.26.0 actually accepts. The format changed between EHRBase 1.x and 2.0, but this breaking change was never documented.

---

## Impact

### Who Is Affected?
- **All new EHRBase users** following official documentation
- **SDK developers** implementing FLAT format support
- **Migration projects** upgrading from 1.x to 2.x
- **Integration developers** submitting compositions via REST API

### How They're Affected?
1. Implement format per documentation
2. Get HTTP 422 errors: `"Could not consume Parts [...]"`
3. Spend hours debugging with no documentation explaining why
4. Eventually discover format through trial-and-error or reverse engineering

---

## Evidence

### Expected Behavior (Per Documentation)

According to https://docs.ehrbase.org/docs/EHRbase/Explore/Simplified-data-template/WebTemplate#simsdt-json:

**Format Rules:**
- Use **template ID** as prefix (e.g., `"conformance-ehrbase.de.v0"`)
- Use **`:0` indexing** for multivalued elements
- Include **/any_event:0/** in observation paths

**Example from Docs:**
```json
{
  "ctx/language": "de",
  "ctx/territory": "US",
  "conformance-ehrbase.de.v0/conformance_section/conformance_observation/any_event:0/dv_quantity|magnitude": 65.9
}
```

**Documentation Quote:**
> "If an element is multivalued, add an index to the path, e.g., :0."

### Actual Behavior (EHRBase 2.26.0)

According to `/rest/openehr/v1/definition/template/adl1.4/{id}/example?format=FLAT`:

**Format Rules:**
- Use **composition tree ID** as prefix (from WebTemplate `tree.id`)
- **NO `:0` indexing** for single observations
- **NO /any_event:0/** in paths (direct observation → element)
- Specific unit requirements (`"°C"` not `"Cel"`)

**Example from EHRBase API:**
```json
{
  "vital_signs_observations/category|code": "433",
  "vital_signs_observations/context/start_time": "2022-02-03T04:05:06",
  "vital_signs_observations/vital_signs/blood_pressure/systolic|magnitude": 500.0,
  "vital_signs_observations/vital_signs/blood_pressure/systolic|unit": "mm[Hg]",
  "vital_signs_observations/vital_signs/body_temperature/temperature|unit": "°C"
}
```

### Side-by-Side Comparison

| Aspect | Documentation (OLD) | EHRBase 2.26.0 (NEW) |
|--------|---------------------|----------------------|
| **Prefix** | Template ID | Composition tree ID |
| **Indexing** | `:0` required | `:0` NOT used |
| **Event paths** | `/any_event:0/` | Direct paths (no event) |
| **Temperature** | Not specified | Must be `"°C"` |
| **SpO2** | Not clear | DV_PROPORTION format |

---

## Reproduction

### Step 1: Follow Documentation
```bash
curl -X POST "http://ehrbase/rest/openehr/v1/ehr/{ehr_id}/composition" \
  -H "Content-Type: application/json" \
  -u user:pass \
  -d '{
    "ctx/language": "en",
    "ctx/territory": "US",
    "IDCR - Vital Signs Encounter.v1/vital_signs:0/blood_pressure:0/any_event:0/systolic|magnitude": 120
  }'
```

### Result
```json
{
  "error": "Unprocessable Entity",
  "message": "Could not consume Parts [IDCR - Vital Signs Encounter.v1/vital_signs:0/blood_pressure:0/any_event:0/systolic|magnitude]"
}
```

### Step 2: Use Correct Format
```bash
curl -X POST "http://ehrbase/rest/openehr/v1/ehr/{ehr_id}/composition" \
  -H "Content-Type: application/json" \
  -u user:pass \
  -d '{
    "vital_signs_observations/category|code": "433",
    "vital_signs_observations/vital_signs/blood_pressure/systolic|magnitude": 120,
    "vital_signs_observations/vital_signs/blood_pressure/systolic|unit": "mm[Hg]"
  }'
```

### Result
```
HTTP 204 No Content
```

---

## Supporting Information

### Research Findings

We conducted extensive research to understand this issue:

1. **openEHR Discourse** - No discussions about format changes
2. **EHRBase Releases** - v2.0.0 mentions "overhauled data structure" but no FLAT format details
3. **UPDATING.md** - Migration guide silent on FLAT format changes
4. **GitHub Issues** - Issue #1117 (May 2023) still shows OLD format!
5. **GitHub PRs** - All FLAT format work was 2021-2022, no PRs about structure changes
6. **openEHR Specifications** - Serial Data Formats spec does NOT include FLAT path construction rules

**Conclusion:** The format change is **completely undocumented**.

### Critical Context: Specification Exists But EHRBase Diverges

**Update:** A formal specification DOES exist, making this issue even more severe.

#### Official Specification

The **[simSDT (Simplified Data Template)](https://specifications.openehr.org/releases/ITS-REST/latest/simplified_data_template.html)** specification was standardized in 2019:
- Based on Marand's (Better platform) FLAT format
- **Uses `:0`, `:1` indexing notation** for array elements
- Part of official openEHR ITS-REST specifications

#### EHRBase 2.26.0 Diverges from Specification

**EHRBase 2.26.0 does NOT follow the official simSDT spec:**
- ❌ **Does NOT use `:0` indexing** for single observations
- ❌ Uses composition tree ID prefix (not template ID like spec examples)
- ❌ No `/any_event/` nodes in paths

#### Three-Way Mismatch

1. **Official simSDT spec (2019)** → uses `:0` indexing, template ID prefix
2. **EHRBase docs** → outdated format (pre-2.0 era)
3. **EHRBase 2.26.0** → evolved format diverging from both

**This makes the documentation gap CRITICAL:**
- Official openEHR spec doesn't match EHRBase behavior
- EHRBase docs don't match EHRBase behavior OR the spec
- Users following either spec or docs will fail
- The `/example?format=FLAT` endpoint is the **only** source of truth

#### FLAT Format Variants

According to [EtherCIS documentation](https://github.com/ethercis/ethercis/blob/master/doc/flat%20json.md), there are two main variants:

**1. Marand FLAT** (Better Platform, basis for simSDT):
- Uses `:0`, `:1` indexing
- Human-readable paths
- Template-dependent

**2. ECISFLAT** (EtherCIS):
- AQL-based paths with archetype IDs
- Bracket notation: `/content[openEHR-EHR-EVALUATION.name.v1]`
- Template-independent

EHRBase 2.26.0 appears to use a **hybrid/evolved variant** not documented anywhere.

### Timeline (Inferred)

| Date | Event | Evidence |
|------|-------|----------|
| Pre-2019 | Multiple vendor implementations | Marand, EtherCIS, EHRScape each had variants |
| **2019** | **simSDT spec standardized** | Based on Marand's format, uses `:0` indexing |
| 2021-2022 | EHRBase FLAT format development | Multiple PRs adding support |
| May 2023 | OLD format still in use | Issue #1117 shows `:0` indices (matches spec) |
| 2.0.0 (2023?) | **Format changed (undocumented)** | "Overhauled data structure", diverged from spec |
| 2.26.0 (2024+) | **NEW format standard** | `/example` endpoint shows evolved format (no `:0`) |

### Related Resources

**Official Specifications:**
- **simSDT Specification (2019):** https://specifications.openehr.org/releases/ITS-REST/latest/simplified_data_template.html
- **Standardization GitHub Issue:** https://github.com/openEHR/specifications-ITS-REST/issues/56

**Vendor Documentation:**
- **EtherCIS FLAT Format:** https://github.com/ethercis/ethercis/blob/master/doc/flat%20json.md (documents Marand & ECISFLAT variants)
- **Outdated EHRBase Docs:** https://docs.ehrbase.org/docs/EHRbase/Explore/Simplified-data-template/WebTemplate

**Our Research:**
- [RESEARCH_FLAT_FORMAT_DISCOURSE.md](../RESEARCH_FLAT_FORMAT_DISCOURSE.md) - Community research
- [FLAT_FORMAT_VERSIONS.md](../FLAT_FORMAT_VERSIONS.md) - Comprehensive format comparison
- [flat-format-learnings.md](../flat-format-learnings.md) - Implementation guide

**EHRBase References:**
- **EHRBase Release 2.0.0:** https://github.com/ehrbase/ehrbase/releases/tag/v2.0.0
- **GitHub Issue #1117:** https://github.com/ehrbase/ehrbase/issues/1117 (May 2023, shows old format)

---

## Workaround

### In Our SDK

We've implemented the **actual** EHRBase 2.26.0 format by:

1. **Fetching WebTemplate** - Get composition tree ID from `tree.id`
2. **Using `/example` endpoint** - Verify actual format accepted by EHRBase
3. **Implementing new structure** - No `:0` indices, direct paths
4. **Documenting differences** - Created comprehensive format guide

**Implementation:** `src/openehr_sdk/templates/builders.py` (VitalSignsBuilder)

### For Other Users

**DON'T** follow docs.ehrbase.org for FLAT format.

**DO:**
1. Fetch WebTemplate: `GET /rest/definition/template/adl1.4/{id}/webtemplate`
2. Get example: `GET /rest/openehr/v1/definition/template/adl1.4/{id}/example?format=FLAT`
3. Use composition `tree.id` as prefix (not template ID)
4. Build paths by concatenating child `id` values
5. Don't use `:0` indices for single observations

---

## Upstream Tracking

- [ ] **GitHub Issue Created:** Not yet filed
- [ ] **Discourse Discussion:** Not yet posted
- [ ] **EHRBase Response:** N/A
- [ ] **Fix Released:** N/A

### Proposed GitHub Issue

**Title:** Documentation: FLAT format structure changed in 2.0 but not documented

**Labels:** documentation, breaking-change

**Body:**
```markdown
## Problem

The official documentation at docs.ehrbase.org describes a FLAT format that doesn't match what EHRBase 2.26.0 actually accepts.

### What docs say (old format):
- Use template ID as prefix
- Use :0 indexing: `template_id/section:0/observation:0/element`
- Include /any_event:0/ in paths

### What EHRBase 2.26.0 expects (new format):
- Use composition tree ID as prefix (from WebTemplate tree.id)
- NO :0 indexing for single observations
- Direct paths: `composition_tree_id/section/observation/element`

## Impact

New users following documentation get HTTP 422 errors and have no idea why.

## Evidence

[Link to our research and examples]

## Request

1. Update docs.ehrbase.org to show 2.0+ format
2. Document the format migration from 1.x to 2.0
3. Add format version history
4. Update UPDATING.md with FLAT format changes
```

---

## Related Issues

- None yet (this is issue #001)

---

## Related SDK Code

- `src/openehr_sdk/serialization/flat.py` - FlatBuilder implementation
- `src/openehr_sdk/templates/builders.py` - VitalSignsBuilder using new format
- `tests/test_templates.py` - Tests validating new format
- `docs/FLAT_FORMAT_VERSIONS.md` - Format comparison documentation
- `docs/flat-format-learnings.md` - Implementation guide

---

## Notes

- This issue cost us ~2 days of debugging to discover
- No public resources explain this change
- Our documentation may be the only comprehensive guide to this format change
- We should share this with the community to help others

---

**Last Updated:** 2026-01-09
