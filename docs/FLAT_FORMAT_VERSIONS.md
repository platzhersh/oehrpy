# FLAT Format Versions: Documentation vs Reality

**Date:** 2026-01-09
**EHRBase Version:** 2.26.0

## TL;DR

**EHRBase 2.26.0 diverges from both:**
1. The **official openEHR simSDT specification** (which uses `:0` indexing)
2. The **EHRBase documentation** (which shows outdated format)

The FLAT format described in specs and docs does NOT match what EHRBase 2.26.0 actually accepts/produces.

---

## FLAT Format Variants in the openEHR Ecosystem

### Official Specification: simSDT (Simplified Data Template)

The **official openEHR specification** defines FLAT format in the [Simplified Data Template (simSDT)](https://specifications.openehr.org/releases/ITS-REST/latest/simplified_data_template.html):

- **Based on:** Marand's "web template" FLAT format (from Better platform)
- **Also known as:** "Simplified JSON Format" or "Flat Format"
- **Standardized:** 2019 (GitHub issue #56 closed as COMPLETED)
- **Key characteristic:** Uses `:0`, `:1` indexing notation for arrays

**Example from specification:**
```json
{
  "/context/participation:0": "Nurse|1345678::Jessica|...",
  "/context/participation:1": "Assistant|1345678::2.16.840.1.113883.2.1.4.3..."
}
```

### Vendor Implementations

According to [EtherCIS documentation](https://github.com/ethercis/ethercis/blob/master/doc/flat%20json.md), there are two main FLAT format variants:

#### 1. **Marand FLAT Format** (Better Platform)
- Path/value pairs using node names and array indexes
- Uses `:0`, `:1` indexing notation
- Human-readable paths (e.g., `serum_sodium`, not `at0001`)
- Template-dependent format

**Characteristics:**
```json
{
  "laboratory_order/_uid": "...",
  "laboratory_order/language|code": "en",
  "laboratory_order/context/_health_care_facility|name": "Hospital"
}
```

#### 2. **ECISFLAT Format** (EtherCIS)
- AQL-based paths with archetype node IDs
- Uses bracket notation: `/content[openEHR-EHR-EVALUATION.name.v1]`
- More verbose, includes full archetype identifiers
- Template-independent format

**Characteristics:**
```json
{
  "/content[openEHR-EHR-EVALUATION.verbal_examination.v1]/participation:0": "...",
  "/content[openEHR-EHR-EVALUATION.verbal_examination.v1]/participation:1": "..."
}
```

### What EHRBase 2.26.0 Actually Uses

**EHRBase 2.26.0 appears to use a hybrid/evolved format:**
- Based on Marand's approach (composition tree IDs, human-readable names)
- **Diverges from simSDT spec:** NO `:0` indexing for single observations
- Uses composition tree ID prefix (not template ID)
- Direct hierarchical paths without event nodes

**This creates a three-way mismatch:**
1. Official simSDT spec → uses `:0` indexing
2. EHRBase docs → outdated format with template IDs
3. EHRBase 2.26.0 → no indexing, composition tree IDs

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

## Critical Context: FLAT Format Standardization Status

### Specification Exists But Implementations Vary

**Correcting earlier assessment:** A formal specification DOES exist:

The **[simSDT (Simplified Data Template)](https://specifications.openehr.org/releases/ITS-REST/latest/simplified_data_template.html)** specification was standardized in 2019 as part of the openEHR ITS-REST specifications. It defines FLAT format based on Marand's original implementation.

**However, implementations still diverge:**

According to [openEHR Discourse](https://discourse.openehr.org/t/understanding-flat-composition-json/1720/4) and [GitHub issue #56](https://github.com/openEHR/specifications-ITS-REST/issues/56):

- The `ctx/` prefix represents "shortcuts for RM fields extracted from deeper canonical structures"
- Different vendors evolved different variants before standardization
- **EHRBase 2.26.0 appears to have evolved beyond the 2019 spec** (no `:0` indexing for single items)
- The [openEHR Serial Data Formats specification](https://specifications.openehr.org/releases/SM/latest/serial_data_formats.html) covers JSON serialization of RM types, **NOT FLAT path construction**

### Historical Evolution

**Timeline:**
1. **Pre-2019:** Multiple vendor-specific implementations (Marand, EtherCIS, EHRScape)
2. **2019:** simSDT specification standardized, based on Marand's format
3. **2023:** EHRBase 2.0 "overhauled data structure" (changes undocumented)
4. **2024+:** EHRBase 2.26.0 uses evolved format diverging from 2019 spec

### Why This Matters

**Despite having a specification:**
- EHRBase 2.26.0 **diverges from the official spec** (removed `:0` indexing for single items)
- EHRBase documentation is **outdated** (doesn't match spec OR implementation)
- No migration guide exists explaining the evolution
- The `/example?format=FLAT` endpoint remains the **only reliable source of truth**

**This explains why:**
- We found contradictions between spec, docs, and implementation
- Format changes were undocumented (considered implementation details)
- We had to reverse-engineer from `/example` endpoint

## Conclusion

The EHRBase FLAT format has **evolved significantly** between versions. The current documentation describes an **older format** that EHRBase 2.26.0 **does not accept**.

**Always verify the actual format with your EHRBase version using the `/example` endpoint!**

Our implementation in oehrpy is based on the **actual EHRBase 2.26.0 behavior**, not the outdated documentation, which is why it works. ✅
