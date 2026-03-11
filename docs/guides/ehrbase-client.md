# EHRBase Client

!!! note "Phase 2"
    This guide is planned for Phase 2 of the documentation site. For now, see the [Quick Start](../getting-started/quick-start.md#ehrbase-rest-client) for usage examples.

## Overview

oehrpy includes an async REST client for [EHRBase](https://ehrbase.org/), supporting EHR creation, composition CRUD, and AQL queries. It uses `httpx` for async HTTP.

## Basic Usage

```python
from openehr_sdk.client import EHRBaseClient

async with EHRBaseClient(
    base_url="http://localhost:8080/ehrbase",
    username="admin",
    password="admin",
) as client:
    # Create an EHR
    ehr = await client.create_ehr()

    # Create a composition (FLAT format)
    result = await client.create_composition(
        ehr_id=ehr.ehr_id,
        template_id="IDCR - Vital Signs Encounter.v1",
        composition=flat_data,
        format="FLAT",
    )

    # Query with AQL
    query_result = await client.query(
        "SELECT c FROM EHR e CONTAINS COMPOSITION c "
        "WHERE e/ehr_id/value = :ehr_id",
        query_parameters={"ehr_id": ehr.ehr_id},
    )
```

## Supported Formats

The client supports three composition formats:

- **FLAT** — EHRBase-specific flat key-value format
- **CANONICAL** — openEHR canonical JSON with `_type` fields
- **STRUCTURED** — Hierarchical JSON structure

## Running EHRBase Locally

See the [Integration Testing](../integration-testing-journey.md) guide for Docker Compose setup.
