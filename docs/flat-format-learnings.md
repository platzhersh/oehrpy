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

## Important Context: No Formal FLAT Format Specification

### Key Finding from openEHR Community

**There is NO single formal specification for FLAT format across the openEHR ecosystem.**

According to [openEHR Discourse discussions](https://discourse.openehr.org/t/understanding-flat-composition-json/1720/4):

- FLAT format is **vendor-specific** - implementations differ between EHRScape, EHRbase, and other servers
- The `ctx/` prefix represents "shortcuts for RM fields extracted from deeper canonical structures"
- Formats are "purely concrete" (implementation-driven, not specification-driven)
- Ongoing harmonization efforts exist but no unified standard

### Why This Matters

**Without a formal specification:**
1. You **cannot** rely on documentation from one vendor for another vendor's implementation
2. You **must** use the `/example?format=FLAT` endpoint to discover actual format requirements
3. Format changes between versions (like EHRBase 1.x → 2.x) may not be documented
4. The "source of truth" is the running CDR instance, not documentation

**This explains:**
- Why EHRBase documentation shows outdated format (see [FLAT_FORMAT_VERSIONS.md](FLAT_FORMAT_VERSIONS.md))
- Why there's no migration guide for FLAT format changes
- Why we had to reverse-engineer the format from the `/example` endpoint

### Recommended Approach

**Always verify FLAT format against your specific CDR version:**

1. ✅ **Use `/example?format=FLAT` endpoint** - most reliable source
2. ✅ **Inspect WebTemplate `tree.id` values** - basis for path construction
3. ✅ **Test against real CDR instance** - verify format acceptance
4. ❌ **Don't assume documentation is current** - may describe different version/vendor

## Resources

### Official Documentation
- EHRBase 2.26.0: https://hub.docker.com/r/ehrbase/ehrbase
- openEHR Discourse: https://discourse.openehr.org/
- openEHR Serial Data Formats: https://specifications.openehr.org/releases/SM/latest/serial_data_formats.html
  - **Note:** This spec covers JSON serialization of RM types, NOT FLAT path construction
- FLAT Format Discussion: https://discourse.openehr.org/t/understanding-flat-composition-json/1720

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
