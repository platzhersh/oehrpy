# Integration Testing with EHRBase - Implementation Journey

## Overview

This document captures the complete journey of implementing integration tests for the oehrpy SDK with EHRBase (currently v2.26.0), including challenges encountered, solutions implemented, and outstanding issues with FLAT format.

**Status**: Integration tests infrastructure complete. FLAT format path structure remains unresolved.

**Date**: 2026-01-09

**Update**: 2026-01-09 - Upgraded to EHRBase 2.26.0 for latest bug fixes. PostgreSQL remains at 16.2 (only available version for ehrbase-v2-postgres image).

**RESOLUTION**: 2026-01-09 - Successfully retrieved Web Template from EHRBase 2.26.0 using `Accept: application/openehr.wt+json` header! Updated FLAT paths based on web template structure. Key fixes:
- Pulse observation ID: `pulse_heart_beat` (not `pulse`), data element: `heart_rate` (not `rate`)
- Respiration observation ID: `respirations` (plural)
- Removed double nesting: `vital_signs/observation:0/...` (not `vital_signs/vital_signs:0/observation:0/...`)
- Web template endpoint: `/rest/openehr/v1/definition/template/adl1.4/{template_id}` with Accept header `application/openehr.wt+json`

---

## Achievements

### ✅ CI Infrastructure (Fully Working)

Successfully implemented GitHub Actions CI workflow with:

- **Docker Compose Setup**: PostgreSQL 16.2 + EHRBase 2.26.0
- **Service Containers**: GitHub Actions service containers for postgres
- **EHRBase Container**: Docker run with `--network host` for EHRBase
- **Health Checks**: Proper wait mechanisms for both postgres and EHRBase
- **Template Upload**: Automated OPT template upload in CI
- **Test Execution**: pytest with integration marker support

**Configuration Files**:
- `.github/workflows/ci.yml` - CI pipeline with 4 jobs (Lint, Type Check, Unit Tests, Integration Tests)
- `docker-compose.yml` - Local development setup (postgres user configuration)
- `tests/integration/conftest.py` - Pytest fixtures for EHRBase client, EHR creation, template upload

### ✅ CI Pipeline (3/4 Passing)

| Check | Status | Notes |
|-------|--------|-------|
| Lint | ✅ PASS | Ruff lint + format |
| Type Check | ✅ PASS | mypy strict mode |
| Unit Tests | ✅ PASS | All 76 tests passing |
| Integration Tests | ❌ FAIL | FLAT path validation errors |

### ✅ Issues Resolved

1. **PostgreSQL Container Initialization**
   - **Issue**: Environment variables mismatch between local and CI
   - **Solution**: Standardized on `POSTGRES_USER=postgres`, `EHRBASE_USER=ehrbase`

2. **EHRBase Health Check**
   - **Issue**: Health check curl missing authentication
   - **Solution**: Added `-u ehrbase-user:SuperSecretPassword` to health check

3. **Template Upload Headers**
   - **Issue**: 406 Not Acceptable responses
   - **Solution**: Added `Accept: */*` header to template upload

4. **Template Upload Response Handling**
   - **Issue**: 201/204 responses with no body
   - **Solution**: Extract template_id from request XML when response has no body

5. **Template Upload 409 Conflicts**
   - **Issue**: Template already exists error on re-run
   - **Solution**: Handle 409 gracefully by extracting template_id from XML

6. **Archetype Name Mismatches**
   - **Issue**: Hardcoded paths used wrong names (`pulse_heart_beat`, `respirations`)
   - **Solution**: Analyzed OPT to extract correct names (`pulse`, `respiration`)
   - **Analysis Method**: Examined archetype IDs in OPT template
     - `openEHR-EHR-OBSERVATION.pulse.v1` → `pulse`
     - `openEHR-EHR-OBSERVATION.respiration.v1` → `respiration`

7. **Ruff Formatting Issues**
   - **Issue**: Long FLAT paths exceeded 100 char line limit
   - **Solution**: Added `E501` exception for `tests/*.py` in pyproject.toml

---

## Outstanding Issue: FLAT Format Path Structure

### The Problem

EHRBase 2.0.0 **rejects ALL compositions** submitted in FLAT format with validation error:
```
ValidationError: Could not consume Parts [vital_signs/vital_signs:0/blood_pressure:0/any_event:0/time, ...]
```

### Template Structure

Using template: `IDCR - Vital Signs Encounter.v1` from ehrbase repository
- Source: https://github.com/ehrbase/ehrbase/tree/develop/service/src/test/resources/knowledge/opt
- Structure: `COMPOSITION.encounter` > `content[SECTION.vital_signs]` > `items[OBSERVATION.*]`

**Observations in template**:
- `openEHR-EHR-OBSERVATION.blood_pressure.v1`
- `openEHR-EHR-OBSERVATION.pulse.v1`
- `openEHR-EHR-OBSERVATION.body_temperature.v1`
- `openEHR-EHR-OBSERVATION.respiration.v1`
- `openEHR-EHR-OBSERVATION.indirect_oximetry.v1`
- `openEHR-EHR-OBSERVATION.avpu.v1`
- `openEHR-EHR-OBSERVATION.news_uk_rcp.v1`

### Path Structures Tried

#### Attempt 1: Single-Level Nesting
```
vital_signs/blood_pressure:0/any_event:0/systolic|magnitude
vital_signs/blood_pressure:0/any_event:0/systolic|unit
vital_signs/pulse:0/any_event:0/rate|magnitude
```
**Result**: ❌ Rejected - "Could not consume Parts"

#### Attempt 2: Double-Level Nesting
Based on example found in EHRBase FLAT format documentation showing:
```json
"vital_signs/vital_signs:0/blood_pressure:0/any_event:0/systolic|magnitude": 120.0
```

Updated paths to:
```
vital_signs/vital_signs:0/blood_pressure:0/any_event:0/systolic|magnitude
vital_signs/vital_signs:0/pulse:0/any_event:0/rate|magnitude
```
**Result**: ❌ Rejected - "Could not consume Parts"

### Attempts to Get Web Template

The Web Template JSON would reveal the exact FLAT path structure. Tried multiple approaches:

#### Attempt 1: Standard openEHR REST API Endpoint
```bash
curl "http://localhost:8080/ehrbase/rest/openehr/v1/definition/template/adl1.4/{template_id}" \
  -H "Accept: application/json"
```
**Result**: ❌ `{"error": "Not Acceptable", "message": "No acceptable representation"}`

#### Attempt 2: Web Template Specific Accept Header
```bash
curl "http://localhost:8080/ehrbase/rest/openehr/v1/definition/template/adl1.4/{template_id}" \
  -H "Accept: application/openehr.wt+json"
```
**Result**: ❌ Same "Not Acceptable" error

#### Attempt 3: `/webtemplate` Endpoint Suffix
```bash
curl "http://localhost:8080/ehrbase/rest/definition/template/adl1.4/{template_id}/webtemplate"
```
**Result**: ❌ `{"error": "Not Found", "message": "No resource found at path: ..."}`

#### Attempt 4: ECIS Alternative Endpoint
```bash
curl "http://localhost:8080/ehrbase/rest/ecis/v1/template/{template_id}"
```
**Result**: Not tested (endpoint path uncertain)

### Analysis

**Why FLAT paths are being rejected**:
1. EHRBase 2.0.0 may not fully support FLAT format, or
2. The path structure requires information only available in the Web Template, or
3. The template wasn't processed correctly during upload, or
4. There's additional path nesting we haven't discovered

**Web Template Unavailability**:
- EHRBase 2.0.0 REST API doesn't expose Web Templates via standard openEHR endpoints
- The `/definition/template/adl1.4/{id}` endpoint only returns OPT XML (not Web Template JSON)
- No alternative documented endpoint provides Web Template in JSON format

---

## Research Findings

### FLAT Format Path Construction

According to EHRBase documentation and examples:

1. **Path Components**: Paths are constructed by concatenating IDs from the Web Template tree
2. **Delimiters**: `/` for hierarchical levels, `:N` for array indices
3. **Attributes**: `|` prefix for DV_* type attributes (e.g., `|magnitude`, `|unit`)

**Example from documentation**:
```json
{
  "ctx/time": "2014-03-19T13:10:00.000Z",
  "ctx/language": "en",
  "vital_signs/body_temperature:0/any_event:0/time": "2014-03-19T13:10:00.000Z",
  "vital_signs/body_temperature:0/any_event:0/temperature|magnitude": 37.1,
  "vital_signs/body_temperature:0/any_event:0/temperature|unit": "°C"
}
```

### Key Discoveries

1. **Template Structure Matters**: Different templates have different FLAT path structures
2. **Web Template is Essential**: Cannot reliably construct FLAT paths without Web Template JSON
3. **Archetype IDs Extract to Short Names**: `openEHR-EHR-OBSERVATION.pulse.v1` → `pulse`
4. **Context Fields Required**: `ctx/time`, `ctx/language`, `ctx/territory` are mandatory

### References

- **EHRBase FLAT Format Docs**: https://docs.ehrbase.org/docs/EHRbase/Explore/Simplified-data-template/
- **Web Template Docs**: https://docs.ehrbase.org/docs/EHRbase/Explore/Simplified-data-template/WebTemplate
- **Template Source**: https://github.com/ehrbase/ehrbase/blob/develop/service/src/test/resources/knowledge/opt/IDCR%20-%20Vital%20Signs%20Encounter.v1.opt
- **EHRBase Test Data**: https://github.com/ehrbase/openEHR_SDK/tree/develop/test-data

---

## Recommendations for Future Work

### Short Term: Use CANONICAL Format

Switch integration tests to use CANONICAL JSON format instead of FLAT:

**Advantages**:
- Well-documented in openEHR specifications
- Directly maps to Reference Model classes (already implemented in SDK)
- No dependency on Web Template
- More robust and portable

**Example**:
```python
# Instead of FLAT:
composition = {
    "vital_signs/blood_pressure:0/any_event:0/systolic|magnitude": 120
}

# Use CANONICAL:
composition = COMPOSITION(
    content=[
        OBSERVATION(
            data=...
        )
    ]
)
```

### Medium Term: Investigate STRUCTURED Format

EHRBase's STRUCTURED format is a middle ground between FLAT and CANONICAL:
- More human-readable than CANONICAL
- More reliable than FLAT (may not require Web Template)
- Less documented but potentially easier to construct

### Long Term: Revisit FLAT Format

When one of the following becomes available:
1. EHRBase implements Web Template GET endpoint
2. EHRBase FLAT format documentation improves with template-specific examples
3. Community provides working FLAT examples for common templates
4. Alternative method to derive FLAT paths from OPT is discovered

**Approach**:
1. Obtain Web Template JSON for the vital signs template
2. Analyze the `tree.id` fields to construct exact FLAT paths
3. Update VitalSignsBuilder with correct paths
4. Re-enable FLAT format tests

---

## Code Changes Summary

### Files Modified

**CI/Infrastructure**:
- `.github/workflows/ci.yml` - Complete CI pipeline with EHRBase setup
- `docker-compose.yml` - Local development environment
- `pyproject.toml` - Added E501 exception for test files

**Source Code**:
- `src/openehr_sdk/client/ehrbase.py` - Template upload 201/204/409 handling
- `src/openehr_sdk/templates/builders.py` - Updated FLAT path prefixes (currently using double-nesting structure)

**Tests**:
- `tests/integration/conftest.py` - EHRBase client fixtures, template upload, 409 handling
- `tests/integration/test_ehr_operations.py` - EHR creation and retrieval
- `tests/integration/test_compositions.py` - Composition CRUD operations
- `tests/integration/test_aql_queries.py` - AQL query execution
- `tests/integration/test_round_trip.py` - End-to-end workflows
- `tests/test_templates.py` - Updated unit tests for new path structure

**Documentation**:
- `INTEGRATION_TEST_STATUS.md` - Detailed tracking document (can be removed)
- `docs/integration-testing-journey.md` - This document

### Current VitalSignsBuilder Paths

Located in `src/openehr_sdk/templates/builders.py`:

```python
# Current implementation (double-nesting, not working):
_BP_PREFIX = "vital_signs/vital_signs:0/blood_pressure"
_PULSE_PREFIX = "vital_signs/vital_signs:0/pulse"
_TEMP_PREFIX = "vital_signs/vital_signs:0/body_temperature"
_RESP_PREFIX = "vital_signs/vital_signs:0/respiration"
_SPO2_PREFIX = "vital_signs/vital_signs:0/indirect_oximetry"

# Previous attempt (single-nesting, not working):
# _BP_PREFIX = "vital_signs/blood_pressure"
# _PULSE_PREFIX = "vital_signs/pulse"
# etc.
```

**Note**: These paths will need to be corrected once we obtain the Web Template or discover the correct structure.

---

## 2026-01-09 Update: Web Template Retrieved and FLAT Format Testing

### Web Template Successfully Retrieved

After upgrading to **EHRBase 2.26.0** (from 2.0.0), we successfully retrieved the Web Template JSON using:

```bash
curl -u "$EHRBASE_USER:$EHRBASE_PASSWORD" \
  -H "Accept: application/openehr.wt+json" \
  "http://localhost:8080/ehrbase/rest/openehr/v1/definition/template/adl1.4/IDCR%20-%20Vital%20Signs%20Encounter.v1"
```

**Key Finding**: The `application/openehr.wt+json` media type was not available in EHRBase 2.0.0 but works in 2.26.0.

### Web Template Analysis

The web template shows a flattened structure where data elements are direct children of observations:

```text
vital_signs (SECTION)
  └─ blood_pressure (OBSERVATION)
      ├─ systolic (DV_QUANTITY)
      ├─ diastolic (DV_QUANTITY)
      ├─ time (DV_DATE_TIME) - required
      ├─ subject (PARTY_PROXY) - required
      ├─ language (CODE_PHRASE) - required
      └─ encoding (CODE_PHRASE) - required
```

**Note**: The `aqlPath` in the web template shows the full RM hierarchy including `/data[at0001]/events[at0006]/data[at0003]/items[...]`, but the FLAT format `id` fields suggest paths like `vital_signs/blood_pressure:0/systolic|magnitude`.

### FLAT Format Testing Results

#### Test 1: Without Event Hierarchy
```json
{
  "vital_signs/blood_pressure:0/systolic|magnitude": 120,
  "vital_signs/blood_pressure:0/systolic|unit": "mm[Hg]",
  "vital_signs/blood_pressure:0/diastolic|magnitude": 80,
  "vital_signs/blood_pressure:0/diastolic|unit": "mm[Hg]"
}
```
**Result**: ❌ `Could not consume Parts` error

#### Test 2: With /any_event:0/
```json
{
  "vital_signs/blood_pressure:0/any_event:0/systolic|magnitude": 120,
  "vital_signs/blood_pressure:0/any_event:0/systolic|unit": "mm[Hg]",
  ...
}
```
**Result**: ❌ `Could not consume Parts` error

#### Test 3: With All Required Fields
```json
{
  "vital_signs/blood_pressure:0/systolic|magnitude": 120,
  "vital_signs/blood_pressure:0/systolic|unit": "mm[Hg]",
  "vital_signs/blood_pressure:0/diastolic|magnitude": 80,
  "vital_signs/blood_pressure:0/diastolic|unit": "mm[Hg]",
  "vital_signs/blood_pressure:0/time": "2026-01-09T12:00:00Z",
  "vital_signs/blood_pressure:0/language|code": "en",
  "vital_signs/blood_pressure:0/language|terminology": "ISO_639-1",
  "vital_signs/blood_pressure:0/encoding|code": "UTF-8",
  "vital_signs/blood_pressure:0/encoding|terminology": "IANA_character-sets"
}
```
**Result**: ❌ `Could not consume Parts` error

### Documentation vs Reality Discrepancy

Official [EHRBase documentation](https://github.com/ehrbase/documentation) shows examples like:
```json
{
  "vital_signs/body_temperature:0/any_event:0/temperature|magnitude": 37.1,
  "vital_signs/body_temperature:0/any_event:0/temperature|unit": "°C"
}
```

However, this template's web template structure doesn't include `any_event` as an ID in the tree. The `aqlPath` uses `events[at0006]` (archetype node ID), not `any_event`.

### Current Blocker

**FLAT format paths are consistently rejected by EHRBase 2.26.0** regardless of:
- Including or excluding event hierarchy
- Adding required fields (time, language, encoding)
- Following web template structure
- Following documentation examples

**Hypothesis**: The FLAT format implementation in EHRBase 2.26.0 may:
1. Require a different path structure not documented in the web template
2. Have different requirements for this specific "IDCR - Vital Signs Encounter.v1" template
3. Need additional context or composition-level fields we haven't identified

### Solution: CANONICAL Format

Created comprehensive integration tests using **CANONICAL JSON format** (`tests/integration/test_canonical_format.py`), which:
- ✅ Uses RM classes directly (COMPOSITION, OBSERVATION, SECTION, DV_QUANTITY)
- ✅ Doesn't require web template knowledge
- ✅ Maps directly to openEHR specifications
- ✅ Provides reliable baseline for composition CRUD operations

## Conclusion

Integration testing infrastructure is **complete and working**. CANONICAL format tests provide a solid baseline for composition operations. FLAT format remains blocked despite retrieving the web template and testing multiple path structures based on both documentation and web template analysis.

**Recommended Actions**:
1. ✅ **DONE**: Use CANONICAL format for integration tests
2. ⏸️ **DEFERRED**: Investigate FLAT format with EHRBase team or wait for clearer documentation/examples
3. ⏸️ **DEFERRED**: Consider FLAT format as a "nice-to-have" rather than essential feature

---

## Appendix: Example Error Output

```python
openehr_sdk.client.ehrbase.ValidationError: Could not consume Parts [
    vital_signs/vital_signs:0/blood_pressure:0/any_event:0/time,
    vital_signs/vital_signs:0/blood_pressure:0/any_event:0/systolic|magnitude,
    vital_signs/vital_signs:0/blood_pressure:0/any_event:0/systolic|unit,
    vital_signs/vital_signs:0/blood_pressure:0/any_event:0/diastolic|magnitude,
    vital_signs/vital_signs:0/blood_pressure:0/any_event:0/diastolic|unit
]
```

This error indicates EHRBase cannot map any of the provided FLAT paths to the template structure, suggesting a fundamental mismatch in path construction.
