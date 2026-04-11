"""Backwards-compatible shim for the renamed oehrpy package.

The 'openehr_sdk' package has been renamed to 'oehrpy'.
This shim exists to allow existing code to continue working
with a deprecation warning. It will be removed in a future release.
"""

import importlib
import warnings


def __getattr__(name: str):  # type: ignore[no-untyped-def]
    warnings.warn(
        "The 'openehr_sdk' module has been renamed to 'oehrpy'. "
        "Please update your imports: "
        "'from oehrpy import ...' instead of 'from openehr_sdk import ...'. "
        "The 'openehr_sdk' name will be removed in a future release.",
        DeprecationWarning,
        stacklevel=2,
    )
    return getattr(importlib.import_module("oehrpy"), name)
