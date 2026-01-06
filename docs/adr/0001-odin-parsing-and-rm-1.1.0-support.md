# 1. Add ODIN Parsing for RM 1.1.0 and Future Version Support

Date: 2026-01-06

## Status

Accepted

## Context

The project currently supports openEHR Reference Model (RM) 1.0.4 by parsing BMM (Basic Meta-Model) files in JSON format. However, RM 1.1.0 is the latest published release (September 2020) and brings important improvements:

- **DV_SCALE**: New data type for scales/scores with decimal values (extends DV_ORDINAL which only supports integers)
- **preferred_term field**: Added to DV_CODED_TEXT for better terminology mapping in integration scenarios
- **Enhanced Folder support**: Archetypeable meta-data, unlimited folder hierarchies

### The Problem

RM 1.1.0 BMM specifications are **not available in JSON format**. The openEHR specifications-ITS-BMM repository provides:

- **RM 1.0.4**: Available in JSON, ODIN, XML, and YAML formats
- **RM 1.1.0**: Available in **ODIN format only** (.bmm files)
- **RM latest**: Available in ODIN format only

Our current `bmm_parser.py` only supports JSON format, which blocks us from supporting RM 1.1.0 and future versions.

### Backward Compatibility Considerations

RM 1.1.0 is **backward compatible** with 1.0.4:
- All 1.0.4 types remain unchanged
- New types and fields are additive only
- No breaking changes to existing structures

This means:
- Code written against 1.0.4 types will work with 1.1.0
- Only consumers who need the new features (DV_SCALE, preferred_term) need to explicitly use them
- Compositions created with 1.1.0 SDK can work with 1.0.4-compliant CDRs (as long as new 1.1.0-specific features aren't used)

### Version Selection Question

Should users be able to specify which RM version they want to use at runtime (e.g., `openehr_sdk.rm.v1_0_4.DV_QUANTITY` vs `openehr_sdk.rm.v1_1_0.DV_QUANTITY`)?

**Arguments against multi-version support:**
- Significant complexity in code generation and package structure
- RM 1.1.0 is backward compatible, so 1.0.4 code works with 1.1.0 classes
- CDRs (like EHRBase) are moving to support 1.1.0
- Violates YAGNI (You Aren't Gonna Need It) principle
- Users can choose which features to use, not which version to import

**Arguments for multi-version support:**
- Some legacy systems may strictly validate against 1.0.4
- Testing and research scenarios
- Gradual migration path

## Decision

We will:

1. **Add ODIN parsing support** to the BMM parser (`generator/bmm_parser.py`)
   - ODIN is a simple, YAML-like format used by openEHR
   - This makes the generator future-proof for upcoming RM releases

2. **Generate RM classes from 1.1.0 by default**
   - The generated package will use RM 1.1.0 as the default and only version
   - All classes will be available at `openehr_sdk.rm.*` (no version namespacing)

3. **Make the generator version-agnostic**
   - The generator will accept a `--rm-version` parameter (e.g., `1.0.4`, `1.1.0`, `latest`)
   - This allows developers to regenerate against different versions if needed
   - Default generator behavior: use RM 1.1.0

4. **Do NOT expose version selection to end users**
   - No runtime version switching
   - No parallel imports like `from openehr_sdk.rm.v1_0_4 import DV_QUANTITY`
   - Users get RM 1.1.0 classes, period

5. **Document compatibility and migration**
   - Clearly document that the SDK uses RM 1.1.0
   - Provide guidance on which features are 1.1.0-specific
   - Note that most 1.1.0 features are backward compatible with 1.0.4 systems

## Consequences

### Positive

- **Future-proof**: Can support RM 1.2.0, 1.3.0, etc. as they are released
- **Latest features**: Users get DV_SCALE, preferred_term, and other improvements immediately
- **Simpler codebase**: Single version reduces complexity
- **Aligns with ecosystem**: EHRBase and other CDRs are moving to 1.1.0 support
- **Better developer experience**: No confusion about which version to import

### Negative

- **Potential breaking change**: Users on strict 1.0.4-only systems may face validation issues
  - *Mitigation*: Document 1.1.0-specific features clearly
  - *Mitigation*: Provide migration guide from 1.0.4 to 1.1.0

- **ODIN parser complexity**: Need to implement a new parser
  - *Mitigation*: ODIN is simpler than JSON Schema, similar to YAML
  - *Mitigation*: Can leverage existing ODIN libraries if available

- **Cannot use 1.0.4 JSON files anymore**: Must use ODIN for 1.1.0
  - *Mitigation*: ODIN is the canonical format for BMM specifications
  - *Mitigation*: Parser will support both JSON (for 1.0.4) and ODIN (for 1.1.0+)

### Implementation Notes

1. **ODIN Parser Implementation**
   - Add `OdinParser` class in `generator/bmm_parser.py`
   - Support subset of ODIN needed for BMM files (not full ODIN spec)
   - Fall back to JSON parser for 1.0.4 compatibility

2. **Generator Updates**
   ```bash
   # Default: Generate from RM 1.1.0
   python -m generator.pydantic_generator

   # Explicit version selection (for development/testing)
   python -m generator.pydantic_generator --rm-version 1.1.0
   python -m generator.pydantic_generator --rm-version 1.0.4
   ```

3. **Documentation Updates**
   - README: Update to state RM 1.1.0 support
   - Migration guide: Document changes from 1.0.4 to 1.1.0
   - API docs: Mark 1.1.0-specific features (DV_SCALE, preferred_term)

4. **Testing**
   - Verify all 1.0.4 tests still pass with 1.1.0 classes
   - Add tests for new 1.1.0 features
   - Test compatibility with EHRBase RM 1.1.0 support

### Migration Path for Users

For users currently on 1.0.4:

```python
# Before (implied 1.0.4)
from openehr_sdk.rm import DV_QUANTITY, DV_CODED_TEXT

# After (explicit 1.1.0, but same imports work)
from openehr_sdk.rm import DV_QUANTITY, DV_CODED_TEXT

# New 1.1.0 features (optional)
from openehr_sdk.rm import DV_SCALE  # New in 1.1.0

# DV_CODED_TEXT now has preferred_term field
coded_text = DV_CODED_TEXT(
    value="Hypertension",
    defining_code=CODE_PHRASE(...),
    preferred_term="High blood pressure"  # New in 1.1.0, optional
)
```

## Alternatives Considered

### Alternative 1: Stay on RM 1.0.4

**Rejected** because:
- Misses valuable improvements (DV_SCALE, preferred_term)
- Falls behind the ecosystem
- Will eventually need to upgrade anyway

### Alternative 2: Manual JSON Conversion

Convert ODIN files to JSON manually for 1.1.0.

**Rejected** because:
- Not scalable for future versions
- Error-prone manual process
- Doesn't solve the fundamental problem

### Alternative 3: Support Multiple Versions at Runtime

Generate classes for both 1.0.4 and 1.1.0, allowing users to choose.

**Rejected** because:
- Significant complexity in code generation and package structure
- Backward compatibility makes this unnecessary
- Violates YAGNI principle
- Can revisit if real-world usage demands it

### Alternative 4: Request JSON Files from openEHR

Ask the openEHR community to generate JSON versions of 1.1.0 BMM files.

**Rejected** as primary strategy because:
- ODIN is the canonical format for BMM
- Unlikely to be prioritized by the community
- Doesn't future-proof us for upcoming releases
- Note: Could still be pursued as a parallel effort

## References

- [openEHR RM 1.1.0 Release Announcement](https://discourse.openehr.org/t/openehr-reference-model-rm-release-1-1-0-published/997)
- [openEHR RM 1.1.0 Specifications](https://specifications.openehr.org/releases/RM/Release-1.1.0)
- [specifications-ITS-BMM Repository](https://github.com/openEHR/specifications-ITS-BMM)
- [ODIN Specification](https://specifications.openehr.org/releases/BASE/latest/odin.html)
- [PRD-0000: Python openEHR SDK](../prd/PRD-0000-python-openehr-sdk.md)
