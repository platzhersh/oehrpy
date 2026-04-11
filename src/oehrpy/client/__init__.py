"""
REST client for EHRBase and openEHR CDR servers.

This module provides async HTTP clients for interacting with
openEHR Clinical Data Repositories.
"""

from .ehrbase import (
    AuthenticationError,
    CDRType,
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
    TemplateResponse,
    ValidationError,
    VersionedCompositionResponse,
)

__all__ = [
    "CDRType",
    "EHRBaseClient",
    "EHRBaseConfig",
    "EHRResponse",
    "CompositionResponse",
    "CompositionFormat",
    "CompositionVersionResponse",
    "QueryResponse",
    "TemplateResponse",
    "VersionedCompositionResponse",
    "EHRBaseError",
    "AuthenticationError",
    "NotFoundError",
    "PreconditionFailedError",
    "ValidationError",
]
