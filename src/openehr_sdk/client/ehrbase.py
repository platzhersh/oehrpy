"""
EHRBase REST client implementation.

This module provides an async HTTP client for EHRBase, implementing
the openEHR REST API specification.

Example:
    >>> async with EHRBaseClient(base_url="http://localhost:8080/ehrbase") as client:
    ...     # Create an EHR
    ...     ehr = await client.create_ehr()
    ...     print(f"Created EHR: {ehr.ehr_id}")
    ...
    ...     # Create a composition
    ...     composition = await client.create_composition(
    ...         ehr_id=ehr.ehr_id,
    ...         template_id="IDCR - Vital Signs Encounter.v1",
    ...         composition=flat_data,
    ...         format="FLAT",
    ...     )
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import httpx
from defusedxml import ElementTree as ET


class CompositionFormat(str, Enum):
    """Supported composition formats."""

    CANONICAL = "CANONICAL"
    FLAT = "FLAT"
    STRUCTURED = "STRUCTURED"


# Custom Exceptions


class EHRBaseError(Exception):
    """Base exception for EHRBase client errors."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class AuthenticationError(EHRBaseError):
    """Authentication failed."""

    pass


class NotFoundError(EHRBaseError):
    """Resource not found."""

    pass


class ValidationError(EHRBaseError):
    """Validation error from server."""

    pass


class PreconditionFailedError(EHRBaseError):
    """Version conflict — the If-Match header did not match (HTTP 412)."""

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
class TemplateResponse:
    """Response from template operations."""

    template_id: str
    concept: str | None = None
    archetype_id: str | None = None

    @classmethod
    def from_response(cls, data: dict[str, Any]) -> TemplateResponse:
        """Create from API response."""
        return cls(
            template_id=data.get("template_id", ""),
            concept=data.get("concept"),
            archetype_id=data.get("archetype_id"),
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
class EHRBaseConfig:
    """Configuration for EHRBase client."""

    base_url: str = "http://localhost:8080/ehrbase"
    username: str | None = None
    password: str | None = None
    timeout: float = 30.0
    verify_ssl: bool = True

    @property
    def auth(self) -> tuple[str, str] | None:
        """Get auth tuple if credentials are provided."""
        if self.username and self.password:
            return (self.username, self.password)
        return None


class EHRBaseClient:
    """Async HTTP client for EHRBase.

    This client implements the openEHR REST API for EHRBase CDR.

    Example:
        >>> config = EHRBaseConfig(
        ...     base_url="http://localhost:8080/ehrbase",
        ...     username="admin",
        ...     password="admin",
        ... )
        >>> async with EHRBaseClient(config=config) as client:
        ...     ehr = await client.create_ehr()
    """

    def __init__(
        self,
        base_url: str | None = None,
        config: EHRBaseConfig | None = None,
        **kwargs: Any,
    ):
        """Initialize the client.

        Args:
            base_url: EHRBase server URL (shortcut for config.base_url).
            config: Full configuration object.
            **kwargs: Additional arguments passed to EHRBaseConfig.
        """
        if config:
            self.config = config
        else:
            self.config = EHRBaseConfig(
                base_url=base_url or "http://localhost:8080/ehrbase",
                **kwargs,
            )
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> EHRBaseClient:
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
            raise EHRBaseError(
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
        if ehr_id:
            response = await self.client.put(
                f"/rest/openehr/v1/ehr/{ehr_id}",
                headers=headers,
            )
        else:
            body = None
            if subject_id and subject_namespace:
                body = {
                    "_type": "EHR_STATUS",
                    "archetype_node_id": "openEHR-EHR-EHR_STATUS.generic.v1",
                    "name": {"value": "EHR Status"},
                    "subject": {
                        "external_ref": {
                            "id": {
                                "_type": "GENERIC_ID",
                                "value": subject_id,
                                "scheme": "id_scheme",
                            },
                            "namespace": subject_namespace,
                            "type": "PERSON",
                        }
                    },
                    "is_modifiable": True,
                    "is_queryable": True,
                }
            response = await self.client.post(
                "/rest/openehr/v1/ehr",
                headers=headers,
                json=body,
            )

        data = self._handle_response(response)
        return EHRResponse.from_response(data)

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
        format_str = format.value if isinstance(format, CompositionFormat) else format

        headers = {
            "Prefer": "return=representation",
            "Content-Type": "application/json",
        }

        params = {}
        if template_id:
            params["templateId"] = template_id
        if format_str:
            params["format"] = format_str

        response = await self.client.post(
            f"/rest/openehr/v1/ehr/{ehr_id}/composition",
            json=composition,
            headers=headers,
            params=params if params else None,
        )

        data = self._handle_response(response)
        return CompositionResponse.from_response(data, ehr_id)

    async def get_composition(
        self,
        ehr_id: str,
        composition_uid: str,
        format: str | CompositionFormat = CompositionFormat.CANONICAL,
    ) -> CompositionResponse:
        """Get a composition by UID.

        Args:
            ehr_id: The EHR ID.
            composition_uid: The composition UID.
            format: Desired response format.

        Returns:
            CompositionResponse with composition data.
        """
        format_str = format.value if isinstance(format, CompositionFormat) else format

        # Extract versioned object UID (uuid::system::version -> uuid::system)
        uid_parts = composition_uid.split("::")
        versioned_object_uid = "::".join(uid_parts[:2]) if len(uid_parts) >= 2 else composition_uid

        params: dict[str, str] = {}
        if format_str:
            params["format"] = format_str

        response = await self.client.get(
            f"/rest/openehr/v1/ehr/{ehr_id}/composition/{versioned_object_uid}",
            params=params if params else None,
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
        format_str = format.value if isinstance(format, CompositionFormat) else format

        headers = {
            "Prefer": "return=representation",
            "Content-Type": "application/json",
            "If-Match": preceding_version_uid,
        }

        params = {}
        if template_id:
            params["templateId"] = template_id
        if format_str:
            params["format"] = format_str

        response = await self.client.put(
            f"/rest/openehr/v1/ehr/{ehr_id}/composition/{versioned_object_uid}",
            json=composition,
            headers=headers,
            params=params if params else None,
        )

        data = self._handle_response(response)
        return CompositionResponse.from_response(data, ehr_id)

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
        format_str = format.value if isinstance(format, CompositionFormat) else format

        params: dict[str, str] = {"version_at_time": version_at_time}
        if format_str:
            params["format"] = format_str

        response = await self.client.get(
            f"/rest/openehr/v1/ehr/{ehr_id}/composition/{versioned_object_uid}",
            params=params,
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

    # Template Operations

    async def list_templates(self) -> list[TemplateResponse]:
        """List all available templates.

        Returns:
            List of TemplateResponse objects.
        """
        response = await self.client.get("/rest/openehr/v1/definition/template/adl1.4")
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
                ns_path = ".//{http://schemas.openehr.org/v1}template_id/{http://schemas.openehr.org/v1}value"
                template_id_elem = root.find(ns_path)
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
