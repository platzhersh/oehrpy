"""Backwards-compatible shim: openehr_sdk.client.ehrbase -> oehrpy.client.ehrbase."""

import importlib
import warnings


def __getattr__(name: str):  # type: ignore[no-untyped-def]
    warnings.warn(
        "The 'openehr_sdk.client.ehrbase' module has been renamed to 'oehrpy.client.ehrbase'. "
        "Please update your imports. "
        "The 'openehr_sdk' name will be removed in a future release.",
        DeprecationWarning,
        stacklevel=2,
    )
    return getattr(importlib.import_module("oehrpy.client.ehrbase"), name)
