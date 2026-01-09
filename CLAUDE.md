# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**oehrpy** (pronounced /oʊ.ɛər.paɪ/ "o-air-pie") is a comprehensive Python SDK for openEHR that provides type-safe Reference Model classes, template-specific composition builders, EHRBase client, and AQL query builder. The project addresses the gap in the openEHR ecosystem where no comprehensive, actively maintained Python SDK exists.

## Key Commands

### Development Setup
```bash
# Install in editable mode with dev dependencies
pip install -e ".[dev,generator]"
```

### Testing
```bash
# Run all tests with verbose output
pytest tests/ -v

# Run tests with coverage
pytest tests/ -v --tb=short --cov=src/openehr_sdk --cov-report=term-missing

# Run specific test file
pytest tests/test_templates.py -v
```

### Linting and Formatting
```bash
# Run ruff linter
ruff check .

# Run ruff formatter
ruff format .

# Check formatting without changes
ruff format --check .
```

### Type Checking
```bash
# Run mypy on the SDK
mypy src/openehr_sdk
```

### Code Generation

**Regenerate RM classes from BMM/JSON Schema:**
```bash
# Default: generates from RM 1.1.0 JSON Schema
python -m generator.pydantic_generator
```

**Generate builder from OPT file:**
```bash
python examples/generate_builder_from_opt.py path/to/template.opt
```

## Architecture

### Core Components

**1. Reference Model (RM) Classes** (`src/openehr_sdk/rm/`)
- 134 Pydantic v2 models for openEHR RM 1.1.0 types (includes BASE types)
- Generated code from BMM/JSON Schema specifications
- Located in single `rm_types.py` module to avoid circular imports
- All classes support Pydantic v2 validation

**2. Serialization Layer** (`src/openehr_sdk/serialization/`)
- **Canonical JSON** (`canonical.py`): Converts RM objects to/from openEHR canonical JSON format (with `_type` fields)
- **FLAT Format** (`flat.py`): EHRBase FLAT format support - flattens hierarchical compositions into dot-separated paths
  - `FlatPath`: Parses FLAT paths (e.g., `"vital_signs/bp:0/systolic|magnitude"`)
  - `FlatContext`: Handles composition context fields (`ctx/language`, `ctx/composer_name`, etc.)
  - `FlatBuilder`: Fluent API for constructing FLAT format compositions

**3. Template System** (`src/openehr_sdk/templates/`)
- **OPT Parser** (`opt_parser.py`): Parses OPT 1.4 XML files to extract template definitions, archetype constraints, and terminology bindings
- **Builder Generator** (`builder_generator.py`): Auto-generates type-safe Python builder classes from OPT files
- **Pre-built Builders** (`builders.py`): Template-specific builders (e.g., VitalSignsBuilder)
- Key workflow: OPT XML → Parser → Template Definition → Builder Generator → Python Builder Class

**4. EHRBase Client** (`src/openehr_sdk/client/ehrbase.py`)
- Async REST client for EHRBase CDR operations
- Uses httpx for async HTTP
- Supports EHR creation, composition CRUD, and AQL queries
- Handles multiple composition formats (CANONICAL, FLAT, STRUCTURED)

**5. AQL Query Builder** (`src/openehr_sdk/aql/builder.py`)
- Fluent API for building type-safe AQL queries
- Avoids manual string concatenation errors

**6. Code Generator** (`generator/`)
- **BMM Parser** (`bmm_parser.py`): Parses BMM JSON specifications
- **JSON Schema Parser** (`json_schema_parser.py`): Parses JSON Schema files from specifications-ITS-JSON
- **Pydantic Generator** (`pydantic_generator.py`): Generates Pydantic models from parsed schemas
- Generates all 134 RM classes into single `rm_types.py` module

### Design Patterns

**Generated Code Convention:**
- RM classes use UPPERCASE naming (e.g., `DV_QUANTITY`, `CODE_PHRASE`) to match openEHR specifications
- Generated code has special linting rules in `pyproject.toml` (allows N801, N817, etc.)
- `rm_types.py` uses `# type: ignore` for type-arg to allow untyped lists in generated code

**FLAT Format Paths:**
- Hierarchical structure flattened to dot-separated keys
- Index notation: `:0`, `:1` for repeating elements
- Attribute separator: `|` for data type attributes
- Example: `"vital_signs/blood_pressure:0/any_event:0/systolic|magnitude"`

**Builder Pattern:**
- Template builders provide type-safe composition construction
- Fluent API with method chaining
- Auto-generate builders from OPT files to eliminate manual FLAT path construction

### Important Files

- **`src/openehr_sdk/rm/rm_types.py`**: All 134 generated RM classes (large file, ~10k lines)
- **`generator/pydantic_generator.py`**: Core code generation logic
- **`pyproject.toml`**: Build config, dependencies, tool settings (mypy, ruff, pytest)
- **`.github/workflows/ci.yml`**: CI pipeline (lint → type-check → test)

## RM Version Support

The SDK uses **openEHR RM 1.1.0** as the default and only version. Key differences from 1.0.4:
- **DV_SCALE**: New data type for decimal scale values (DV_ORDINAL only supports integers)
- **preferred_term**: Optional field in DV_CODED_TEXT for terminology mapping
- RM 1.1.0 is backward compatible with 1.0.4

See `docs/adr/0001-odin-parsing-and-rm-1.1.0-support.md` for the decision rationale.

## Testing Strategy

Tests are organized by component:
- `test_rm_types.py`: RM class instantiation and validation
- `test_serialization.py`: Canonical JSON and FLAT format conversion
- `test_templates.py`: OPT parsing and builder generation
- `test_aql.py`: AQL query builder
- `test_flat.py`: FLAT path parsing and context handling

Tests use `pytest-asyncio` for async client tests.

### Integration Testing

**Status:** Fully implemented with conditional CI execution

Integration tests validate the SDK against a real EHRBase CDR instance. Tests are located in `tests/integration/` and cover:
- **EHR operations** (`test_ehr_operations.py`): Create, retrieve, and query EHRs
- **Composition operations** (`test_compositions.py`): CRUD operations with VitalSignsBuilder and FLAT format
- **AQL queries** (`test_aql_queries.py`): Query execution, parameters, aggregations, pagination
- **Round-trip workflows** (`test_round_trip.py`): End-to-end scenarios including template upload

**Running integration tests locally:**

```bash
# Start EHRBase with Docker Compose
docker-compose up -d

# Wait for services to be healthy (may take 60-90 seconds)
docker-compose ps

# Run integration tests
pytest tests/ -m integration -v

# Run specific integration test file
pytest tests/integration/test_ehr_operations.py -v

# Clean up when done
docker-compose down -v
```

**Note:** The `docker-compose.yml` uses `ehrbase/ehrbase:2.0.0` and `ehrbase/ehrbase-v2-postgres:16.2` images. If you encounter database initialization issues, ensure the PostgreSQL image has the required extensions (`uuid-ossp`, `temporal_tables`).

**CI Execution:**
- Integration tests run conditionally (not on every PR):
  - Automatically on pushes to `main` or `develop` branches
  - On PRs labeled with `integration`
  - Uses GitHub Actions service containers for EHRBase + PostgreSQL
- Unit tests always run (fast feedback on every PR)

**Test Configuration:**
- Tests use `@pytest.mark.integration` marker
- Fixtures in `tests/integration/conftest.py` handle:
  - EHRBase client setup with authentication
  - Test EHR creation
  - Template upload (Vital Signs OPT)
  - Health checks before running tests
- Environment variables (auto-configured in CI, customizable locally):
  - `EHRBASE_URL`: Default `http://localhost:8080/ehrbase`
  - `EHRBASE_USER`: Default `ehrbase-user`
  - `EHRBASE_PASSWORD`: Default `SuperSecretPassword`

## Ruff Configuration

Per-file ignores in `pyproject.toml`:
- `src/openehr_sdk/rm/*.py`: N801, N817, E402, SIM105 (generated code)
- `generator/*.py`: E501, F541, F401 (generator code)
- `src/openehr_sdk/templates/opt_parser.py`: N817 (allows ET acronym for ElementTree)

## Python Version Support

Requires Python 3.10+ (uses modern type hints like `X | None`, `list[str]`)

## Key Dependencies

**Runtime:**
- `pydantic>=2.0`: Data validation and RM classes
- `httpx>=0.25`: Async HTTP client for EHRBase
- `defusedxml>=0.7`: Safe XML parsing for OPT files

**Development:**
- `pytest`, `pytest-asyncio`: Testing
- `mypy`: Type checking (strict mode enabled)
- `ruff`: Linting and formatting

**Generator:**
- `jinja2>=3.0`: Template rendering for code generation
- `lxml>=4.9`: XML processing for OPT parsing
