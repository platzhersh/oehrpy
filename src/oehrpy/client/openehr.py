"""
Vendor-neutral openEHR ITS-REST client.

:class:`OpenEHRClient` implements the openEHR REST API (ITS-REST 1.1.0) as
the spec describes it: EHR, EHR_STATUS, COMPOSITION, CONTRIBUTION, DIRECTORY,
template definitions, AQL and stored queries. Vendor adapters
(:class:`~oehrpy.client.EHRBaseClient`, :class:`~oehrpy.client.FerroEHRClient`)
subclass it and override only the handful of hooks where a CDR deviates from
the spec (media types, admin API location, ...). See ADR-0011.

Example:
    >>> async with OpenEHRClient(base_url="https://cdr.example.org/openehr") as client:
    ...     ehr = await client.create_ehr()
    ...     print(f"Created EHR: {ehr.ehr_id}")
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, TypeVar

import httpx
from defusedxml import ElementTree as ET

from .auth import NO_AUTH, AuthMethod


class ServerType(str, Enum):
    """CDR vendors oehrpy has an adapter for."""

    EHRBASE = "ehrbase"
    FERROEHR = "ferroehr"
    GENERIC = "generic"


class CompositionFormat(str, Enum):
    """Supported composition formats."""

    CANONICAL = "CANONICAL"
    JSON = "JSON"  # EHRBase 2.0 uses JSON instead of CANONICAL
    FLAT = "FLAT"
    STRUCTURED = "STRUCTURED"


class ExampleDetailLevel(str, Enum):
    """Detail level of a generated template example (ITS-REST ``detail_level``).

    The spec default is ``REQUIRED``. Only ``REQUIRED`` and ``MEDIUM`` are
    intended to be committable; ``COMPLETE`` is reference material.
    """

    REQUIRED = "required"
    MEDIUM = "medium"
    COMPLETE = "complete"


class ExampleType(str, Enum):
    """Type of a generated template example (ITS-REST ``type``)."""

    INPUT = "input"
    OUTPUT = "output"


# ITS-REST 1.1.0 media types per composition format
_SPEC_MEDIA_TYPES: dict[CompositionFormat, str] = {
    CompositionFormat.CANONICAL: "application/json",
    CompositionFormat.JSON: "application/json",
    CompositionFormat.FLAT: "application/openehr.wt.flat+json",
    CompositionFormat.STRUCTURED: "application/openehr.wt.structured+json",
}

# Kept under its historical name for the template example endpoint
_EXAMPLE_MEDIA_TYPES = _SPEC_MEDIA_TYPES

# EHRBase 2.x media types, which predate the ITS-REST 1.1.0 ones
_EHRBASE_EXAMPLE_MEDIA_TYPES: dict[CompositionFormat, str] = {
    CompositionFormat.FLAT: "application/openehr.wt.flat.schema+json",
    CompositionFormat.STRUCTURED: "application/openehr.wt.structured.schema+json",
}

_EHR_STATUS_ARCHETYPE = "openEHR-EHR-EHR_STATUS.generic.v1"
_OPT_TEMPLATE_ID_PATH = (
    ".//{http://schemas.openehr.org/v1}template_id/{http://schemas.openehr.org/v1}value"
)


# Custom Exceptions


class OpenEHRError(Exception):
    """Base exception for openEHR client errors."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


#: Backwards-compatible alias; ``except EHRBaseError`` catches every client error.
EHRBaseError = OpenEHRError


class AuthenticationError(OpenEHRError):
    """Authentication failed (HTTP 401)."""

    pass


class AuthorizationError(OpenEHRError):
    """Authenticated, but not allowed (HTTP 403), e.g. an RBAC denial such as a
    ``READONLY`` user writing, or a non-``ADMIN`` user calling the admin API."""

    pass


class NotFoundError(OpenEHRError):
    """Resource not found."""

    pass


class ValidationError(OpenEHRError):
    """Validation error from server."""

    pass


class PreconditionFailedError(OpenEHRError):
    """Version conflict — the If-Match header did not match (HTTP 412)."""

    pass


class UnsupportedOperationError(OpenEHRError):
    """The operation is a vendor extension this client has no adapter for."""

    pass


# Response dataclasses


@dataclass
class EHRResponse:
    """Response from EHR operations."""

    ehr_id: str
    ehr_status: dict[str, Any] | None = None
    system_id: str | None = None
    time_created: str | None = None

    @classmethod
    def from_response(cls, data: dict[str, Any]) -> EHRResponse:
        """Create from API response."""
        system_id_data = data.get("system_id")
        time_created_data = data.get("time_created")
        return cls(
            ehr_id=data.get("ehr_id", {}).get("value", data.get("ehr_id", "")),
            ehr_status=data.get("ehr_status"),
            system_id=system_id_data.get("value") if system_id_data else None,
            time_created=time_created_data.get("value") if time_created_data else None,
        )


@dataclass
class CompositionResponse:
    """Response from composition operations."""

    uid: str
    ehr_id: str | None = None
    template_id: str | None = None
    archetype_id: str | None = None
    composition: dict[str, Any] | None = None

    @classmethod
    def from_response(cls, data: dict[str, Any], ehr_id: str | None = None) -> CompositionResponse:
        """Create from API response."""
        # Try canonical format first (uid is a dict with "value" key)
        uid_data = data.get("uid")
        uid = uid_data.get("value", "") if isinstance(uid_data, dict) else uid_data or ""

        template_id = data.get("archetype_details", {}).get("template_id", {}).get("value")
        archetype_id = data.get("archetype_details", {}).get("archetype_id", {}).get("value")

        # For FLAT format responses, extract uid from */_uid key
        if not uid:
            for key, value in data.items():
                if key.endswith("/_uid") and isinstance(value, str):
                    uid = value
                    break

        return cls(
            uid=uid,
            ehr_id=ehr_id,
            template_id=template_id,
            archetype_id=archetype_id,
            composition=data,
        )


@dataclass
class QueryResponse:
    """Response from AQL query."""

    name: str | None = None
    query: str | None = None
    columns: list[dict[str, Any]] = field(default_factory=list)
    rows: list[list[Any]] = field(default_factory=list)

    @classmethod
    def from_response(cls, data: dict[str, Any]) -> QueryResponse:
        """Create from API response."""
        return cls(
            name=data.get("name"),
            query=data.get("q"),
            columns=data.get("columns", []),
            rows=data.get("rows", []),
        )

    def as_dicts(self) -> list[dict[str, Any]]:
        """Convert rows to list of dictionaries with column names as keys."""
        if not self.columns:
            return []
        col_names = [col.get("name", f"col_{i}") for i, col in enumerate(self.columns)]
        return [dict(zip(col_names, row, strict=False)) for row in self.rows]


@dataclass
class StoredQueryResponse:
    """A STORED_QUERY definition (``/definition/query``)."""

    name: str
    version: str | None = None
    query_type: str | None = None
    saved: str | None = None
    q: str | None = None

    @classmethod
    def from_response(cls, data: dict[str, Any]) -> StoredQueryResponse:
        """Create from API response."""
        return cls(
            name=data.get("name") or data.get("qualified_query_name") or "",
            version=data.get("version"),
            query_type=data.get("type"),
            saved=data.get("saved") or data.get("saved_time"),
            q=data.get("q"),
        )


@dataclass
class TemplateResponse:
    """Response from template operations."""

    template_id: str
    concept: str | None = None
    archetype_id: str | None = None
    version: str | None = None
    created_timestamp: str | None = None

    @classmethod
    def from_response(cls, data: dict[str, Any]) -> TemplateResponse:
        """Create from API response."""
        return cls(
            template_id=data.get("template_id", ""),
            concept=data.get("concept"),
            archetype_id=data.get("archetype_id"),
            version=data.get("version"),
            created_timestamp=data.get("created_timestamp"),
        )


@dataclass
class VersionedCompositionResponse:
    """Response from versioned composition metadata endpoint."""

    uid: str
    owner_id: str | None = None
    time_created: str | None = None

    @classmethod
    def from_response(cls, data: dict[str, Any]) -> VersionedCompositionResponse:
        """Create from API response."""
        uid_data = data.get("uid", {})
        uid = uid_data.get("value", "") if isinstance(uid_data, dict) else uid_data or ""
        owner_data = data.get("owner_id", {})
        owner_id = owner_data.get("value", "") if isinstance(owner_data, dict) else owner_data
        time_created_data = data.get("time_created", {})
        time_created = (
            time_created_data.get("value", "")
            if isinstance(time_created_data, dict)
            else time_created_data
        )
        return cls(uid=uid, owner_id=owner_id, time_created=time_created)


@dataclass
class CompositionVersionResponse:
    """Response from a specific composition version endpoint."""

    version_uid: str
    preceding_version_uid: str | None = None
    lifecycle_state: str | None = None
    commit_audit: dict[str, Any] | None = None
    data: dict[str, Any] | None = None

    @classmethod
    def from_response(cls, data: dict[str, Any]) -> CompositionVersionResponse:
        """Create from API response."""
        uid_data = data.get("uid", {})
        version_uid = uid_data.get("value", "") if isinstance(uid_data, dict) else uid_data or ""
        preceding = data.get("preceding_version_uid", {})
        preceding_uid = preceding.get("value", "") if isinstance(preceding, dict) else preceding
        lifecycle = data.get("lifecycle_state", {})
        lifecycle_state = lifecycle.get("value", "") if isinstance(lifecycle, dict) else lifecycle
        return cls(
            version_uid=version_uid,
            preceding_version_uid=preceding_uid or None,
            lifecycle_state=lifecycle_state or None,
            commit_audit=data.get("commit_audit"),
            data=data.get("data"),
        )


@dataclass
class ContributionResponse:
    """Response from contribution operations.

    A contribution groups one or more versioned-object changes committed
    atomically with shared audit metadata (see PRD-0003).
    """

    contribution_uid: str
    versions: list[str] = field(default_factory=list)
    audit: dict[str, Any] | None = None
    ehr_id: str | None = None

    @classmethod
    def from_response(cls, data: dict[str, Any], ehr_id: str | None = None) -> ContributionResponse:
        """Create from API response."""
        uid_data = data.get("uid", {})
        contribution_uid = (
            uid_data.get("value", "") if isinstance(uid_data, dict) else uid_data or ""
        )

        # ``versions`` is a list of OBJECT_REF; extract the referenced ids.
        versions: list[str] = []
        for ref in data.get("versions", []) or []:
            if isinstance(ref, dict):
                ref_id = ref.get("id", {})
                value = ref_id.get("value") if isinstance(ref_id, dict) else None
                versions.append(value if value is not None else str(ref_id))
            elif ref is not None:
                versions.append(str(ref))

        return cls(
            contribution_uid=contribution_uid,
            versions=versions,
            audit=data.get("audit"),
            ehr_id=ehr_id,
        )


@dataclass
class ServerInfo:
    """What a CDR reports about itself on ``GET {base}/rest/status``."""

    server_type: ServerType
    server_version: str | None = None
    openehr_rest_api_version: str | None = None
    status: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_status_body(cls, body: str) -> ServerInfo:
        """Parse a ``/rest/status`` body, inferring the vendor from its shape.

        FerroEHR answers with JSON ``{status, server_version,
        openehr_rest_api_version, ...}``; EHRBase with ``ehrbase_version`` and
        friends, as XML by default or JSON when asked for it.
        """
        data: dict[str, Any] = {}
        try:
            parsed = json.loads(body)
            if isinstance(parsed, dict):
                data = parsed
        except ValueError:
            try:
                root = ET.fromstring(body)
            except ET.ParseError:
                return cls(server_type=ServerType.GENERIC)
            data = {child.tag.split("}")[-1]: (child.text or "").strip() for child in root.iter()}

        if "ehrbase_version" in data:
            return cls(
                server_type=ServerType.EHRBASE,
                server_version=data.get("ehrbase_version"),
                openehr_rest_api_version=data.get("openehr_sdk_version"),
                raw=data,
            )
        if "server_version" in data:
            return cls(
                server_type=ServerType.FERROEHR,
                server_version=data.get("server_version"),
                openehr_rest_api_version=data.get("openehr_rest_api_version"),
                status=data.get("status"),
                raw=data,
            )
        return cls(server_type=ServerType.GENERIC, raw=data)


@dataclass
class OpenEHRConfig:
    """Configuration for :class:`OpenEHRClient`.

    Credentials can be given as ``username``/``password`` (HTTP Basic, the
    historical EHRBase style) or as any :data:`~oehrpy.client.auth.AuthMethod`
    via ``auth_method`` — e.g. :class:`~oehrpy.client.BearerAuth` for OIDC.
    ``auth_method`` wins when both are set. The same applies to the admin
    credentials used for vendor admin APIs; when none are configured, admin
    calls fall back to the regular credentials.
    """

    base_url: str = "http://localhost:8080"
    username: str | None = None
    password: str | None = None
    admin_username: str | None = None
    admin_password: str | None = None
    timeout: float = 30.0
    verify_ssl: bool = True
    auth_method: AuthMethod = None
    admin_auth_method: AuthMethod = None
    headers: dict[str, str] = field(default_factory=dict)

    @property
    def auth(self) -> AuthMethod:
        """Credentials for regular requests, or None."""
        if self.auth_method is not None:
            return self.auth_method
        if self.username and self.password:
            return (self.username, self.password)
        return None

    @property
    def admin_auth(self) -> AuthMethod:
        """Explicitly configured admin credentials, or None."""
        if self.admin_auth_method is not None:
            return self.admin_auth_method
        if self.admin_username and self.admin_password:
            return (self.admin_username, self.admin_password)
        return None


_ClientT = TypeVar("_ClientT", bound="OpenEHRClient")


class OpenEHRClient:
    """Async HTTP client for an ITS-REST 1.1.0 openEHR CDR.

    Use it directly for CDRs without an adapter, or use a vendor subclass
    (:class:`~oehrpy.client.EHRBaseClient`,
    :class:`~oehrpy.client.FerroEHRClient`) or
    :func:`~oehrpy.client.create_client`.

    Web Templates fetched via :meth:`get_web_template` are cached in memory
    for the lifetime of the client instance to avoid repeated CDR round-trips
    (see ADR-0005).

    Example:
        >>> config = OpenEHRConfig(
        ...     base_url="https://cdr.example.org/openehr",
        ...     auth_method=BearerAuth("eyJ..."),
        ... )
        >>> async with OpenEHRClient(config=config) as client:
        ...     ehr = await client.create_ehr()
    """

    #: Vendor this client targets.
    server_type: ServerType = ServerType.GENERIC
    #: Config class instantiated from ``**kwargs`` when no config is given.
    config_class: type[OpenEHRConfig] = OpenEHRConfig
    #: Path of the vendor admin API relative to the base URL, if any.
    admin_prefix: str | None = None
    #: Whether ``/rest/status`` needs credentials.
    status_requires_auth: bool = True
    #: Whether the server honours ITS-REST's ``version`` filter on the template
    #: list (and collapses to the latest version without it).
    supports_template_version_filter: bool = False
    #: Always send an EHR_STATUS body when creating an EHR.
    always_send_ehr_status: bool = False

    def __init__(
        self,
        base_url: str | None = None,
        config: OpenEHRConfig | None = None,
        **kwargs: Any,
    ):
        """Initialize the client.

        Args:
            base_url: CDR base URL, without ``/rest/openehr/v1`` (shortcut for
                ``config.base_url``).
            config: Full configuration object.
            **kwargs: Additional arguments passed to the config class.
        """
        if config:
            self.config = config
        else:
            if base_url:
                kwargs["base_url"] = base_url
            self.config = self.config_class(**kwargs)
        self._client: httpx.AsyncClient | None = None
        self._web_template_cache: dict[str, dict[str, Any]] = {}
        # Formats for which the CDR only accepts EHRBase's example media types
        self._example_ehrbase_formats: set[CompositionFormat] = set()

    async def __aenter__(self: _ClientT) -> _ClientT:
        """Enter async context."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context."""
        await self.close()

    async def connect(self) -> None:
        """Create the HTTP client connection."""
        self._client = httpx.AsyncClient(
            base_url=self.config.base_url,
            auth=self.config.auth,
            timeout=self.config.timeout,
            verify=self.config.verify_ssl,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                **self.config.headers,
            },
        )

    async def close(self) -> None:
        """Close the HTTP client connection."""
        if self._client:
            await self._client.aclose()
            self._client = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Get the HTTP client, raising if not connected."""
        if not self._client:
            raise RuntimeError("Client not connected. Use 'async with' or call connect() first.")
        return self._client

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """Handle response and raise appropriate errors."""
        if response.status_code == 401:
            raise AuthenticationError(
                "Authentication failed",
                status_code=response.status_code,
            )
        if response.status_code == 403:
            raise AuthorizationError(
                "Forbidden: the credentials lack the role this operation requires",
                status_code=response.status_code,
            )
        if response.status_code == 404:
            raise NotFoundError(
                "Resource not found",
                status_code=response.status_code,
            )
        if response.status_code == 412:
            raise PreconditionFailedError(
                "Version conflict: the preceding version UID does not match the latest version",
                status_code=response.status_code,
            )
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
        if response.status_code == 400 or response.status_code == 422:
            try:
                error_data = response.json()
            except Exception:
                error_data = {"message": response.text}
            raise ValidationError(
                error_data.get("message", "Validation error"),
                status_code=response.status_code,
                response=error_data,
            )
        if response.status_code >= 400:
            try:
                # Truncate response to avoid logging sensitive data (PII/PHI)
                error_text = response.text[:200] if response.text else ""
                suffix = "..." if len(response.text) > 200 else ""
                error_body = f" - {error_text}{suffix}"
            except Exception:
                error_body = ""
            raise OpenEHRError(
                f"Request failed: {response.status_code}{error_body}",
                status_code=response.status_code,
            )

        if response.status_code == 204:
            return {}

        try:
            data: dict[str, Any] = response.json()
            return data
        except Exception:
            return {"raw": response.text}

    @staticmethod
    def _uid_from_headers(response: httpx.Response) -> str:
        """Object/version UID of a representation-less write response.

        ITS-REST returns it in ``ETag`` (quoted) and as the last segment of
        ``Location`` — the only place it lives when a CDR answers 204 or
        ignores ``Prefer: return=representation``.
        """
        try:
            headers = response.headers
            etag = headers.get("ETag")
            location = headers.get("Location")
        except Exception:
            return ""
        if isinstance(etag, str):
            value = etag.removeprefix("W/").strip('"')
            if value:
                return value
        if isinstance(location, str) and location:
            return location.rstrip("/").rsplit("/", 1)[-1]
        return ""

    def _admin_url(self, path: str) -> str:
        """URL of a vendor admin API resource, e.g. ``ehr/{id}``."""
        if self.admin_prefix is None:
            raise UnsupportedOperationError(
                f"{type(self).__name__} has no admin API; this operation is a vendor "
                "extension outside ITS-REST. Use a vendor client (see create_client)."
            )
        return f"{self.admin_prefix}/{path}"

    def _admin_auth(self) -> Any:
        """Admin credentials, falling back to the client's regular ones."""
        return self.config.admin_auth or httpx.USE_CLIENT_DEFAULT

    @staticmethod
    def _format_value(format: str | CompositionFormat | None) -> str | None:
        return format.value if isinstance(format, CompositionFormat) else format

    def _if_match(self, version_uid: str) -> str:
        """``If-Match`` value for a preceding version UID (an entity tag)."""
        if version_uid.startswith('"') or version_uid.startswith("W/"):
            return version_uid
        return f'"{version_uid}"'

    def _media_type(self, format: str | None) -> str:
        try:
            return _SPEC_MEDIA_TYPES[CompositionFormat(format)] if format else "application/json"
        except ValueError:
            return "application/json"

    def _composition_write_request(
        self, format: str | None, template_id: str | None
    ) -> tuple[dict[str, str], dict[str, str]]:
        """Headers and query params for a composition commit.

        ITS-REST selects the format via ``Content-Type`` and requires the
        ``openehr-template-id`` header for simplified formats (FLAT,
        STRUCTURED). The ``templateId`` query parameter is not in the spec but
        is harmless and what EHRBase-style servers expect, so both are sent.
        """
        headers = {
            "Prefer": "return=representation",
            "Content-Type": self._media_type(format),
            "Accept": "application/json",
        }
        params: dict[str, str] = {}
        if template_id:
            headers["openehr-template-id"] = template_id
            params["templateId"] = template_id
        return headers, params

    def _composition_read_request(
        self, format: str | None
    ) -> tuple[dict[str, str], dict[str, str]]:
        """Headers and query params for reading a composition in ``format``."""
        return {"Accept": self._media_type(format)}, {}

    def _composition_from_response(
        self, response: httpx.Response, ehr_id: str
    ) -> CompositionResponse:
        data = self._handle_response(response)
        result = CompositionResponse.from_response(data, ehr_id)
        if not result.uid:
            result.uid = self._uid_from_headers(response)
            if not data:
                result.composition = None
        return result

    def _ehr_status_body(
        self, subject_id: str | None, subject_namespace: str | None
    ) -> dict[str, Any] | None:
        """EHR_STATUS to create an EHR with, or None to let the server default.

        ``archetype_details`` is mandatory on an archetype root (RM invariant
        ``Archetyped_valid``); EHRBase fills it in server-side, stricter CDRs
        such as FerroEHR reject the request with 422 without it.
        """
        has_subject = bool(subject_id and subject_namespace)
        if not has_subject and not self.always_send_ehr_status:
            return None
        subject: dict[str, Any] = {"_type": "PARTY_SELF"}
        if has_subject:
            subject["external_ref"] = {
                "_type": "PARTY_REF",
                "id": {
                    "_type": "GENERIC_ID",
                    "value": subject_id,
                    "scheme": "id_scheme",
                },
                "namespace": subject_namespace,
                "type": "PERSON",
            }
        return {
            "_type": "EHR_STATUS",
            "archetype_node_id": _EHR_STATUS_ARCHETYPE,
            "archetype_details": {
                "_type": "ARCHETYPED",
                "archetype_id": {"_type": "ARCHETYPE_ID", "value": _EHR_STATUS_ARCHETYPE},
                "rm_version": "1.0.4",
            },
            "name": {"_type": "DV_TEXT", "value": "EHR Status"},
            "subject": subject,
            "is_modifiable": True,
            "is_queryable": True,
        }

    # Server info

    async def get_server_info(self) -> ServerInfo:
        """Fetch ``GET {base}/rest/status`` and parse it.

        Returns:
            ServerInfo with the detected vendor and version.
        """
        auth: Any = httpx.USE_CLIENT_DEFAULT if self.status_requires_auth else NO_AUTH
        response = await self.client.get(
            "/rest/status",
            headers={"Accept": "application/json, application/xml;q=0.9"},
            auth=auth,
        )
        if response.status_code >= 400:
            self._handle_response(response)
        return ServerInfo.from_status_body(response.text)

    # EHR Operations

    async def create_ehr(
        self,
        ehr_id: str | None = None,
        subject_id: str | None = None,
        subject_namespace: str | None = None,
    ) -> EHRResponse:
        """Create a new EHR.

        Args:
            ehr_id: Optional specific EHR ID to use.
            subject_id: Optional subject external ID.
            subject_namespace: Namespace for subject ID.

        Returns:
            EHRResponse with the created EHR details.
        """
        headers: dict[str, str] = {"Prefer": "return=representation"}
        body = self._ehr_status_body(subject_id, subject_namespace)
        if ehr_id:
            if body is None:
                response = await self.client.put(
                    f"/rest/openehr/v1/ehr/{ehr_id}",
                    headers=headers,
                )
            else:
                response = await self.client.put(
                    f"/rest/openehr/v1/ehr/{ehr_id}",
                    headers=headers,
                    json=body,
                )
        else:
            response = await self.client.post(
                "/rest/openehr/v1/ehr",
                headers=headers,
                json=body,
            )

        data = self._handle_response(response)
        result = EHRResponse.from_response(data)
        if not result.ehr_id:
            result.ehr_id = ehr_id or self._uid_from_headers(response)
        return result

    async def get_ehr(self, ehr_id: str) -> EHRResponse:
        """Get an EHR by ID.

        Args:
            ehr_id: The EHR ID.

        Returns:
            EHRResponse with EHR details.
        """
        response = await self.client.get(f"/rest/openehr/v1/ehr/{ehr_id}")
        data = self._handle_response(response)
        return EHRResponse.from_response(data)

    async def get_ehr_by_subject(
        self,
        subject_id: str,
        subject_namespace: str,
    ) -> EHRResponse:
        """Get an EHR by subject ID.

        Args:
            subject_id: The subject external ID.
            subject_namespace: The namespace for the subject ID.

        Returns:
            EHRResponse with EHR details.
        """
        response = await self.client.get(
            "/rest/openehr/v1/ehr",
            params={
                "subject_id": subject_id,
                "subject_namespace": subject_namespace,
            },
        )
        data = self._handle_response(response)
        return EHRResponse.from_response(data)

    async def delete_ehr(self, ehr_id: str) -> None:
        """Physically delete an EHR and everything in it (irreversible).

        ITS-REST has no EHR deletion; this uses the vendor admin API with the
        admin credentials (falling back to the regular ones). The generic
        client tries ``DELETE /ehr/{ehr_id}``, which some servers accept.

        Raises:
            AuthorizationError: If the credentials lack the admin role (403).
            NotFoundError: If the EHR does not exist (404).
        """
        if self.admin_prefix is None:
            response = await self.client.delete(f"/rest/openehr/v1/ehr/{ehr_id}")
        else:
            response = await self.client.delete(
                self._admin_url(f"ehr/{ehr_id}"),
                auth=self._admin_auth(),
            )
        self._handle_response(response)

    # EHR_STATUS Operations

    async def get_ehr_status(
        self,
        ehr_id: str,
        *,
        version_at_time: str | None = None,
    ) -> dict[str, Any]:
        """Get the EHR_STATUS of an EHR (latest, or as of ``version_at_time``)."""
        params = {"version_at_time": version_at_time} if version_at_time else None
        response = await self.client.get(
            f"/rest/openehr/v1/ehr/{ehr_id}/ehr_status",
            params=params,
        )
        return self._handle_response(response)

    async def update_ehr_status(
        self,
        ehr_id: str,
        preceding_version_uid: str,
        ehr_status: dict[str, Any],
    ) -> dict[str, Any]:
        """Replace the EHR_STATUS of an EHR.

        Args:
            ehr_id: The EHR ID.
            preceding_version_uid: Version UID being updated (``If-Match``).
            ehr_status: The new canonical EHR_STATUS.

        Returns:
            The new EHR_STATUS (empty if the server returned no body).
        """
        response = await self.client.put(
            f"/rest/openehr/v1/ehr/{ehr_id}/ehr_status",
            json=ehr_status,
            headers={
                "Prefer": "return=representation",
                "If-Match": self._if_match(preceding_version_uid),
            },
        )
        return self._handle_response(response)

    # Composition Operations

    async def create_composition(
        self,
        ehr_id: str,
        composition: dict[str, Any],
        template_id: str | None = None,
        format: str | CompositionFormat = CompositionFormat.FLAT,
    ) -> CompositionResponse:
        """Create a new composition.

        Args:
            ehr_id: The EHR ID.
            composition: The composition data.
            template_id: Template ID (required for FLAT format).
            format: Composition format (FLAT, CANONICAL, STRUCTURED).

        Returns:
            CompositionResponse with composition details.
        """
        headers, params = self._composition_write_request(self._format_value(format), template_id)

        response = await self.client.post(
            f"/rest/openehr/v1/ehr/{ehr_id}/composition",
            json=composition,
            headers=headers,
            params=params if params else None,
        )

        return self._composition_from_response(response, ehr_id)

    async def get_composition(
        self,
        ehr_id: str,
        composition_uid: str,
        format: str | CompositionFormat = CompositionFormat.CANONICAL,
    ) -> CompositionResponse:
        """Get a composition by UID.

        Args:
            ehr_id: The EHR ID.
            composition_uid: The composition UID (can be versioned object UID or full version UID).
            format: Desired response format.

        Returns:
            CompositionResponse with composition data.
        """
        # The full UID is used as provided:
        # - versioned_object_uid (uuid::system) returns latest version
        # - full version_uid (uuid::system::version) returns that specific version
        headers, params = self._composition_read_request(self._format_value(format))

        response = await self.client.get(
            f"/rest/openehr/v1/ehr/{ehr_id}/composition/{composition_uid}",
            params=params if params else None,
            headers=headers or None,
        )

        data = self._handle_response(response)
        return CompositionResponse.from_response(data, ehr_id)

    async def update_composition(
        self,
        ehr_id: str,
        versioned_object_uid: str,
        preceding_version_uid: str,
        composition: dict[str, Any],
        template_id: str | None = None,
        format: str | CompositionFormat = CompositionFormat.FLAT,
    ) -> CompositionResponse:
        """Update an existing composition.

        Servers may answer with the new composition (200) or with no body
        (204); in the latter case ``composition`` is None and ``uid`` is taken
        from the ``ETag``/``Location`` headers.

        Args:
            ehr_id: The EHR ID.
            versioned_object_uid: The composition's UUID (used in the request path).
            preceding_version_uid: Full version string (e.g. ``uuid::domain::1``),
                sent as the ``If-Match`` header for optimistic concurrency.
            composition: The updated composition data.
            template_id: Template ID.
            format: Composition format.

        Returns:
            CompositionResponse with updated composition.

        Raises:
            PreconditionFailedError: If the preceding version UID does not match
                the latest version (HTTP 412).
            NotFoundError: If the composition has been deleted (HTTP 404).
        """
        headers, params = self._composition_write_request(self._format_value(format), template_id)
        headers["If-Match"] = self._if_match(preceding_version_uid)

        response = await self.client.put(
            f"/rest/openehr/v1/ehr/{ehr_id}/composition/{versioned_object_uid}",
            json=composition,
            headers=headers,
            params=params if params else None,
        )

        return self._composition_from_response(response, ehr_id)

    async def delete_composition(
        self,
        ehr_id: str,
        composition_uid: str,
    ) -> None:
        """Delete a composition.

        Args:
            ehr_id: The EHR ID.
            composition_uid: The composition UID.
        """
        # Extract versioned object UID (uuid::system::version -> uuid::system)
        uid_parts = composition_uid.split("::")
        versioned_object_uid = "::".join(uid_parts[:2]) if len(uid_parts) >= 2 else composition_uid

        response = await self.client.delete(
            f"/rest/openehr/v1/ehr/{ehr_id}/composition/{versioned_object_uid}",
        )
        self._handle_response(response)

    # Composition Versioning Operations

    async def get_composition_at_time(
        self,
        ehr_id: str,
        versioned_object_uid: str,
        version_at_time: str,
        format: str | CompositionFormat = CompositionFormat.CANONICAL,
    ) -> CompositionResponse:
        """Get a composition as it existed at a specific point in time.

        Args:
            ehr_id: The EHR ID.
            versioned_object_uid: The composition's UUID.
            version_at_time: ISO 8601 timestamp.
            format: Desired response format.

        Returns:
            CompositionResponse with the composition at that time.
        """
        headers, format_params = self._composition_read_request(self._format_value(format))
        params: dict[str, str] = {"version_at_time": version_at_time, **format_params}

        response = await self.client.get(
            f"/rest/openehr/v1/ehr/{ehr_id}/composition/{versioned_object_uid}",
            params=params,
            headers=headers or None,
        )

        data = self._handle_response(response)
        return CompositionResponse.from_response(data, ehr_id)

    async def get_versioned_composition(
        self,
        ehr_id: str,
        versioned_object_uid: str,
    ) -> VersionedCompositionResponse:
        """Get versioned composition metadata.

        Args:
            ehr_id: The EHR ID.
            versioned_object_uid: The composition's UUID.

        Returns:
            VersionedCompositionResponse with metadata (UID, owner ID, time created).
        """
        response = await self.client.get(
            f"/rest/openehr/v1/ehr/{ehr_id}/versioned_composition/{versioned_object_uid}",
        )

        data = self._handle_response(response)
        return VersionedCompositionResponse.from_response(data)

    async def get_composition_version(
        self,
        ehr_id: str,
        versioned_object_uid: str,
        version_uid: str,
    ) -> CompositionVersionResponse:
        """Get a specific version of a composition.

        Args:
            ehr_id: The EHR ID.
            versioned_object_uid: The composition's UUID.
            version_uid: The specific version UID (e.g. ``uuid::domain::1``).

        Returns:
            CompositionVersionResponse with full version and audit metadata.
        """
        response = await self.client.get(
            f"/rest/openehr/v1/ehr/{ehr_id}/versioned_composition/{versioned_object_uid}/version/{version_uid}",
        )

        data = self._handle_response(response)
        return CompositionVersionResponse.from_response(data)

    async def list_composition_versions(
        self,
        ehr_id: str,
        versioned_object_uid: str,
    ) -> list[CompositionVersionResponse]:
        """List all versions of a composition.

        Args:
            ehr_id: The EHR ID.
            versioned_object_uid: The composition's UUID.

        Returns:
            List of CompositionVersionResponse with version descriptors.
        """
        response = await self.client.get(
            f"/rest/openehr/v1/ehr/{ehr_id}/versioned_composition/{versioned_object_uid}/version",
        )

        data = self._handle_response(response)
        if isinstance(data, list):
            return [CompositionVersionResponse.from_response(v) for v in data]
        # Some servers return the list under a key
        versions = data.get("versions", data.get("items", []))
        if isinstance(versions, list):
            return [CompositionVersionResponse.from_response(v) for v in versions]
        return []

    # Contribution Operations

    async def create_contribution(
        self,
        ehr_id: str,
        contribution: dict[str, Any],
    ) -> ContributionResponse:
        """Commit a contribution (atomic changeset of one or more versions).

        A contribution groups one or more versioned-object changes
        (compositions) into a single atomic commit with shared audit metadata.
        Build the request body with :class:`~oehrpy.client.ContributionBuilder`.

        Args:
            ehr_id: The EHR ID.
            contribution: CANONICAL contribution body (e.g. from
                ``ContributionBuilder.build()``).

        Returns:
            ContributionResponse with the contribution UID and referenced
            version UIDs.

        Raises:
            ValidationError: If the contribution is rejected by the server (422).
            NotFoundError: If the EHR does not exist (404).
            PreconditionFailedError: If an amendment's preceding version UID does
                not match the latest version (412).
        """
        headers = {
            "Prefer": "return=representation",
            "Content-Type": "application/json",
        }

        response = await self.client.post(
            f"/rest/openehr/v1/ehr/{ehr_id}/contribution",
            json=contribution,
            headers=headers,
        )

        data = self._handle_response(response)
        return ContributionResponse.from_response(data, ehr_id)

    async def get_contribution(
        self,
        ehr_id: str,
        contribution_uid: str,
    ) -> ContributionResponse:
        """Retrieve a contribution by UID.

        Args:
            ehr_id: The EHR ID.
            contribution_uid: The contribution UID.

        Returns:
            ContributionResponse with audit metadata and referenced version UIDs.

        Raises:
            NotFoundError: If the contribution does not exist (404).
        """
        response = await self.client.get(
            f"/rest/openehr/v1/ehr/{ehr_id}/contribution/{contribution_uid}",
        )

        data = self._handle_response(response)
        return ContributionResponse.from_response(data, ehr_id)

    # DIRECTORY Operations

    async def get_directory(
        self,
        ehr_id: str,
        *,
        version_uid: str | None = None,
        version_at_time: str | None = None,
        path: str | None = None,
    ) -> dict[str, Any]:
        """Get the EHR's DIRECTORY (root FOLDER).

        Args:
            ehr_id: The EHR ID.
            version_uid: A specific version; latest if omitted.
            version_at_time: ISO 8601 timestamp (ignored with ``version_uid``).
            path: Sub-folder path, e.g. ``episodes/a``.

        Returns:
            The canonical FOLDER, or an empty dict if the EHR has none (204).
        """
        url = f"/rest/openehr/v1/ehr/{ehr_id}/directory"
        params: dict[str, str] = {}
        if version_uid:
            url = f"{url}/{version_uid}"
        elif version_at_time:
            params["version_at_time"] = version_at_time
        if path:
            params["path"] = path
        response = await self.client.get(url, params=params if params else None)
        return self._handle_response(response)

    async def create_directory(self, ehr_id: str, folder: dict[str, Any]) -> dict[str, Any]:
        """Create the EHR's DIRECTORY from a canonical FOLDER."""
        response = await self.client.post(
            f"/rest/openehr/v1/ehr/{ehr_id}/directory",
            json=folder,
            headers={"Prefer": "return=representation"},
        )
        return self._handle_response(response)

    async def update_directory(
        self,
        ehr_id: str,
        preceding_version_uid: str,
        folder: dict[str, Any],
    ) -> dict[str, Any]:
        """Replace the EHR's DIRECTORY (``If-Match: preceding_version_uid``)."""
        response = await self.client.put(
            f"/rest/openehr/v1/ehr/{ehr_id}/directory",
            json=folder,
            headers={
                "Prefer": "return=representation",
                "If-Match": self._if_match(preceding_version_uid),
            },
        )
        return self._handle_response(response)

    async def delete_directory(self, ehr_id: str, preceding_version_uid: str) -> None:
        """Logically delete the EHR's DIRECTORY."""
        response = await self.client.delete(
            f"/rest/openehr/v1/ehr/{ehr_id}/directory",
            headers={"If-Match": self._if_match(preceding_version_uid)},
        )
        self._handle_response(response)

    # Query Operations

    async def query(
        self,
        aql: str,
        query_parameters: dict[str, Any] | None = None,
        ehr_id: str | None = None,
    ) -> QueryResponse:
        """Execute an AQL query.

        Args:
            aql: The AQL query string.
            query_parameters: Optional query parameters.
            ehr_id: Optional EHR ID to scope the query.

        Returns:
            QueryResponse with query results.
        """
        body: dict[str, Any] = {"q": aql}
        if query_parameters:
            body["query_parameters"] = query_parameters

        params = {}
        if ehr_id:
            params["ehr_id"] = ehr_id

        response = await self.client.post(
            "/rest/openehr/v1/query/aql",
            json=body,
            params=params if params else None,
        )

        data = self._handle_response(response)
        return QueryResponse.from_response(data)

    async def query_get(
        self,
        aql: str,
        ehr_id: str | None = None,
        offset: int | None = None,
        fetch: int | None = None,
    ) -> QueryResponse:
        """Execute an AQL query via GET.

        Args:
            aql: The AQL query string.
            ehr_id: Optional EHR ID to scope the query.
            offset: Result offset for pagination.
            fetch: Number of results to fetch.

        Returns:
            QueryResponse with query results.
        """
        params: dict[str, Any] = {"q": aql}
        if ehr_id:
            params["ehr_id"] = ehr_id
        if offset is not None:
            params["offset"] = offset
        if fetch is not None:
            params["fetch"] = fetch

        response = await self.client.get(
            "/rest/openehr/v1/query/aql",
            params=params,
        )

        data = self._handle_response(response)
        return QueryResponse.from_response(data)

    # Stored Query Operations

    @staticmethod
    def _stored_query_path(qualified_query_name: str, version: str | None) -> str:
        return f"{qualified_query_name}/{version}" if version else qualified_query_name

    async def list_stored_queries(
        self, qualified_query_name: str | None = None
    ) -> list[StoredQueryResponse]:
        """List STORED_QUERY definitions, optionally filtered by name.

        The returned definitions carry metadata only; use
        :meth:`get_stored_query` for the AQL text.
        """
        url = "/rest/openehr/v1/definition/query"
        if qualified_query_name:
            url = f"{url}/{qualified_query_name}"
        response = await self.client.get(url)
        data: Any = self._handle_response(response)
        items = data if isinstance(data, list) else data.get("queries", [])
        return [StoredQueryResponse.from_response(item) for item in items]

    async def get_stored_query(
        self, qualified_query_name: str, version: str | None = None
    ) -> StoredQueryResponse:
        """Get a stored query definition (latest version if ``version`` is omitted)."""
        response = await self.client.get(
            "/rest/openehr/v1/definition/query/"
            + self._stored_query_path(qualified_query_name, version)
        )
        data: Any = self._handle_response(response)
        if isinstance(data, list):
            data = data[0] if data else {}
        result = StoredQueryResponse.from_response(data)
        result.name = result.name or qualified_query_name
        return result

    async def store_query(
        self,
        qualified_query_name: str,
        aql: str,
        version: str | None = None,
        *,
        query_type: str = "AQL",
    ) -> None:
        """Register (or replace) a stored query.

        Args:
            qualified_query_name: e.g. ``org.example::vital_signs``.
            aql: The query text.
            version: SEMVER version; the server assigns one if omitted.
            query_type: Query language (default ``AQL``).
        """
        response = await self.client.put(
            "/rest/openehr/v1/definition/query/"
            + self._stored_query_path(qualified_query_name, version),
            content=aql,
            params={"query_type": query_type},
            headers={"Content-Type": "text/plain"},
        )
        self._handle_response(response)

    async def execute_stored_query(
        self,
        qualified_query_name: str,
        version: str | None = None,
        *,
        query_parameters: dict[str, Any] | None = None,
        ehr_id: str | None = None,
        offset: int | None = None,
        fetch: int | None = None,
    ) -> QueryResponse:
        """Execute a stored query by name (and optionally version)."""
        body: dict[str, Any] = {}
        if query_parameters:
            body["query_parameters"] = query_parameters
        if ehr_id:
            body["ehr_id"] = ehr_id
        if offset is not None:
            body["offset"] = offset
        if fetch is not None:
            body["fetch"] = fetch
        response = await self.client.post(
            "/rest/openehr/v1/query/" + self._stored_query_path(qualified_query_name, version),
            json=body,
        )
        return QueryResponse.from_response(self._handle_response(response))

    async def delete_stored_query(self, qualified_query_name: str, version: str) -> None:
        """Physically delete a stored query version via the vendor admin API.

        ITS-REST defines no DELETE for stored queries, so this is only
        available on vendor clients and uses the admin credentials.

        Raises:
            UnsupportedOperationError: On the generic client.
            AuthorizationError: If the credentials lack the admin role (403).
        """
        response = await self.client.delete(
            self._admin_url(f"query/{qualified_query_name}/{version}"),
            auth=self._admin_auth(),
        )
        self._handle_response(response)

    # Template Operations

    async def list_templates(self, *, all_versions: bool = True) -> list[TemplateResponse]:
        """List available templates.

        Args:
            all_versions: List every stored version of each template. ITS-REST
                servers that implement the ``version`` filter (e.g. FerroEHR)
                otherwise collapse the list to the latest version per template,
                while EHRBase always lists all of them. Pass False for the
                server's default.

        Returns:
            List of TemplateResponse objects.
        """
        params = (
            {"version": "*"} if all_versions and self.supports_template_version_filter else None
        )
        response = await self.client.get(
            "/rest/openehr/v1/definition/template/adl1.4",
            params=params,
        )
        data = self._handle_response(response)

        if isinstance(data, list):
            return [TemplateResponse.from_response(t) for t in data]
        return []

    async def get_template(self, template_id: str) -> dict[str, Any]:
        """Get a template definition.

        Args:
            template_id: The template ID.

        Returns:
            Template definition as dictionary.
        """
        response = await self.client.get(
            f"/rest/openehr/v1/definition/template/adl1.4/{template_id}"
        )
        return self._handle_response(response)

    async def get_web_template(
        self,
        template_id: str,
        *,
        use_cache: bool = True,
    ) -> dict[str, Any]:
        """Fetch the Web Template JSON for a given template.

        The Web Template is the sole authoritative source for FLAT path
        derivation (see ADR-0005). Results are cached in memory for the
        lifetime of the client instance.

        Args:
            template_id: The template ID.
            use_cache: If True (default), return a cached copy when available.
                Pass False to force a fresh fetch from the CDR.

        Returns:
            Web Template JSON dict (contains a ``tree`` key).
        """
        if use_cache and template_id in self._web_template_cache:
            return self._web_template_cache[template_id]

        response = await self.client.get(
            f"/rest/openehr/v1/definition/template/adl1.4/{template_id}",
            headers={"Accept": "application/openehr.wt+json"},
        )
        wt: dict[str, Any] = self._handle_response(response)
        self._web_template_cache[template_id] = wt
        return wt

    def clear_web_template_cache(self, template_id: str | None = None) -> None:
        """Clear cached Web Templates.

        Args:
            template_id: If given, only clear the cache for this template.
                If None, clear the entire cache.
        """
        if template_id is not None:
            self._web_template_cache.pop(template_id, None)
        else:
            self._web_template_cache.clear()

    async def get_template_example(
        self,
        template_id: str,
        *,
        detail_level: str | ExampleDetailLevel = ExampleDetailLevel.MEDIUM,
        example_type: str | ExampleType = ExampleType.INPUT,
        format: str | CompositionFormat = CompositionFormat.FLAT,
    ) -> dict[str, Any]:
        """Generate an example composition for a template.

        Calls ``GET /definition/template/adl1.4/{template_id}/example`` as
        specified by ITS-REST 1.1.0: ``detail_level`` and ``type`` are sent
        as query parameters and the format is negotiated via ``Accept``.

        Detail levels:

        - ``required``: only mandatory data points; committable as-is.
        - ``medium``: a realistic set including some optional elements;
          intended to be committable.
        - ``complete``: every possible data point; reference material only,
          not expected to be committable.

        The spec default is ``required``, which spec-conformant CDRs (e.g.
        FerroEHR) honour with a very sparse example. This method defaults to
        ``medium`` so results are useful and comparable across CDRs.

        Vendors may produce different examples, and a server that does not
        support the requested level may fall back to the closest one or
        return 400 (raised as :class:`ValidationError`). EHRBase 2.x ignores
        ``detail_level`` and ``type`` entirely and only accepts its own FLAT
        and STRUCTURED media types (``application/openehr.wt.flat.schema+json``);
        when the spec media type is rejected with 406, the request is retried
        once with EHRBase's media type and ``format`` query parameter, and
        that choice is remembered per format for the lifetime of the client.

        Args:
            template_id: The template ID.
            detail_level: ``required``, ``medium`` (default) or ``complete``.
            example_type: ``input`` (default, ready to commit) or ``output``
                (as the CDR would return it).
            format: Composition format of the example (default FLAT).

        Returns:
            The example composition as a dictionary.
        """
        level = ExampleDetailLevel(detail_level)
        kind = ExampleType(example_type)
        fmt = CompositionFormat(format.value if isinstance(format, CompositionFormat) else format)

        path = f"/rest/openehr/v1/definition/template/adl1.4/{template_id}/example"
        params = {"type": kind.value, "detail_level": level.value}

        ehrbase_media_type = _EHRBASE_EXAMPLE_MEDIA_TYPES.get(fmt)

        if ehrbase_media_type is None or fmt not in self._example_ehrbase_formats:
            response = await self.client.get(
                path,
                params=params,
                headers={"Accept": _EXAMPLE_MEDIA_TYPES[fmt]},
            )
            if response.status_code != 406 or ehrbase_media_type is None:
                return self._handle_response(response)

        response = await self.client.get(
            path,
            params={**params, "format": fmt.value},
            headers={"Accept": ehrbase_media_type},
        )
        data = self._handle_response(response)
        self._example_ehrbase_formats.add(fmt)
        return data

    async def upload_template(self, template_xml: str) -> TemplateResponse:
        """Upload a new template.

        Args:
            template_xml: The OPT XML content.

        Returns:
            TemplateResponse with template details.
        """
        response = await self.client.post(
            "/rest/openehr/v1/definition/template/adl1.4",
            content=template_xml,
            headers={
                "Content-Type": "application/xml",
                "Accept": "*/*",
            },
        )

        # EHRBase 2.0.0 returns 201 Created with no body on successful upload
        if response.status_code == 201 or response.status_code == 204:
            # Extract template_id from request XML
            try:
                root = ET.fromstring(template_xml)
                # Template ID is in <template_id><value>...</value></template_id>
                template_id_elem = root.find(_OPT_TEMPLATE_ID_PATH)
                if template_id_elem is None:
                    # Try without namespace
                    template_id_elem = root.find(".//template_id/value")

                template_id = ""
                if template_id_elem is not None and template_id_elem.text:
                    template_id = template_id_elem.text

                if not template_id:
                    raise ValidationError(
                        "Template uploaded but could not extract template_id from XML",
                        status_code=response.status_code,
                    )

                return TemplateResponse(template_id=template_id)
            except ET.ParseError as e:
                raise ValidationError(
                    f"Template uploaded but XML parsing failed: {e}",
                    status_code=response.status_code,
                ) from e

        data = self._handle_response(response)
        return TemplateResponse.from_response(data)

    async def get_template_opt(self, template_id: str) -> str:
        """Download the raw OPT 1.4 XML for a template.

        Uses the standard openEHR REST endpoint with ``Accept: application/xml``.

        Args:
            template_id: The template ID.

        Returns:
            The OPT XML content as a string.

        Raises:
            NotFoundError: If the template does not exist.
        """
        response = await self.client.get(
            f"/rest/openehr/v1/definition/template/adl1.4/{template_id}",
            headers={"Accept": "application/xml"},
        )

        if response.status_code == 404:
            raise NotFoundError(
                f"Template not found: {template_id}",
                status_code=404,
            )
        if response.status_code >= 400:
            self._handle_response(response)

        return response.text

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
        # Validate that the XML's embedded template ID matches the argument
        # to prevent deleting template A and uploading template B.
        try:
            root = ET.fromstring(template_xml)
            xml_tid_elem = root.find(_OPT_TEMPLATE_ID_PATH)
            if xml_tid_elem is None:
                xml_tid_elem = root.find(".//template_id/value")
            if xml_tid_elem is not None and xml_tid_elem.text and xml_tid_elem.text != template_id:
                raise ValidationError(
                    f"Template ID mismatch: argument is '{template_id}' "
                    f"but the XML contains '{xml_tid_elem.text}'",
                )
        except ET.ParseError as e:
            raise ValidationError(
                f"Could not parse template XML: {e}",
            ) from e

        # Try standard PUT first (future-proofing)
        response = await self.client.put(
            f"/rest/openehr/v1/definition/template/adl1.4/{template_id}",
            content=template_xml,
            headers={
                "Content-Type": "application/xml",
                "Accept": "*/*",
            },
        )

        if response.status_code in (200, 204):
            self.clear_web_template_cache(template_id)
            if response.status_code == 204:
                return TemplateResponse(template_id=template_id)
            data = self._handle_response(response)
            return TemplateResponse.from_response(data)

        # PUT not supported — fall back to delete + re-upload
        if response.status_code in (405, 501):
            # Delete the existing template (may raise NotFoundError or ValidationError)
            await self.delete_template(template_id)

            # Re-upload
            try:
                result = await self.upload_template(template_xml)
                self.clear_web_template_cache(template_id)
                return result
            except (ValidationError, OpenEHRError) as upload_err:
                raise ValidationError(
                    f"Template update failed: old template was deleted but new "
                    f"template could not be uploaded ({upload_err}). Re-upload "
                    f"the template manually to restore it.",
                    status_code=getattr(upload_err, "status_code", None),
                ) from upload_err

        # Any other error — let _handle_response raise the appropriate exception
        self._handle_response(response)
        # Should not reach here, but satisfy type checker
        return TemplateResponse(template_id=template_id)  # pragma: no cover

    async def delete_template(
        self,
        template_id: str,
        *,
        permanent: bool = False,
    ) -> None:
        """Delete a template from the CDR.

        Tries the standard ``DELETE /definition/template/adl1.4/{id}``. Many
        CDRs answer 405 there; when admin credentials are configured and the
        vendor has an admin API, the client falls back to
        ``{admin API}/template/{id}``.

        Args:
            template_id: The template ID to delete.
            permanent: Only meaningful for Better (see
                :meth:`EHRBaseClient.delete_template`).

        Raises:
            NotFoundError: If the template does not exist.
            ValidationError: If the template cannot be deleted because
                compositions reference it (HTTP 409).
            OpenEHRError: If the server does not support template deletion
                and no admin credentials are configured.
        """
        response = await self.client.delete(
            f"/rest/openehr/v1/definition/template/adl1.4/{template_id}",
        )

        # Fall back to the admin API when admin credentials are available.
        if response.status_code == 405 and self.admin_prefix and self.config.admin_auth:
            response = await self.client.delete(
                self._admin_url(f"template/{template_id}"),
                auth=self._admin_auth(),
            )

        if response.status_code in (200, 204):
            self.clear_web_template_cache(template_id)
            return

        self._handle_response(response)

    # Health Check

    async def health_check(self) -> bool:
        """Check if the server is healthy.

        Returns:
            True if server is healthy.
        """
        try:
            response = await self.client.get("/rest/status")
            return response.status_code == 200
        except Exception:
            return False
