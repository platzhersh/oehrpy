"""Backwards-compatible shim: openehr_sdk.validate_opt_cli -> oehrpy.validate_opt_cli."""

import importlib
import warnings


def __getattr__(name: str):  # type: ignore[no-untyped-def]
    warnings.warn(
        "The 'openehr_sdk.validate_opt_cli' module has been renamed to "
        "'oehrpy.validate_opt_cli'. "
        "Please update your imports. "
        "The 'openehr_sdk' name will be removed in a future release.",
        DeprecationWarning,
        stacklevel=2,
    )
    return getattr(importlib.import_module("oehrpy.validate_opt_cli"), name)


def main() -> None:
    """Entry point shim for backwards compatibility."""
    warnings.warn(
        "The 'openehr_sdk.validate_opt_cli' module has been renamed to "
        "'oehrpy.validate_opt_cli'. "
        "The 'openehr_sdk' name will be removed in a future release.",
        DeprecationWarning,
        stacklevel=2,
    )
    importlib.import_module("oehrpy.validate_opt_cli").main()
