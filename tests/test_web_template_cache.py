"""Tests for EHRBaseClient web template caching (ADR-0005)."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import httpx
import pytest

from oehrpy.client.ehrbase import EHRBaseClient, EHRBaseConfig


def _fake_web_template(template_id: str = "test-template") -> dict[str, Any]:
    """Build a minimal Web Template JSON for testing."""
    return {
        "templateId": template_id,
        "version": "2.3",
        "defaultLanguage": "en",
        "tree": {
            "id": "test_composition",
            "name": "Test Composition",
            "rmType": "COMPOSITION",
            "children": [],
        },
    }


@pytest.fixture()
def client() -> EHRBaseClient:
    config = EHRBaseConfig(base_url="http://localhost:8080/ehrbase")
    return EHRBaseClient(config=config)


class TestWebTemplateCaching:
    """Tests for in-memory web template caching (ADR-0005)."""

    def test_cache_starts_empty(self, client: EHRBaseClient) -> None:
        assert client._web_template_cache == {}

    @pytest.mark.asyncio()
    async def test_get_web_template_caches_result(self, client: EHRBaseClient) -> None:
        wt = _fake_web_template()
        mock_response = AsyncMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = wt

        client._client = AsyncMock(spec=httpx.AsyncClient)
        client._client.get = AsyncMock(return_value=mock_response)

        # First call — should hit the network
        result = await client.get_web_template("test-template")
        assert result == wt
        assert client._client.get.call_count == 1

        # Second call — should come from cache
        result2 = await client.get_web_template("test-template")
        assert result2 == wt
        assert client._client.get.call_count == 1  # no additional call

    @pytest.mark.asyncio()
    async def test_get_web_template_bypass_cache(self, client: EHRBaseClient) -> None:
        wt = _fake_web_template()
        mock_response = AsyncMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = wt

        client._client = AsyncMock(spec=httpx.AsyncClient)
        client._client.get = AsyncMock(return_value=mock_response)

        await client.get_web_template("test-template")
        assert client._client.get.call_count == 1

        # Bypass cache
        await client.get_web_template("test-template", use_cache=False)
        assert client._client.get.call_count == 2

    @pytest.mark.asyncio()
    async def test_get_web_template_sends_accept_header(self, client: EHRBaseClient) -> None:
        wt = _fake_web_template()
        mock_response = AsyncMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = wt

        client._client = AsyncMock(spec=httpx.AsyncClient)
        client._client.get = AsyncMock(return_value=mock_response)

        await client.get_web_template("test-template")

        call_kwargs = client._client.get.call_args
        assert call_kwargs.kwargs["headers"]["Accept"] == "application/openehr.wt+json"

    def test_clear_cache_all(self, client: EHRBaseClient) -> None:
        client._web_template_cache["a"] = {"tree": {}}
        client._web_template_cache["b"] = {"tree": {}}

        client.clear_web_template_cache()
        assert client._web_template_cache == {}

    def test_clear_cache_specific(self, client: EHRBaseClient) -> None:
        client._web_template_cache["a"] = {"tree": {}}
        client._web_template_cache["b"] = {"tree": {}}

        client.clear_web_template_cache("a")
        assert "a" not in client._web_template_cache
        assert "b" in client._web_template_cache

    def test_clear_cache_nonexistent_key_is_noop(self, client: EHRBaseClient) -> None:
        client.clear_web_template_cache("nonexistent")
        assert client._web_template_cache == {}
