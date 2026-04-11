"""Tests for import paths: both new (oehrpy) and legacy (openehr_sdk) shim."""

import warnings


class TestNewImportPaths:
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


class TestLegacyShimImports:
    """Verify that legacy 'openehr_sdk' imports still work with deprecation warnings."""

    def test_import_openehr_sdk_top_level(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            from openehr_sdk import to_canonical

            assert to_canonical is not None
            assert len(w) >= 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "renamed to 'oehrpy'" in str(w[0].message)

    def test_import_openehr_sdk_rm(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            from openehr_sdk.rm import DV_TEXT

            assert DV_TEXT is not None
            assert len(w) >= 1
            assert issubclass(w[0].category, DeprecationWarning)

    def test_import_openehr_sdk_aql(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            from openehr_sdk.aql import AQLBuilder

            assert AQLBuilder is not None
            assert len(w) >= 1
            assert issubclass(w[0].category, DeprecationWarning)

    def test_import_openehr_sdk_client(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            from openehr_sdk.client import EHRBaseClient

            assert EHRBaseClient is not None
            assert len(w) >= 1
            assert issubclass(w[0].category, DeprecationWarning)

    def test_import_openehr_sdk_serialization(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            from openehr_sdk.serialization import to_canonical

            assert to_canonical is not None
            assert len(w) >= 1
            assert issubclass(w[0].category, DeprecationWarning)

    def test_import_openehr_sdk_templates(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            from openehr_sdk.templates import VitalSignsBuilder

            assert VitalSignsBuilder is not None
            assert len(w) >= 1
            assert issubclass(w[0].category, DeprecationWarning)

    def test_import_openehr_sdk_validation(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            from openehr_sdk.validation import FlatValidator

            assert FlatValidator is not None
            assert len(w) >= 1
            assert issubclass(w[0].category, DeprecationWarning)

    def test_import_openehr_sdk_validation_opt(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            from openehr_sdk.validation.opt import OPTValidator

            assert OPTValidator is not None
            assert len(w) >= 1
            assert issubclass(w[0].category, DeprecationWarning)

    def test_legacy_objects_are_same_as_new(self):
        """Verify shim returns the exact same objects as the new package."""
        from oehrpy.rm import DV_TEXT as NewDvText  # noqa: N811

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            from openehr_sdk.rm import DV_TEXT as OldDvText  # noqa: N811

        assert NewDvText is OldDvText
