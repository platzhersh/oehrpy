"""
openEHR SDK - A Python SDK for openEHR with type-safe Reference Model classes.

This package provides:
- Type-safe Pydantic models for all openEHR Reference Model 1.0.4 types
- Template-specific composition builders
- Serialization support for canonical JSON and FLAT formats
- REST client for EHRBase operations
"""

__version__ = "0.1.0"

# Re-export main components for convenient access
from openehr_sdk.serialization import to_canonical, from_canonical

__all__ = [
    "__version__",
    "to_canonical",
    "from_canonical",
]
