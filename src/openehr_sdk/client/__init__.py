"""
REST client for EHRBase and openEHR CDR servers.

This module provides async HTTP clients for interacting with
openEHR Clinical Data Repositories.
"""

from .ehrbase import (
    AuthenticationError,
    CompositionFormat,
    CompositionResponse,
    CompositionVersionResponse,
    EHRBaseClient,
    EHRBaseConfig,
    EHRBaseError,
    EHRResponse,
    NotFoundError,
    PreconditionFailedError,
    QueryResponse,
    ValidationError,
    VersionedCompositionResponse,
)

__all__ = [
    "EHRBaseClient",
    "EHRBaseConfig",
    "EHRResponse",
    "CompositionResponse",
    "CompositionFormat",
    "CompositionVersionResponse",
    "QueryResponse",
    "VersionedCompositionResponse",
    "EHRBaseError",
    "AuthenticationError",
    "NotFoundError",
    "PreconditionFailedError",
    "ValidationError",
]
