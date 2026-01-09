# FLAT Format Versions: Documentation vs Reality

**Date:** 2026-01-09
**EHRBase Version:** 2.26.0

## TL;DR

The **official EHRBase documentation is outdated**. The FLAT format described in the docs does NOT match what EHRBase 2.26.0 actually accepts/produces.

---

## Documentation Says (docs.ehrbase.org)

According to https://docs.ehrbase.org/docs/EHRbase/Explore/Simplified-data-template/WebTemplate#simsdt-json:

### Old FLAT Format Rules:
1. ✅ Use template ID as prefix: `"conformance-ehrbase.de.v0/..."`
2. ✅ Use `:0` indexing for multivalued elements: `any_event:0`
3. ✅ Use `ctx/` prefix for context fields
4. ✅ Use `|` pipe for attributes: `|magnitude`, `|unit`

### Example from Docs:
```json
{
  "ctx/language": "de",
  "ctx/territory": "US",
  "conformance-ehrbase.de.v0/conformance_section/conformance_observation/any_event:0/dv_quantity|magnitude": 65.9
}
```

**Key features:**
- Template ID prefix (`conformance-ehrbase.de.v0`)
- Index notation (`:0`)
- Event path (`/any_event:0/`)

---

## EHRBase 2.26.0 ACTUALLY Expects

According to the `/rest/openehr/v1/definition/template/adl1.4/{id}/example?format=FLAT` endpoint:

### New FLAT Format Rules:
1. ✅ Use **composition tree ID** as prefix (from WebTemplate `tree.id`)
2. ❌ **NO** `:0` indexing for single observations
3. ✅ Use `ctx/` OR composition prefix for context fields
4. ✅ Use `|` pipe for attributes (same as before)
5. ❌ **NO** `/any_event:0/` in paths (direct observation → element)

### Example from EHRBase 2.26.0:
```json
{
  "vital_signs_observations/category|code": "433",
  "vital_signs_observations/context/start_time": "2022-02-03T04:05:06",
  "vital_signs_observations/vital_signs/blood_pressure/systolic|magnitude": 500.0,
  "vital_signs_observations/vital_signs/blood_pressure/systolic|unit": "mm[Hg]",
  "vital_signs_observations/vital_signs/body_temperature/temperature|unit": "°C"
}
```

**Key differences:**
- ✅ Composition tree ID prefix (`vital_signs_observations` NOT `IDCR - Vital Signs Encounter.v1`)
- ❌ NO index notation (`:0`) on observations
- ❌ NO `/any_event:0/` in paths
- ✅ Temperature unit is `"°C"` not `"Cel"`

---

## Critical Differences

| Feature | Docs Say | EHRBase 2.26.0 Does |
|---------|----------|---------------------|
| **Prefix** | Template ID | Composition tree ID |
| **Indexing** | `:0` required | `:0` NOT used for single obs |
| **Event paths** | `/any_event:0/` | Direct paths (no event) |
| **Temperature unit** | Not specified | `"°C"` required |
| **SpO2 format** | Not clear | DV_PROPORTION (numerator/denominator) |

---

## Why This Matters

### ❌ If you follow the documentation:
```json
{
  "IDCR - Vital Signs Encounter.v1/vital_signs:0/blood_pressure:0/any_event:0/systolic|magnitude": 120
}
```
**Result:** HTTP 422 - "Could not consume Parts"

### ✅ If you follow the actual EHRBase behavior:
```json
{
  "vital_signs_observations/vital_signs/blood_pressure/systolic|magnitude": 120
}
```
**Result:** HTTP 204 - Success!

---

## How We Discovered This

1. **Started with docs** - Implemented FLAT format per documentation
2. **Got rejected** - EHRBase returned "Could not consume Parts" errors
3. **Fetched web template** - Downloaded actual WebTemplate JSON from EHRBase
4. **Found tree.id** - Discovered `"id": "vital_signs_observations"` in composition node
5. **Fetched example** - Used `/example?format=FLAT` endpoint to get actual format
6. **Compared** - Realized documentation is outdated

---

## The Correct Approach (EHRBase 2.26.0)

### Step 1: Get the WebTemplate
```bash
curl -u user:pass \
  "http://ehrbase/rest/definition/template/adl1.4/{template_id}/webtemplate"
```

### Step 2: Extract the composition tree ID
```json
{
  "tree": {
    "id": "vital_signs_observations",  // <-- Use this as prefix!
    "rmType": "COMPOSITION",
    ...
  }
}
```

### Step 3: Build paths using tree IDs
Navigate the `tree.children` array and concatenate `id` fields:
```
composition_tree_id / section_id / observation_id / element_id | attribute
```

### Step 4: Use correct data types
- Temperature: `"°C"` (not `"Cel"`)
- SpO2: `numerator`/`denominator` (not `magnitude`/`unit`)
- Blood pressure: `mm[Hg]`
- Pulse: `/min`

---

## Version History (Inferred)

Based on our findings, it appears:

### Pre-2.0 (Old FLAT Format):
- Used template ID as prefix
- Required `:0` indexing
- Had `/any_event:0/` paths
- Used in documentation examples

### 2.0+ (New FLAT Format):
- Uses composition tree ID as prefix
- No `:0` indexing for single observations
- Direct observation → element paths
- Specific unit requirements (`°C`, not `Cel`)

**EHRBase 2.26.0 uses the NEW format, but docs still show the OLD format.**

---

## Recommendations

### For EHRBase Users:
1. **Don't trust the docs** - Always fetch `/example?format=FLAT` to see actual format
2. **Get the WebTemplate** - Use `tree.id` values for path construction
3. **Test with real EHRBase** - Verify your FLAT format against actual API
4. **Check data types** - Use WebTemplate to verify `rmType` (DV_QUANTITY vs DV_PROPORTION)

### For oehrpy SDK:
1. ✅ **Implemented correctly** - Our VitalSignsBuilder uses the new format
2. ✅ **Uses tree IDs** - Paths like `vital_signs_observations/vital_signs/blood_pressure/...`
3. ✅ **No `:0` indices** - Single observations don't need indexing
4. ✅ **Correct units** - Temperature is `"°C"`, SpO2 is proportion

### For EHRBase Project:
1. **Update documentation** - docs.ehrbase.org needs to reflect 2.0+ format
2. **Version the format** - Clearly document FLAT v1 vs v2
3. **Migration guide** - Help users transition from old to new format
4. **Deprecation warnings** - If old format is still supported, document it

---

## References

- **Outdated Docs:** https://docs.ehrbase.org/docs/EHRbase/Explore/Simplified-data-template/WebTemplate
- **Working Example:** GET `/rest/openehr/v1/definition/template/adl1.4/{id}/example?format=FLAT`
- **WebTemplate Spec:** GET `/rest/definition/template/adl1.4/{id}/webtemplate`
- **Our Implementation:** `src/openehr_sdk/templates/builders.py` (VitalSignsBuilder)

---

## Critical Context: No Formal FLAT Format Specification

### Vendor-Specific Implementation

According to [openEHR Discourse](https://discourse.openehr.org/t/understanding-flat-composition-json/1720/4), **there is NO single formal specification for FLAT format** across the openEHR ecosystem:

- FLAT format is **vendor-specific** - implementations differ between EHRScape, EHRbase, and other servers
- The `ctx/` prefix represents "shortcuts for RM fields extracted from deeper canonical structures"
- Formats are "purely concrete" (implementation-driven, not specification-driven)
- The [openEHR Serial Data Formats specification](https://specifications.openehr.org/releases/SM/latest/serial_data_formats.html) covers JSON serialization of RM types, **NOT FLAT path construction**

### Why This Matters

**Without a formal specification:**
- You **cannot** rely on documentation from one vendor for another
- Format changes may not be announced or documented (as we discovered)
- The `/example?format=FLAT` endpoint is your **only reliable source of truth**

**This explains why:**
- EHRBase docs are outdated - no spec to enforce documentation standards
- No migration guide exists - format changes are implementation details
- We had to reverse-engineer from `/example` endpoint - no alternative approach

## Conclusion

The EHRBase FLAT format has **evolved significantly** between versions. The current documentation describes an **older format** that EHRBase 2.26.0 **does not accept**.

**Always verify the actual format with your EHRBase version using the `/example` endpoint!**

Our implementation in oehrpy is based on the **actual EHRBase 2.26.0 behavior**, not the outdated documentation, which is why it works. ✅
