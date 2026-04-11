"""Backwards-compatible shim: openehr_sdk.templates -> oehrpy.templates."""

import importlib
import warnings


def __getattr__(name: str):  # type: ignore[no-untyped-def]
    warnings.warn(
        "The 'openehr_sdk.templates' module has been renamed to 'oehrpy.templates'. "
        "Please update your imports. "
        "The 'openehr_sdk' name will be removed in a future release.",
        DeprecationWarning,
        stacklevel=2,
    )
    return getattr(importlib.import_module("oehrpy.templates"), name)
