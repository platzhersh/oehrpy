"""
REST clients for openEHR CDR servers.

- :class:`OpenEHRClient` — vendor-neutral ITS-REST 1.1.0 client
- :class:`EHRBaseClient` — EHRBase adapter (the default)
- :class:`FerroEHRClient` — FerroEHR adapter
- :func:`create_client` — pick an adapter by ``server_type``
"""

from .auth import AuthMethod, BasicAuth, BearerAuth
from .contribution import ContributionBuilder
from .ehrbase import CDRType, EHRBaseClient, EHRBaseConfig
from .factory import create_client, detect_server_type
from .ferroehr import FerroEHRClient, FerroEHRConfig
from .openehr import (
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
    InsecureTransportWarning,
    NotFoundError,
    OpenEHRClient,
    OpenEHRConfig,
    OpenEHRError,
    PreconditionFailedError,
    QueryResponse,
    ServerInfo,
    ServerType,
    StoredQueryResponse,
    TemplateResponse,
    UnsupportedOperationError,
    ValidationError,
    VersionedCompositionResponse,
)

__all__ = [
    # Clients & configuration
    "OpenEHRClient",
    "OpenEHRConfig",
    "EHRBaseClient",
    "EHRBaseConfig",
    "FerroEHRClient",
    "FerroEHRConfig",
    "CDRType",
    "ServerType",
    "create_client",
    "detect_server_type",
    # Authentication
    "AuthMethod",
    "BasicAuth",
    "BearerAuth",
    # Requests & responses
    "EHRResponse",
    "CompositionResponse",
    "CompositionFormat",
    "CompositionVersionResponse",
    "ExampleDetailLevel",
    "ExampleType",
    "ContributionBuilder",
    "ContributionResponse",
    "QueryResponse",
    "ServerInfo",
    "StoredQueryResponse",
    "TemplateResponse",
    "VersionedCompositionResponse",
    # Errors
    "OpenEHRError",
    "EHRBaseError",
    "AuthenticationError",
    "AuthorizationError",
    "InsecureTransportWarning",
    "NotFoundError",
    "PreconditionFailedError",
    "UnsupportedOperationError",
    "ValidationError",
]
