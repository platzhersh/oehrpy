"""
Canonical JSON serialization for openEHR Reference Model objects.

The canonical JSON format is the standard openEHR JSON serialization format,
which includes a `_type` field for polymorphic type identification.

Example:
    >>> from openehr_sdk.rm import DV_QUANTITY
    >>> from openehr_sdk.serialization import to_canonical, from_canonical
    >>>
    >>> # Create a DV_QUANTITY
    >>> bp = DV_QUANTITY(magnitude=120.0, units="mm[Hg]", property=...)
    >>>
    >>> # Serialize to canonical JSON
    >>> json_data = to_canonical(bp)
    >>> # {
    >>> #   "_type": "DV_QUANTITY",
    >>> #   "magnitude": 120.0,
    >>> #   "units": "mm[Hg]",
    >>> #   ...
    >>> # }
    >>>
    >>> # Deserialize back (with type detection)
    >>> restored = from_canonical(json_data)
    >>> assert isinstance(restored, DV_QUANTITY)
"""

from __future__ import annotations

from typing import Any, TypeVar

from pydantic import BaseModel

# Type registry: maps _type string to class
_TYPE_REGISTRY: dict[str, type[BaseModel]] = {}

T = TypeVar("T", bound=BaseModel)


def register_type(cls: type[T]) -> type[T]:
    """Register a type in the canonical JSON type registry.

    Args:
        cls: The Pydantic model class to register.

    Returns:
        The same class (allows use as decorator).
    """
    type_name = getattr(cls, "_type_", cls.__name__)
    _TYPE_REGISTRY[type_name] = cls
    return cls


def get_type_registry() -> dict[str, type[BaseModel]]:
    """Get a copy of the type registry."""
    return _TYPE_REGISTRY.copy()


def _build_registry() -> None:
    """Build the type registry from all RM classes."""
    if _TYPE_REGISTRY:
        return  # Already built

    # Import all RM types and register them
    from openehr_sdk import rm

    for name in dir(rm):
        cls = getattr(rm, name)
        if isinstance(cls, type) and issubclass(cls, BaseModel) and cls is not BaseModel:
            type_name = getattr(cls, "_type_", name)
            _TYPE_REGISTRY[type_name] = cls


def to_canonical(
    obj: BaseModel,
    *,
    exclude_none: bool = True,
    by_alias: bool = False,
) -> dict[str, Any]:
    """Serialize a Pydantic model to canonical JSON format.

    The canonical format includes a `_type` field at the root level and
    recursively in any nested objects that have a _type_ class attribute.

    Args:
        obj: The Pydantic model to serialize.
        exclude_none: Whether to exclude None values from output.
        by_alias: Whether to use field aliases in output.

    Returns:
        A dictionary suitable for JSON serialization.
    """
    data = obj.model_dump(exclude_none=exclude_none, by_alias=by_alias)

    # Add _type field
    type_name = getattr(obj.__class__, "_type_", obj.__class__.__name__)
    result = {"_type": type_name}
    result.update(data)

    # Recursively add _type to nested objects
    _add_types_recursive(result, obj, exclude_none)

    return result


def _add_types_recursive(
    data: dict[str, Any],
    obj: BaseModel,
    exclude_none: bool,
) -> None:
    """Recursively add _type fields to nested objects."""
    for key, value in list(data.items()):
        if key == "_type":
            continue

        # Get the corresponding attribute from the object
        attr = getattr(obj, key, None)

        if attr is None:
            continue

        if isinstance(attr, BaseModel):
            # Nested Pydantic model
            type_name = getattr(attr.__class__, "_type_", attr.__class__.__name__)
            nested_data = {"_type": type_name}
            if isinstance(value, dict):
                nested_data.update(value)
                data[key] = nested_data
                _add_types_recursive(nested_data, attr, exclude_none)
        elif isinstance(attr, list):
            # List of objects
            for i, item in enumerate(attr):
                if isinstance(item, BaseModel) and i < len(value):
                    type_name = getattr(item.__class__, "_type_", item.__class__.__name__)
                    if isinstance(value[i], dict):
                        nested_data = {"_type": type_name}
                        nested_data.update(value[i])
                        value[i] = nested_data
                        _add_types_recursive(nested_data, item, exclude_none)


def from_canonical(
    data: dict[str, Any],
    *,
    expected_type: type[T] | None = None,
) -> T | BaseModel:
    """Deserialize canonical JSON to a Pydantic model.

    Uses the `_type` field to determine the correct class for polymorphic
    deserialization.

    Args:
        data: The canonical JSON data.
        expected_type: Optional expected type. If provided, validates that
            the deserialized object is of this type.

    Returns:
        The deserialized Pydantic model.

    Raises:
        ValueError: If the _type is not recognized or doesn't match expected_type.
    """
    _build_registry()

    # Get the type from the data
    type_name = data.get("_type")
    if not type_name:
        if expected_type:
            return expected_type.model_validate(data)
        raise ValueError("Missing _type field in canonical JSON data")

    # Look up the class
    cls = _TYPE_REGISTRY.get(type_name)
    if not cls:
        raise ValueError(f"Unknown type: {type_name}")

    # Validate expected_type if provided
    if expected_type and not issubclass(cls, expected_type):
        raise ValueError(f"Type mismatch: expected {expected_type.__name__}, got {type_name}")

    # Remove _type field from data before validation
    clean_data = {k: v for k, v in data.items() if k != "_type"}

    # Recursively process nested objects
    _process_nested_types(clean_data)

    return cls.model_validate(clean_data)


def _process_nested_types(data: dict[str, Any]) -> None:
    """Recursively remove _type fields from nested data."""
    for _key, value in data.items():
        if isinstance(value, dict):
            # Remove _type and recurse
            if "_type" in value:
                value.pop("_type")
            _process_nested_types(value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    if "_type" in item:
                        item.pop("_type")
                    _process_nested_types(item)
