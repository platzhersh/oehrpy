# 2. Integration Testing with EHRBase

Date: 2026-01-08

## Status

Accepted

## Context

The oehrpy SDK provides a REST client for EHRBase CDR operations and serialization to/from EHRBase FLAT format (see PRD-0000 Phase 3: REST Client & Integration). While we have comprehensive unit tests for individual components (RM types, serialization, OPT parsing, AQL building), we lack integration tests that validate the complete workflow against a real EHRBase instance.

**Gap identified:**
- Unit tests validate internal logic but don't verify actual CDR compatibility
- No validation that generated FLAT format works with real EHRBase
- No testing of round-trip operations (create → retrieve → deserialize)
- No verification of AQL queries against real data
- Template upload and composition submission workflows untested

**Why integration tests matter:**
1. **EHRBase API compatibility** - Ensure our client works with actual EHRBase versions
2. **FLAT format validation** - Verify our FLAT serialization matches EHRBase expectations
3. **Template handling** - Test OPT upload and template-based composition creation
4. **Real-world workflows** - Validate end-to-end use cases (create EHR → upload template → submit composition → query)
5. **Version compatibility** - Detect breaking changes in EHRBase releases early

**CI/CD considerations:**
- Integration tests are slower (require EHRBase + PostgreSQL startup)
- Every PR doesn't need full integration validation
- Main branch and releases should be fully validated
- Developers need ability to run integration tests locally

## Decision

We will implement integration testing with the following approach:

### 1. Test Organization

**Pytest markers:**
- Unit tests: No marker (default, fast)
- Integration tests: `@pytest.mark.integration` (requires EHRBase)

**File structure:**
```text
tests/
├── test_rm_types.py           # Unit tests
├── test_serialization.py      # Unit tests
├── test_templates.py          # Unit tests
├── test_aql.py                # Unit tests
├── test_flat.py               # Unit tests
└── integration/
    ├── __init__.py
    ├── conftest.py            # Integration fixtures (EHRBase client, template upload)
    ├── test_ehr_operations.py # EHR create/read/update
    ├── test_compositions.py   # Composition CRUD with real templates
    ├── test_aql_queries.py    # AQL execution against real data
    └── test_round_trip.py     # End-to-end workflows
```

### 2. CI Strategy: Conditional Integration Tests

**GitHub Actions approach:**

- **Unit tests**: Run on every PR, push to any branch (fast feedback)
  - Command: `pytest tests/ -m "not integration"`
  - No EHRBase required
  - ~30 seconds execution time

- **Integration tests**: Run conditionally (comprehensive validation)
  - Trigger conditions:
    - Pushes to `main` or `develop` branches
    - Pull requests with `integration` label
    - Manual workflow dispatch
  - Command: `pytest tests/ -m integration`
  - Requires EHRBase + PostgreSQL service containers

**Rationale:**
- Saves CI time - most PRs don't need full integration validation
- Main branch always fully validated before deployment
- Developers can request integration tests when needed (add label)
- Maintains fast feedback loop for typical development

### 3. EHRBase Deployment in CI: Service Containers

Use GitHub Actions **service containers** instead of Docker Compose.

**Configuration:**
```yaml
services:
  postgres:
    image: postgres:14
    env:
      POSTGRES_DB: ehrbase
      POSTGRES_USER: ehrbase
      POSTGRES_PASSWORD: ehrbase
    options: >-
      --health-cmd pg_isready
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5
    ports:
      - 5432:5432

  ehrbase:
    image: ehrbase/ehrbase:2.0.0
    env:
      DB_URL: jdbc:postgresql://postgres:5432/ehrbase
      DB_USER: ehrbase
      DB_PASS: ehrbase
      SECURITY_AUTHTYPE: BASIC
      SECURITY_AUTHUSER: ehrbase-user
      SECURITY_AUTHPASSWORD: SuperSecretPassword
      SECURITY_AUTHADMINUSER: ehrbase-admin
      SECURITY_AUTHADMINPASSWORD: EvenMoreSecretPassword
    ports:
      - 8080:8080
    options: >-
      --health-cmd "curl -f http://localhost:8080/ehrbase/rest/status || exit 1"
      --health-interval 10s
      --health-timeout 5s
      --health-retries 15
```

**Rationale:**
- Native GitHub Actions feature (no custom scripts)
- Automatic container lifecycle management
- Health checks ensure EHRBase is ready before tests run
- Cleaner than docker-compose in CI context
- Consistent with GitHub Actions best practices

**EHRBase version:** `ehrbase/ehrbase:2.0.0`
- Latest stable 2.x release
- Full RM 1.1.0 support
- REST API compatible with our client

### 4. Local Development: Docker Compose

Provide `docker-compose.yml` for local integration testing:

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: ehrbase
      POSTGRES_USER: ehrbase
      POSTGRES_PASSWORD: ehrbase
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ehrbase"]
      interval: 10s
      timeout: 5s
      retries: 5

  ehrbase:
    image: ehrbase/ehrbase:2.0.0
    environment:
      DB_URL: jdbc:postgresql://postgres:5432/ehrbase
      DB_USER: ehrbase
      DB_PASS: ehrbase
      SECURITY_AUTHTYPE: BASIC
      SECURITY_AUTHUSER: ehrbase-user
      SECURITY_AUTHPASSWORD: SuperSecretPassword
      SECURITY_AUTHADMINUSER: ehrbase-admin
      SECURITY_AUTHADMINPASSWORD: EvenMoreSecretPassword
    ports:
      - "8080:8080"
    depends_on:
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/ehrbase/rest/status"]
      interval: 10s
      timeout: 5s
      retries: 15
```

**Developer workflow:**
```bash
# Start EHRBase locally
docker-compose up -d

# Wait for health check
docker-compose ps  # Check all services healthy

# Run integration tests
pytest tests/ -m integration -v

# Cleanup
docker-compose down -v
```

**Rationale:**
- Developers can test locally before pushing
- Same EHRBase version as CI
- Easy to debug integration issues
- Volumes can be persisted for inspection

### 5. Template Upload Strategy

Templates (OPT files) will be uploaded **as part of the integration test flow**, not pre-loaded into EHRBase image.

**Implementation:**
- `tests/integration/conftest.py` provides fixtures for template upload
- Each test that needs a template uses the fixture
- Templates located in `tests/fixtures/*.opt`

**Example:**
```python
# tests/integration/conftest.py

import pytest
from openehr_sdk.client import EHRBaseClient

@pytest.fixture
async def ehrbase_client():
    """Provide authenticated EHRBase client."""
    async with EHRBaseClient(
        base_url="http://localhost:8080/ehrbase",
        username="ehrbase-user",
        password="SuperSecretPassword"
    ) as client:
        yield client

@pytest.fixture
async def vital_signs_template(ehrbase_client):
    """Upload Vital Signs template and return template ID."""
    opt_path = "tests/fixtures/vital_signs.opt"
    template_id = await ehrbase_client.upload_template(opt_path)
    return template_id

# tests/integration/test_compositions.py

@pytest.mark.integration
async def test_create_composition(ehrbase_client, vital_signs_template):
    """Test creating a composition with VitalSignsBuilder."""
    from openehr_sdk.templates import VitalSignsBuilder

    # Create EHR
    ehr = await ehrbase_client.create_ehr()

    # Build composition
    builder = VitalSignsBuilder(composer_name="Dr. Test")
    builder.add_blood_pressure(systolic=120, diastolic=80)
    flat_data = builder.build()

    # Submit to EHRBase
    composition = await ehrbase_client.create_composition(
        ehr_id=ehr.ehr_id,
        template_id=vital_signs_template,
        composition=flat_data,
        format="FLAT"
    )

    assert composition.uid is not None
```

**Rationale:**
- **Explicit test dependencies** - Each test declares which templates it needs
- **Flexibility** - Easy to test with different template versions
- **Cleanliness** - No pre-seeded state in EHRBase
- **Debugging** - Clear what template was used for failing tests
- **Realism** - Tests the actual template upload workflow users will use

### 6. pytest Configuration

Add to `pyproject.toml`:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
markers = [
    "integration: marks tests as integration tests (require EHRBase)",
]
```

### 7. CI Workflow Structure

```yaml
jobs:
  test:
    name: Unit Tests
    runs-on: ubuntu-latest
    steps:
      # ... setup Python, install deps
      - name: Run unit tests
        run: pytest tests/ -m "not integration" -v --cov

  integration-test:
    name: Integration Tests
    runs-on: ubuntu-latest
    # Only run on main/develop or PRs with 'integration' label
    if: |
      github.ref == 'refs/heads/main' ||
      github.ref == 'refs/heads/develop' ||
      contains(github.event.pull_request.labels.*.name, 'integration')

    services:
      postgres:
        # ... postgres service config
      ehrbase:
        # ... ehrbase service config

    steps:
      # ... setup Python, install deps
      - name: Wait for EHRBase
        run: |
          timeout 60 bash -c 'until curl -f http://localhost:8080/ehrbase/rest/status; do sleep 2; done'

      - name: Run integration tests
        run: pytest tests/ -m integration -v
        env:
          EHRBASE_URL: http://localhost:8080/ehrbase
          EHRBASE_USER: ehrbase-user
          EHRBASE_PASSWORD: SuperSecretPassword
```

## Consequences

### Positive

- **Comprehensive validation** - Real-world EHRBase compatibility verified
- **Fast feedback** - Unit tests run quickly on every PR
- **Flexible CI** - Integration tests run when needed, not always
- **Developer-friendly** - Easy to run integration tests locally
- **Template testing** - Real OPT upload and composition workflows validated
- **Version tracking** - Pinned EHRBase version prevents surprises
- **Maintainable** - Service containers auto-managed by GitHub Actions

### Negative

- **CI complexity** - Two separate test jobs with different configurations
- **Longer CI time on main** - Integration tests add ~2-3 minutes to main branch builds
- **EHRBase version maintenance** - Need to periodically update `ehrbase:2.0.0` to newer versions
- **Template fixtures** - Need to maintain OPT files in `tests/fixtures/`

### Neutral

- **Two ways to run EHRBase** - docker-compose locally, service containers in CI (but same config)
- **Manual label required** - Developers must add `integration` label to PR if they want integration tests

## Implementation Checklist

- [ ] Add pytest `integration` marker to `pyproject.toml`
- [ ] Create `tests/integration/` directory structure
- [ ] Create `docker-compose.yml` for local development
- [ ] Add integration test job to `.github/workflows/ci.yml`
- [ ] Implement `conftest.py` with EHRBase client and template upload fixtures
- [ ] Write integration tests:
  - [ ] `test_ehr_operations.py` - EHR CRUD
  - [ ] `test_compositions.py` - Composition CRUD with templates
  - [ ] `test_aql_queries.py` - AQL execution
  - [ ] `test_round_trip.py` - End-to-end workflows
- [ ] Update CLAUDE.md with integration testing instructions
- [ ] Update README.md with integration testing section
- [ ] Document how to add `integration` label to PRs

## References

- [PRD-0000: Python openEHR SDK](../prd/PRD-0000-python-openehr-sdk.md) - Phase 3: REST Client & Integration
- [GitHub Actions Service Containers](https://docs.github.com/en/actions/using-containerized-services/about-service-containers)
- [EHRBase Docker Hub](https://hub.docker.com/r/ehrbase/ehrbase)
- [EHRBase REST API Documentation](https://ehrbase.readthedocs.io/en/latest/03_development/04_rest_api/index.html)
- [pytest markers documentation](https://docs.pytest.org/en/stable/how-to/mark.html)
