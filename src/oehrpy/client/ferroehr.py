"""
FerroEHR REST client implementation.

FerroEHR (https://github.com/rubentalstra/FerroEHR) follows ITS-REST 1.1.0
closely, so :class:`FerroEHRClient` mostly uses the spec behaviour of
:class:`~oehrpy.client.OpenEHRClient`. The FerroEHR specifics it adds:

- default base URL ``http://localhost:8080/ferroehr``
- ``GET {base}/rest/status`` is unauthenticated and returns JSON, so
  :meth:`~OpenEHRClient.get_server_info` works even with bad credentials
- EHR creation always sends an EHR_STATUS with ``archetype_details``
  (mandatory on FerroEHR, 422 otherwise)
- the admin API (physical EHR, template and stored-query deletion) lives
  under ``{base}/rest/openehr/v1/admin`` and needs the ``ADMIN`` role
- the template list collapses to the latest version per template unless
  ``version=*`` is passed; :meth:`~OpenEHRClient.list_templates` sends it

Known server issue: FerroEHR's FLAT ``GET`` drops nested HISTORY item-tree
content (OEH-50). oehrpy does not work around it; read compositions in
CANONICAL format if you need the full content.

Example:
    >>> async with FerroEHRClient(username="ferroehr", password="ferroehr") as client:
    ...     info = await client.get_server_info()
    ...     ehr = await client.create_ehr()
"""

from __future__ import annotations

from dataclasses import dataclass

from .openehr import OpenEHRClient, OpenEHRConfig, ServerType


@dataclass
class FerroEHRConfig(OpenEHRConfig):
    """Configuration for :class:`FerroEHRClient`."""

    base_url: str = "http://localhost:8080/ferroehr"


class FerroEHRClient(OpenEHRClient):
    """Async HTTP client for FerroEHR.

    Supports HTTP Basic (``username``/``password``) and OIDC bearer tokens
    (``auth_method=BearerAuth(...)``). Admin operations use
    ``admin_username``/``admin_password`` or ``admin_auth_method`` when set,
    and otherwise the regular credentials, which then need the ``ADMIN`` role.

    Example:
        >>> from oehrpy.client import BearerAuth
        >>> async with FerroEHRClient(
        ...     base_url="https://cdr.example.org/ferroehr",
        ...     auth_method=BearerAuth(token_provider=get_access_token),
        ... ) as client:
        ...     ehr = await client.create_ehr()
    """

    server_type = ServerType.FERROEHR
    config_class = FerroEHRConfig
    admin_prefix = "/rest/openehr/v1/admin"
    status_requires_auth = False
    supports_template_version_filter = True
    always_send_ehr_status = True
