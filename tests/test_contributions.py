"""Unit tests for contributions (audit & atomic changesets) — PRD-0003."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from oehrpy.client import (
    ContributionBuilder,
    ContributionResponse,
    EHRBaseClient,
    NotFoundError,
    PreconditionFailedError,
    ValidationError,
)

EHR_ID = "7d44b88c-4199-4bad-97dc-d78268e01398"
DOMAIN = "local.ehrbase.org"
VERSIONED_UID = "8849182c-82ad-4088-a07f-48ead4180515"
VERSION_UID_V1 = f"{VERSIONED_UID}::{DOMAIN}::1"
CONTRIBUTION_UID = "c0ffee00-0000-4000-8000-000000000000"


def _mock_response(status_code: int, json_data: dict | list | None = None) -> httpx.Response:
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


_COMP = {"_type": "COMPOSITION", "name": {"_type": "DV_TEXT", "value": "Vitals"}}


# ── MR-2: ContributionBuilder ────────────────────────────────────────────────


class TestContributionBuilder:
    def test_empty_build_raises(self) -> None:
        with pytest.raises(ValueError):
            ContributionBuilder().build()

    def test_creation_has_no_preceding_uid(self) -> None:
        body = ContributionBuilder().add_creation(composition=_COMP).build()

        assert body["_type"] == "CONTRIBUTION"
        assert len(body["versions"]) == 1
        version = body["versions"][0]
        assert version["_type"] == "ORIGINAL_VERSION"
        assert "preceding_version_uid" not in version
        assert version["data"] == _COMP
        change_type = version["commit_audit"]["change_type"]
        assert change_type["value"] == "creation"
        assert change_type["defining_code"]["code_string"] == "249"

    def test_amendment_sets_preceding_uid_and_code(self) -> None:
        body = (
            ContributionBuilder()
            .add_amendment(
                preceding_version_uid=VERSION_UID_V1,
                composition=_COMP,
                description="fix",
            )
            .build()
        )

        version = body["versions"][0]
        assert version["preceding_version_uid"]["value"] == VERSION_UID_V1
        assert version["preceding_version_uid"]["_type"] == "OBJECT_VERSION_ID"
        assert version["commit_audit"]["change_type"]["defining_code"]["code_string"] == "250"
        assert version["commit_audit"]["description"]["value"] == "fix"

    def test_modification_code(self) -> None:
        body = (
            ContributionBuilder()
            .add_modification(preceding_version_uid=VERSION_UID_V1, composition=_COMP)
            .build()
        )
        code = body["versions"][0]["commit_audit"]["change_type"]["defining_code"]["code_string"]
        assert code == "251"

    def test_deletion_omits_data_and_sets_code(self) -> None:
        body = ContributionBuilder().add_deletion(preceding_version_uid=VERSION_UID_V1).build()

        version = body["versions"][0]
        assert "data" not in version
        assert version["preceding_version_uid"]["value"] == VERSION_UID_V1
        assert version["commit_audit"]["change_type"]["value"] == "deleted"
        assert version["commit_audit"]["change_type"]["defining_code"]["code_string"] == "523"

    def test_multi_operation_contribution(self) -> None:
        body = (
            ContributionBuilder()
            .add_creation(composition=_COMP)
            .add_amendment(preceding_version_uid=VERSION_UID_V1, composition=_COMP)
            .build()
        )
        assert len(body["versions"]) == 2
        assert body["versions"][0]["commit_audit"]["change_type"]["value"] == "creation"
        assert body["versions"][1]["commit_audit"]["change_type"]["value"] == "amendment"

    def test_set_audit_with_committer(self) -> None:
        body = (
            ContributionBuilder()
            .add_creation(composition=_COMP)
            .set_audit(committer="Dr. Smith", description="Routine vitals")
            .build()
        )
        audit = body["audit"]
        assert audit["_type"] == "AUDIT_DETAILS"
        assert audit["committer"]["name"] == "Dr. Smith"
        assert audit["description"]["value"] == "Routine vitals"

    def test_audit_omitted_when_not_set(self) -> None:
        body = ContributionBuilder().add_creation(composition=_COMP).build()
        assert "audit" not in body

    def test_unknown_lifecycle_state_raises(self) -> None:
        with pytest.raises(ValueError, match="lifecycle_state"):
            ContributionBuilder().add_creation(composition=_COMP, lifecycle_state="incompete")

    def test_system_id_omitted_by_default(self) -> None:
        body = ContributionBuilder().add_creation(composition=_COMP).build()
        commit_audit = body["versions"][0]["commit_audit"]
        assert "system_id" not in commit_audit
        assert "time_committed" not in commit_audit

    def test_system_id_populates_audit_and_time(self) -> None:
        body = (
            ContributionBuilder(system_id="oehrpy.example.org")
            .add_creation(composition=_COMP)
            .set_audit(committer="Dr. Smith")
            .build()
        )
        commit_audit = body["versions"][0]["commit_audit"]
        assert commit_audit["system_id"] == "oehrpy.example.org"
        assert commit_audit["time_committed"]["_type"] == "DV_DATE_TIME"
        assert commit_audit["time_committed"]["value"]
        # The contribution-level audit also carries the system_id.
        assert body["audit"]["system_id"] == "oehrpy.example.org"


# ── FR-1: create_contribution ────────────────────────────────────────────────


class TestCreateContribution:
    async def test_posts_to_contribution_endpoint(self, client: EHRBaseClient) -> None:
        response_data = {
            "uid": {"value": CONTRIBUTION_UID},
            "versions": [{"id": {"value": VERSION_UID_V1}}],
        }
        client._client.post = AsyncMock(return_value=_mock_response(201, response_data))

        body = ContributionBuilder().add_creation(composition=_COMP).build()
        result = await client.create_contribution(EHR_ID, body)

        call = client._client.post.call_args
        assert call.args[0].endswith(f"/ehr/{EHR_ID}/contribution")
        assert call.kwargs["headers"]["Prefer"] == "return=representation"
        assert call.kwargs["json"] == body
        assert isinstance(result, ContributionResponse)
        assert result.contribution_uid == CONTRIBUTION_UID
        assert result.versions == [VERSION_UID_V1]

    async def test_validation_error_raises(self, client: EHRBaseClient) -> None:
        client._client.post = AsyncMock(return_value=_mock_response(422, {"message": "bad"}))

        body = ContributionBuilder().add_creation(composition=_COMP).build()
        with pytest.raises(ValidationError):
            await client.create_contribution(EHR_ID, body)

    async def test_version_conflict_raises_precondition_failed(self, client: EHRBaseClient) -> None:
        client._client.post = AsyncMock(return_value=_mock_response(412))

        body = (
            ContributionBuilder()
            .add_amendment(preceding_version_uid=VERSION_UID_V1, composition=_COMP)
            .build()
        )
        with pytest.raises(PreconditionFailedError):
            await client.create_contribution(EHR_ID, body)


# ── FR-2: get_contribution ───────────────────────────────────────────────────


class TestGetContribution:
    async def test_gets_contribution_by_uid(self, client: EHRBaseClient) -> None:
        response_data = {
            "uid": {"value": CONTRIBUTION_UID},
            "versions": [{"id": {"value": VERSION_UID_V1}}],
            "audit": {"committer": {"name": "Dr. Smith"}},
        }
        client._client.get = AsyncMock(return_value=_mock_response(200, response_data))

        result = await client.get_contribution(EHR_ID, CONTRIBUTION_UID)

        call = client._client.get.call_args
        assert call.args[0].endswith(f"/ehr/{EHR_ID}/contribution/{CONTRIBUTION_UID}")
        assert result.contribution_uid == CONTRIBUTION_UID
        assert result.versions == [VERSION_UID_V1]
        assert result.audit is not None and result.audit["committer"]["name"] == "Dr. Smith"

    async def test_missing_contribution_raises_not_found(self, client: EHRBaseClient) -> None:
        client._client.get = AsyncMock(return_value=_mock_response(404))

        with pytest.raises(NotFoundError):
            await client.get_contribution(EHR_ID, CONTRIBUTION_UID)
