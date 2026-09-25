"""
Client factory: pick the right adapter for a CDR from configuration.

Example:
    >>> client = create_client("ferroehr", base_url=os.environ["CDR_URL"],
    ...                        username="ferroehr", password="ferroehr")
    >>> async with client:
    ...     ehr = await client.create_ehr()
"""

from __future__ import annotations

from typing import Any

import httpx

from .auth import AuthMethod
from .ehrbase import EHRBaseClient
from .ferroehr import FerroEHRClient
from .openehr import OpenEHRClient, ServerInfo, ServerType

_CLIENTS: dict[ServerType, type[OpenEHRClient]] = {
    ServerType.EHRBASE: EHRBaseClient,
    ServerType.FERROEHR: FerroEHRClient,
    ServerType.GENERIC: OpenEHRClient,
}


def create_client(
    server_type: str | ServerType = ServerType.EHRBASE,
    base_url: str | None = None,
    **kwargs: Any,
) -> OpenEHRClient:
    """Create a client for the given CDR vendor.

    Args:
        server_type: ``"ehrbase"`` (default), ``"ferroehr"`` or ``"generic"``.
        base_url: CDR base URL; the vendor's local default if omitted.
        **kwargs: Passed to the vendor's config class (``username``,
            ``password``, ``auth_method``, ``admin_auth_method``, ...), or
            ``config=`` with a ready-made config object.

    Returns:
        An unconnected client; use it with ``async with``.
    """
    try:
        client_class = _CLIENTS[ServerType(server_type)]
    except ValueError:
        valid = ", ".join(t.value for t in ServerType)
        raise ValueError(f"Unknown server_type {server_type!r}; expected one of: {valid}") from None
    return client_class(base_url=base_url, **kwargs)


async def detect_server_type(
    base_url: str,
    *,
    auth: AuthMethod = None,
    timeout: float = 10.0,
    verify_ssl: bool = True,
) -> ServerInfo:
    """Probe ``GET {base_url}/rest/status`` to identify the CDR vendor.

    FerroEHR answers unauthenticated with JSON; EHRBase answers with its
    ``ehrbase_version`` document and may require credentials, so the probe is
    retried with ``auth`` after a 401. Anything else is reported as generic.

    Returns:
        ServerInfo whose ``server_type`` can be passed to :func:`create_client`.
    """
    async with httpx.AsyncClient(base_url=base_url, timeout=timeout, verify=verify_ssl) as http:
        headers = {"Accept": "application/json, application/xml;q=0.9"}
        response = await http.get("/rest/status", headers=headers)
        if response.status_code == 401 and auth is not None:
            response = await http.get("/rest/status", headers=headers, auth=auth)
    if response.status_code != 200:
        return ServerInfo(server_type=ServerType.GENERIC)
    return ServerInfo.from_status_body(response.text)
