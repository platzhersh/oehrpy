# ADR-0011: Vendor Adapters over a Generic ITS-REST Client

**Date:** 2026-09-25

## Status

Accepted

**Related:** OEH-83 (FerroEHR support), openEHR Explorer's `ServerType`
branching in `src-tauri/src/commands/*.rs`.

## Context

oehrpy's REST client was EHRBase-only: `EHRBaseClient`/`EHRBaseConfig` with
EHRBase defaults (base URL `…/ehrbase`, Basic auth, `format` query parameter,
admin API at `/rest/admin`). We want to support FerroEHR, a stricter
ITS-REST 1.1.0 implementation, without breaking existing EHRBase users
(including Open CIS), and leave room for Better or EHRServer later.

The differences between the two CDRs are few but real:

| Concern | EHRBase 2.x | FerroEHR |
|---|---|---|
| `GET /rest/status` | authenticated, `ehrbase_version` (XML by default) | unauthenticated JSON `{status, server_version, …}` |
| Composition format | `format` query parameter | `Content-Type`/`Accept` media type (spec) |
| FLAT media type | `application/openehr.wt.flat.schema+json` | `application/openehr.wt.flat+json` (spec) |
| FLAT commit template | `templateId` query parameter | `openehr-template-id` header (spec) |
| EHR creation | fills `EHR_STATUS.archetype_details` | requires it (422) |
| Template list | always all versions | latest only unless `version=*` (spec) |
| Admin API | `{base}/rest/admin/…` | `{base}/rest/openehr/v1/admin/…`, `ADMIN` role |

The openEHR Explorer handles the same differences with a `server_type` field
and `match` arms at every call site.

## Decision

1. **`OpenEHRClient` implements plain ITS-REST 1.1.0** (EHR, EHR_STATUS,
   COMPOSITION, CONTRIBUTION, DIRECTORY, template definitions, AQL, stored
   queries). It is usable on its own for CDRs without an adapter.
2. **Vendor behaviour lives in thin subclasses** (`EHRBaseClient`,
   `FerroEHRClient`) that override a small set of hooks rather than whole
   methods: class attributes (`admin_prefix`, `status_requires_auth`,
   `supports_template_version_filter`, `always_send_ehr_status`) and two
   request builders (`_composition_write_request`,
   `_composition_read_request`) plus `_if_match`. FerroEHR needs only class
   attributes, because it follows the spec.
3. **Auth is pluggable** via `auth_method`/`admin_auth_method` on the config:
   `None`, `BasicAuth`, `BearerAuth` (static token or sync/async token
   provider) or any `httpx.Auth`. `username`/`password` keep working. Token
   acquisition (OIDC flows) stays the caller's job.
4. **`create_client(server_type=…)`** picks the adapter from configuration;
   `detect_server_type()` probes `/rest/status` for apps that want to
   auto-detect.
5. **No breaking change.** Every name previously importable from
   `oehrpy.client` and `oehrpy.client.ehrbase` still is; `EHRBaseError` is an
   alias of the new base `OpenEHRError`; 403 now raises `AuthorizationError`,
   which subclasses it. EHRBase requests are byte-for-byte unchanged.

## Alternatives considered

- **One client with `server_type` flags** (the Explorer approach). Simple for
  two vendors, but every method grows `if/elif` arms, vendor quirks are
  scattered, and adding a third CDR touches every call site. The adapter
  pattern keeps each vendor's deviations in one short class.
- **Separate, independent clients per vendor.** Maximum freedom, but ~1,000
  lines of duplicated ITS-REST code that would drift.

## Consequences

- New CDR support is a subclass that sets a few attributes and, where needed,
  overrides a hook; spec-compliant servers may need nothing but a base URL.
- Behaviour that is spec-correct but untested on EHRBase (quoted `If-Match`,
  media-type negotiation) is kept out of `EHRBaseClient` until verified there.
- FerroEHR bugs are not worked around in the SDK: e.g. OEH-50 (FLAT `GET`
  drops nested HISTORY content) is documented and marked as an expected
  failure in the FerroEHR integration run.
- Integration tests run against one CDR at a time (`OEHRPY_CDR`); CI runs a
  blocking EHRBase job and a non-blocking FerroEHR job.
