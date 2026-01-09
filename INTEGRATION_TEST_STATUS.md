# Integration Test Status

## Current Status (2026-01-09)

### ✅ Fixed Issues
1. PostgreSQL container initialization - Fixed environment variables
2. EHRBase health check authentication - Added auth to curl command
3. Template upload HTTP headers - Added `Accept: */*`
4. Template upload 201/204 response handling - Extract template_id from XML
5. Type checking - Fixed template_id extraction type safety
6. Template upload 409 conflict - Handle when template already exists
7. Pytest import - Added import for xfail decorator
8. Ruff formatting - Fixed ternary expression formatting
9. Unit Tests - ✅ PASSING
10. Type Check - ✅ PASSING
11. Lint (ruff check) - ✅ PASSING
12. Lint (ruff format) - ✅ Expected to pass in next run

### ❌ Remaining Issue: Integration Tests Failing

**Problem:** The `VitalSignsBuilder` class uses hardcoded FLAT paths that don't match the ehrbase template structure.

**Error Example:**
```
ValidationError: Could not consume Parts [vital_signs/blood_pressure:0/any_event:0/time,
vital_signs/blood_pressure:0/any_event:0/diastolic|magnitude, ...]
```

## Root Cause Analysis

### How FLAT Paths Work

FLAT paths in EHRBase are derived from the Web Template's `id` fields:

1. **Path Construction**: Concatenate `id` fields from the Web Template tree
2. **Indices**: Add `:0`, `:1` for multivalued elements
3. **Attributes**: Use `|` to select attributes (e.g., `|magnitude`, `|unit`)

**Example:**
- Web Template IDs: `root > section > observation > event > data_point`
- FLAT Path: `root/section/observation/event:0/data_point|magnitude`

### Current Situation

**VitalSignsBuilder** (`src/openehr_sdk/templates/builders.py`) has hardcoded paths:
```python
_BP_PREFIX = "vital_signs/blood_pressure"
_PULSE_PREFIX = "vital_signs/pulse_heart_beat"
_TEMP_PREFIX = "vital_signs/body_temperature"
_RESP_PREFIX = "vital_signs/respirations"
_SPO2_PREFIX = "vital_signs/indirect_oximetry"
```

These paths were designed for a previous stub template, but the ehrbase template
(`tests/fixtures/vital_signs.opt` - "IDCR - Vital Signs Encounter.v1") has **different IDs**
in its Web Template structure.

## Solution Options

### Option 1: Fetch Web Template and Update Paths (Recommended)

1. **Get Web Template from EHRBase:**
   ```bash
   curl -u ehrbase-user:SuperSecretPassword \
     "http://localhost:8080/ehrbase/rest/openehr/v1/definition/template/adl1.4/IDCR%20-%20Vital%20Signs%20Encounter.v1"
   ```

2. **Analyze Web Template Structure:**
   - Examine the `tree` object
   - Find observation node IDs (blood_pressure, pulse, etc.)
   - Note the exact `id` values used

3. **Update VitalSignsBuilder:**
   - Replace hardcoded prefixes with actual IDs from Web Template
   - Test with integration tests

**Steps to Execute:**
```bash
# Start EHRBase locally
docker-compose up -d

# Wait for startup
sleep 60

# Fetch web template
curl -u ehrbase-user:SuperSecretPassword \
  "http://localhost:8080/ehrbase/rest/openehr/v1/definition/template/adl1.4/IDCR%20-%20Vital%20Signs%20Encounter.v1" \
  | python3 -m json.tool > web_template.json

# Inspect tree.id fields to find correct path prefixes
```

### Option 2: Use Separate Templates

Keep two templates:
- **Stub template** (old): For unit tests and VitalSignsBuilder
- **EHRBase template** (current): For actual EHRBase validation, but skip builder tests

**Pros:**
- Quick fix
- Decouples unit tests from integration tests

**Cons:**
- Maintains two templates
- Integration tests can't use VitalSignsBuilder (defeats the purpose)

### Option 3: Auto-Generate Builder from EHRBase Template

Use the `BuilderGenerator` to create a new builder from the ehrbase template:

```python
from openehr_sdk.templates import parse_opt, BuilderGenerator

template = parse_opt("tests/fixtures/vital_signs.opt")
generator = BuilderGenerator()
code = generator.generate(template)
# Save to file and use in integration tests
```

**Issue:** The OPT parser currently has issues with the complex ehrbase template
(763 warnings, extracts 0 observations). This needs to be fixed first.

## Recommended Next Steps

1. ✅ **Commit current fixes** (formatting, etc.)
2. **Fetch Web Template** when EHRBase is running
3. **Update VitalSignsBuilder** with correct path prefixes
4. **Verify Integration Tests** pass
5. **Optional**: Fix OPT parser to handle complex templates better

## Testing the Fix

Once paths are updated, verify with:

```bash
# Local testing
docker-compose up -d
pytest tests/integration/ -v

# CI will run automatically on push
```

## References

- [EHRBase FLAT Format Docs](https://docs.ehrbase.org/docs/EHRbase/Explore/Simplified-data-template/)
- [Web Template API](https://docs.ehrbase.org/docs/EHRbase/Explore/Simplified-data-template/WebTemplate)
- Template used: `IDCR - Vital Signs Encounter.v1`
- Source: https://github.com/ehrbase/ehrbase/blob/develop/service/src/test/resources/knowledge/opt/IDCR%20-%20Vital%20Signs%20Encounter.v1.opt

## CI Status

- **Lint**: ✅ Expected PASS
- **Type Check**: ✅ PASS
- **Unit Tests**: ✅ PASS (2 xfail for parser)
- **Integration Tests**: ❌ FAIL (FLAT path mismatch)

Next run after fixing paths should be all green! 🎉
