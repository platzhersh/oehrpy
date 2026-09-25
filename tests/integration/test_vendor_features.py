"""Integration tests for vendor detection, admin API, stored queries and auth.

Runs against whichever CDR ``OEHRPY_CDR`` selects (see ``conftest.py``);
FerroEHR-only tests (RBAC, bearer JWTs) are skipped against EHRBase.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
import uuid

import pytest

from oehrpy.client import (
    AuthorizationError,
    BearerAuth,
    FerroEHRClient,
    NotFoundError,
    OpenEHRClient,
    ServerType,
    detect_server_type,
)

pytestmark = pytest.mark.integration

requires_ferroehr = pytest.mark.skipif(
    ServerType(os.getenv("OEHRPY_CDR", "ehrbase")) is not ServerType.FERROEHR,
    reason="FerroEHR-specific",
)


def _hs256_jwt(secret: str, claims: dict[str, object]) -> str:
    """Sign ``claims`` as an HS256 JWT (FerroEHR's dev-only OIDC trust)."""

    def b64(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

    header = b64(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = b64(json.dumps(claims).encode())
    signature = hmac.new(secret.encode(), f"{header}.{payload}".encode(), hashlib.sha256)
    return f"{header}.{payload}.{b64(signature.digest())}"


def _token(settings: dict[str, str], roles: list[str]) -> str:
    claims = {
        "sub": "oehrpy-tests",
        "iss": settings["issuer"],
        "aud": settings["audience"],
        "exp": int(time.time()) + 600,
        "roles": roles,
    }
    return _hs256_jwt(settings["hmac_secret"], claims)


class TestServerInfo:
    async def test_get_server_info_detects_vendor(
        self, ehrbase_client: OpenEHRClient, cdr_server_type: ServerType
    ) -> None:
        info = await ehrbase_client.get_server_info()
        assert info.server_type is cdr_server_type
        assert info.server_version

    async def test_detect_server_type(
        self, ehrbase_client: OpenEHRClient, cdr_server_type: ServerType
    ) -> None:
        info = await detect_server_type(
            ehrbase_client.config.base_url, auth=ehrbase_client.config.auth
        )
        assert info.server_type is cdr_server_type

    @requires_ferroehr
    async def test_ferroehr_status_works_with_bad_credentials(
        self, ferroehr_settings: dict[str, str]
    ) -> None:
        async with FerroEHRClient(
            base_url=ferroehr_settings["url"], username="nobody", password="wrong"
        ) as client:
            info = await client.get_server_info()
        assert info.server_type is ServerType.FERROEHR


class TestAdminApi:
    async def test_delete_ehr(self, ehrbase_client: OpenEHRClient) -> None:
        ehr = await ehrbase_client.create_ehr()

        await ehrbase_client.delete_ehr(ehr.ehr_id)

        with pytest.raises(NotFoundError):
            await ehrbase_client.get_ehr(ehr.ehr_id)

    async def test_stored_query_lifecycle(self, ehrbase_client: OpenEHRClient) -> None:
        name = f"org.oehrpy::it_{uuid.uuid4().hex[:8]}"
        aql = "SELECT e/ehr_id/value FROM EHR e"

        await ehrbase_client.store_query(name, aql, "1.0.0")
        stored = await ehrbase_client.get_stored_query(name, "1.0.0")
        assert "EHR e" in (stored.q or "")

        result = await ehrbase_client.execute_stored_query(name, "1.0.0", fetch=5)
        assert result.columns

        await ehrbase_client.delete_stored_query(name, "1.0.0")
        with pytest.raises(NotFoundError):
            await ehrbase_client.get_stored_query(name, "1.0.0")


@requires_ferroehr
class TestFerroEHRAuth:
    async def test_bearer_token(self, ferroehr_settings: dict[str, str]) -> None:
        async with FerroEHRClient(
            base_url=ferroehr_settings["url"],
            auth_method=BearerAuth(_token(ferroehr_settings, ["USER"])),
        ) as client:
            ehr = await client.create_ehr()
            assert (await client.get_ehr(ehr.ehr_id)).ehr_id == ehr.ehr_id

    async def test_bearer_token_provider(self, ferroehr_settings: dict[str, str]) -> None:
        calls = 0

        async def provider() -> str:
            nonlocal calls
            calls += 1
            return _token(ferroehr_settings, ["USER"])

        async with FerroEHRClient(
            base_url=ferroehr_settings["url"],
            auth_method=BearerAuth(token_provider=provider),
        ) as client:
            await client.create_ehr()
        assert calls == 1

    async def test_readonly_write_is_forbidden(self, ferroehr_settings: dict[str, str]) -> None:
        async with FerroEHRClient(
            base_url=ferroehr_settings["url"],
            username=ferroehr_settings["readonly_user"],
            password=ferroehr_settings["password"],
        ) as client:
            with pytest.raises(AuthorizationError):
                await client.create_ehr()

    async def test_readonly_bearer_write_is_forbidden(
        self, ferroehr_settings: dict[str, str]
    ) -> None:
        async with FerroEHRClient(
            base_url=ferroehr_settings["url"],
            auth_method=BearerAuth(_token(ferroehr_settings, ["READONLY"])),
        ) as client:
            with pytest.raises(AuthorizationError):
                await client.create_ehr()

    async def test_admin_api_requires_admin_role(self, ferroehr_settings: dict[str, str]) -> None:
        async with FerroEHRClient(
            base_url=ferroehr_settings["url"],
            username=ferroehr_settings["user"],
            password=ferroehr_settings["password"],
        ) as client:
            ehr = await client.create_ehr()
            with pytest.raises(AuthorizationError):
                await client.delete_ehr(ehr.ehr_id)
