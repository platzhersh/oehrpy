# FLAT Format Learnings - EHRBase 2.26.0

## Date: 2026-01-09

## Critical Discovery

EHRBase 2.26.0 uses a **completely different FLAT format** than documented in the SDK test data and examples. The format has fundamentally changed, making previous SDK examples incompatible.

## Format Differences

### Old Format (SDK Test Data - DOES NOT WORK)

```json
{
  "ehrn_vital_signs.v2/language|terminology": "ISO_639-1",
  "ehrn_vital_signs.v2/language|code": "fr",
  "ehrn_vital_signs.v2/composer|name": "Renaud Subiger",
  "ehrn_vital_signs.v2/vital_signs:0/blood_pressure:0/any_event:0/systolic|magnitude": 120.0,
  "ehrn_vital_signs.v2/vital_signs:0/blood_pressure:0/any_event:0/systolic|unit": "mm[Hg]"
}
```

**Characteristics:**
- Uses template ID as prefix (`ehrn_vital_signs.v2/...`)
- Uses `:0` index notation for repeating elements
- Includes `/any_event:0/` in observation paths
- Simple context format

### New Format (EHRBase 2.26.0+ - WORKS)

```json
{
  "vital_signs_observations/category|code": "433",
  "vital_signs_observations/category|value": "event",
  "vital_signs_observations/category|terminology": "openehr",
  "vital_signs_observations/context/start_time": "2026-01-09T12:00:00Z",
  "vital_signs_observations/context/setting|code": "238",
  "vital_signs_observations/context/setting|value": "other care",
  "vital_signs_observations/context/setting|terminology": "openehr",
  "vital_signs_observations/vital_signs/blood_pressure/systolic|magnitude": 120.0,
  "vital_signs_observations/vital_signs/blood_pressure/systolic|unit": "mm[Hg]",
  "vital_signs_observations/vital_signs/blood_pressure/diastolic|magnitude": 80.0,
  "vital_signs_observations/vital_signs/blood_pressure/diastolic|unit": "mm[Hg]",
  "vital_signs_observations/vital_signs/blood_pressure/time": "2026-01-09T12:00:00Z",
  "vital_signs_observations/vital_signs/blood_pressure/language|code": "en",
  "vital_signs_observations/vital_signs/blood_pressure/language|terminology": "ISO_639-1",
  "vital_signs_observations/vital_signs/blood_pressure/encoding|terminology": "IANA_character-sets",
  "vital_signs_observations/vital_signs/blood_pressure/encoding|code": "UTF-8",
  "vital_signs_observations/language|terminology": "ISO_639-1",
  "vital_signs_observations/language|code": "en",
  "vital_signs_observations/territory|code": "US",
  "vital_signs_observations/territory|terminology": "ISO_3166-1",
  "vital_signs_observations/composer|name": "Test User"
}
```

**Characteristics:**
- Uses composition tree ID as prefix (`vital_signs_observations/...`)
- NO `:0` index notation
- NO `/any_event:0/` paths
- Direct hierarchical paths: `composition_id/section_id/observation_id/element`
- Rich context structure with `context/start_time` and `context/setting`
- Each level includes language, territory, encoding metadata
- Category field is required at composition level

## Key Structural Rules

### 1. Path Structure

**Pattern:** `{composition_tree_id}/{section_id}/{observation_id}/{element_id}`

**Example:**
- Composition ID: `vital_signs_observations` (from web template root)
- Section ID: `vital_signs` (from template section)
- Observation ID: `blood_pressure` (from template observation)
- Element: `systolic` (from archetype)

**Path:** `vital_signs_observations/vital_signs/blood_pressure/systolic|magnitude`

### 2. Required Fields

#### Composition Level (Root)
```json
{
  "{composition_id}/category|code": "433",
  "{composition_id}/category|value": "event",
  "{composition_id}/category|terminology": "openehr",
  "{composition_id}/language|terminology": "ISO_639-1",
  "{composition_id}/language|code": "en",
  "{composition_id}/territory|terminology": "ISO_3166-1",
  "{composition_id}/territory|code": "US",
  "{composition_id}/composer|name": "Composer Name"
}
```

#### Context Level
```json
{
  "{composition_id}/context/start_time": "2026-01-09T12:00:00Z",
  "{composition_id}/context/setting|code": "238",
  "{composition_id}/context/setting|value": "other care",
  "{composition_id}/context/setting|terminology": "openehr"
}
```

#### Observation Level
```json
{
  "{composition_id}/{section}/{observation}/language|code": "en",
  "{composition_id}/{section}/{observation}/language|terminology": "ISO_639-1",
  "{composition_id}/{section}/{observation}/encoding|code": "UTF-8",
  "{composition_id}/{section}/{observation}/encoding|terminology": "IANA_character-sets",
  "{composition_id}/{section}/{observation}/time": "2026-01-09T12:00:00Z"
}
```

### 3. Data Type Attributes

Use `|` separator for data type attributes:

**DV_QUANTITY:**
```json
{
  "path/to/element|magnitude": 120.0,
  "path/to/element|unit": "mm[Hg]"
}
```

**DV_CODED_TEXT:**
```json
{
  "path/to/element|code": "433",
  "path/to/element|value": "event",
  "path/to/element|terminology": "openehr"
}
```

**DV_DATE_TIME:**
```json
{
  "path/to/element": "2026-01-09T12:00:00Z"
}
```

## How to Get Correct FLAT Format

### Method 1: Web Template Inspection

1. Download the web template:
   ```bash
   curl -u user:pass \
     "http://localhost:8080/ehrbase/rest/openehr/v1/definition/template/adl1.4/{template_id}" \
     > web_template.json
   ```

2. Extract the composition tree ID from `tree.id` field
3. Navigate `tree.children` to find section and observation IDs
4. Build paths: `{tree.id}/{section.id}/{observation.id}/{element.id}`

### Method 2: Example Endpoint (Most Reliable)

Request a FLAT example directly from EHRBase:

```bash
curl -u user:pass \
  "http://localhost:8080/ehrbase/rest/openehr/v1/definition/template/adl1.4/{template_id}/example?format=FLAT" \
  | python3 -m json.tool
```

This returns a pre-populated FLAT composition with the exact path structure expected by EHRBase.

## Common Pitfalls

### ❌ Using Template ID as Prefix
```json
{
  "IDCR - Vital Signs Encounter.v1/vital_signs/blood_pressure/systolic|magnitude": 120
}
```
**Error:** "Could not consume Parts"

### ❌ Using Index Notation
```json
{
  "vital_signs_observations/vital_signs:0/blood_pressure:0/systolic|magnitude": 120
}
```
**Error:** "Could not consume Parts"

### ❌ Including /any_event/ in Paths
```json
{
  "vital_signs_observations/vital_signs/blood_pressure/any_event:0/systolic|magnitude": 120
}
```
**Error:** "Could not consume Parts"

### ❌ Using ctx/ for Context
```json
{
  "ctx/language": "en",
  "ctx/territory": "US"
}
```
**Error:** Incomplete composition, missing required fields

### ✅ Correct Format
```json
{
  "vital_signs_observations/vital_signs/blood_pressure/systolic|magnitude": 120,
  "vital_signs_observations/vital_signs/blood_pressure/systolic|unit": "mm[Hg]",
  "vital_signs_observations/language|code": "en",
  "vital_signs_observations/language|terminology": "ISO_639-1"
}
```

## SDK Implementation Changes

### FlatContext Changes
- `to_flat()` now accepts `prefix` parameter
- Default: `"ctx"` (legacy format)
- EHRBase 2.26.0+: Use composition tree ID (e.g., `"vital_signs_observations"`)

### FlatBuilder Changes
- Constructor accepts `composition_prefix` parameter
- Auto-generates category fields when prefix is set
- Auto-generates context/start_time and context/setting if not provided

### VitalSignsBuilder Changes
- Always uses `composition_prefix="vital_signs_observations"`
- Paths changed from `vital_signs/blood_pressure:0` to `vital_signs_observations/vital_signs/blood_pressure`
- Removed event_index parameters (no longer needed)
- Added language and encoding fields to all observations

## Testing

### Successful Tests
1. ✅ Manual FLAT submission (`test_correct_flat.sh`): HTTP 204
2. ✅ Builder-generated FLAT (`test_builder_ehrbase.sh`): HTTP 204

### Format Verification Checklist

Before submitting FLAT format to EHRBase 2.26.0:

- [ ] Uses composition tree ID prefix (not template ID)
- [ ] No `:0`, `:1` index notation in paths
- [ ] No `/any_event/` in observation paths
- [ ] Includes `category|code`, `category|value`, `category|terminology`
- [ ] Includes `context/start_time` and `context/setting`
- [ ] Includes `language|code` and `language|terminology` at composition level
- [ ] Includes `territory|code` and `territory|terminology` at composition level
- [ ] Includes `composer|name`
- [ ] Each observation includes `language`, `encoding`, and `time` fields
- [ ] All DV_QUANTITY have both `|magnitude` and `|unit`
- [ ] All DV_CODED_TEXT have `|code`, `|value`, and `|terminology`

## Important Context: FLAT Format Specification and Variants

### Key Finding: Specification Exists But EHRBase 2.26.0 Diverges

**Correcting earlier assessment:** A formal specification DOES exist, but EHRBase 2.26.0 doesn't follow it completely.

#### Official Specification: simSDT

The **[simSDT (Simplified Data Template)](https://specifications.openehr.org/releases/ITS-REST/latest/simplified_data_template.html)** was standardized in 2019:

- Based on Marand's (Better platform) "web template" FLAT format
- **Uses `:0`, `:1` indexing notation** for array elements
- Part of official openEHR ITS-REST specifications
- Standardization closed [GitHub issue #56](https://github.com/openEHR/specifications-ITS-REST/issues/56)

**Example from specification:**
```json
{
  "/context/participation:0": "Nurse|1345678::Jessica|...",
  "/context/participation:1": "Assistant|1345678::2.16.840.1.113883.2.1.4.3..."
}
```

#### FLAT Format Variants in the Ecosystem

According to [EtherCIS documentation](https://github.com/ethercis/ethercis/blob/master/doc/flat%20json.md):

**1. Marand FLAT Format** (Better Platform):
- Path/value pairs with human-readable node names
- Uses `:0`, `:1` indexing notation
- Template-dependent format
- Basis for simSDT specification

**2. ECISFLAT Format** (EtherCIS):
- AQL-based paths with archetype node IDs
- Uses bracket notation: `/content[openEHR-EHR-EVALUATION.name.v1]`
- Template-independent format
- More verbose

#### EHRBase 2.26.0's Divergence

**EHRBase 2.26.0 appears to have evolved beyond the 2019 simSDT spec:**

- ✅ Based on Marand's approach (composition tree IDs)
- ❌ **Does NOT use `:0` indexing for single observations** (diverges from spec)
- ✅ Uses human-readable paths
- ❌ No `/any_event/` nodes (diverges from RM structure)

**This creates a three-way mismatch:**
1. **Official simSDT spec (2019)** → uses `:0` indexing
2. **EHRBase docs** → outdated format with template IDs
3. **EHRBase 2.26.0** → no indexing for single items, composition tree IDs

### Why This Matters

**Despite having a specification:**
1. EHRBase 2.26.0 **diverges from the official spec** (removed `:0` indexing)
2. EHRBase documentation is **outdated** (matches neither spec nor implementation)
3. Format changes between versions may not be documented
4. The "source of truth" is the running CDR instance, not spec or docs

**This explains:**
- Why EHRBase documentation shows outdated format (see [FLAT_FORMAT_VERSIONS.md](FLAT_FORMAT_VERSIONS.md))
- Why the official spec doesn't match EHRBase behavior
- Why there's no migration guide for FLAT format changes
- Why we had to reverse-engineer the format from the `/example` endpoint

### Recommended Approach

**Always verify FLAT format against your specific CDR version:**

1. ✅ **Use `/example?format=FLAT` endpoint** - most reliable source (implementation trumps spec)
2. ✅ **Inspect WebTemplate `tree.id` values** - basis for path construction
3. ✅ **Test against real CDR instance** - verify format acceptance
4. ❌ **Don't assume spec/docs are current** - implementations may diverge

### Historical Context

According to [openEHR Discourse](https://discourse.openehr.org/t/understanding-flat-composition-json/1720/4):

- The `ctx/` prefix represents "shortcuts for RM fields extracted from deeper canonical structures"
- Multiple vendors developed different variants before 2019 standardization
- EHRBase appears to have evolved its implementation post-standardization
- Formats are somewhat "implementation-driven" despite formal specification

## Resources

### Official Specifications
- **simSDT (Simplified Data Template)**: https://specifications.openehr.org/releases/ITS-REST/latest/simplified_data_template.html
  - Official openEHR FLAT format specification (2019)
  - **Note:** EHRBase 2.26.0 diverges from this spec (no `:0` indexing)
- openEHR Serial Data Formats: https://specifications.openehr.org/releases/SM/latest/serial_data_formats.html
  - **Note:** This spec covers JSON serialization of RM types, NOT FLAT path construction

### Vendor Documentation
- EHRBase 2.26.0: https://hub.docker.com/r/ehrbase/ehrbase
- EtherCIS FLAT Format: https://github.com/ethercis/ethercis/blob/master/doc/flat%20json.md
  - Documents both Marand FLAT and ECISFLAT variants

### Community Discussion
- openEHR Discourse: https://discourse.openehr.org/
- FLAT Format Discussion: https://discourse.openehr.org/t/understanding-flat-composition-json/1720
- GitHub Issue #56 (Standardization): https://github.com/openEHR/specifications-ITS-REST/issues/56

### Key Endpoints
- Web Template: `GET /rest/openehr/v1/definition/template/adl1.4/{template_id}`
- FLAT Example: `GET /rest/openehr/v1/definition/template/adl1.4/{template_id}/example?format=FLAT`
- Submit FLAT: `POST /rest/openehr/v1/ehr/{ehr_id}/composition?format=FLAT&templateId={template_id}`

## Version Notes

- **EHRBase 2.26.0:** Uses new FLAT format (composition tree ID based)
- **EHRBase SDK Test Data:** Uses old FLAT format (template ID based)
- **Compatibility:** SDK test data is NOT compatible with EHRBase 2.26.0

## Lessons Learned

1. **Always use the example endpoint** to verify FLAT format structure
2. **Web template tree IDs** are the source of truth for path construction
3. **SDK test data may be outdated** - verify against running EHRBase instance
4. **Format differences are breaking** - no backward compatibility
5. **Error messages are cryptic** - "Could not consume Parts" means path structure is wrong
