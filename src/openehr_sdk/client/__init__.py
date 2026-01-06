"""
REST client for EHRBase and openEHR CDR servers.

This module provides async HTTP clients for interacting with
openEHR Clinical Data Repositories.
"""

from .ehrbase import (
    EHRBaseClient,
    EHRBaseConfig,
    EHRResponse,
    CompositionResponse,
    QueryResponse,
    EHRBaseError,
    AuthenticationError,
    NotFoundError,
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
