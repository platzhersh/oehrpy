"""
REST client for EHRBase and openEHR CDR servers.

This module provides async HTTP clients for interacting with
openEHR Clinical Data Repositories.
"""

from .ehrbase import (
    AuthenticationError,
    CompositionResponse,
    EHRBaseClient,
    EHRBaseConfig,
    EHRBaseError,
    EHRResponse,
    NotFoundError,
    QueryResponse,
    ValidationError,
)

__all__ = [
    "EHRBaseClient",
    "EHRBaseConfig",
    "EHRResponse",
    "CompositionResponse",
    "QueryResponse",
    "EHRBaseError",
    "AuthenticationError",
    "NotFoundError",
    "ValidationError",
]
