"""Tests for template management methods (PRD-0013).

Tests get_template_opt(), update_template(), and delete_template() across
both EHRBase and Better CDR types.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import httpx
import pytest

from openehr_sdk.client.ehrbase import (
    CDRType,
    EHRBaseClient,
    EHRBaseConfig,
    EHRBaseError,
    NotFoundError,
    TemplateResponse,
    ValidationError,
)

SAMPLE_OPT_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<template xmlns="http://schemas.openehr.org/v1">
  <template_id><value>Test Template.v1</value></template_id>
  <concept>Test Template</concept>
</template>
"""

MISMATCHED_OPT_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<template xmlns="http://schemas.openehr.org/v1">
  <template_id><value>Different Template.v1</value></template_id>
  <concept>Different Template</concept>
</template>
"""


def _mock_response(
    status_code: int = 200,
    json_data: dict[str, Any] | None = None,
    text: str = "",
) -> AsyncMock:
    """Build a mock httpx.Response."""
    resp = AsyncMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.text = text or (str(json_data) if json_data else "")
    if json_data is not None:
        resp.json.return_value = json_data
    else:
        resp.json.side_effect = Exception("No JSON")
    return resp


@pytest.fixture()
def ehrbase_client() -> EHRBaseClient:
    config = EHRBaseConfig(base_url="http://localhost:8080/ehrbase")
    client = EHRBaseClient(config=config)
    client._client = AsyncMock(spec=httpx.AsyncClient)
    return client


@pytest.fixture()
def better_client() -> EHRBaseClient:
    config = EHRBaseConfig(
        base_url="https://cdr.example.com",
        cdr_type=CDRType.BETTER,
    )
    client = EHRBaseClient(config=config)
    client._client = AsyncMock(spec=httpx.AsyncClient)
    return client


# --- get_template_opt ---


class TestGetTemplateOpt:
    """Tests for get_template_opt()."""

    @pytest.mark.asyncio()
    async def test_returns_raw_xml_ehrbase(self, ehrbase_client: EHRBaseClient) -> None:
        """EHRBase: GET with Accept: application/xml returns raw XML string."""
        ehrbase_client._client.get = AsyncMock(
            return_value=_mock_response(200, text=SAMPLE_OPT_XML),
        )

        result = await ehrbase_client.get_template_opt("Test Template.v1")

        assert result == SAMPLE_OPT_XML
        call_args = ehrbase_client._client.get.call_args
        assert "application/xml" in call_args.kwargs["headers"]["Accept"]

    @pytest.mark.asyncio()
    async def test_returns_raw_xml_better(self, better_client: EHRBaseClient) -> None:
        """Better: GET on openEHR REST endpoint returns OPT XML."""
        better_client._client.get = AsyncMock(
            return_value=_mock_response(200, text=SAMPLE_OPT_XML),
        )

        result = await better_client.get_template_opt("Test Template.v1")

        assert result == SAMPLE_OPT_XML

    @pytest.mark.asyncio()
    async def test_not_found_raises(self, ehrbase_client: EHRBaseClient) -> None:
        """404 response raises NotFoundError."""
        ehrbase_client._client.get = AsyncMock(
            return_value=_mock_response(404),
        )

        with pytest.raises(NotFoundError, match="Template not found"):
            await ehrbase_client.get_template_opt("nonexistent")

    @pytest.mark.asyncio()
    async def test_server_error_raises(self, ehrbase_client: EHRBaseClient) -> None:
        """5xx response raises EHRBaseError."""
        ehrbase_client._client.get = AsyncMock(
            return_value=_mock_response(500, text="Internal Server Error"),
        )

        with pytest.raises(EHRBaseError):
            await ehrbase_client.get_template_opt("Test Template.v1")


# --- delete_template ---


class TestDeleteTemplate:
    """Tests for delete_template()."""

    @pytest.mark.asyncio()
    async def test_successful_delete_ehrbase(self, ehrbase_client: EHRBaseClient) -> None:
        """EHRBase: 204 response returns None."""
        ehrbase_client._client.delete = AsyncMock(
            return_value=_mock_response(204),
        )

        await ehrbase_client.delete_template("Test Template.v1")

        call_args = ehrbase_client._client.delete.call_args
        assert "/rest/openehr/v1/definition/template/adl1.4/Test Template.v1" in call_args.args[0]

    @pytest.mark.asyncio()
    async def test_successful_retire_better(self, better_client: EHRBaseClient) -> None:
        """Better: EHR Server API DELETE returns 200 with action body."""
        better_client._client.delete = AsyncMock(
            return_value=_mock_response(200, json_data={"action": "DELETE"}),
        )

        await better_client.delete_template("Test Template.v1")

        call_args = better_client._client.delete.call_args
        assert "/rest/v1/template/Test Template.v1" in call_args.args[0]

    @pytest.mark.asyncio()
    async def test_permanent_delete_better(self, better_client: EHRBaseClient) -> None:
        """Better: Admin API DELETE with permanent=True."""
        better_client._client.delete = AsyncMock(
            return_value=_mock_response(204),
        )

        await better_client.delete_template("Test Template.v1", permanent=True)

        call_args = better_client._client.delete.call_args
        assert "/admin/rest/v1/templates/Test Template.v1" in call_args.args[0]

    @pytest.mark.asyncio()
    async def test_permanent_ignored_on_ehrbase(self, ehrbase_client: EHRBaseClient) -> None:
        """EHRBase: permanent flag is ignored (always hard-delete)."""
        ehrbase_client._client.delete = AsyncMock(
            return_value=_mock_response(204),
        )

        await ehrbase_client.delete_template("Test Template.v1", permanent=True)

        call_args = ehrbase_client._client.delete.call_args
        assert "/rest/openehr/v1/definition/template/adl1.4/" in call_args.args[0]

    @pytest.mark.asyncio()
    async def test_not_found_raises(self, ehrbase_client: EHRBaseClient) -> None:
        """404 response raises NotFoundError."""
        ehrbase_client._client.delete = AsyncMock(
            return_value=_mock_response(404),
        )

        with pytest.raises(NotFoundError):
            await ehrbase_client.delete_template("nonexistent")

    @pytest.mark.asyncio()
    async def test_conflict_raises_validation_error(self, ehrbase_client: EHRBaseClient) -> None:
        """409 response raises ValidationError with descriptive message."""
        ehrbase_client._client.delete = AsyncMock(
            return_value=_mock_response(
                409,
                json_data={"message": "Cannot delete template: compositions still reference it"},
            ),
        )

        with pytest.raises(ValidationError) as exc_info:
            await ehrbase_client.delete_template("Test Template.v1")

        assert exc_info.value.status_code == 409

    @pytest.mark.asyncio()
    async def test_cache_invalidation(self, ehrbase_client: EHRBaseClient) -> None:
        """Successful delete clears web template cache for that template."""
        ehrbase_client._web_template_cache["Test Template.v1"] = {"tree": {}}
        ehrbase_client._web_template_cache["Other Template"] = {"tree": {}}

        ehrbase_client._client.delete = AsyncMock(
            return_value=_mock_response(204),
        )

        await ehrbase_client.delete_template("Test Template.v1")

        assert "Test Template.v1" not in ehrbase_client._web_template_cache
        assert "Other Template" in ehrbase_client._web_template_cache


# --- update_template ---


class TestUpdateTemplate:
    """Tests for update_template()."""

    @pytest.mark.asyncio()
    async def test_put_supported(self, ehrbase_client: EHRBaseClient) -> None:
        """200 from PUT returns TemplateResponse (future-proofing)."""
        ehrbase_client._client.put = AsyncMock(
            return_value=_mock_response(
                200,
                json_data={"template_id": "Test Template.v1", "concept": "Test"},
            ),
        )

        result = await ehrbase_client.update_template("Test Template.v1", SAMPLE_OPT_XML)

        assert isinstance(result, TemplateResponse)
        assert result.template_id == "Test Template.v1"

    @pytest.mark.asyncio()
    async def test_put_204_supported(self, ehrbase_client: EHRBaseClient) -> None:
        """204 from PUT returns TemplateResponse with template_id only."""
        ehrbase_client._client.put = AsyncMock(
            return_value=_mock_response(204),
        )

        result = await ehrbase_client.update_template("Test Template.v1", SAMPLE_OPT_XML)

        assert result.template_id == "Test Template.v1"

    @pytest.mark.asyncio()
    async def test_put_unsupported_falls_back(self, ehrbase_client: EHRBaseClient) -> None:
        """405 from PUT triggers delete + re-upload fallback."""
        # PUT returns 405
        ehrbase_client._client.put = AsyncMock(
            return_value=_mock_response(405, text="Method Not Allowed"),
        )
        # DELETE returns 204
        ehrbase_client._client.delete = AsyncMock(
            return_value=_mock_response(204),
        )
        # POST (re-upload) returns 201
        upload_response = _mock_response(201, text="")
        upload_response.status_code = 201
        ehrbase_client._client.post = AsyncMock(return_value=upload_response)

        result = await ehrbase_client.update_template("Test Template.v1", SAMPLE_OPT_XML)

        assert isinstance(result, TemplateResponse)
        assert result.template_id == "Test Template.v1"
        # Verify delete was called
        ehrbase_client._client.delete.assert_called_once()

    @pytest.mark.asyncio()
    async def test_put_501_falls_back(self, ehrbase_client: EHRBaseClient) -> None:
        """501 from PUT also triggers delete + re-upload fallback."""
        ehrbase_client._client.put = AsyncMock(
            return_value=_mock_response(501, text="Not Implemented"),
        )
        ehrbase_client._client.delete = AsyncMock(
            return_value=_mock_response(204),
        )
        upload_response = _mock_response(201, text="")
        upload_response.status_code = 201
        ehrbase_client._client.post = AsyncMock(return_value=upload_response)

        result = await ehrbase_client.update_template("Test Template.v1", SAMPLE_OPT_XML)

        assert isinstance(result, TemplateResponse)

    @pytest.mark.asyncio()
    async def test_fallback_delete_conflict(self, ehrbase_client: EHRBaseClient) -> None:
        """409 from DELETE in fallback raises ValidationError."""
        ehrbase_client._client.put = AsyncMock(
            return_value=_mock_response(405, text="Method Not Allowed"),
        )
        ehrbase_client._client.delete = AsyncMock(
            return_value=_mock_response(
                409,
                json_data={"message": "Cannot delete: compositions exist"},
            ),
        )

        with pytest.raises(ValidationError) as exc_info:
            await ehrbase_client.update_template("Test Template.v1", SAMPLE_OPT_XML)

        assert exc_info.value.status_code == 409

    @pytest.mark.asyncio()
    async def test_fallback_upload_failure(self, ehrbase_client: EHRBaseClient) -> None:
        """Fallback upload failure raises with note about deleted template."""
        ehrbase_client._client.put = AsyncMock(
            return_value=_mock_response(405, text="Method Not Allowed"),
        )
        ehrbase_client._client.delete = AsyncMock(
            return_value=_mock_response(204),
        )
        ehrbase_client._client.post = AsyncMock(
            return_value=_mock_response(400, json_data={"message": "Schema validation failed"}),
        )

        with pytest.raises(ValidationError, match="old template was deleted"):
            await ehrbase_client.update_template("Test Template.v1", SAMPLE_OPT_XML)

    @pytest.mark.asyncio()
    async def test_put_validation_error(self, ehrbase_client: EHRBaseClient) -> None:
        """400 from PUT raises ValidationError directly (no fallback)."""
        ehrbase_client._client.put = AsyncMock(
            return_value=_mock_response(400, json_data={"message": "Schema validation failed"}),
        )

        with pytest.raises(ValidationError):
            await ehrbase_client.update_template("Test Template.v1", SAMPLE_OPT_XML)

    @pytest.mark.asyncio()
    async def test_template_id_mismatch_raises(self, ehrbase_client: EHRBaseClient) -> None:
        """Mismatched template ID in XML vs argument raises ValidationError."""
        with pytest.raises(ValidationError, match="Template ID mismatch"):
            await ehrbase_client.update_template("Test Template.v1", MISMATCHED_OPT_XML)

        # Verify no HTTP calls were made
        ehrbase_client._client.put.assert_not_called()
        ehrbase_client._client.delete.assert_not_called()

    @pytest.mark.asyncio()
    async def test_malformed_xml_raises(self, ehrbase_client: EHRBaseClient) -> None:
        """Unparseable XML raises ValidationError before any HTTP calls."""
        with pytest.raises(ValidationError, match="Could not parse template XML"):
            await ehrbase_client.update_template("Test Template.v1", "not xml at all <<<")

        ehrbase_client._client.put.assert_not_called()

    @pytest.mark.asyncio()
    async def test_cache_invalidation_on_put(self, ehrbase_client: EHRBaseClient) -> None:
        """Successful PUT update clears web template cache."""
        ehrbase_client._web_template_cache["Test Template.v1"] = {"tree": {}}

        ehrbase_client._client.put = AsyncMock(
            return_value=_mock_response(204),
        )

        await ehrbase_client.update_template("Test Template.v1", SAMPLE_OPT_XML)

        assert "Test Template.v1" not in ehrbase_client._web_template_cache

    @pytest.mark.asyncio()
    async def test_cache_invalidation_on_fallback(self, ehrbase_client: EHRBaseClient) -> None:
        """Successful fallback update clears web template cache."""
        ehrbase_client._web_template_cache["Test Template.v1"] = {"tree": {}}

        ehrbase_client._client.put = AsyncMock(
            return_value=_mock_response(405, text="Method Not Allowed"),
        )
        ehrbase_client._client.delete = AsyncMock(
            return_value=_mock_response(204),
        )
        upload_response = _mock_response(201, text="")
        upload_response.status_code = 201
        ehrbase_client._client.post = AsyncMock(return_value=upload_response)

        await ehrbase_client.update_template("Test Template.v1", SAMPLE_OPT_XML)

        assert "Test Template.v1" not in ehrbase_client._web_template_cache


# --- CDRType ---


class TestCDRType:
    """Tests for CDRType enum and config."""

    def test_default_is_ehrbase(self) -> None:
        """Default cdr_type is EHRBASE for backward compatibility."""
        config = EHRBaseConfig()
        assert config.cdr_type == CDRType.EHRBASE

    def test_better_config(self) -> None:
        """CDRType.BETTER can be set."""
        config = EHRBaseConfig(cdr_type=CDRType.BETTER)
        assert config.cdr_type == CDRType.BETTER

    def test_string_values(self) -> None:
        """CDRType values are lowercase strings."""
        assert CDRType.EHRBASE.value == "ehrbase"
        assert CDRType.BETTER.value == "better"


# --- HTTP 409 handling ---


class TestHandle409:
    """Tests for HTTP 409 Conflict handling in _handle_response()."""

    def test_409_raises_validation_error(self, ehrbase_client: EHRBaseClient) -> None:
        """HTTP 409 is mapped to ValidationError."""
        response = AsyncMock(spec=httpx.Response)
        response.status_code = 409
        response.json.return_value = {"message": "Template in use"}
        response.text = '{"message": "Template in use"}'

        with pytest.raises(ValidationError) as exc_info:
            ehrbase_client._handle_response(response)

        assert exc_info.value.status_code == 409
        assert "Template in use" in str(exc_info.value)

    def test_409_without_json_body(self, ehrbase_client: EHRBaseClient) -> None:
        """HTTP 409 with non-JSON body still raises ValidationError."""
        response = AsyncMock(spec=httpx.Response)
        response.status_code = 409
        response.json.side_effect = Exception("Not JSON")
        response.text = "Conflict"

        with pytest.raises(ValidationError) as exc_info:
            ehrbase_client._handle_response(response)

        assert exc_info.value.status_code == 409
