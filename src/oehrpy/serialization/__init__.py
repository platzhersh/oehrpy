"""
Serialization utilities for openEHR Reference Model objects.

This module provides functions for serializing and deserializing
openEHR RM objects to/from various formats:

- Canonical JSON: Standard openEHR JSON with _type discriminator
- FLAT format: Simplified format used by EHRBase
"""

from .canonical import (
    from_canonical,
    get_type_registry,
    register_type,
    to_canonical,
)
from .flat import (
    FlatBuilder,
    FlatContext,
    FlatPath,
    flatten_dict,
    unflatten_dict,
)

__all__ = [
    # Canonical JSON
    "from_canonical",
    "to_canonical",
    "register_type",
    "get_type_registry",
    # FLAT format
    "FlatBuilder",
    "FlatContext",
    "FlatPath",
    "flatten_dict",
    "unflatten_dict",
]
