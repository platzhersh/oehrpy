"""
FLAT format serialization for EHRBase.

The FLAT format is a simplified key-value representation used by EHRBase
for composition submission and retrieval. It flattens the hierarchical
openEHR composition structure into dot-separated paths.

Example FLAT format:
    {
        "ctx/language": "en",
        "ctx/territory": "US",
        "vital_signs/blood_pressure:0/any_event:0/systolic|magnitude": 120,
        "vital_signs/blood_pressure:0/any_event:0/systolic|unit": "mm[Hg]",
        ...
    }

Note: Full FLAT format support requires template knowledge (OPT files).
This module provides utilities for working with FLAT format data.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class FlatPath:
    """Represents a parsed FLAT format path."""

    segments: list[str] = field(default_factory=list)
    index: int | None = None
    attribute: str | None = None

    @classmethod
    def parse(cls, path: str) -> FlatPath:
        """Parse a FLAT format path string.

        Examples:
            - "ctx/language" -> FlatPath(["ctx", "language"])
            - "vital_signs/bp:0/systolic|magnitude" ->
              FlatPath(["vital_signs", "bp", "systolic"], 0, "magnitude")
        """
        result = cls()

        # Split by attribute separator first
        if "|" in path:
            path_part, result.attribute = path.rsplit("|", 1)
        else:
            path_part = path

        # Split by path separator
        parts = path_part.split("/")

        for part in parts:
            # Check for index notation (e.g., "bp:0")
            match = re.match(r"^(.+):(\d+)$", part)
            if match:
                result.segments.append(match.group(1))
                result.index = int(match.group(2))
            else:
                result.segments.append(part)

        return result

    def __str__(self) -> str:
        """Convert back to FLAT path string."""
        path = "/".join(self.segments)
        if self.index is not None:
            # Add index to the last segment
            parts = path.rsplit("/", 1)
            if len(parts) == 2:
                path = f"{parts[0]}/{parts[1]}:{self.index}"
            else:
                path = f"{parts[0]}:{self.index}"
        if self.attribute:
            path = f"{path}|{self.attribute}"
        return path


@dataclass
class FlatContext:
    """Context fields for FLAT format compositions."""

    language: str = "en"
    territory: str = "US"
    composer_name: str | None = None
    composer_id: str | None = None
    id_scheme: str | None = None
    id_namespace: str | None = None
    health_care_facility_name: str | None = None
    health_care_facility_id: str | None = None
    time: str | None = None
    end_time: str | None = None
    history_origin: str | None = None
    participation_name: str | None = None
    participation_function: str | None = None
    participation_mode: str | None = None
    participation_id: str | None = None

    def to_flat(self, prefix: str = "ctx") -> dict[str, Any]:
        """Convert context to FLAT format.

        Args:
            prefix: Path prefix to use. Use "ctx" for legacy format,
                   or composition ID (e.g., "vital_signs_observations") for EHRBase 2.26.0+.
        """
        result: dict[str, Any] = {
            f"{prefix}/language|terminology": "ISO_639-1",
            f"{prefix}/language|code": self.language,
            f"{prefix}/territory|terminology": "ISO_3166-1",
            f"{prefix}/territory|code": self.territory,
        }

        if self.composer_name:
            result[f"{prefix}/composer|name"] = self.composer_name
        if self.composer_id:
            result[f"{prefix}/composer|id"] = self.composer_id
        if self.id_scheme:
            result[f"{prefix}/id_scheme"] = self.id_scheme
        if self.id_namespace:
            result[f"{prefix}/id_namespace"] = self.id_namespace
        if self.health_care_facility_name:
            result[f"{prefix}/health_care_facility|name"] = self.health_care_facility_name
        if self.health_care_facility_id:
            result[f"{prefix}/health_care_facility|id"] = self.health_care_facility_id
        if self.time:
            result[f"{prefix}/time"] = self.time
        if self.end_time:
            result[f"{prefix}/end_time"] = self.end_time
        if self.history_origin:
            result[f"{prefix}/history_origin"] = self.history_origin
        if self.participation_name:
            result[f"{prefix}/participation_name"] = self.participation_name
        if self.participation_function:
            result[f"{prefix}/participation_function"] = self.participation_function
        if self.participation_mode:
            result[f"{prefix}/participation_mode"] = self.participation_mode
        if self.participation_id:
            result[f"{prefix}/participation_id"] = self.participation_id

        return result

    @classmethod
    def from_flat(cls, data: dict[str, Any]) -> FlatContext:
        """Create context from FLAT format data."""
        return cls(
            language=data.get("ctx/language", "en"),
            territory=data.get("ctx/territory", "US"),
            composer_name=data.get("ctx/composer_name"),
            composer_id=data.get("ctx/composer_id"),
            id_scheme=data.get("ctx/id_scheme"),
            id_namespace=data.get("ctx/id_namespace"),
            health_care_facility_name=data.get("ctx/health_care_facility|name"),
            health_care_facility_id=data.get("ctx/health_care_facility|id"),
            time=data.get("ctx/time"),
            end_time=data.get("ctx/end_time"),
            history_origin=data.get("ctx/history_origin"),
            participation_name=data.get("ctx/participation_name"),
            participation_function=data.get("ctx/participation_function"),
            participation_mode=data.get("ctx/participation_mode"),
            participation_id=data.get("ctx/participation_id"),
        )


def flatten_dict(data: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    """Flatten a nested dictionary to FLAT format paths.

    Args:
        data: Nested dictionary to flatten.
        prefix: Prefix for all keys.

    Returns:
        Flattened dictionary with path keys.
    """
    result: dict[str, Any] = {}

    for key, value in data.items():
        new_key = f"{prefix}/{key}" if prefix else key

        if isinstance(value, dict):
            # Recursively flatten nested dicts
            result.update(flatten_dict(value, new_key))
        elif isinstance(value, list):
            # Handle lists with index notation
            for i, item in enumerate(value):
                indexed_key = f"{new_key}:{i}"
                if isinstance(item, dict):
                    result.update(flatten_dict(item, indexed_key))
                else:
                    result[indexed_key] = item
        else:
            result[new_key] = value

    return result


def unflatten_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Unflatten FLAT format paths to nested dictionary.

    Args:
        data: Flattened dictionary with path keys.

    Returns:
        Nested dictionary.
    """
    result: dict[str, Any] = {}

    for path, value in data.items():
        parts = path.replace("|", "/").split("/")
        current = result

        for _i, part in enumerate(parts[:-1]):
            # Check for index notation
            match = re.match(r"^(.+):(\d+)$", part)
            if match:
                name, idx = match.group(1), int(match.group(2))
                if name not in current:
                    current[name] = []
                while len(current[name]) <= idx:
                    current[name].append({})
                current = current[name][idx]
            else:
                if part not in current:
                    current[part] = {}
                current = current[part]

        # Set the final value
        final_key = parts[-1]
        match = re.match(r"^(.+):(\d+)$", final_key)
        if match:
            name, idx = match.group(1), int(match.group(2))
            if name not in current:
                current[name] = []
            while len(current[name]) <= idx:
                current[name].append(None)
            current[name][idx] = value
        else:
            current[final_key] = value

    return result


class FlatBuilder:
    """Builder for creating FLAT format compositions.

    This provides a fluent API for constructing FLAT format data
    without needing to know the exact path structure.

    Example:
        >>> builder = FlatBuilder()
        >>> builder.context(language="en", territory="US", composer_name="Dr. Smith")
        >>> builder.set("vital_signs/blood_pressure:0/any_event:0/systolic|magnitude", 120)
        >>> builder.set("vital_signs/blood_pressure:0/any_event:0/systolic|unit", "mm[Hg]")
        >>> flat_data = builder.build()
    """

    def __init__(self, composition_prefix: str | None = None) -> None:
        """Initialize the builder.

        Args:
            composition_prefix: Composition ID prefix for EHRBase 2.26.0+ format.
                              If None, uses legacy "ctx" format.
        """
        self._data: dict[str, Any] = {}
        self._context = FlatContext()
        self._composition_prefix = composition_prefix

    def context(
        self,
        language: str = "en",
        territory: str = "US",
        composer_name: str | None = None,
        **kwargs: Any,
    ) -> FlatBuilder:
        """Set context fields."""
        self._context.language = language
        self._context.territory = territory
        if composer_name:
            self._context.composer_name = composer_name
        for key, value in kwargs.items():
            if hasattr(self._context, key):
                setattr(self._context, key, value)
        return self

    def set(self, path: str, value: Any) -> FlatBuilder:
        """Set a value at the given FLAT path."""
        self._data[path] = value
        return self

    def set_quantity(
        self,
        path: str,
        magnitude: float,
        unit: str,
        precision: int | None = None,
    ) -> FlatBuilder:
        """Set a DV_QUANTITY at the given path."""
        self._data[f"{path}|magnitude"] = magnitude
        self._data[f"{path}|unit"] = unit
        if precision is not None:
            self._data[f"{path}|precision"] = precision
        return self

    def set_coded_text(
        self,
        path: str,
        value: str,
        code: str,
        terminology: str = "local",
    ) -> FlatBuilder:
        """Set a DV_CODED_TEXT at the given path."""
        self._data[f"{path}|value"] = value
        self._data[f"{path}|code"] = code
        self._data[f"{path}|terminology"] = terminology
        return self

    def set_proportion(self, path: str, numerator: float, denominator: float) -> FlatBuilder:
        """Set a DV_PROPORTION at the given path."""
        self._data[f"{path}|numerator"] = numerator
        self._data[f"{path}|denominator"] = denominator
        return self

    def set_text(self, path: str, value: str) -> FlatBuilder:
        """Set a DV_TEXT at the given path."""
        self._data[path] = value
        return self

    def set_datetime(self, path: str, value: str) -> FlatBuilder:
        """Set a DV_DATE_TIME at the given path."""
        self._data[path] = value
        return self

    def build(self) -> dict[str, Any]:
        """Build the final FLAT format dictionary."""
        prefix = self._composition_prefix if self._composition_prefix else "ctx"
        result = self._context.to_flat(prefix=prefix)

        # Add category and context fields for EHRBase 2.26.0+ format
        if self._composition_prefix:
            from datetime import datetime, timezone

            # Add category
            result[f"{self._composition_prefix}/category|terminology"] = "openehr"
            result[f"{self._composition_prefix}/category|code"] = "433"
            result[f"{self._composition_prefix}/category|value"] = "event"

            # Add context/start_time if not already set
            context_time_key = f"{self._composition_prefix}/context/start_time"
            if context_time_key not in result and context_time_key not in self._data:
                result[context_time_key] = datetime.now(timezone.utc).isoformat()

            # Add context/setting if not already set
            context_setting_code = f"{self._composition_prefix}/context/setting|code"
            if context_setting_code not in result and context_setting_code not in self._data:
                result[f"{self._composition_prefix}/context/setting|terminology"] = "openehr"
                result[context_setting_code] = "238"
                result[f"{self._composition_prefix}/context/setting|value"] = "other care"

        result.update(self._data)
        return result


# Re-export for convenience
__all__ = [
    "FlatPath",
    "FlatContext",
    "FlatBuilder",
    "flatten_dict",
    "unflatten_dict",
]
