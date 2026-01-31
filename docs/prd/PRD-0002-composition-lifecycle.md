# PRD-0002: Composition Lifecycle (Update & Versioning)

**Version:** 1.0
**Date:** 2026-01-31
**Status:** Draft
**Owner:** Open CIS Project
**Priority:** P0 (Critical)

---

## Executive Summary

Extend the oehrpy SDK to support the full composition lifecycle: updating/amending existing compositions and retrieving prior versions. These capabilities are fundamental to clinical data management — without them, records are write-once and audit history is inaccessible.

This PRD covers two tightly coupled gaps identified in the oehrpy gap analysis:
1. **Composition Update/Amendment** — `PUT /ehr/{ehr_id}/composition/{uid}`
2. **Composition Versioning** — retrieving compositions at a point in time, listing version history, and accessing the versioned composition container

---

## Problem Statement

oehrpy currently supports creating and deleting compositions but provides no way to:

1. **Amend a composition** — Clinicians routinely correct errors, add addenda, or update status fields on existing records. The openEHR model supports this through versioning: each update creates a new version while preserving the original.

2. **Retrieve previous versions** — Regulatory requirements (e.g., HIPAA, GDPR health data provisions) mandate access to the full history of changes to a clinical record. Without version retrieval, there is no way to answer "what did this record say last Tuesday?"

3. **List version history** — Governance workflows need to enumerate all versions of a composition to display audit trails, compare changes, or roll back.

---

## Requirements

### Functional Requirements

#### FR-1: Update Composition

| Field | Detail |
|---|---|
| Endpoint | `PUT /ehr/{ehr_id}/composition/{versioned_object_uid}` |
| SDK method | `EHRBaseClient.update_composition(ehr_id, versioned_object_uid, preceding_version_uid, template_id, composition, format)` |
| Input | EHR ID, `versioned_object_uid` (the composition's UUID, used in the request path), `preceding_version_uid` (the full version string, e.g. `uuid::domain::1`, sent in the `If-Match` header per RFC 7232), template ID, updated composition body, format (CANONICAL / FLAT / STRUCTURED) |
| Output | Updated composition with new version UID |
| Headers | `If-Match: {preceding_version_uid}` for optimistic concurrency |

- Must support all three composition formats (CANONICAL, FLAT, STRUCTURED)
- Must return the new version UID on success
- Must raise a clear error on version conflict (HTTP 412 Precondition Failed, per RFC 7232 `If-Match` semantics)
- Must raise a clear error if the composition has been deleted (HTTP 404)

#### FR-2: Get Composition at Version

| Field | Detail |
|---|---|
| Endpoint | `GET /ehr/{ehr_id}/composition/{versioned_object_uid}` with `version_at_time` parameter |
| SDK method | `EHRBaseClient.get_composition_at_time(ehr_id, versioned_object_uid, version_at_time, format)` |
| Input | EHR ID, `versioned_object_uid` (the composition's UUID), ISO 8601 timestamp, optional format |
| Output | Composition as it existed at the given point in time |

#### FR-3: Get Versioned Composition

| Field | Detail |
|---|---|
| Endpoint | `GET /ehr/{ehr_id}/versioned_composition/{versioned_object_uid}` |
| SDK method | `EHRBaseClient.get_versioned_composition(ehr_id, versioned_object_uid)` |
| Output | Versioned composition metadata (UID, owner ID, time created) |

#### FR-4: Get Version by Version UID

| Field | Detail |
|---|---|
| Endpoint | `GET /ehr/{ehr_id}/versioned_composition/{versioned_object_uid}/version/{version_uid}` |
| SDK method | `EHRBaseClient.get_composition_version(ehr_id, versioned_object_uid, version_uid)` |
| Output | Specific version of the composition with full audit metadata |

#### FR-5: List Composition Versions

| Field | Detail |
|---|---|
| Endpoint | `GET /ehr/{ehr_id}/versioned_composition/{versioned_object_uid}/version` |
| SDK method | `EHRBaseClient.list_composition_versions(ehr_id, versioned_object_uid)` |
| Output | List of version descriptors (version UID, commit audit, lifecycle state) |

### Non-Functional Requirements

- **NFR-1**: All new methods must be async (consistent with existing client)
- **NFR-2**: Optimistic concurrency via `If-Match` must be handled transparently — the caller passes the preceding version UID and the SDK sets the header
- **NFR-3**: Version conflict errors (HTTP 412 Precondition Failed) must raise a typed `PreconditionFailedError` exception
- **NFR-4**: Full test coverage with both unit tests (mocked HTTP) and integration tests against EHRBase

---

## API Design

```python
# Update a composition
new_version_uid = await client.update_composition(
    ehr_id=ehr_id,
    versioned_object_uid=versioned_object_uid,
    preceding_version_uid=preceding_version_uid,
    template_id="vital_signs",
    composition=updated_flat_data,
    format=CompositionFormat.FLAT,
)

# Get composition as it was at a specific time
old_composition = await client.get_composition_at_time(
    ehr_id=ehr_id,
    versioned_object_uid=versioned_object_uid,
    version_at_time="2026-01-15T10:00:00Z",
)

# List all versions
versions = await client.list_composition_versions(
    ehr_id=ehr_id,
    versioned_object_uid=versioned_object_uid,
)
```

---

## Testing Strategy

- **Unit tests**: Mock HTTP responses for each endpoint, verify request construction (headers, URL, body)
- **Integration tests**: Create → Update → Retrieve version history against EHRBase 2.0
- **Edge cases**: Version conflict (concurrent update), deleted composition, invalid timestamp format

---

## Success Criteria

1. All five SDK methods implemented and passing integration tests against EHRBase 2.0
2. Version conflict handling works correctly with `If-Match` / HTTP 412
3. Round-trip test: create → update → retrieve both versions → verify content differs
