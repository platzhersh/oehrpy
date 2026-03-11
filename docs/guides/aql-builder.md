# AQL Query Builder

!!! note "Phase 2"
    This guide is planned for Phase 2 of the documentation site. For now, see the [Quick Start](../getting-started/quick-start.md#aql-query-builder) for usage examples.

## Overview

The AQL (Archetype Query Language) builder provides a fluent API for constructing type-safe queries, avoiding manual string concatenation errors.

## Basic Usage

```python
from openehr_sdk.aql import AQLBuilder

query = (
    AQLBuilder()
    .select("c/uid/value", alias="composition_id")
    .select("c/context/start_time/value", alias="time")
    .from_ehr()
    .contains_composition()
    .contains_observation(
        archetype_id="openEHR-EHR-OBSERVATION.blood_pressure.v1"
    )
    .where_ehr_id()
    .order_by_time(descending=True)
    .limit(100)
    .build()
)

print(query.to_string())
```

## Query Parameters

Use named parameters with `:param_name` syntax for safe query parameterization:

```python
result = await client.query(
    "SELECT c FROM EHR e CONTAINS COMPOSITION c "
    "WHERE e/ehr_id/value = :ehr_id",
    query_parameters={"ehr_id": ehr.ehr_id},
)
```
