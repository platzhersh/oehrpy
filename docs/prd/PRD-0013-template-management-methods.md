# PRD-0013: Template Management Methods (get_template_opt, update_template, delete_template)

**Version:** 0.2
**Date:** 2026-04-10
**Status:** Draft
**Owner:** Open CIS Project
**Priority:** P0 (Critical)

---

## Executive Summary

Add three missing template lifecycle methods to `EHRBaseClient`:

1. **`get_template_opt()`** — Download the raw OPT 1.4 XML for a template
2. **`update_template()`** — Replace an existing template definition
3. **`delete_template()`** — Remove a template from the CDR

These are fundamental operations for template migration, CI/CD pipelines, and
multi-CDR deployments. Without them, SDK users must fall back to raw HTTP calls
for routine template management tasks.

This PRD also introduces a **CDR compatibility layer** for template operations,
since EHRBase and Better Platform differ in their handling of template updates
and deletion.

---

## Problem Statement

The oehrpy client (v0.7.0) covers template *listing*, *retrieval* (JSON), *web
template fetching*, and *upload*. Three standard operations are missing:

| Gap | Impact |
|-----|--------|
| **No OPT XML download** — `get_template()` returns a JSON dict, but there is no way to retrieve the original OPT 1.4 XML. | Cannot export templates for backup, migration between CDRs, or offline analysis with `OPTParser`. Users must use `curl` or `httpx` directly. |
| **No template update** — There is no way to replace a template that has already been uploaded. | Template iteration during development requires manual HTTP calls or workarounds (delete + re-upload on EHRBase). |
| **No template deletion** — There is no way to remove a template from a CDR. | Stale or incorrect templates accumulate. CI/CD pipelines cannot clean up test templates. Migration scripts cannot remove deprecated templates. |

These gaps are especially painful in multi-CDR workflows (e.g., migrating
templates from EHRBase to Better, or maintaining templates across staging and
production environments).

---

## Requirements

### Functional Requirements

#### FR-1: Get Template OPT XML

| Field | Detail |
|---|---|
| SDK method | `EHRBaseClient.get_template_opt(template_id)` |
| Input | Template ID (string) |
| Output | Raw OPT 1.4 XML as `str` |

**CDR-specific endpoints:**

| CDR | Endpoint | Mechanism |
|-----|----------|-----------|
| **EHRBase** | `GET /rest/openehr/v1/definition/template/adl1.4/{template_id}` | `Accept: application/xml` header on the standard template endpoint |
| **Better** | `GET /rest/v1/template/{templateId}/opt` | Dedicated `/opt` sub-resource (proprietary); the base `GET /rest/v1/template/{templateId}` always returns the Web Template JSON |

- Must return the raw XML string, not a parsed dict
- Must raise `NotFoundError` if the template does not exist (HTTP 404)
- The CDR-specific endpoint difference is handled internally by the client based on the configured CDR type (see section "CDR Compatibility — Abstraction Strategy")

**Use cases:**
- Export a template from a CDR for backup or version control
- Download from one CDR and `upload_template()` to another (migration)
- Feed into `OPTParser.parse_string()` for offline metadata extraction
- Round-trip test: upload OPT XML, retrieve it, compare

#### FR-2: Update Template

| Field | Detail |
|---|---|
| SDK method | `EHRBaseClient.update_template(template_id, template_xml)` |
| Input | Template ID (string), updated OPT 1.4 XML (string) |
| Output | `TemplateResponse` |

- Must send OPT XML with `Content-Type: application/xml`
- Must raise `NotFoundError` if the template does not exist
- Must raise `ValidationError` if the XML is malformed or fails CDR validation
- Must invalidate the web template cache entry for `template_id` on success (the web template tree may have changed)

**CDR-specific behavior** (see section "CDR Compatibility"):

Neither EHRBase nor Better supports a standard `PUT` for replacing template
content. Both require a **delete-and-re-upload** strategy:

| CDR | PUT support | Fallback strategy |
|-----|-------------|-------------------|
| **EHRBase** | Not supported (returns 405 or 501). | `DELETE` + `POST` (re-upload). Only works if no compositions reference the template; otherwise the delete fails with HTTP 409 and a `ValidationError` is raised. |
| **Better** | Not supported. `PUT` is only available for tagging (`/rest/v1/template/{id}/tag`) and retire/unretire (`/admin/rest/v1/templates/{id}/retire`). | `DELETE` + `POST` (re-upload). The EHR Server API DELETE retires the template (soft-delete); the Admin API DELETE permanently removes it. See section "CDR Compatibility" for which to use. |

- The SDK should attempt `PUT` on the standard openEHR REST endpoint first (future-proofing for CDRs that may add support), then fall back to delete-and-re-upload if the CDR returns 405 Method Not Allowed or 501 Not Implemented
- The fallback must be atomic in intent: if the delete succeeds but the re-upload fails, the method must raise an error clearly stating that the template was deleted but the new version could not be uploaded (so the caller knows to retry the upload)

#### FR-3: Delete Template

| Field | Detail |
|---|---|
| SDK method | `EHRBaseClient.delete_template(template_id)` |
| Input | Template ID (string) |
| Output | `None` on success |

- Must raise `NotFoundError` if the template does not exist (HTTP 404)
- Must raise `ValidationError` if the template cannot be deleted because compositions reference it (HTTP 409 Conflict on EHRBase)
- Must invalidate the web template cache entry for `template_id` on success
- Must handle HTTP 409 Conflict with a descriptive error message (e.g., "Cannot delete template: compositions still reference it")

**CDR-specific behavior:**

| CDR | Endpoint | Behavior |
|-----|----------|----------|
| **EHRBase** | `DELETE /rest/openehr/v1/definition/template/adl1.4/{template_id}` | Hard-delete. Returns 204 on success. Returns 409 Conflict if compositions exist. Returns 404 if not found. |
| **Better (EHR Server API)** | `DELETE /rest/v1/template/{templateId}` | **Retire** (soft-delete). Returns 200 with `{"action": "DELETE"}`. Returns 404 if not found (TMPL-3021). Template can be unretired via Admin API. |
| **Better (Admin API)** | `DELETE /admin/rest/v1/templates/{templateId}` | **Permanent delete**. Requires admin credentials. Returns 200 on success. Returns 404 if not found. |

Better's two-tier deletion model introduces a design decision: should
`delete_template()` use the EHR Server API (retire, reversible) or the Admin
API (permanent, irreversible)? See section "CDR Compatibility — Better
Delete Semantics" for the proposed approach.

### Non-Functional Requirements

- **NFR-1**: All methods must be async (consistent with existing client)
- **NFR-2**: Web template cache must be invalidated after successful `update_template()` or `delete_template()` calls
- **NFR-3**: Error messages must clearly describe CDR-specific restrictions (e.g., "EHRBase does not allow deleting templates that are referenced by compositions")
- **NFR-4**: No new dependencies required — `httpx`, `defusedxml` already cover all needs
- **NFR-5**: PII/PHI protection — response text in error messages must be truncated per existing `_handle_response()` patterns
- **NFR-6**: Adding `cdr_type` to `EHRBaseConfig` must be backward-compatible — default is `CDRType.EHRBASE`, so existing code continues to work without changes
- **NFR-7**: Public method signatures must be CDR-agnostic — callers never pass CDR-specific paths or headers

---

## API Design

### New Types

```python
class CDRType(str, Enum):
    """Supported CDR backends."""
    EHRBASE = "ehrbase"
    BETTER = "better"

@dataclass
class EHRBaseConfig:
    base_url: str = "http://localhost:8080/ehrbase"
    cdr_type: CDRType = CDRType.EHRBASE  # NEW — default preserves backward compat
    username: str | None = None
    password: str | None = None
    timeout: float = 30.0
    verify_ssl: bool = True
```

### Method Signatures

```python
class EHRBaseClient:

    async def get_template_opt(self, template_id: str) -> str:
        """Download the raw OPT 1.4 XML for a template.

        On EHRBase, uses the standard openEHR REST endpoint with
        ``Accept: application/xml``. On Better, uses the dedicated
        ``/rest/v1/template/{id}/opt`` sub-resource.

        Args:
            template_id: The template ID.

        Returns:
            The OPT XML content as a string.

        Raises:
            NotFoundError: If the template does not exist.
        """

    async def update_template(
        self,
        template_id: str,
        template_xml: str,
    ) -> TemplateResponse:
        """Update an existing template.

        Attempts a standard PUT. If the CDR does not support PUT
        (neither EHRBase nor Better do today), falls back to
        delete-and-re-upload.

        Warning:
            The delete-and-re-upload fallback is not atomic. If the
            delete succeeds but the re-upload fails, the template will
            be missing from the CDR. The error message will indicate
            this so the caller can re-upload manually.

        Args:
            template_id: The template ID to update.
            template_xml: The updated OPT 1.4 XML content.

        Returns:
            TemplateResponse with the updated template details.

        Raises:
            NotFoundError: If the template does not exist.
            ValidationError: If the XML is invalid, or if the template
                cannot be deleted because compositions reference it
                (EHRBase, HTTP 409).
        """

    async def delete_template(
        self,
        template_id: str,
        *,
        permanent: bool = False,
    ) -> None:
        """Delete a template from the CDR.

        On EHRBase, always performs a hard-delete (the ``permanent``
        parameter is ignored since EHRBase has no soft-delete).

        On Better, the default behavior retires the template
        (soft-delete, reversible via the Admin API's unretire
        endpoint). Pass ``permanent=True`` to permanently delete
        via the Admin API (requires admin credentials).

        Args:
            template_id: The template ID to delete.
            permanent: If True, permanently delete on Better
                (uses Admin API). Ignored on EHRBase.

        Raises:
            NotFoundError: If the template does not exist.
            ValidationError: If the template cannot be deleted because
                compositions reference it (HTTP 409, EHRBase).
        """
```

### Usage Examples

```python
# --- EHRBase usage (default, backward-compatible) ---
config = EHRBaseConfig(
    base_url="http://localhost:8080/ehrbase",
    username="ehrbase-user",
    password="SuperSecretPassword",
)

async with EHRBaseClient(config=config) as client:

    # Download OPT XML
    opt_xml = await client.get_template_opt("Vital Signs.v1")
    Path("templates/vital_signs.opt").write_text(opt_xml)

    # Parse offline
    template_def = OPTParser().parse_string(opt_xml)

    # Update a template (delete + re-upload on EHRBase)
    updated_xml = Path("templates/vital_signs_v2.opt").read_text()
    result = await client.update_template("Vital Signs.v1", updated_xml)

    # Web template cache is automatically invalidated:
    wt = await client.get_web_template("Vital Signs.v1")  # fresh fetch

    # Delete a template
    await client.delete_template("Vital Signs.v1")


# --- Better Platform usage ---
better_config = EHRBaseConfig(
    base_url="https://cdr.example.com",
    cdr_type=CDRType.BETTER,
    username="admin",
    password="secret",
)

async with EHRBaseClient(config=better_config) as client:

    # Download OPT XML (uses /rest/v1/template/{id}/opt)
    opt_xml = await client.get_template_opt("Vital Signs.v1")

    # Delete: retire (soft-delete, default)
    await client.delete_template("Vital Signs.v1")

    # Delete: permanent (uses Admin API, requires admin credentials)
    await client.delete_template("Vital Signs.v1", permanent=True)


# --- Cross-CDR migration ---
async with EHRBaseClient(config=ehrbase_config) as source:
    opt_xml = await source.get_template_opt("Vital Signs.v1")

async with EHRBaseClient(config=better_config) as target:
    await target.upload_template(opt_xml)
```

### Error Handling

```python
# Template referenced by compositions (EHRBase)
try:
    await client.delete_template("Vital Signs.v1")
except ValidationError as e:
    print(e)  # "Cannot delete template: compositions still reference it"
    print(e.status_code)  # 409

# Template not found
try:
    opt_xml = await client.get_template_opt("nonexistent")
except NotFoundError:
    print("Template does not exist")

# Update fallback failure (delete succeeded, re-upload failed)
try:
    await client.update_template("Vital Signs.v1", invalid_xml)
except ValidationError as e:
    # e.message explains what happened:
    # "Template update failed: old template was deleted but new template
    #  could not be uploaded (validation error). Re-upload the template
    #  manually to restore it."
    print(e)
```

---

## CDR Compatibility

### API Surface Comparison

Better Platform exposes **three** API layers, each with template endpoints.
EHRBase exposes one (the openEHR REST standard). The table below maps every
relevant endpoint discovered so far:

| Operation | EHRBase (openEHR REST) | Better — EHR Server API | Better — Admin API | Better — OpenEHR REST API |
|-----------|------------------------|------------------------|--------------------|--------------------------|
| **List templates** | `GET /rest/openehr/v1/definition/template/adl1.4` | `GET /rest/v1/template` (supports tag filtering & search) | `GET /admin/rest/v1/templates` | Likely mirrors standard |
| **Upload template** | `POST /rest/openehr/v1/definition/template/adl1.4` | `POST /rest/v1/template` (supports tags param) | `POST /admin/rest/v1/templates` | Likely mirrors standard |
| **Get web template** | `GET .../adl1.4/{id}` with `Accept: application/openehr.wt+json` | `GET /rest/v1/template/{id}` (returns web template JSON by default) | `GET /admin/rest/v1/templates/{id}` | Likely mirrors standard |
| **Get OPT XML** | `GET .../adl1.4/{id}` with `Accept: application/xml` | `GET /rest/v1/template/{id}/opt` (dedicated sub-resource) | — | Unknown |
| **Delete template** | `DELETE .../adl1.4/{id}` → 204 (hard-delete; 409 if compositions exist) | `DELETE /rest/v1/template/{id}` → 200 (**retire**/soft-delete) | `DELETE /admin/rest/v1/templates/{id}` → 200 (**permanent** delete) | Unknown |
| **Update template** | Not supported (405/501) | Not supported (PUT is for tagging only) | Not supported | Unknown |
| **Retire template** | N/A | Implicit via DELETE (see above) | `PUT /admin/rest/v1/templates/{id}/retire` | N/A |
| **Unretire template** | N/A | N/A | `PUT /admin/rest/v1/templates/{id}/unretire` | N/A |
| **Tag template** | N/A | `PUT /rest/v1/template/{id}/tag` | — | N/A |
| **Head (last modified)** | N/A | `HEAD /rest/v1/template` | — | N/A |
| **Get metadata + tags** | N/A | `GET /rest/v1/template/{id}/meta` | — | N/A |
| **Get XSD** | N/A | `GET /rest/v1/template/{id}/xsd` | — | N/A |
| **Get TDS** | N/A | `GET /rest/v1/template/{id}/tds` | — | N/A |

### Abstraction Strategy

The SDK targets the **openEHR REST API specification** as its primary
interface. Because Better and EHRBase differ in URL structure and behavior,
the client needs a **CDR type** configuration to select the correct endpoints:

```python
class CDRType(str, Enum):
    EHRBASE = "ehrbase"
    BETTER = "better"

@dataclass
class EHRBaseConfig:
    base_url: str = "http://localhost:8080/ehrbase"
    cdr_type: CDRType = CDRType.EHRBASE  # NEW
    ...
```

The CDR type determines internal URL routing. The public method signatures
remain identical regardless of CDR type — callers never see CDR-specific
paths.

**Decision: why explicit `cdr_type` instead of auto-detection?**

Auto-detection (e.g., probing `/rest/v1/template` vs
`/rest/openehr/v1/definition/template/adl1.4`) adds latency and fragility.
Since the user always knows which CDR they're connecting to, an explicit
enum is simpler and more reliable.

### Flow: `update_template()`

```
update_template(template_id, xml)
    │
    ├── PUT on standard openEHR REST endpoint (future-proofing)
    │       Content-Type: application/xml
    │
    ├── 200/204 → success (CDR supports PUT — neither does today)
    │
    ├── 405/501 → CDR does not support PUT → fallback:
    │       │
    │       ├── DELETE template (CDR-appropriate endpoint)
    │       │       ├── EHRBase 409 → raise ValidationError (compositions exist)
    │       │       └── Better 404 → raise NotFoundError
    │       │
    │       └── POST template (re-upload, CDR-appropriate endpoint)
    │               └── 400/422 → raise ValidationError
    │                   (include note that old template was deleted)
    │
    └── 400/422 → raise ValidationError (XML invalid)
```

### Better Delete Semantics

Better has a two-tier deletion model:

| Tier | Endpoint | Effect | Reversible? | Auth required |
|------|----------|--------|-------------|---------------|
| **Retire** (EHR Server API) | `DELETE /rest/v1/template/{id}` | Soft-delete; template is retired but not removed from the database | Yes — via `PUT /admin/rest/v1/templates/{id}/unretire` | Standard user |
| **Permanent delete** (Admin API) | `DELETE /admin/rest/v1/templates/{id}` | Hard-delete; template is permanently removed | No | Admin credentials |

**Proposed SDK behavior:**

`delete_template()` uses the **EHR Server API** (retire) by default, since
it is reversible and does not require admin credentials. A `permanent`
parameter allows callers to opt in to the Admin API hard-delete:

```python
async def delete_template(
    self,
    template_id: str,
    *,
    permanent: bool = False,
) -> None:
```

| `cdr_type` | `permanent=False` (default) | `permanent=True` |
|------------|----------------------------|-------------------|
| `EHRBASE` | `DELETE .../adl1.4/{id}` (hard-delete; EHRBase has no soft-delete) | Same as default (EHRBase only has hard-delete) |
| `BETTER` | `DELETE /rest/v1/template/{id}` (retire) | `DELETE /admin/rest/v1/templates/{id}` (permanent) |

On EHRBase, the `permanent` flag is a no-op (EHRBase only supports
hard-delete). On Better, it selects between retire and permanent delete.

### Open Questions

| # | Question | Impact on implementation |
|---|----------|------------------------|
| 1 | Does Better's EHR Server API DELETE (retire) block when compositions reference the template, or does it retire regardless? | Determines whether `delete_template()` on Better can fail with a conflict error, or always succeeds. |
| 2 | Does Better's `POST /rest/v1/template` handle re-upload of an existing template ID (upsert), or reject it as a duplicate? | If upsert is supported, `update_template()` on Better could skip the delete step entirely. |
| 3 | Does Better's OpenEHR REST API layer (third sidebar item) mirror the standard endpoints, and could it serve as a unified path? | Could simplify the abstraction if Better's openEHR REST layer supports the same paths as EHRBase. |
| 4 | Does the Admin API permanent delete block when compositions reference the template? | Affects error handling for `permanent=True` on Better. |

---

## Implementation Plan

### Phase 1: CDR Abstraction + EHRBase

| Task | Effort | Details |
|------|--------|---------|
| Add `CDRType` enum and `cdr_type` field to `EHRBaseConfig` | 0.25 day | Default to `EHRBASE` for backward compatibility |
| Implement `get_template_opt()` | 0.5 day | EHRBase: `Accept: application/xml`; Better: `/rest/v1/template/{id}/opt` |
| Implement `delete_template()` | 0.75 day | EHRBase: standard DELETE; Better: retire vs permanent; cache invalidation |
| Implement `update_template()` | 1 day | PUT attempt + delete-and-re-upload fallback (both CDRs) |
| Add HTTP 409 handling to `_handle_response()` | 0.25 day | Map to `ValidationError` with descriptive message |
| Unit tests (mocked HTTP) | 1.5 days | Both CDR types, all methods, all error paths, cache invalidation |
| Integration tests (EHRBase) | 1 day | Round-trip: upload → get_opt → update → delete |
| **Phase 1 total** | **~5.25 days** | |

### Phase 2: Better Platform Integration Testing

| Task | Effort | Details |
|------|--------|---------|
| Resolve remaining open questions (retire semantics, upsert, conflict behavior) | 0.5 day | Test against a Better instance or confirm with docs |
| Integration tests (Better) | 1 day | Same test scenarios against Better |
| **Phase 2 total** | **~1.5 days** | |

### Future: Better-Only Features (Out of Scope)

These Better-specific features are documented for future consideration but
are **not** part of this PRD:

| Feature | Better endpoint | Potential SDK method |
|---------|----------------|---------------------|
| Template tagging | `PUT /rest/v1/template/{id}/tag` | `tag_template(template_id, tags)` |
| Template metadata + tags | `GET /rest/v1/template/{id}/meta` | `get_template_metadata(template_id)` |
| Unretire template | `PUT /admin/rest/v1/templates/{id}/unretire` | `unretire_template(template_id)` |
| XSD generation | `GET /rest/v1/template/{id}/xsd` | `get_template_xsd(template_id)` |
| TDS format | `GET /rest/v1/template/{id}/tds` | `get_template_tds(template_id)` |
| Last-modified check | `HEAD /rest/v1/template` | `get_template_last_modified(template_id)` |

---

## Testing Strategy

### Unit Tests

```python
# test_template_management.py

class TestGetTemplateOpt:
    """Tests for get_template_opt()."""

    async def test_returns_raw_xml(self, mock_client):
        """GET with Accept: application/xml returns raw XML string."""

    async def test_not_found_raises(self, mock_client):
        """404 response raises NotFoundError."""

class TestDeleteTemplate:
    """Tests for delete_template()."""

    async def test_successful_delete(self, mock_client):
        """204 response returns None."""

    async def test_not_found_raises(self, mock_client):
        """404 response raises NotFoundError."""

    async def test_conflict_raises_validation_error(self, mock_client):
        """409 response raises ValidationError with descriptive message."""

    async def test_cache_invalidation(self, mock_client):
        """Successful delete clears web template cache for that template."""

class TestUpdateTemplate:
    """Tests for update_template()."""

    async def test_put_supported(self, mock_client):
        """200/204 from PUT returns TemplateResponse."""

    async def test_put_unsupported_falls_back(self, mock_client):
        """405 from PUT triggers delete + re-upload fallback."""

    async def test_fallback_delete_conflict(self, mock_client):
        """409 from DELETE in fallback raises ValidationError."""

    async def test_fallback_upload_failure(self, mock_client):
        """Fallback upload failure raises with note about deleted template."""

    async def test_cache_invalidation(self, mock_client):
        """Successful update clears web template cache."""
```

### Integration Tests

```python
# tests/integration/test_template_management.py

@pytest.mark.integration
class TestTemplateManagement:

    async def test_upload_and_get_opt_round_trip(self, client, opt_xml):
        """Upload OPT → get_template_opt() → compare XML content."""

    async def test_delete_template(self, client, opt_xml):
        """Upload → delete → list_templates() confirms removal."""

    async def test_delete_with_compositions_fails(self, client, ehr_with_composition):
        """Delete template with existing compositions raises ValidationError."""

    async def test_update_template(self, client, opt_xml, updated_opt_xml):
        """Upload → update → get_template_opt() returns updated XML."""

    async def test_update_invalidates_web_template_cache(self, client, opt_xml):
        """get_web_template() after update returns fresh data."""
```

---

## Changes to Existing Code

### `_handle_response()` — Add HTTP 409 Handling

The current `_handle_response()` method does not handle HTTP 409 (Conflict).
Add a case:

```python
if response.status_code == 409:
    try:
        error_data = response.json()
    except Exception:
        error_data = {"message": response.text}
    raise ValidationError(
        error_data.get("message", "Conflict: resource cannot be modified"),
        status_code=response.status_code,
        response=error_data,
    )
```

This also benefits future operations (e.g., directory operations in PRD-0005)
that may encounter 409 responses.

### Web Template Cache Invalidation

Both `update_template()` and `delete_template()` must call
`self.clear_web_template_cache(template_id)` on success to ensure subsequent
`get_web_template()` calls fetch fresh data from the CDR.

---

## Success Criteria

1. `get_template_opt()` returns valid OPT XML that can be re-uploaded to any CDR (both EHRBase and Better)
2. `delete_template()` removes/retires the template and invalidates the cache
3. `delete_template(permanent=True)` permanently deletes on Better via Admin API
4. `update_template()` works on both CDRs via the delete-and-re-upload fallback
5. `CDRType` config selects the correct endpoint paths without changing the public API
6. All three methods raise typed exceptions with descriptive messages on failure
7. HTTP 409 is handled as `ValidationError` across the client
8. Unit tests cover all success and error paths for both CDR types
9. Integration tests pass against EHRBase 2.x
10. No regressions in existing template operations (`list_templates`, `get_template`, `upload_template`, `get_web_template`)
11. Existing code that does not set `cdr_type` continues to work unchanged (backward compatibility)

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **update_template() fallback is non-atomic**: if delete succeeds but re-upload fails, the template is lost from the CDR | Medium | High | Raise a clearly-worded error so the caller knows to re-upload manually. Document this risk in the method docstring. Consider fetching the OPT XML before deleting as a local backup. |
| **Better retire vs permanent delete confusion**: users may not understand that the default Better delete is a soft-delete | Medium | Medium | Document behavior clearly in docstring. The `permanent` parameter name makes the distinction explicit. |
| **`CDRType` config adds complexity** to the client | Low | Medium | The enum has only two values and defaults to `EHRBASE` for backward compatibility. Internal routing is handled by private methods, keeping the public API clean. |
| **EHRBase behavior changes across versions** (e.g., future EHRBase versions might support PUT) | Low | Low | The try-PUT-first approach automatically benefits from future CDR support without code changes. |
| **409 vs 422 ambiguity**: some CDRs may return 422 instead of 409 for conflict scenarios | Low | Low | The existing 422 → `ValidationError` mapping already handles this; the error message from the CDR body will clarify the cause. |
| **Better Admin API requires elevated credentials**: `permanent=True` may fail if the client is configured with non-admin credentials | Medium | Low | Raise `AuthenticationError` with a clear message if the Admin API returns 401/403. Document that admin credentials are required for permanent delete. |

---

## Dependencies

- **ADR-0005** (Web Template as source of truth) — cache invalidation behavior aligns with this decision
- **PRD-0002** (Composition Lifecycle) — already implemented; `delete_template()` interacts with composition existence

---

## References

- [openEHR REST API — Definition (Template)](https://specifications.openehr.org/releases/ITS-REST/latest/definition.html#tag/ADL1.4)
- [EHRBase Template API Documentation](https://ehrbase.readthedocs.io/)
- Better Platform — EHR Server API: Template endpoints (`/rest/v1/template/...`)
- Better Platform — EHR Admin API: Template Admin Rest Controller (`/admin/rest/v1/templates/...`)
- ADR-0005: Web Template as Primary Source of Truth for FLAT Paths
- PRD-0002: Composition Lifecycle (Update & Versioning)
