# PRD-0003: Audit & Contributions

**Version:** 1.0
**Date:** 2026-01-31
**Status:** Draft
**Owner:** Open CIS Project
**Priority:** P1 (High)
**Depends on:** PRD-0002 (Composition Lifecycle)

---

## Executive Summary

Add support for openEHR Contributions — atomic changesets that group one or more composition changes with audit metadata. Contributions provide the answer to "who changed what, when, and why" and are required for regulatory compliance in any production clinical system.

---

## Problem Statement

Every composition change in openEHR is wrapped in a Contribution, but oehrpy currently ignores this layer entirely. This means:

1. **No audit trail** — There is no way to retrieve the provenance of a change (committer identity, timestamp, change description)
2. **No atomic multi-composition commits** — Clinical workflows sometimes require multiple compositions to be committed as a single logical unit (e.g., a medication order and a corresponding encounter note). Without Contributions, each composition is an independent request with no transactional grouping.
3. **Regulatory gaps** — Healthcare regulations require demonstrable audit trails. Without Contribution access, an oehrpy-based system cannot satisfy audit requirements.

---

## Requirements

### Functional Requirements

#### FR-1: Create Contribution

| Field | Detail |
|---|---|
| Endpoint | `POST /ehr/{ehr_id}/contribution` |
| SDK method | `EHRBaseClient.create_contribution(ehr_id, contribution)` |
| Input | EHR ID, Contribution object containing: list of version changes (each with composition + change type), audit details (committer, description, time) |
| Output | Contribution UID |

Change types per the openEHR spec:
- `creation` — new composition
- `amendment` — update to existing composition
- `modification` — structural change
- `deleted` — logical deletion

#### FR-2: Get Contribution

| Field | Detail |
|---|---|
| Endpoint | `GET /ehr/{ehr_id}/contribution/{contribution_uid}` |
| SDK method | `EHRBaseClient.get_contribution(ehr_id, contribution_uid)` |
| Output | Contribution object with audit metadata and list of version references |

### Model Requirements

#### MR-1: Contribution Model

A `Contribution` Pydantic model (or use the existing RM `CONTRIBUTION` class) with:
- `uid`: Contribution identifier
- `versions`: List of object references to the versioned objects included
- `audit`: `AUDIT_DETAILS` with committer, time_committed, change_type, description

#### MR-2: Contribution Builder

A helper to construct Contribution request bodies:

```python
contribution = (
    ContributionBuilder(ehr_id=ehr_id)
    .add_creation(template_id="vital_signs", composition=vitals_data)
    .add_amendment(uid=existing_uid, template_id="vital_signs", composition=updated_data)
    .set_audit(committer="Dr. Smith", description="Routine vitals and correction")
    .build()
)

uid = await client.create_contribution(ehr_id, contribution)
```

### Non-Functional Requirements

- **NFR-1**: Async methods consistent with existing client
- **NFR-2**: Audit details must support both minimal (auto-filled by server) and explicit (caller-provided) modes
- **NFR-3**: Full test coverage including multi-composition atomic commits

---

## Testing Strategy

- **Unit tests**: Mock HTTP, verify Contribution request body structure matches openEHR spec
- **Integration tests**:
  - Create a contribution with a single composition creation, retrieve it, verify audit fields
  - Create a contribution with multiple operations (create + amend), verify atomicity
  - Verify contribution UID appears in composition version metadata

---

## Success Criteria

1. `create_contribution()` and `get_contribution()` implemented and passing integration tests
2. `ContributionBuilder` provides a fluent API for multi-operation contributions
3. Audit metadata (committer, timestamp, description) round-trips correctly
