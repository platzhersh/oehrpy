"""Unit tests for composition lifecycle (update & versioning) — PRD-0002."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from openehr_sdk.client import (
    CompositionFormat,
    CompositionVersionResponse,
    EHRBaseClient,
    NotFoundError,
    PreconditionFailedError,
    VersionedCompositionResponse,
)

EHR_ID = "7d44b88c-4199-4bad-97dc-d78268e01398"
VERSIONED_UID = "8849182c-82ad-4088-a07f-48ead4180515"
DOMAIN = "local.ehrbase.org"
VERSION_UID_V1 = f"{VERSIONED_UID}::{DOMAIN}::1"
VERSION_UID_V2 = f"{VERSIONED_UID}::{DOMAIN}::2"


def _mock_response(status_code: int, json_data: dict | list | None = None) -> httpx.Response:
    """Build a fake httpx.Response."""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.text = ""
    if json_data is not None:
        resp.json.return_value = json_data
    else:
        resp.json.side_effect = Exception("no body")
    return resp


@pytest.fixture
async def client() -> EHRBaseClient:
    c = EHRBaseClient(base_url="http://localhost:8080/ehrbase")
    c._client = AsyncMock(spec=httpx.AsyncClient)
    return c


# ── FR-1: update_composition ─────────────────────────────────────────────────


class TestUpdateComposition:
    async def test_sends_if_match_header(self, client: EHRBaseClient) -> None:
        response_data = {"uid": {"value": VERSION_UID_V2}, "archetype_details": {}}
        client._client.put = AsyncMock(return_value=_mock_response(200, response_data))

        result = await client.update_composition(
            ehr_id=EHR_ID,
            versioned_object_uid=VERSIONED_UID,
            preceding_version_uid=VERSION_UID_V1,
            composition={"ctx/language": "en"},
            template_id="vital_signs",
            format=CompositionFormat.FLAT,
        )

        call_kwargs = client._client.put.call_args
        assert call_kwargs.kwargs["headers"]["If-Match"] == VERSION_UID_V1
        assert VERSIONED_UID in call_kwargs.args[0]
        assert result.uid == VERSION_UID_V2

    async def test_version_conflict_raises_precondition_failed(self, client: EHRBaseClient) -> None:
        client._client.put = AsyncMock(return_value=_mock_response(412))

        with pytest.raises(PreconditionFailedError):
            await client.update_composition(
                ehr_id=EHR_ID,
                versioned_object_uid=VERSIONED_UID,
                preceding_version_uid=VERSION_UID_V1,
                composition={},
            )

    async def test_deleted_composition_raises_not_found(self, client: EHRBaseClient) -> None:
        client._client.put = AsyncMock(return_value=_mock_response(404))

        with pytest.raises(NotFoundError):
            await client.update_composition(
                ehr_id=EHR_ID,
                versioned_object_uid=VERSIONED_UID,
                preceding_version_uid=VERSION_UID_V1,
                composition={},
            )


# ── FR-2: get_composition_at_time ────────────────────────────────────────────


class TestGetCompositionAtTime:
    async def test_passes_version_at_time_param(self, client: EHRBaseClient) -> None:
        response_data = {"uid": {"value": VERSION_UID_V1}, "archetype_details": {}}
        client._client.get = AsyncMock(return_value=_mock_response(200, response_data))

        result = await client.get_composition_at_time(
            ehr_id=EHR_ID,
            versioned_object_uid=VERSIONED_UID,
            version_at_time="2026-01-15T10:00:00Z",
        )

        call_kwargs = client._client.get.call_args
        assert call_kwargs.kwargs["params"]["version_at_time"] == "2026-01-15T10:00:00Z"
        assert result.uid == VERSION_UID_V1


# ── FR-3: get_versioned_composition ──────────────────────────────────────────


class TestGetVersionedComposition:
    async def test_returns_metadata(self, client: EHRBaseClient) -> None:
        response_data = {
            "uid": {"value": VERSIONED_UID},
            "owner_id": {"value": EHR_ID},
            "time_created": {"value": "2026-01-10T08:00:00Z"},
        }
        client._client.get = AsyncMock(return_value=_mock_response(200, response_data))

        result = await client.get_versioned_composition(
            ehr_id=EHR_ID,
            versioned_object_uid=VERSIONED_UID,
        )

        assert isinstance(result, VersionedCompositionResponse)
        assert result.uid == VERSIONED_UID
        assert result.owner_id == EHR_ID
        assert result.time_created == "2026-01-10T08:00:00Z"
        assert "versioned_composition" in client._client.get.call_args.args[0]


# ── FR-4: get_composition_version ────────────────────────────────────────────


class TestGetCompositionVersion:
    async def test_returns_version_with_audit(self, client: EHRBaseClient) -> None:
        response_data = {
            "uid": {"value": VERSION_UID_V1},
            "preceding_version_uid": {},
            "lifecycle_state": {"value": "complete"},
            "commit_audit": {"change_type": {"value": "creation"}},
            "data": {"_type": "COMPOSITION"},
        }
        client._client.get = AsyncMock(return_value=_mock_response(200, response_data))

        result = await client.get_composition_version(
            ehr_id=EHR_ID,
            versioned_object_uid=VERSIONED_UID,
            version_uid=VERSION_UID_V1,
        )

        assert isinstance(result, CompositionVersionResponse)
        assert result.version_uid == VERSION_UID_V1
        assert result.lifecycle_state == "complete"
        assert result.commit_audit is not None
        url = client._client.get.call_args.args[0]
        assert f"/version/{VERSION_UID_V1}" in url


# ── FR-5: list_composition_versions ──────────────────────────────────────────


class TestListCompositionVersions:
    async def test_returns_list(self, client: EHRBaseClient) -> None:
        response_data = [
            {"uid": {"value": VERSION_UID_V1}, "lifecycle_state": {"value": "complete"}},
            {"uid": {"value": VERSION_UID_V2}, "lifecycle_state": {"value": "complete"}},
        ]
        client._client.get = AsyncMock(return_value=_mock_response(200, response_data))

        result = await client.list_composition_versions(
            ehr_id=EHR_ID,
            versioned_object_uid=VERSIONED_UID,
        )

        assert len(result) == 2
        assert result[0].version_uid == VERSION_UID_V1
        assert result[1].version_uid == VERSION_UID_V2

    async def test_returns_list_from_dict_wrapper(self, client: EHRBaseClient) -> None:
        response_data = {
            "versions": [
                {"uid": {"value": VERSION_UID_V1}},
            ]
        }
        client._client.get = AsyncMock(return_value=_mock_response(200, response_data))

        result = await client.list_composition_versions(
            ehr_id=EHR_ID,
            versioned_object_uid=VERSIONED_UID,
        )

        assert len(result) == 1


# ── NFR-3: PreconditionFailedError ───────────────────────────────────────────


class TestPreconditionFailedError:
    def test_is_ehrbase_error(self) -> None:
        from openehr_sdk.client import EHRBaseError

        err = PreconditionFailedError("conflict", status_code=412)
        assert isinstance(err, EHRBaseError)
        assert err.status_code == 412
