# PRD-0013: Template Management Methods (get_template_opt, update_template, delete_template)

**Version:** 0.1
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
| Endpoint | `GET /rest/openehr/v1/definition/template/adl1.4/{template_id}` |
| SDK method | `EHRBaseClient.get_template_opt(template_id)` |
| Input | Template ID (string) |
| Output | Raw OPT 1.4 XML as `str` |
| Accept header | `application/xml` |

- Must return the raw XML string, not a parsed dict
- Must raise `NotFoundError` if the template does not exist (HTTP 404)
- Must work identically on EHRBase and Better (both support `Accept: application/xml` on this endpoint per the openEHR REST spec)

**Use cases:**
- Export a template from a CDR for backup or version control
- Download from one CDR and `upload_template()` to another (migration)
- Feed into `OPTParser.parse_string()` for offline metadata extraction
- Round-trip test: upload OPT XML, retrieve it, compare

#### FR-2: Update Template

| Field | Detail |
|---|---|
| Endpoint (standard) | `PUT /rest/openehr/v1/definition/template/adl1.4/{template_id}` |
| SDK method | `EHRBaseClient.update_template(template_id, template_xml)` |
| Input | Template ID (string), updated OPT 1.4 XML (string) |
| Output | `TemplateResponse` |

- Must send OPT XML with `Content-Type: application/xml`
- Must raise `NotFoundError` if the template does not exist
- Must raise `ValidationError` if the XML is malformed or fails CDR validation
- Must invalidate the web template cache entry for `template_id` on success (the web template tree may have changed)

**CDR-specific behavior** (see section "CDR Compatibility"):

| CDR | PUT support | Fallback strategy |
|-----|-------------|-------------------|
| **EHRBase** | Not supported (returns 405 or 501). | SDK performs `DELETE` then `POST` (re-upload). This only works if no compositions reference the template; otherwise the delete fails and a `ValidationError` is raised with a clear message. |
| **Better** | **Open question** — needs confirmation from Better API docs. May support PUT directly, or may require a proprietary endpoint. |

- The SDK should attempt `PUT` first and fall back to delete-and-re-upload if the CDR returns 405 Method Not Allowed or 501 Not Implemented
- The fallback must be atomic in intent: if the delete succeeds but the re-upload fails, the method must raise an error clearly stating that the template was deleted but the new version could not be uploaded (so the caller knows to retry the upload)

#### FR-3: Delete Template

| Field | Detail |
|---|---|
| Endpoint | `DELETE /rest/openehr/v1/definition/template/adl1.4/{template_id}` |
| SDK method | `EHRBaseClient.delete_template(template_id)` |
| Input | Template ID (string) |
| Output | `None` (HTTP 204 on success) |

- Must raise `NotFoundError` if the template does not exist (HTTP 404)
- Must raise `ValidationError` if the template cannot be deleted because compositions reference it (HTTP 409 Conflict on EHRBase)
- Must invalidate the web template cache entry for `template_id` on success
- Must handle HTTP 409 Conflict with a descriptive error message (e.g., "Cannot delete template: compositions still reference it")

**CDR-specific behavior:**

| CDR | DELETE behavior |
|-----|----------------|
| **EHRBase** | Returns 204 on success. Returns 409 Conflict if compositions exist. Returns 404 if template not found. |
| **Better** | **Open question** — may soft-delete/archive rather than hard-delete. May return different status codes. |

### Non-Functional Requirements

- **NFR-1**: All methods must be async (consistent with existing client)
- **NFR-2**: Web template cache must be invalidated after successful `update_template()` or `delete_template()` calls
- **NFR-3**: Error messages must clearly describe CDR-specific restrictions (e.g., "EHRBase does not allow deleting templates that are referenced by compositions")
- **NFR-4**: No new dependencies required — `httpx`, `defusedxml` already cover all needs
- **NFR-5**: PII/PHI protection — response text in error messages must be truncated per existing `_handle_response()` patterns

---

## API Design

### Method Signatures

```python
class EHRBaseClient:

    async def get_template_opt(self, template_id: str) -> str:
        """Download the raw OPT 1.4 XML for a template.

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

        Attempts a standard PUT. If the CDR does not support PUT for
        templates (e.g., EHRBase returns 405/501), falls back to
        delete-and-re-upload.

        Args:
            template_id: The template ID to update.
            template_xml: The updated OPT 1.4 XML content.

        Returns:
            TemplateResponse with the updated template details.

        Raises:
            NotFoundError: If the template does not exist.
            ValidationError: If the XML is invalid, or if the template
                cannot be deleted because compositions reference it
                (EHRBase fallback path).
        """

    async def delete_template(self, template_id: str) -> None:
        """Delete a template from the CDR.

        Args:
            template_id: The template ID to delete.

        Raises:
            NotFoundError: If the template does not exist.
            ValidationError: If the template cannot be deleted because
                compositions reference it (HTTP 409).
        """
```

### Usage Examples

```python
async with EHRBaseClient(config=config) as client:

    # --- FR-1: Download OPT XML ---
    opt_xml = await client.get_template_opt("Vital Signs.v1")

    # Save to file for version control
    Path("templates/vital_signs.opt").write_text(opt_xml)

    # Parse offline
    template_def = OPTParser().parse_string(opt_xml)
    print(template_def.template_id)  # "Vital Signs.v1"

    # Migrate to another CDR
    async with EHRBaseClient(config=target_config) as target:
        await target.upload_template(opt_xml)


    # --- FR-2: Update a template ---
    updated_xml = Path("templates/vital_signs_v2.opt").read_text()
    result = await client.update_template("Vital Signs.v1", updated_xml)
    print(result.template_id)  # "Vital Signs.v1"

    # Web template cache is automatically invalidated:
    wt = await client.get_web_template("Vital Signs.v1")  # fresh fetch


    # --- FR-3: Delete a template ---
    await client.delete_template("Vital Signs.v1")

    # Cache is automatically cleared:
    # client.get_web_template("Vital Signs.v1") would now fetch fresh
    # (and raise NotFoundError since it's deleted)
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

### Abstraction Strategy

The SDK targets the **openEHR REST API specification** and does not expose
CDR-specific API surfaces. Where CDR behavior diverges from the spec (or where
the spec leaves behavior undefined), the SDK uses a **try-standard-first,
fallback-if-needed** approach:

```
update_template(template_id, xml)
    │
    ├── PUT /definition/template/adl1.4/{template_id}
    │       Content-Type: application/xml
    │
    ├── 200/204 → success (CDR supports PUT)
    │
    ├── 405/501 → CDR does not support PUT
    │       │
    │       ├── DELETE /definition/template/adl1.4/{template_id}
    │       │       └── 409 → raise ValidationError (compositions exist)
    │       │
    │       └── POST /definition/template/adl1.4 (re-upload)
    │               └── 400/422 → raise ValidationError
    │                   (include note that old template was deleted)
    │
    └── 400/422 → raise ValidationError (XML invalid)
```

### Known CDR Differences

| Operation | openEHR REST Spec | EHRBase 2.x | Better Platform |
|-----------|-------------------|-------------|-----------------|
| GET template as XML | `Accept: application/xml` | Supported | Needs confirmation |
| PUT template | Defined in spec | Not supported (405/501) | Needs confirmation |
| DELETE template | Defined in spec | Supported; 409 if compositions exist | Needs confirmation |
| DELETE response code | 204 No Content | 204 | Needs confirmation |
| Conflict response | 409 Conflict | 409 with error body | Needs confirmation |

### Open Questions Requiring Better Documentation

| # | Question | Impact on implementation |
|---|----------|------------------------|
| 1 | Does Better support `GET` with `Accept: application/xml` on the standard template endpoint, or is there a proprietary endpoint for OPT download? | Determines whether `get_template_opt()` needs CDR-specific logic. |
| 2 | Does Better support `PUT` for template updates? If so, what are the semantics (versioned? overwrite? validation)? | Determines whether the delete-and-re-upload fallback is needed for Better. |
| 3 | Does Better support `DELETE` on templates? If yes: hard-delete or soft-delete (archive)? What status code for conflict? | Determines error handling in `delete_template()`. |
| 4 | Does Better return HTTP 409 when attempting to delete a template referenced by compositions, or a different code? | Affects error mapping in `_handle_response()`. |
| 5 | Does Better have additional proprietary template management endpoints (e.g., under `/admin/` or `/management/`) that we should support? | May require a separate method or config flag. |

---

## Implementation Plan

### Phase 1: Core Methods (EHRBase)

| Task | Effort | Details |
|------|--------|---------|
| Implement `get_template_opt()` | 0.5 day | `Accept: application/xml`, return raw text |
| Implement `delete_template()` | 0.5 day | DELETE + cache invalidation + 409 handling |
| Implement `update_template()` | 1 day | PUT attempt + delete-and-re-upload fallback |
| Add HTTP 409 handling to `_handle_response()` | 0.25 day | Map to `ValidationError` with descriptive message |
| Unit tests (mocked HTTP) | 1 day | All three methods, all error paths, cache invalidation |
| Integration tests (EHRBase) | 1 day | Round-trip: upload → get_opt → update → delete |
| **Phase 1 total** | **~4.25 days** | |

### Phase 2: Better Platform Support

| Task | Effort | Details |
|------|--------|---------|
| Review Better API documentation | 0.5 day | Confirm endpoint behavior for all three methods |
| Implement CDR-specific adjustments | 0.5–2 days | Depends on findings from Better docs |
| Integration tests (Better) | 1 day | Same test scenarios against Better |
| **Phase 2 total** | **~2–3.5 days** | |

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

1. `get_template_opt()` returns valid OPT XML that can be re-uploaded to any CDR
2. `delete_template()` removes the template and invalidates the cache
3. `update_template()` works on EHRBase via the delete-and-re-upload fallback
4. All three methods raise typed exceptions with descriptive messages on failure
5. HTTP 409 is handled as `ValidationError` across the client
6. Unit tests cover all success and error paths
7. Integration tests pass against EHRBase 2.x
8. No regressions in existing template operations (`list_templates`, `get_template`, `upload_template`, `get_web_template`)

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **update_template() fallback is non-atomic**: if delete succeeds but re-upload fails, the template is lost from the CDR | Medium | High | Raise a clearly-worded error so the caller knows to re-upload manually. Document this risk in the method docstring. Consider fetching the OPT XML before deleting as a local backup. |
| **Better uses proprietary endpoints** for template management, not the openEHR REST standard | Medium | Medium | Phase 2 adds Better-specific logic after reviewing their API docs. Methods work for EHRBase in Phase 1. |
| **EHRBase behavior changes across versions** (e.g., future EHRBase versions might support PUT) | Low | Low | The try-PUT-first approach automatically benefits from future CDR support without code changes. |
| **409 vs 422 ambiguity**: some CDRs may return 422 instead of 409 for conflict scenarios | Low | Low | The existing 422 → `ValidationError` mapping already handles this; the error message from the CDR body will clarify the cause. |

---

## Dependencies

- **ADR-0005** (Web Template as source of truth) — cache invalidation behavior aligns with this decision
- **PRD-0002** (Composition Lifecycle) — already implemented; `delete_template()` interacts with composition existence
- **Better Platform API docs** — required for Phase 2 (open questions in section "CDR Compatibility")

---

## References

- [openEHR REST API — Definition (Template)](https://specifications.openehr.org/releases/ITS-REST/latest/definition.html#tag/ADL1.4)
- [EHRBase Template API Documentation](https://ehrbase.readthedocs.io/)
- ADR-0005: Web Template as Primary Source of Truth for FLAT Paths
- PRD-0002: Composition Lifecycle (Update & Versioning)
