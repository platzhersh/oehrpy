"""
oehrpy - A Python SDK for openEHR.

This package provides:
- Type-safe Pydantic models for all openEHR Reference Model 1.1.0 types
- Template-specific composition builders (e.g., Vital Signs)
- Serialization support for canonical JSON and FLAT formats
- Async REST client for EHRBase CDR
- AQL query builder

Quick Start:
    >>> from openehr_sdk.rm import DV_QUANTITY, DV_TEXT
    >>> from openehr_sdk import to_canonical, from_canonical
    >>>
    >>> # Create RM objects
    >>> text = DV_TEXT(value="Hello")
    >>>
    >>> # Serialize to canonical JSON
    >>> json_data = to_canonical(text)
    >>> # {"_type": "DV_TEXT", "value": "Hello"}

For template-based compositions:
    >>> from openehr_sdk.templates import VitalSignsBuilder
    >>>
    >>> builder = VitalSignsBuilder(composer_name="Dr. Smith")
    >>> builder.add_blood_pressure(systolic=120, diastolic=80)
    >>> builder.add_pulse(rate=72)
    >>> flat_data = builder.build()
"""

__version__ = "0.1.0"

# Re-export main components for convenient access
from openehr_sdk.serialization import (
    FlatBuilder,
    FlatContext,
    from_canonical,
    to_canonical,
)

__all__ = [
    "__version__",
    # Canonical JSON
    "to_canonical",
    "from_canonical",
    # FLAT format
    "FlatBuilder",
    "FlatContext",
]
