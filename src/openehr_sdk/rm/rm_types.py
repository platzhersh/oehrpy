"""
Generated Pydantic models for openEHR Reference Model 1.1.0.

Includes both RM and BASE types from specifications-ITS-JSON.
Auto-generated - DO NOT EDIT MANUALLY.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

# openEHR RM 1.1.0 and BASE Types


# Rebuild all models to resolve forward references
import sys as _sys
_module = _sys.modules[__name__]
for _name in dir(_module):
    _obj = getattr(_module, _name)
    if isinstance(_obj, type) and issubclass(_obj, BaseModel) and _obj is not BaseModel:
        try:
            _obj.model_rebuild()
        except Exception:
            pass  # Skip if rebuild fails