# PRD-0005: EHR Management & Query Extensions

**Version:** 1.0
**Date:** 2026-01-31
**Status:** Draft
**Owner:** Open CIS Project
**Priority:** P2 (Medium)

---

## Executive Summary

Round out the oehrpy SDK's REST API coverage by adding three independent feature groups:

1. **EHR Directory** — Folder-based organization of compositions within an EHR
2. **EHR Status Updates** — Modify EHR metadata (subject link, modifiable flag, active/inactive)
3. **Stored Queries** — Register, retrieve, and execute named AQL queries on the server

These are medium-value, low-to-medium effort additions that complete the SDK's coverage of the openEHR REST API.

---

## Problem Statement

After PRDs 0002–0004, three areas of the openEHR REST API remain uncovered:

1. **No folder organization** — All compositions in an EHR exist as a flat list. Clinical systems typically organize records by episode, department, or encounter type using the EHR Directory (FOLDER structure). Without this, applications must implement their own organization layer outside of openEHR.

2. **No EHR status management** — Once an EHR is created, its metadata cannot be modified. There is no way to link a subject after creation, mark an EHR as non-modifiable (locked), or deactivate it.

3. **No stored query support** — Every AQL query must be sent in full on each request. Production systems benefit from registering commonly used queries once and executing them by name with parameters, reducing payload size and enabling server-side query optimization.

---

## Requirements

### Feature Group 1: EHR Directory

#### FR-1.1: Create / Update Directory

| Field | Detail |
|---|---|
| Endpoint | `PUT /ehr/{ehr_id}/directory` |
| SDK method | `EHRBaseClient.update_directory(ehr_id, directory)` |
| Input | EHR ID, FOLDER structure (name, folders, items) |
| Output | Updated directory with version UID |

#### FR-1.2: Get Directory

| Field | Detail |
|---|---|
| Endpoint | `GET /ehr/{ehr_id}/directory` |
| SDK method | `EHRBaseClient.get_directory(ehr_id, version_at_time=None, path=None)` |
| Input | EHR ID, optional timestamp, optional sub-path |
| Output | FOLDER structure |

#### FR-1.3: Delete Directory

| Field | Detail |
|---|---|
| Endpoint | `DELETE /ehr/{ehr_id}/directory` |
| SDK method | `EHRBaseClient.delete_directory(ehr_id, preceding_version_uid)` |
| Input | EHR ID, preceding version UID |
| Output | None (HTTP 204) |

#### FR-1.4: Directory Builder

Helper for constructing FOLDER hierarchies:

```python
directory = (
    DirectoryBuilder()
    .add_folder("episodes", items=[composition_ref_1])
    .add_folder("encounters/2026-01", items=[composition_ref_2, composition_ref_3])
    .build()
)

await client.update_directory(ehr_id, directory)
```

### Feature Group 2: EHR Status Updates

#### FR-2.1: Get EHR Status

| Field | Detail |
|---|---|
| Endpoint | `GET /ehr/{ehr_id}/ehr_status` |
| SDK method | `EHRBaseClient.get_ehr_status(ehr_id)` |
| Output | EHR_STATUS object (subject, is_modifiable, is_queryable) |

#### FR-2.2: Update EHR Status

| Field | Detail |
|---|---|
| Endpoint | `PUT /ehr/{ehr_id}/ehr_status` |
| SDK method | `EHRBaseClient.update_ehr_status(ehr_id, status, preceding_version_uid)` |
| Input | EHR ID, updated EHR_STATUS, preceding version UID (If-Match) |
| Output | Updated EHR_STATUS with new version UID |

Common use cases:
- Link a subject (patient) to an EHR after anonymous creation
- Mark an EHR as non-modifiable (locked for legal hold)
- Set `is_queryable` to false to exclude from AQL queries

### Feature Group 3: Stored Queries

#### FR-3.1: Register Query

| Field | Detail |
|---|---|
| Endpoint | `PUT /definition/query/{qualified_query_name}/{version}` |
| SDK method | `EHRBaseClient.register_query(name, version, aql, query_type="AQL")` |
| Input | Qualified name (e.g., `org.example::vitals_latest`), version, AQL string |
| Output | Query definition metadata |

#### FR-3.2: Get Query Definition

| Field | Detail |
|---|---|
| Endpoint | `GET /definition/query/{qualified_query_name}/{version}` |
| SDK method | `EHRBaseClient.get_query(name, version=None)` |
| Output | Stored query definition (name, version, AQL text, saved timestamp) |

#### FR-3.3: List Stored Queries

| Field | Detail |
|---|---|
| Endpoint | `GET /definition/query` |
| SDK method | `EHRBaseClient.list_queries()` |
| Output | List of registered query definitions |

#### FR-3.4: Execute Stored Query

| Field | Detail |
|---|---|
| Endpoint | `GET /query/{qualified_query_name}/{version}` |
| SDK method | `EHRBaseClient.execute_stored_query(name, version=None, params=None, fetch=None, offset=None)` |
| Input | Query name, optional version, optional parameters dict, optional pagination |
| Output | AQL result set (same format as ad-hoc query execution) |

```python
# Register a reusable query
await client.register_query(
    name="org.example::latest_bp",
    version="1.0.0",
    aql="SELECT c FROM COMPOSITION c WHERE c/archetype_details/template_id/value = 'vital_signs' ORDER BY c/context/start_time DESC LIMIT 1",
)

# Execute by name with parameters
result = await client.execute_stored_query(
    name="org.example::latest_bp",
    version="1.0.0",
)
```

### Non-Functional Requirements

- **NFR-1**: All methods async, consistent with existing client
- **NFR-2**: Directory operations must use `If-Match` for optimistic concurrency (same pattern as PRD-0002)
- **NFR-3**: Stored query names must follow the openEHR qualified name format (`{namespace}::{query-name}`)

---

## Testing Strategy

- **Unit tests**: Mock HTTP for all endpoints, verify request/response mapping
- **Integration tests**:
  - Directory: Create directory → add compositions → retrieve by path → delete
  - EHR Status: Create EHR → update status → verify changes persist
  - Stored Queries: Register → list → execute → verify results match ad-hoc query
- **Edge cases**: Directory version conflicts, updating locked EHR, executing non-existent stored query

---

## Success Criteria

1. All three feature groups implemented with full unit test coverage
2. Integration tests passing against EHRBase 2.0
3. Directory builder provides a usable API for constructing folder hierarchies
4. Stored queries round-trip correctly (register → execute → same results as ad-hoc)
