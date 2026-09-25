"""
EHRBase REST client implementation.

:class:`EHRBaseClient` is a thin adapter over the vendor-neutral
:class:`~oehrpy.client.OpenEHRClient` that keeps EHRBase's deviations from
ITS-REST: composition formats selected via the ``format`` query parameter,
the ``.schema`` FLAT media types, unquoted ``If-Match`` values and the admin
API mounted at ``{base}/rest/admin``. See ADR-0011.

All names historically importable from this module are re-exported here.

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

from dataclasses import dataclass
from enum import Enum

from .openehr import (
    _EHRBASE_EXAMPLE_MEDIA_TYPES,
    _EXAMPLE_MEDIA_TYPES,
    AuthenticationError,
    AuthorizationError,
    CompositionFormat,
    CompositionResponse,
    CompositionVersionResponse,
    ContributionResponse,
    EHRBaseError,
    EHRResponse,
    ExampleDetailLevel,
    ExampleType,
    NotFoundError,
    OpenEHRClient,
    OpenEHRConfig,
    OpenEHRError,
    PreconditionFailedError,
    QueryResponse,
    ServerType,
    TemplateResponse,
    ValidationError,
    VersionedCompositionResponse,
)

__all__ = [
    "AuthenticationError",
    "AuthorizationError",
    "CDRType",
    "CompositionFormat",
    "CompositionResponse",
    "CompositionVersionResponse",
    "ContributionResponse",
    "EHRBaseClient",
    "EHRBaseConfig",
    "EHRBaseError",
    "EHRResponse",
    "ExampleDetailLevel",
    "ExampleType",
    "NotFoundError",
    "OpenEHRError",
    "PreconditionFailedError",
    "QueryResponse",
    "TemplateResponse",
    "ValidationError",
    "VersionedCompositionResponse",
    "_EHRBASE_EXAMPLE_MEDIA_TYPES",
    "_EXAMPLE_MEDIA_TYPES",
]


class CDRType(str, Enum):
    """CDR flavours served by :class:`EHRBaseClient`."""

    EHRBASE = "ehrbase"
    BETTER = "better"


@dataclass
class EHRBaseConfig(OpenEHRConfig):
    """Configuration for EHRBase client."""

    base_url: str = "http://localhost:8080/ehrbase"
    cdr_type: CDRType = CDRType.EHRBASE


class EHRBaseClient(OpenEHRClient):
    """Async HTTP client for EHRBase.

    This client implements the openEHR REST API for EHRBase CDR.

    Web Templates fetched via :meth:`get_web_template` are cached in memory
    for the lifetime of the client instance to avoid repeated CDR round-trips
    (see ADR-0005).

    Example:
        >>> config = EHRBaseConfig(
        ...     base_url="http://localhost:8080/ehrbase",
        ...     username="admin",
        ...     password="admin",
        ... )
        >>> async with EHRBaseClient(config=config) as client:
        ...     ehr = await client.create_ehr()
    """

    server_type = ServerType.EHRBASE
    config_class = EHRBaseConfig
    admin_prefix = "/rest/admin"

    config: EHRBaseConfig

    def __init__(
        self,
        base_url: str | None = None,
        config: EHRBaseConfig | None = None,
        **kwargs: object,
    ):
        """Initialize the client.

        Args:
            base_url: EHRBase server URL (shortcut for config.base_url).
            config: Full configuration object.
            **kwargs: Additional arguments passed to EHRBaseConfig.
        """
        super().__init__(base_url=base_url, config=config, **kwargs)

    def _if_match(self, version_uid: str) -> str:
        # EHRBase accepts the bare version UID
        return version_uid

    def _composition_write_request(
        self, format: str | None, template_id: str | None
    ) -> tuple[dict[str, str], dict[str, str]]:
        # EHRBase selects the format via the ``format`` query parameter
        headers = {
            "Prefer": "return=representation",
            "Content-Type": "application/json",
        }
        params: dict[str, str] = {}
        if template_id:
            params["templateId"] = template_id
        if format:
            params["format"] = format
        return headers, params

    def _composition_read_request(
        self, format: str | None
    ) -> tuple[dict[str, str], dict[str, str]]:
        return {}, ({"format": format} if format else {})

    async def delete_template(
        self,
        template_id: str,
        *,
        permanent: bool = False,
    ) -> None:
        """Delete a template from the CDR.

        On EHRBase 2.x the standard openEHR REST endpoint does not
        support ``DELETE`` (returns 405).  When admin credentials are
        configured the client automatically falls back to the EHRBase
        admin API (``/rest/admin/template/{id}``).

        On Better, the default behavior retires the template
        (soft-delete, reversible via the Admin API's unretire
        endpoint). Pass ``permanent=True`` to permanently delete
        via the Admin API (requires admin credentials). Note: the
        Admin API permanently deletes **all active and inactive**
        versions of the template.

        Args:
            template_id: The template ID to delete.
            permanent: If True, permanently delete on Better
                (uses Admin API). Ignored on EHRBase.

        Raises:
            NotFoundError: If the template does not exist.
            ValidationError: If the template cannot be deleted because
                compositions reference it (HTTP 409, EHRBase).
            EHRBaseError: If the server does not support template deletion
                and no admin credentials are configured.
        """
        if getattr(self.config, "cdr_type", CDRType.EHRBASE) != CDRType.BETTER:
            await super().delete_template(template_id)
            return

        if permanent:
            response = await self.client.delete(
                f"/admin/rest/v1/templates/{template_id}",
                auth=self._admin_auth(),
            )
        else:
            response = await self.client.delete(
                f"/rest/v1/template/{template_id}",
            )

        # Better EHR Server API returns 200 with {"action": "DELETE"}
        # Better Admin API returns 204
        if response.status_code in (200, 204):
            self.clear_web_template_cache(template_id)
            return

        self._handle_response(response)
