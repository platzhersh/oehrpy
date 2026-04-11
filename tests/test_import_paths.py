"""Tests for import paths: verify all public submodules are importable via 'oehrpy'."""

import pytest


class TestImportPaths:
    """Verify that all public submodules are importable via 'oehrpy'."""

    def test_import_oehrpy(self):
        import oehrpy

        assert hasattr(oehrpy, "__version__")

    def test_import_rm(self):
        from oehrpy.rm import DV_QUANTITY, DV_TEXT

        assert DV_TEXT is not None
        assert DV_QUANTITY is not None

    def test_import_aql(self):
        from oehrpy.aql import AQLBuilder

        assert AQLBuilder is not None

    def test_import_client(self):
        from oehrpy.client import EHRBaseClient

        assert EHRBaseClient is not None

    def test_import_serialization(self):
        from oehrpy.serialization import from_canonical, to_canonical

        assert to_canonical is not None
        assert from_canonical is not None

    def test_import_templates(self):
        from oehrpy.templates import VitalSignsBuilder

        assert VitalSignsBuilder is not None

    def test_import_validation(self):
        from oehrpy.validation import FlatValidator

        assert FlatValidator is not None

    def test_import_validation_opt(self):
        from oehrpy.validation.opt import OPTValidator

        assert OPTValidator is not None

    def test_old_import_name_not_available(self):
        """Confirm openehr_sdk is no longer importable (breaking change)."""
        with pytest.raises(ModuleNotFoundError):
            import openehr_sdk  # noqa: F401
