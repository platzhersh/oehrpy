# Compatibility

## Python

| Python Version | Supported |
|---------------|-----------|
| 3.10 | Yes |
| 3.11 | Yes |
| 3.12 | Yes |
| 3.13 | Yes |
| < 3.10 | No — uses modern type hints (`X | None`, `list[str]`) |

## openEHR Reference Model

The SDK targets **openEHR RM 1.1.0** exclusively. This version is backward compatible with RM 1.0.4, with the following additions:

- **DV_SCALE** — New data type for decimal scale values (DV_ORDINAL only supports integers)
- **preferred_term** — Optional field in DV_CODED_TEXT for terminology mapping
- **Enhanced Folder support** — Archetypeable meta-data in EHR folders

See [ADR-0001: RM 1.1.0 Support](../adr/0001-odin-parsing-and-rm-1.1.0-support.md) for the decision rationale.

## EHRBase

| EHRBase Version | Supported | Notes |
|----------------|-----------|-------|
| 2.26.0+ | Yes | Uses new FLAT format with composition tree IDs |
| 2.0–2.25 | Partial | FLAT format structure differs |
| 1.x | No | Completely different FLAT format |

!!! warning "FLAT Format Breaking Changes"
    EHRBase 2.0+ introduced breaking changes to the FLAT format. This SDK implements the **new format** used by EHRBase 2.26.0+. For details, see the [FLAT Format Versions](../FLAT_FORMAT_VERSIONS.md) guide.

## Key Dependencies

| Package | Minimum Version | Purpose |
|---------|----------------|---------|
| `pydantic` | 2.0 | Data validation and RM classes |
| `httpx` | 0.25 | Async HTTP client for EHRBase |
| `defusedxml` | 0.7 | Safe XML parsing for OPT files |
