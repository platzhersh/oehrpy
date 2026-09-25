"""Tests for the vendor-neutral client, the EHRBase/FerroEHR adapters and auth."""

from __future__ import annotations

import json
import warnings
from collections.abc import Callable
from typing import Any

import httpx
import pytest

from oehrpy.client import (
    AuthorizationError,
    BasicAuth,
    BearerAuth,
    CDRType,
    CompositionFormat,
    EHRBaseClient,
    EHRBaseConfig,
    EHRBaseError,
    FerroEHRClient,
    FerroEHRConfig,
    InsecureTransportWarning,
    OpenEHRClient,
    OpenEHRError,
    ServerInfo,
    ServerType,
    UnsupportedOperationError,
    create_client,
    detect_server_type,
)
from oehrpy.client import factory as factory_module

EHR_ID = "7d44b88c-4199-4bad-97dc-d78268e01398"
VERSION_UID = "8849182c-82ad-4088-a07f-48ead4180515::local.ferroehr::1"
FERRO_STATUS = {
    "status": "UP",
    "server_version": "4.3.1",
    "openehr_rest_api_version": "1.1.0",
    "timestamp": "2026-09-25T12:00:00Z",
}
EHRBASE_STATUS_XML = (
    "<status><ehrbase_version>2.26.0</ehrbase_version>"
    "<openehr_sdk_version>2.20.0</openehr_sdk_version></status>"
)

Handler = Callable[[httpx.Request], httpx.Response]


class Recorder:
    """Mock transport handler that records requests and replays responses."""

    def __init__(self, *responses: httpx.Response) -> None:
        self.responses = list(responses)
        self.requests: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if len(self.responses) > 1:
            return self.responses.pop(0)
        return self.responses[0] if self.responses else httpx.Response(200, json={})

    @property
    def last(self) -> httpx.Request:
        return self.requests[-1]


def _wire(client: OpenEHRClient, handler: Handler) -> OpenEHRClient:
    """Connect ``client`` over a mock transport (same setup as ``connect()``)."""
    client._client = httpx.AsyncClient(
        base_url=client.config.base_url,
        auth=client.config.auth,
        transport=httpx.MockTransport(handler),
        headers={"Accept": "application/json", "Content-Type": "application/json"},
    )
    return client


def _ferro(handler: Handler, **kwargs: Any) -> FerroEHRClient:
    client = FerroEHRClient(username="ferroehr", password="ferroehr", **kwargs)
    _wire(client, handler)
    return client


def _ehrbase(handler: Handler, **kwargs: Any) -> EHRBaseClient:
    client = EHRBaseClient(username="ehrbase-user", password="pw", **kwargs)
    _wire(client, handler)
    return client


# --- configuration & factory ---


class TestConfig:
    def test_vendor_default_base_urls(self) -> None:
        assert EHRBaseClient().config.base_url == "http://localhost:8080/ehrbase"
        assert FerroEHRClient().config.base_url == "http://localhost:8080/ferroehr"

    def test_basic_credentials_stay_a_tuple(self) -> None:
        config = EHRBaseConfig(username="u", password="p", admin_username="a", admin_password="b")
        assert config.auth == ("u", "p")
        assert config.admin_auth == ("a", "b")

    def test_auth_method_wins_over_username(self) -> None:
        bearer = BearerAuth("token")
        config = FerroEHRConfig(username="u", password="p", auth_method=bearer)
        assert config.auth is bearer
        assert config.admin_auth is None

    def test_ehrbase_error_is_openehr_error(self) -> None:
        assert EHRBaseError is OpenEHRError
        assert issubclass(AuthorizationError, EHRBaseError)


class TestCreateClient:
    @pytest.mark.parametrize(
        ("server_type", "expected"),
        [
            ("ehrbase", EHRBaseClient),
            ("ferroehr", FerroEHRClient),
            (ServerType.GENERIC, OpenEHRClient),
        ],
    )
    def test_maps_server_type(self, server_type: str, expected: type) -> None:
        client = create_client(server_type, base_url="http://cdr", username="u", password="p")
        assert type(client) is expected
        assert client.config.base_url == "http://cdr"
        assert client.config.auth == ("u", "p")

    def test_defaults_to_ehrbase(self) -> None:
        assert type(create_client()) is EHRBaseClient

    def test_unknown_server_type(self) -> None:
        with pytest.raises(ValueError, match="Unknown server_type"):
            create_client("better")


# --- auth ---


class TestAuth:
    @pytest.mark.asyncio()
    async def test_static_bearer_token(self) -> None:
        recorder = Recorder()
        client = _wire(FerroEHRClient(auth_method=BearerAuth("abc")), recorder)
        await client.get_ehr(EHR_ID)
        assert recorder.last.headers["Authorization"] == "Bearer abc"

    @pytest.mark.asyncio()
    async def test_async_token_provider_called_per_request(self) -> None:
        tokens = iter(["t1", "t2"])

        async def provider() -> str:
            return next(tokens)

        recorder = Recorder()
        client = _wire(FerroEHRClient(auth_method=BearerAuth(token_provider=provider)), recorder)
        await client.get_ehr(EHR_ID)
        await client.get_ehr(EHR_ID)
        assert [r.headers["Authorization"] for r in recorder.requests] == [
            "Bearer t1",
            "Bearer t2",
        ]

    @pytest.mark.asyncio()
    async def test_sync_token_provider(self) -> None:
        recorder = Recorder()
        auth = BearerAuth(token_provider=lambda: "sync-token")
        client = _wire(FerroEHRClient(auth_method=auth), recorder)
        await client.get_ehr(EHR_ID)
        assert recorder.last.headers["Authorization"] == "Bearer sync-token"

    def test_bearer_needs_exactly_one_source(self) -> None:
        with pytest.raises(ValueError):
            BearerAuth()
        with pytest.raises(ValueError):
            BearerAuth("a", token_provider=lambda: "b")

    def test_reprs_hide_secrets(self) -> None:
        assert "secret" not in repr(BasicAuth("user", "secret"))
        assert "secret" not in repr(BearerAuth("secret"))

    @pytest.mark.asyncio()
    async def test_forbidden_raises_authorization_error(self) -> None:
        client = _ferro(Recorder(httpx.Response(403)))
        with pytest.raises(AuthorizationError) as exc_info:
            await client.create_ehr()
        assert exc_info.value.status_code == 403


# --- server info & detection ---


class TestServerInfo:
    def test_parses_ferroehr_json(self) -> None:
        info = ServerInfo.from_status_body(json.dumps(FERRO_STATUS))
        assert info.server_type is ServerType.FERROEHR
        assert info.server_version == "4.3.1"
        assert info.openehr_rest_api_version == "1.1.0"
        assert info.status == "UP"

    def test_parses_ehrbase_xml(self) -> None:
        info = ServerInfo.from_status_body(EHRBASE_STATUS_XML)
        assert info.server_type is ServerType.EHRBASE
        assert info.server_version == "2.26.0"

    def test_parses_ehrbase_json(self) -> None:
        info = ServerInfo.from_status_body('{"ehrbase_version": "2.26.0"}')
        assert info.server_type is ServerType.EHRBASE

    def test_unknown_body_is_generic(self) -> None:
        assert ServerInfo.from_status_body("not a status").server_type is ServerType.GENERIC

    @pytest.mark.asyncio()
    async def test_ferroehr_status_sent_without_credentials(self) -> None:
        recorder = Recorder(httpx.Response(200, json=FERRO_STATUS))
        client = _ferro(recorder)
        info = await client.get_server_info()
        assert info.server_type is ServerType.FERROEHR
        assert recorder.last.url.path == "/ferroehr/rest/status"
        assert "Authorization" not in recorder.last.headers

    @pytest.mark.asyncio()
    async def test_ehrbase_status_sent_with_credentials(self) -> None:
        recorder = Recorder(httpx.Response(200, text=EHRBASE_STATUS_XML))
        client = _ehrbase(recorder)
        info = await client.get_server_info()
        assert info.server_type is ServerType.EHRBASE
        assert recorder.last.headers["Authorization"].startswith("Basic ")

    @pytest.mark.asyncio()
    async def test_detect_server_type_retries_with_auth(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if "Authorization" not in request.headers:
                return httpx.Response(401)
            return httpx.Response(200, text=EHRBASE_STATUS_XML)

        original = httpx.AsyncClient

        def patched(**kwargs: Any) -> httpx.AsyncClient:
            return original(transport=httpx.MockTransport(handler), **kwargs)

        monkeypatch.setattr(factory_module.httpx, "AsyncClient", patched)
        info = await detect_server_type("http://cdr/ehrbase", auth=("u", "p"))
        assert info.server_type is ServerType.EHRBASE

    @pytest.mark.asyncio()
    async def test_detect_server_type_unreachable_status_is_generic(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        original = httpx.AsyncClient

        def patched(**kwargs: Any) -> httpx.AsyncClient:
            return original(transport=httpx.MockTransport(lambda r: httpx.Response(404)), **kwargs)

        monkeypatch.setattr(factory_module.httpx, "AsyncClient", patched)
        info = await detect_server_type("http://cdr")
        assert info.server_type is ServerType.GENERIC


# --- EHR creation ---


class TestCreateEhr:
    @pytest.mark.asyncio()
    async def test_ferroehr_always_sends_archetype_details(self) -> None:
        recorder = Recorder(httpx.Response(201, json={"ehr_id": {"value": EHR_ID}}))
        client = _ferro(recorder)

        ehr = await client.create_ehr()

        assert ehr.ehr_id == EHR_ID
        body = json.loads(recorder.last.content)
        assert body["_type"] == "EHR_STATUS"
        assert body["archetype_details"]["archetype_id"]["value"] == (
            "openEHR-EHR-EHR_STATUS.generic.v1"
        )
        assert body["subject"] == {"_type": "PARTY_SELF"}

    @pytest.mark.asyncio()
    async def test_ehrbase_without_subject_sends_no_body(self) -> None:
        recorder = Recorder(httpx.Response(201, json={"ehr_id": {"value": EHR_ID}}))
        client = _ehrbase(recorder)
        await client.create_ehr()
        assert recorder.last.content in (b"", b"null")

    @pytest.mark.asyncio()
    async def test_subject_status_has_archetype_details(self) -> None:
        recorder = Recorder(httpx.Response(201, json={"ehr_id": {"value": EHR_ID}}))
        client = _ehrbase(recorder)
        await client.create_ehr(subject_id="123", subject_namespace="patients")
        body = json.loads(recorder.last.content)
        assert body["archetype_details"]["_type"] == "ARCHETYPED"
        external_ref = body["subject"]["external_ref"]
        assert external_ref["id"]["value"] == "123"
        assert external_ref["namespace"] == "patients"

    @pytest.mark.asyncio()
    async def test_ehr_id_from_headers_when_no_body(self) -> None:
        response = httpx.Response(204, headers={"ETag": f'"{EHR_ID}"'})
        client = _ferro(Recorder(response))
        ehr = await client.create_ehr()
        assert ehr.ehr_id == EHR_ID


# --- compositions ---


class TestCompositionRequests:
    @pytest.mark.asyncio()
    async def test_ferroehr_flat_commit_uses_spec_media_type(self) -> None:
        recorder = Recorder(httpx.Response(201, json={"uid": {"value": VERSION_UID}}))
        client = _ferro(recorder)

        result = await client.create_composition(
            EHR_ID, {"ctx/language": "en"}, template_id="vital_signs.v1"
        )

        request = recorder.last
        assert result.uid == VERSION_UID
        assert request.headers["Content-Type"] == "application/openehr.wt.flat+json"
        assert request.headers["openehr-template-id"] == "vital_signs.v1"
        assert request.url.params["templateId"] == "vital_signs.v1"
        assert "format" not in request.url.params

    @pytest.mark.asyncio()
    async def test_ferroehr_canonical_commit(self) -> None:
        recorder = Recorder(httpx.Response(201, json={"uid": {"value": VERSION_UID}}))
        client = _ferro(recorder)
        await client.create_composition(EHR_ID, {"_type": "COMPOSITION"}, format="CANONICAL")
        assert recorder.last.headers["Content-Type"] == "application/json"
        assert "openehr-template-id" not in recorder.last.headers

    @pytest.mark.asyncio()
    async def test_ehrbase_commit_unchanged(self) -> None:
        recorder = Recorder(httpx.Response(201, json={"uid": {"value": VERSION_UID}}))
        client = _ehrbase(recorder)
        await client.create_composition(EHR_ID, {"ctx/language": "en"}, template_id="vs")
        request = recorder.last
        assert request.headers["Content-Type"] == "application/json"
        assert request.url.params["format"] == "FLAT"
        assert request.url.params["templateId"] == "vs"

    @pytest.mark.asyncio()
    async def test_ferroehr_flat_read_negotiates_via_accept(self) -> None:
        recorder = Recorder(httpx.Response(200, json={"vital_signs/_uid": VERSION_UID}))
        client = _ferro(recorder)
        result = await client.get_composition(EHR_ID, VERSION_UID, format=CompositionFormat.FLAT)
        assert result.uid == VERSION_UID
        assert recorder.last.headers["Accept"] == "application/openehr.wt.flat+json"
        assert "format" not in recorder.last.url.params

    @pytest.mark.asyncio()
    async def test_ehrbase_read_uses_format_param(self) -> None:
        recorder = Recorder(httpx.Response(200, json={}))
        client = _ehrbase(recorder)
        await client.get_composition(EHR_ID, VERSION_UID, format=CompositionFormat.FLAT)
        assert recorder.last.url.params["format"] == "FLAT"

    @pytest.mark.asyncio()
    async def test_ferroehr_update_204_quoted_if_match(self) -> None:
        new_uid = VERSION_UID.replace("::1", "::2")
        recorder = Recorder(httpx.Response(204, headers={"ETag": f'"{new_uid}"'}))
        client = _ferro(recorder)

        result = await client.update_composition(
            EHR_ID,
            versioned_object_uid=VERSION_UID.split("::")[0],
            preceding_version_uid=VERSION_UID,
            composition={"ctx/language": "en"},
            template_id="vital_signs.v1",
        )

        assert result.uid == new_uid
        assert result.composition is None
        assert recorder.last.headers["If-Match"] == f'"{VERSION_UID}"'
        assert recorder.last.headers["openehr-template-id"] == "vital_signs.v1"

    @pytest.mark.asyncio()
    async def test_update_uid_from_location_header(self) -> None:
        new_uid = VERSION_UID.replace("::1", "::2")
        location = f"http://cdr/ferroehr/rest/openehr/v1/ehr/{EHR_ID}/composition/{new_uid}"
        client = _ferro(Recorder(httpx.Response(204, headers={"Location": location})))
        result = await client.update_composition(EHR_ID, "x", VERSION_UID, {}, "vs")
        assert result.uid == new_uid

    @pytest.mark.asyncio()
    async def test_ehrbase_if_match_unquoted(self) -> None:
        recorder = Recorder(httpx.Response(200, json={"uid": {"value": VERSION_UID}}))
        client = _ehrbase(recorder)
        await client.update_composition(EHR_ID, "x", VERSION_UID, {}, "vs")
        assert recorder.last.headers["If-Match"] == VERSION_UID


# --- templates ---


class TestTemplates:
    @pytest.mark.asyncio()
    async def test_ferroehr_lists_all_versions(self) -> None:
        body = [
            {"template_id": "vs.v1", "version": "1.0.0"},
            {"template_id": "vs.v2", "version": "2.0.0"},
        ]
        recorder = Recorder(httpx.Response(200, json=body))
        client = _ferro(recorder)

        templates = await client.list_templates()

        assert recorder.last.url.params["version"] == "*"
        assert [t.version for t in templates] == ["1.0.0", "2.0.0"]

    @pytest.mark.asyncio()
    async def test_ferroehr_latest_only(self) -> None:
        recorder = Recorder(httpx.Response(200, json=[]))
        client = _ferro(recorder)
        await client.list_templates(all_versions=False)
        assert "version" not in recorder.last.url.params

    @pytest.mark.asyncio()
    async def test_ehrbase_sends_no_version_filter(self) -> None:
        recorder = Recorder(httpx.Response(200, json=[]))
        client = _ehrbase(recorder)
        await client.list_templates()
        assert "version" not in recorder.last.url.params

    @pytest.mark.asyncio()
    async def test_ferroehr_example_requests_medium(self) -> None:
        recorder = Recorder(httpx.Response(200, json={"ctx/language": "en"}))
        client = _ferro(recorder)
        await client.get_template_example("vs.v1")
        assert recorder.last.url.params["detail_level"] == "medium"
        assert recorder.last.headers["Accept"] == "application/openehr.wt.flat+json"

    @pytest.mark.asyncio()
    async def test_ferroehr_template_delete_falls_back_to_admin_api(self) -> None:
        recorder = Recorder(httpx.Response(405), httpx.Response(204))
        client = _ferro(recorder, admin_username="ferroehr-admin", admin_password="ferroehr")
        await client.delete_template("vs.v1")
        assert recorder.last.url.path == "/ferroehr/rest/openehr/v1/admin/template/vs.v1"


# --- admin API ---


def _basic_user(request: httpx.Request) -> str:
    import base64

    encoded = request.headers["Authorization"].removeprefix("Basic ")
    return base64.b64decode(encoded).decode().split(":")[0]


class TestAdminApi:
    @pytest.mark.asyncio()
    async def test_ferroehr_delete_ehr_uses_nested_admin_path(self) -> None:
        recorder = Recorder(httpx.Response(204))
        client = _ferro(recorder, admin_username="ferroehr-admin", admin_password="ferroehr")

        await client.delete_ehr(EHR_ID)

        assert recorder.last.method == "DELETE"
        assert recorder.last.url.path == f"/ferroehr/rest/openehr/v1/admin/ehr/{EHR_ID}"
        assert _basic_user(recorder.last) == "ferroehr-admin"

    @pytest.mark.asyncio()
    async def test_admin_falls_back_to_regular_credentials(self) -> None:
        recorder = Recorder(httpx.Response(204))
        client = _ferro(recorder)
        await client.delete_ehr(EHR_ID)
        assert _basic_user(recorder.last) == "ferroehr"

    @pytest.mark.asyncio()
    async def test_admin_bearer_auth_method(self) -> None:
        recorder = Recorder(httpx.Response(204))
        client = _ferro(recorder, admin_auth_method=BearerAuth("admin-token"))
        await client.delete_ehr(EHR_ID)
        assert recorder.last.headers["Authorization"] == "Bearer admin-token"

    @pytest.mark.asyncio()
    async def test_ehrbase_delete_ehr_uses_sibling_admin_path(self) -> None:
        recorder = Recorder(httpx.Response(204))
        client = _ehrbase(recorder)
        await client.delete_ehr(EHR_ID)
        assert recorder.last.url.path == f"/ehrbase/rest/admin/ehr/{EHR_ID}"

    @pytest.mark.asyncio()
    async def test_ferroehr_delete_stored_query(self) -> None:
        recorder = Recorder(httpx.Response(204))
        client = _ferro(recorder)
        await client.delete_stored_query("org.example::vitals", "1.0.0")
        assert recorder.last.url.path == (
            "/ferroehr/rest/openehr/v1/admin/query/org.example::vitals/1.0.0"
        )

    @pytest.mark.asyncio()
    async def test_generic_has_no_admin_api(self) -> None:
        client = _wire(OpenEHRClient(base_url="http://cdr"), Recorder())
        with pytest.raises(UnsupportedOperationError):
            await client.delete_stored_query("org.example::vitals", "1.0.0")


# --- other ITS-REST resources ---


class TestItsRestResources:
    @pytest.mark.asyncio()
    async def test_update_ehr_status(self) -> None:
        recorder = Recorder(httpx.Response(200, json={"_type": "EHR_STATUS"}))
        client = _ferro(recorder)
        await client.update_ehr_status(EHR_ID, VERSION_UID, {"_type": "EHR_STATUS"})
        assert recorder.last.method == "PUT"
        assert recorder.last.url.path.endswith(f"/ehr/{EHR_ID}/ehr_status")
        assert recorder.last.headers["If-Match"] == f'"{VERSION_UID}"'

    @pytest.mark.asyncio()
    async def test_get_directory_version(self) -> None:
        recorder = Recorder(httpx.Response(200, json={"_type": "FOLDER"}))
        client = _ferro(recorder)
        folder = await client.get_directory(EHR_ID, version_uid=VERSION_UID, path="a/b")
        assert folder == {"_type": "FOLDER"}
        assert recorder.last.url.path.endswith(f"/ehr/{EHR_ID}/directory/{VERSION_UID}")
        assert recorder.last.url.params["path"] == "a/b"

    @pytest.mark.asyncio()
    async def test_store_and_execute_stored_query(self) -> None:
        recorder = Recorder(
            httpx.Response(200),
            httpx.Response(200, json={"columns": [{"name": "c"}], "rows": [[1]]}),
        )
        client = _ferro(recorder)

        await client.store_query("org.example::count", "SELECT 1", "1.0.0")
        put = recorder.last
        assert put.url.path.endswith("/definition/query/org.example::count/1.0.0")
        assert put.url.params["query_type"] == "AQL"
        assert put.headers["Content-Type"] == "text/plain"
        assert put.content == b"SELECT 1"

        result = await client.execute_stored_query(
            "org.example::count", query_parameters={"ehr_id": EHR_ID}, fetch=10
        )
        post = recorder.last
        assert post.url.path.endswith("/query/org.example::count")
        assert json.loads(post.content) == {"query_parameters": {"ehr_id": EHR_ID}, "fetch": 10}
        assert result.as_dicts() == [{"c": 1}]

    @pytest.mark.asyncio()
    async def test_list_and_get_stored_queries(self) -> None:
        listing = [{"name": "org.example::count", "version": "1.0.0", "type": "AQL"}]
        recorder = Recorder(
            httpx.Response(200, json=listing),
            httpx.Response(200, json={**listing[0], "q": "SELECT 1"}),
        )
        client = _ferro(recorder)

        queries = await client.list_stored_queries()
        assert queries[0].name == "org.example::count"
        assert queries[0].query_type == "AQL"

        query = await client.get_stored_query("org.example::count", "1.0.0")
        assert query.q == "SELECT 1"


# --- transport security ---


class TestTransportSecurity:
    @pytest.mark.asyncio()
    async def test_bearer_over_remote_http_is_refused(self) -> None:
        client = FerroEHRClient(
            base_url="http://cdr.example.org/ferroehr", auth_method=BearerAuth("t")
        )
        with pytest.raises(ValueError, match="plain HTTP"):
            await client.connect()

    @pytest.mark.asyncio()
    async def test_basic_credentials_over_remote_http_warn(self) -> None:
        client = EHRBaseClient(base_url="http://ehrbase:8080/ehrbase", username="u", password="p")
        with pytest.warns(InsecureTransportWarning):
            await client.connect()
        await client.close()

    @pytest.mark.asyncio()
    @pytest.mark.parametrize(
        ("base_url", "kwargs"),
        [
            ("http://localhost:8080/ferroehr", {"auth_method": BearerAuth("t")}),
            ("http://127.0.0.1:8080/ferroehr", {"auth_method": BearerAuth("t")}),
            ("http://[::1]:8080/ferroehr", {"auth_method": BearerAuth("t")}),
            ("https://cdr.example.org/ferroehr", {"auth_method": BearerAuth("t")}),
            ("http://cdr.example.org/ferroehr", {}),
            (
                "http://cdr.example.org/ferroehr",
                {"auth_method": BearerAuth("t"), "allow_insecure_http": True},
            ),
        ],
    )
    async def test_allowed_combinations(self, base_url: str, kwargs: dict[str, Any]) -> None:
        client = FerroEHRClient(base_url=base_url, **kwargs)
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            await client.connect()
        await client.close()

    @pytest.mark.asyncio()
    async def test_better_permanent_delete_uses_admin_credentials(self) -> None:
        recorder = Recorder(httpx.Response(204))
        client = _ehrbase(
            recorder,
            cdr_type=CDRType.BETTER,
            admin_username="better-admin",
            admin_password="pw",
        )
        await client.delete_template("vs.v1", permanent=True)
        assert recorder.last.url.path.endswith("/admin/rest/v1/templates/vs.v1")
        assert _basic_user(recorder.last) == "better-admin"
