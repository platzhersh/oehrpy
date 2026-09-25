"""Tests for EHRBaseClient.get_template_example (ITS-REST template /example)."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import httpx
import pytest

from oehrpy.client import (
    CompositionFormat,
    EHRBaseClient,
    EHRBaseConfig,
    EHRBaseError,
    ExampleDetailLevel,
    ExampleType,
    ValidationError,
)

EXAMPLE_PATH = "/rest/openehr/v1/definition/template/adl1.4/vital_signs/example"
FLAT_EXAMPLE = {"ctx/language": "en", "vital_signs/category|code": "433"}


def _response(status_code: int, body: dict[str, Any] | None = None) -> AsyncMock:
    response = AsyncMock(spec=httpx.Response)
    response.status_code = status_code
    response.json.return_value = body or {}
    response.text = ""
    return response


@pytest.fixture()
def client() -> EHRBaseClient:
    client = EHRBaseClient(config=EHRBaseConfig(base_url="http://localhost:8080/ehrbase"))
    client._client = AsyncMock(spec=httpx.AsyncClient)
    return client


def _mock_get(client: EHRBaseClient, *responses: AsyncMock) -> AsyncMock:
    get = AsyncMock(side_effect=list(responses))
    client._client.get = get  # type: ignore[union-attr]
    return get


class TestSpecRequest:
    """The first request follows ITS-REST 1.1.0."""

    @pytest.mark.asyncio()
    async def test_defaults_to_medium_input_flat(self, client: EHRBaseClient) -> None:
        get = _mock_get(client, _response(200, FLAT_EXAMPLE))

        result = await client.get_template_example("vital_signs")

        assert result == FLAT_EXAMPLE
        get.assert_called_once_with(
            EXAMPLE_PATH,
            params={"type": "input", "detail_level": "medium"},
            headers={"Accept": "application/openehr.wt.flat+json"},
        )

    @pytest.mark.asyncio()
    async def test_passes_detail_level_and_type(self, client: EHRBaseClient) -> None:
        get = _mock_get(client, _response(200))

        await client.get_template_example(
            "vital_signs",
            detail_level=ExampleDetailLevel.COMPLETE,
            example_type=ExampleType.OUTPUT,
        )

        assert get.call_args.kwargs["params"] == {"type": "output", "detail_level": "complete"}

    @pytest.mark.asyncio()
    async def test_accepts_plain_strings(self, client: EHRBaseClient) -> None:
        get = _mock_get(client, _response(200))

        await client.get_template_example(
            "vital_signs", detail_level="required", example_type="input", format="STRUCTURED"
        )

        assert get.call_args.kwargs["params"]["detail_level"] == "required"
        assert get.call_args.kwargs["headers"] == {
            "Accept": "application/openehr.wt.structured+json"
        }

    @pytest.mark.asyncio()
    @pytest.mark.parametrize("fmt", [CompositionFormat.CANONICAL, CompositionFormat.JSON])
    async def test_canonical_uses_application_json(
        self, client: EHRBaseClient, fmt: CompositionFormat
    ) -> None:
        get = _mock_get(client, _response(200))

        await client.get_template_example("vital_signs", format=fmt)

        assert get.call_args.kwargs["headers"] == {"Accept": "application/json"}

    @pytest.mark.asyncio()
    async def test_invalid_detail_level_raises(self, client: EHRBaseClient) -> None:
        with pytest.raises(ValueError):
            await client.get_template_example("vital_signs", detail_level="full")

    @pytest.mark.asyncio()
    async def test_unsupported_level_400_raises_validation_error(
        self, client: EHRBaseClient
    ) -> None:
        _mock_get(client, _response(400, {"message": "detail_level not supported"}))

        with pytest.raises(ValidationError, match="detail_level not supported"):
            await client.get_template_example("vital_signs")


class TestEHRBaseFallback:
    """EHRBase 2.x rejects the spec media types with 406 and needs its own."""

    @pytest.mark.asyncio()
    async def test_retries_with_ehrbase_media_type_on_406(self, client: EHRBaseClient) -> None:
        get = _mock_get(client, _response(406), _response(200, FLAT_EXAMPLE))

        result = await client.get_template_example("vital_signs")

        assert result == FLAT_EXAMPLE
        assert get.call_count == 2
        assert get.call_args.kwargs == {
            "params": {"type": "input", "detail_level": "medium", "format": "FLAT"},
            "headers": {"Accept": "application/openehr.wt.flat.schema+json"},
        }

    @pytest.mark.asyncio()
    async def test_structured_fallback_media_type(self, client: EHRBaseClient) -> None:
        get = _mock_get(client, _response(406), _response(200))

        await client.get_template_example("vital_signs", format=CompositionFormat.STRUCTURED)

        assert get.call_args.kwargs["headers"] == {
            "Accept": "application/openehr.wt.structured.schema+json"
        }
        assert get.call_args.kwargs["params"]["format"] == "STRUCTURED"

    @pytest.mark.asyncio()
    async def test_fallback_is_remembered_per_format(self, client: EHRBaseClient) -> None:
        get = _mock_get(client, _response(406), _response(200), _response(200), _response(200))

        await client.get_template_example("vital_signs")
        await client.get_template_example("vital_signs")
        assert get.call_count == 3
        assert get.call_args.kwargs["params"]["format"] == "FLAT"

        # STRUCTURED has not been negotiated yet, so it starts with the spec media type
        await client.get_template_example("vital_signs", format=CompositionFormat.STRUCTURED)
        assert get.call_args.kwargs["headers"] == {
            "Accept": "application/openehr.wt.structured+json"
        }

    @pytest.mark.asyncio()
    async def test_failed_fallback_is_not_remembered(self, client: EHRBaseClient) -> None:
        get = _mock_get(client, _response(406), _response(406), _response(200))

        with pytest.raises(EHRBaseError) as exc_info:
            await client.get_template_example("vital_signs")
        assert exc_info.value.status_code == 406

        await client.get_template_example("vital_signs")
        assert get.call_args.kwargs["headers"] == {"Accept": "application/openehr.wt.flat+json"}

    @pytest.mark.asyncio()
    async def test_canonical_406_is_not_retried(self, client: EHRBaseClient) -> None:
        get = _mock_get(client, _response(406))

        with pytest.raises(EHRBaseError):
            await client.get_template_example("vital_signs", format=CompositionFormat.CANONICAL)
        assert get.call_count == 1
