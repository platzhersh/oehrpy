"""
Serialization utilities for openEHR Reference Model objects.

This module provides functions for serializing and deserializing
openEHR RM objects to/from various formats:

- Canonical JSON: Standard openEHR JSON with _type discriminator
- FLAT format: Simplified format used by EHRBase (planned)
"""

from .canonical import (
    from_canonical,
    to_canonical,
    register_type,
    get_type_registry,
)

__all__ = [
    "from_canonical",
    "to_canonical",
    "register_type",
    "get_type_registry",
]
