# PRD-0001: ODIN Parser for openEHR - Future Project

**Version:** 1.0
**Date:** 2026-01-06
**Status:** Future / Not Started
**Owner:** Open CIS Project
**Priority:** P3 (Nice to Have)

---

## Executive Summary

This PRD documents a future project to build a Python ODIN (Object Data Instance Notation) parser for openEHR specifications. While not immediately needed (thanks to JSON Schema availability for RM 1.1.0 - see ADR-0001), an ODIN parser would provide:

1. **Direct access to canonical BMM specifications** without relying on Archie-generated JSON Schema
2. **Future-proofing** for openEHR releases where JSON Schema may not be available
3. **Broader applicability** for parsing ADL archetypes, OPT templates, and other ODIN-based formats
4. **Educational value** in understanding openEHR's native data formats

**Current Status**: This project is **postponed** in favor of using JSON Schema files for RM 1.1.0 (see ADR-0001). This PRD serves as documentation for potential future implementation.

---

## Background

### What is ODIN?

ODIN (Object Data Instance Notation) is a simple, human-readable data syntax used throughout the openEHR ecosystem:

- **BMM files**: Basic Meta-Model specifications defining the Reference Model
- **ADL files**: Archetype Definition Language files
- **OPT files**: Operational Template files (OPT 1.4 format)
- **Configuration files**: Various openEHR tooling configurations

ODIN is similar to JSON/YAML but with openEHR-specific features:
- Angle bracket notation for complex values: `value = <123>`
- Square bracket notation for object IDs: `[id1] = <...>`
- Terminology references: `<[ISO_639-1::en]>`
- Strongly typed values

### Why Not Needed Immediately?

The discovery of JSON Schema files for RM 1.1.0 in the `specifications-ITS-JSON` repository (see ADR-0001) means we can:
- Generate Pydantic models from JSON Schema using existing tools
- Avoid the complexity of implementing an ODIN parser
- Leverage well-maintained JSON Schema ecosystem

### Why Consider This Future Project?

Despite JSON Schema availability, an ODIN parser would be valuable because:

1. **Canonical Source**: BMM ODIN files are the authoritative specification format
2. **Independence**: No dependency on Archie's JSON Schema generation
3. **Broader Use Cases**:
   - Parse ADL archetypes directly
   - Parse OPT 1.4 templates (currently XML-based, but ODIN used in ADL 2)
   - Parse openEHR configuration files
4. **Community Contribution**: Python lacks a good ODIN parser
5. **Educational**: Deep understanding of openEHR formats

---

## Problem Statement

**Current Gap:**

The Python ecosystem lacks a robust, actively maintained ODIN parser. Existing options:
- **pyEHR**: Abandoned (~7 years unmaintained)
- **openEHR-Python**: Limited scope, no ODIN parser
- **Manual parsing**: Error-prone and not reusable

**Use Cases (Future):**

1. **Direct BMM Parsing**: Parse RM specifications from ODIN without JSON Schema intermediary
2. **ADL Archetype Parsing**: Load and validate archetypes in Python
3. **OPT Template Parsing**: Parse operational templates for code generation
4. **Validation**: Validate ODIN syntax in openEHR tools
5. **Conversion**: Convert between ODIN and other formats (JSON, YAML)

---

## Goals & Success Metrics

### Goals

1. **Parse BMM ODIN files** successfully for RM specifications
2. **Support core ODIN syntax** needed for openEHR use cases
3. **Provide clean Python API** for accessing parsed data
4. **Maintain compatibility** with openEHR ODIN specification
5. **Enable future expansions** (ADL parsing, OPT parsing)

### Success Metrics

| Metric | Target |
|--------|--------|
| BMM files parsed | 100% of RM 1.1.0 BMM files |
| ADL archetypes parsed | 90%+ of CKM archetypes (stretch) |
| Parse speed | < 1 second for typical BMM file |
| Python API coverage | All ODIN data types supported |
| Community adoption | 5+ external users/contributors |

### Non-Goals

- **Full ADL 2 parser** (focus on ODIN subset first)
- **GUI tools** (command-line and library only)
- **ODIN serialization** (parsing only, not generation - future enhancement)

---

## Technical Requirements

### Phase 1: Core ODIN Parser (MVP)

**Priority:** P0 (Must Have for MVP)

#### 1.1 Lexer/Tokenizer

Parse ODIN syntax into tokens:

```python
from odin_parser import OdinLexer

lexer = OdinLexer()
tokens = lexer.tokenize("""
    bmm_version = <"2.3">
    rm_publisher = <"openehr">
""")
# [('IDENTIFIER', 'bmm_version'), ('EQUALS', '='), ('VALUE_START', '<'), ...]
```

**Token Types:**
- Identifiers: `bmm_version`, `schema_name`
- Values: strings, numbers, booleans, dates
- Delimiters: `<`, `>`, `[`, `]`, `=`
- Comments: `--` line comments

#### 1.2 Parser

Build AST (Abstract Syntax Tree) from tokens:

```python
from odin_parser import OdinParser

parser = OdinParser()
ast = parser.parse_file("openehr_rm_data_types_110.bmm")
# Returns structured data representation
```

**Supported Structures:**
- **Attributes**: `key = <value>`
- **Objects**: `<attr1 = <...>; attr2 = <...>>`
- **Lists**: `<["1"] = <...>; ["2"] = <...>>`
- **Nested objects**: Multiple levels of nesting
- **Primitive types**: String, Integer, Real, Boolean, Date/Time

#### 1.3 Data Model

Python objects representing parsed ODIN:

```python
from dataclasses import dataclass
from typing import Any, Dict, List

@dataclass
class OdinObject:
    """Represents an ODIN object with attributes."""
    attributes: Dict[str, Any]
    type_name: str | None = None

@dataclass
class OdinAttribute:
    """Represents a key-value attribute."""
    name: str
    value: Any

# Usage
schema = parser.parse_file("openehr_rm_data_types_110.bmm")
print(schema.attributes["bmm_version"])  # "2.3"
print(schema.attributes["rm_release"])   # "1.1.0"
```

#### 1.4 Python API

Clean interface for accessing parsed data:

```python
from odin_parser import parse_odin_file, parse_odin_string

# Parse from file
data = parse_odin_file("path/to/file.bmm")

# Parse from string
odin_str = 'version = <"1.0">'
data = parse_odin_string(odin_str)

# Access data
assert data["version"] == "1.0"
```

### Phase 2: BMM-Specific Features (Stretch)

**Priority:** P1 (Should Have)

#### 2.1 BMM Schema Loader

Load BMM schemas with includes:

```python
from odin_parser.bmm import BmmSchemaLoader

loader = BmmSchemaLoader()
schema = loader.load_schema("openehr_rm_data_types_110.bmm")

# Automatically resolves includes
assert "DV_QUANTITY" in schema.classes
assert "Real" in schema.primitive_types
```

#### 2.2 Type Resolution

Resolve BMM type references:

```python
# BMM defines inheritance and references
dv_quantity = schema.get_class("DV_QUANTITY")
assert "DV_AMOUNT" in dv_quantity.ancestors

magnitude_prop = dv_quantity.properties["magnitude"]
assert magnitude_prop.type == "Real"
```

### Phase 3: ADL/OPT Support (Future)

**Priority:** P2 (Nice to Have)

- Parse ADL archetypes (using ODIN for data blocks)
- Parse OPT 1.4 templates
- Validate archetype constraints

---

## Architecture

### Component Structure

```
odin_parser/
├── __init__.py           # Public API
├── lexer.py              # Tokenization
├── parser.py             # AST building
├── data_model.py         # Python data structures
├── bmm/
│   ├── __init__.py
│   ├── schema_loader.py  # BMM-specific loading
│   └── types.py          # BMM type system
└── exceptions.py         # Error handling
```

### Example ODIN Syntax

**Simple Attributes:**
```odin
bmm_version = <"2.3">
rm_publisher = <"openehr">
schema_name = <"rm_data_types">
rm_release = <"1.1.0">
```

**Objects:**
```odin
includes = <
    ["1"] = <
        id = <"openehr_base_1.1.0">
    >
>
```

**Nested Structures:**
```odin
packages = <
    ["org.openehr.rm.data_types"] = <
        name = <"org.openehr.rm.data_types">
        classes = <
            ["DV_QUANTITY"] = <
                name = <"DV_QUANTITY">
                ancestors = <"DV_AMOUNT", ...>
                properties = <
                    ["magnitude"] = <
                        name = <"magnitude">
                        type = <"Real">
                        is_mandatory = <True>
                    >
                >
            >
        >
    >
>
```

**Terminology References:**
```odin
language = <[ISO_639-1::en]>
territory = <[ISO_3166-1::US]>
```

---

## Implementation Plan

### Milestone 1: ODIN Lexer (1-2 weeks)

- [ ] Implement tokenizer for ODIN syntax
- [ ] Handle strings, numbers, booleans, dates
- [ ] Support comments (`--`)
- [ ] Handle brackets `<>`, `[]`, `=`
- [ ] Write lexer tests

**Deliverable:** Working tokenizer with comprehensive tests

### Milestone 2: ODIN Parser (2-3 weeks)

- [ ] Build parser using lexer tokens
- [ ] Create AST data structures
- [ ] Handle nested objects and lists
- [ ] Support all ODIN data types
- [ ] Write parser tests

**Deliverable:** Parse simple ODIN files into Python objects

### Milestone 3: BMM Schema Support (2-3 weeks)

- [ ] Parse BMM-specific structures
- [ ] Handle schema includes
- [ ] Resolve type references
- [ ] Build BMM class hierarchy
- [ ] Test with RM 1.1.0 BMM files

**Deliverable:** Successfully parse all RM 1.1.0 BMM files

### Milestone 4: Documentation & Publishing (1 week)

- [ ] Write comprehensive documentation
- [ ] Create usage examples
- [ ] Publish to PyPI as `odin-parser`
- [ ] Write blog post about implementation

**Deliverable:** Published package with documentation

---

## Technical Decisions

### Parser Implementation Approach

**Decision:** Hand-written recursive descent parser

**Rationale:**
- ODIN grammar is relatively simple
- No need for parser generator (PLY, ANTLR)
- Better error messages
- Easier to maintain and understand

**Alternatives Considered:**
- **PLY (Python Lex-Yacc)**: Overkill for simple grammar
- **ANTLR**: Requires external tool, adds complexity
- **Lark**: Good option, but hand-written is simpler

### Data Representation

**Decision:** Hybrid approach - dict-like for flexibility, dataclasses for BMM

**Rationale:**
- ODIN is dynamic (unknown structure at parse time)
- Use dicts for general ODIN
- Use dataclasses for known structures (BMM schemas)

---

## Dependencies

**Python Packages:**
- No required dependencies for core parser (stdlib only)
- Optional: `dataclasses` (Python 3.7+)
- Testing: `pytest`
- Type checking: `mypy`

**Development Tools:**
- ODIN specification for reference
- BMM files from specifications-ITS-BMM
- ADL files from CKM (for testing)

---

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| ODIN spec incomplete | High | Low | Cross-reference with existing parsers (Java ADL Tools) |
| Complex edge cases | Medium | Medium | Start with BMM subset, expand gradually |
| Low adoption | Low | Medium | Market as general ODIN parser, not just openEHR |
| Maintenance burden | Medium | High | Keep scope focused on parsing only |

---

## Success Criteria

**Phase 1 Complete When:**
- [ ] Can parse 100% of RM 1.1.0 BMM files
- [ ] All ODIN data types supported
- [ ] Comprehensive test coverage (>90%)

**Project Complete When:**
- [ ] Published on PyPI
- [ ] Documentation site live
- [ ] At least 1 external user/contributor
- [ ] Successfully used in oehrpy generator

---

## Alternatives Considered

### Alternative 1: Use Existing ODIN Parser

**Rejected** because:
- No actively maintained Python ODIN parser exists
- pyEHR is abandoned
- Java/JavaScript parsers not suitable for Python ecosystem

### Alternative 2: Convert ODIN to JSON Manually

**Rejected** because:
- Not scalable
- Error-prone
- Defeats purpose of having canonical ODIN format

### Alternative 3: Use JSON Schema (Current Approach)

**ACCEPTED** for RM 1.1.0 (see ADR-0001).

**Why this PRD still valuable:**
- Future-proofing for RM versions without JSON Schema
- Broader use cases (ADL, OPT parsing)
- Independence from Archie-generated schemas

---

## Timeline

**If Prioritized:**

- Milestone 1: Weeks 1-2 (Lexer)
- Milestone 2: Weeks 3-5 (Parser)
- Milestone 3: Weeks 6-8 (BMM Support)
- Milestone 4: Week 9 (Documentation)

**Total Effort:** ~9 weeks (1 developer)

**Current Status:** Not scheduled (P3 priority)

---

## Future Considerations

### Beyond BMM Parsing

1. **ADL Archetype Parsing**: Parse CKM archetypes
2. **OPT Template Parsing**: Parse operational templates
3. **ODIN Serialization**: Generate ODIN from Python objects
4. **Schema Validation**: Validate ODIN against BMM schemas
5. **CLI Tools**: Command-line utilities for ODIN operations

### Integration Points

- **oehrpy Generator**: Use ODIN parser instead of JSON
- **Archetype Validator**: Validate ADL files
- **Template Compiler**: Compile OPT to Python builders

---

## References

- [ODIN Specification](https://specifications.openehr.org/releases/LANG/latest/odin.html)
- [specifications-ITS-BMM Repository](https://github.com/openEHR/specifications-ITS-BMM)
- [ADL Workbench](https://github.com/openEHR/adl-tools) - Reference implementation (Eiffel)
- [Archie](https://github.com/openEHR/archie) - Java implementation with ODIN support
- [ADR-0001: Support RM 1.1.0 Using JSON Schema](../adr/0001-odin-parsing-and-rm-1.1.0-support.md)
- [ODIN GitHub Repository](https://github.com/openEHR/odin) - Examples and documentation

---

## Appendix A: ODIN Grammar Subset (Simplified)

```bnf
odin_document ::= attribute*

attribute ::= IDENTIFIER '=' value

value ::= '<' primitive '>'
        | '<' object '>'
        | '<' list '>'

primitive ::= STRING
            | INTEGER
            | REAL
            | BOOLEAN
            | DATE
            | DATETIME
            | terminology_ref

object ::= attribute* ( ';' attribute* )*

list ::= list_item ( ';' list_item )*

list_item ::= '[' STRING ']' '=' value

terminology_ref ::= '[' IDENTIFIER '::' IDENTIFIER ']'

STRING ::= '"' .* '"'
INTEGER ::= [0-9]+
REAL ::= [0-9]+ '.' [0-9]+
BOOLEAN ::= 'True' | 'False'
```

---

## Appendix B: Example Parser Usage

```python
from odin_parser import parse_odin_file
from odin_parser.bmm import BmmSchemaLoader

# Parse a simple ODIN file
data = parse_odin_file("config.odin")
print(data["version"])

# Load a BMM schema
loader = BmmSchemaLoader()
schema = loader.load_schema("openehr_rm_data_types_110.bmm")

# Access BMM class definitions
dv_quantity = schema.get_class("DV_QUANTITY")
print(f"Ancestors: {dv_quantity.ancestors}")
print(f"Properties: {list(dv_quantity.properties.keys())}")

# Use in code generation (future)
from generator.pydantic_generator import generate_from_bmm_schema

generate_from_bmm_schema(
    schema,
    output_dir="src/openehr_sdk/rm",
    rm_version="1.1.0"
)
```

---

**Note:** This PRD documents a future project that is **not currently prioritized**. The immediate focus is on implementing RM 1.1.0 support using JSON Schema files (see ADR-0001).
