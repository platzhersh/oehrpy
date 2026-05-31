# PRD-0003: Audit & Contributions

**Version:** 2.0
**Date:** 2026-05-31
**Status:** Approved (ready for implementation)
**Owner:** Open CIS Project
**Priority:** P1 (High)
**Depends on:** PRD-0002 (Composition Lifecycle)
**Supersedes:** PRD-0003 v1.0 (Draft)

---

## Executive Summary

Add support for openEHR **Contributions** — atomic changesets that group one or
more versioned-object changes (compositions, and later EHR_STATUS / FOLDER) with
shared audit metadata. Contributions are the openEHR mechanism that answers
"who changed what, when, and why," and provide transactional grouping of
multiple changes into a single logical commit. They are required for regulatory
compliance in any production clinical system.

At the Reference Model level the SDK already generates the `CONTRIBUTION` and
`X_CONTRIBUTION` Pydantic classes (`src/oehrpy/rm/rm_types.py`). What is missing
is (a) the EHRBase client methods to commit and retrieve contributions, and
(b) a fluent builder to construct well-formed contribution request bodies.

---

## Problem Statement

Every composition change in openEHR is wrapped in a Contribution, but oehrpy
exposes only the composition layer today. The `EHRBaseClient`
(`src/oehrpy/client/ehrbase.py`) implements EHR, composition (incl.
versioned/at-time/version), and template operations, but **no** contribution
endpoints. This means:

1. **No audit trail access** — there is no way to retrieve the provenance of a
   change (committer identity, timestamp, change description, change type).
2. **No atomic multi-composition commits** — clinical workflows sometimes
   require multiple compositions to be committed as a single logical unit (e.g.,
   a medication order plus a corresponding encounter note). Without
   Contributions, each composition is an independent request with no
   transactional grouping; a partial failure leaves the record inconsistent.
3. **Regulatory gaps** — healthcare regulations require demonstrable audit
   trails. Without Contribution access, an oehrpy-based system cannot satisfy
   audit requirements.

---

## Goals & Non-Goals

### Goals

- Commit a contribution containing one or more composition changes atomically.
- Retrieve a contribution by UID, including its audit metadata and the list of
  version references it produced.
- Provide a fluent `ContributionBuilder` so callers do not hand-assemble the
  nested CANONICAL request body.
- Support all four openEHR change types: `creation`, `amendment`,
  `modification`, `deleted`.
- Support both **server-filled** audit (minimal input) and **caller-provided**
  audit (explicit committer/description).

### Non-Goals (this iteration)

- Contributions over EHR_STATUS and FOLDER versioned objects (compositions
  only for v2.0; tracked as a follow-up).
- FLAT-format versions inside a contribution. The openEHR/EHRBase contribution
  endpoint consumes **CANONICAL** `ORIGINAL_VERSION` wrappers; FLAT input is
  out of scope (see Open Questions).
- Listing all contributions for an EHR (no standard openEHR REST endpoint;
  use AQL instead).

---

## Background: openEHR Contribution REST contract

EHRBase exposes the standard openEHR REST CONTRIBUTION API:

| Operation | Method & Path |
|---|---|
| Commit contribution | `POST /rest/openehr/v1/ehr/{ehr_id}/contribution` |
| Get contribution | `GET /rest/openehr/v1/ehr/{ehr_id}/contribution/{contribution_uid}` |

The request body is a CANONICAL `CONTRIBUTION` whose `versions` array holds
`ORIGINAL_VERSION` objects, each wrapping the change to one versioned object:

```jsonc
{
  "_type": "CONTRIBUTION",
  "versions": [
    {
      "_type": "ORIGINAL_VERSION",
      // Required for amendment/modification/deleted; omit for creation:
      "preceding_version_uid": { "_type": "OBJECT_VERSION_ID", "value": "..::..::N" },
      "data": { "_type": "COMPOSITION", /* canonical composition */ },
      "lifecycle_state": {
        "_type": "DV_CODED_TEXT", "value": "complete",
        "defining_code": { "_type": "CODE_PHRASE",
          "terminology_id": { "_type": "TERMINOLOGY_ID", "value": "openehr" },
          "code_string": "532" }
      },
      "commit_audit": {
        "_type": "AUDIT_DETAILS",
        "change_type": {
          "_type": "DV_CODED_TEXT", "value": "creation",
          "defining_code": { "_type": "CODE_PHRASE",
            "terminology_id": { "_type": "TERMINOLOGY_ID", "value": "openehr" },
            "code_string": "249" }
        },
        "description": { "_type": "DV_TEXT", "value": "New vitals reading" }
      }
    }
  ],
  "audit": {
    "_type": "AUDIT_DETAILS",
    "committer": { "_type": "PARTY_IDENTIFIED", "name": "Dr. Smith" },
    "description": { "_type": "DV_TEXT", "value": "Routine vitals" }
  }
}
```

**openEHR change-type terminology codes** (terminology `openehr`):

| change_type | code_string |
|---|---|
| `creation` | `249` |
| `amendment` | `250` |
| `modification` | `251` |
| `deleted` | `523` |

Notes:
- For a **deletion**, the `data` field is omitted; only `preceding_version_uid`
  and a `change_type=deleted` audit are sent.
- `committer`/`time_committed` may be filled by the server when authentication is
  configured; the builder must allow omitting them.

---

## Requirements

### Functional Requirements

#### FR-1: Create / commit a Contribution

| Field | Detail |
|---|---|
| Endpoint | `POST /rest/openehr/v1/ehr/{ehr_id}/contribution` |
| SDK method | `EHRBaseClient.create_contribution(ehr_id, contribution)` |
| Input | `ehr_id: str`, `contribution: dict[str, Any]` (CANONICAL contribution body, typically from `ContributionBuilder.build()`) |
| Headers | `Prefer: return=representation`, `Content-Type: application/json` |
| Output | `ContributionResponse` (contribution UID + list of created version UIDs + audit) |
| Errors | `ValidationError` (422), `NotFoundError` (404 EHR), `PreconditionFailedError` (412 on amendment version mismatch) |

#### FR-2: Get a Contribution

| Field | Detail |
|---|---|
| Endpoint | `GET /rest/openehr/v1/ehr/{ehr_id}/contribution/{contribution_uid}` |
| SDK method | `EHRBaseClient.get_contribution(ehr_id, contribution_uid)` |
| Output | `ContributionResponse` with `uid`, `audit`, and `versions` (object references to the versioned objects included) |
| Errors | `NotFoundError` (404) |

Both methods are `async`, consistent with the existing client style
(`async def`, `await self.client.<verb>(...)`, `self._handle_response(...)`).

### Model Requirements

#### MR-1: ContributionResponse dataclass

A new `@dataclass ContributionResponse` alongside the existing response
dataclasses (`CompositionResponse`, `VersionedCompositionResponse`, etc.) in
`ehrbase.py`, with a `from_response(cls, data, ehr_id=None)` classmethod:

```python
@dataclass
class ContributionResponse:
    contribution_uid: str
    versions: list[str]          # version UIDs referenced by the contribution
    audit: dict[str, Any] | None
    ehr_id: str | None = None
```

The existing RM `CONTRIBUTION` / `X_CONTRIBUTION` classes remain the typed
model for callers who want full RM objects; `ContributionResponse` is the
lightweight client return type matching SDK conventions.

#### MR-2: ContributionBuilder (fluent API)

A `ContributionBuilder` (location: `src/oehrpy/client/contribution.py` or
`src/oehrpy/templates/` — to be confirmed at implementation) that assembles the
CANONICAL request body so callers never hand-write `ORIGINAL_VERSION` wrappers:

```python
from oehrpy.client import ContributionBuilder

contribution = (
    ContributionBuilder()
    .add_creation(composition=vitals_canonical)
    .add_amendment(
        preceding_version_uid="abc::ehrbase::1",
        composition=updated_canonical,
        description="Corrected systolic value",
    )
    .add_deletion(preceding_version_uid="def::ehrbase::2")
    .set_audit(committer="Dr. Smith", description="Routine vitals and correction")
    .build()
)

result = await client.create_contribution(ehr_id, contribution)
print(result.contribution_uid, result.versions)
```

Builder methods:

| Method | Purpose |
|---|---|
| `add_creation(composition, *, lifecycle_state="complete", description=None)` | Append a `creation` version (no preceding UID). |
| `add_amendment(preceding_version_uid, composition, *, description=None)` | Append an `amendment` version. |
| `add_modification(preceding_version_uid, composition, *, description=None)` | Append a `modification` version. |
| `add_deletion(preceding_version_uid, *, description=None)` | Append a `deleted` version (no `data`). |
| `set_audit(*, committer=None, description=None)` | Set the contribution-level audit. |
| `build()` | Return the assembled `dict[str, Any]` body; raise `ValueError` if no versions were added. |

The builder is responsible for emitting correct `_type`, change-type codes, and
terminology blocks per the table above. Compositions are accepted as already-
CANONICAL dicts (a CANONICAL composition can be produced from RM objects via the
existing `serialization/canonical.py` layer).

### Non-Functional Requirements

- **NFR-1**: Async methods consistent with the existing client; reuse
  `self._handle_response` and the existing exception hierarchy.
- **NFR-2**: Audit must support both minimal (server-filled committer/time) and
  explicit (caller-provided) modes.
- **NFR-3**: Builder output must validate against the openEHR CANONICAL schema
  for `CONTRIBUTION` (verified via integration commit succeeding).
- **NFR-4**: No new runtime dependencies.

---

## Public API Surface

Add to the `oehrpy.client` package exports:

- `EHRBaseClient.create_contribution`
- `EHRBaseClient.get_contribution`
- `ContributionResponse`
- `ContributionBuilder`

---

## Testing Strategy

### Unit tests (`tests/test_client.py` or new `tests/test_contributions.py`)
- Mock HTTP; assert `create_contribution` POSTs to the correct path with
  `Prefer: return=representation` and the builder-produced body.
- `ContributionBuilder` snapshot tests: each `add_*` method produces the correct
  `_type`, `change_type` code, `preceding_version_uid` presence/absence.
- `build()` raises `ValueError` when no versions added.
- `ContributionResponse.from_response` parses UID + version list from a sample
  EHRBase response payload.

### Integration tests (`tests/integration/test_contributions.py`, `@pytest.mark.integration`)
- Commit a contribution with a single composition **creation**; retrieve it;
  assert audit fields and that exactly one version UID is returned.
- Commit a multi-operation contribution (**create + amend**); assert atomicity
  and two version UIDs.
- Commit an **amendment** with a stale `preceding_version_uid`; assert
  `PreconditionFailedError` (412) and that no partial change was applied.
- Verify the returned `contribution_uid` is retrievable via `get_contribution`.

---

## Rollout & Documentation

- Update `README.md` client capability table to list contribution support.
- Add a short "Contributions & audit" usage section with the builder example.
- Add a `CHANGELOG.md` entry under a `feat(client)` heading.
- Consider an ADR only if a non-obvious design choice arises (e.g., where the
  builder lives, or how FLAT compositions are handled).

---

## Open Questions

1. **FLAT inside contributions** — EHRBase's contribution endpoint expects
   CANONICAL `ORIGINAL_VERSION` wrappers. Do we (a) require callers to pass
   CANONICAL compositions (simplest, this PRD's assumption), or (b) accept FLAT
   and auto-convert via the serialization layer? Recommendation: (a) for v2.0,
   revisit if demand appears.
2. **Builder location** — `src/oehrpy/client/contribution.py` (co-located with
   the client) vs. `src/oehrpy/templates/`. Recommendation: client package,
   since it produces a transport request body, not a template artifact.
3. **EHR_STATUS / FOLDER versions** — deferred to a follow-up PRD.

---

## Success Criteria

1. `create_contribution()` and `get_contribution()` implemented and passing
   integration tests against EHRBase.
2. `ContributionBuilder` provides a fluent API covering all four change types
   plus multi-operation contributions.
3. Audit metadata (committer, timestamp, description, change type) round-trips
   correctly through commit → retrieve.
4. Unit and integration tests added; CI green.
