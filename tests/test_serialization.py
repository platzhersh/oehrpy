"""Tests for canonical JSON serialization."""

import pytest

from openehr_sdk.rm import (
    CODE_PHRASE,
    DV_CODED_TEXT,
    DV_QUANTITY,
    DV_TEXT,
    TERMINOLOGY_ID,
)
from openehr_sdk.serialization import from_canonical, to_canonical


class TestToCanonical:
    """Tests for to_canonical function."""

    def test_simple_type(self) -> None:
        """Test serializing a simple type."""
        text = DV_TEXT(value="Hello")
        canonical = to_canonical(text)

        assert canonical["_type"] == "DV_TEXT"
        assert canonical["value"] == "Hello"

    def test_nested_types(self) -> None:
        """Test serializing nested types."""
        term_id = TERMINOLOGY_ID(value="openehr")
        property_code = CODE_PHRASE(terminology_id=term_id, code_string="382")

        quantity = DV_QUANTITY(
            magnitude=120.0,
            units="mm[Hg]",
            property=property_code,
        )

        canonical = to_canonical(quantity)

        assert canonical["_type"] == "DV_QUANTITY"
        assert canonical["magnitude"] == 120.0
        assert canonical["property"]["_type"] == "CODE_PHRASE"
        assert canonical["property"]["terminology_id"]["_type"] == "TERMINOLOGY_ID"

    def test_exclude_none(self) -> None:
        """Test that None values are excluded by default."""
        text = DV_TEXT(value="Hello")
        canonical = to_canonical(text)

        # These should not be present
        assert "hyperlink" not in canonical
        assert "language" not in canonical

    def test_include_none(self) -> None:
        """Test that None values can be included."""
        text = DV_TEXT(value="Hello")
        canonical = to_canonical(text, exclude_none=False)

        assert "hyperlink" in canonical
        assert canonical["hyperlink"] is None


class TestFromCanonical:
    """Tests for from_canonical function."""

    def test_simple_type(self) -> None:
        """Test deserializing a simple type."""
        data = {
            "_type": "DV_TEXT",
            "value": "Hello World",
        }

        result = from_canonical(data)

        assert isinstance(result, DV_TEXT)
        assert result.value == "Hello World"

    def test_with_expected_type(self) -> None:
        """Test deserializing with expected type."""
        data = {
            "_type": "DV_TEXT",
            "value": "Hello",
        }

        result = from_canonical(data, expected_type=DV_TEXT)
        assert isinstance(result, DV_TEXT)

    def test_nested_types(self) -> None:
        """Test deserializing nested types."""
        data = {
            "_type": "DV_QUANTITY",
            "magnitude": 120.0,
            "units": "mm[Hg]",
            "property": {
                "_type": "CODE_PHRASE",
                "terminology_id": {
                    "_type": "TERMINOLOGY_ID",
                    "value": "openehr",
                },
                "code_string": "382",
            },
        }

        result = from_canonical(data)

        assert isinstance(result, DV_QUANTITY)
        assert result.magnitude == 120.0
        assert result.units == "mm[Hg]"
        assert result.property.code_string == "382"

    def test_missing_type_raises(self) -> None:
        """Test that missing _type raises ValueError."""
        data = {"value": "Hello"}

        with pytest.raises(ValueError, match="Missing _type"):
            from_canonical(data)

    def test_unknown_type_raises(self) -> None:
        """Test that unknown _type raises ValueError."""
        data = {
            "_type": "UNKNOWN_TYPE",
            "value": "Hello",
        }

        with pytest.raises(ValueError, match="Unknown type"):
            from_canonical(data)

    def test_type_mismatch_raises(self) -> None:
        """Test that type mismatch raises ValueError."""
        data = {
            "_type": "DV_TEXT",
            "value": "Hello",
        }

        with pytest.raises(ValueError, match="Type mismatch"):
            from_canonical(data, expected_type=DV_QUANTITY)


class TestRoundTrip:
    """Tests for serialization round-trip."""

    def test_dv_text_round_trip(self) -> None:
        """Test DV_TEXT round-trip."""
        original = DV_TEXT(value="Hello World")

        canonical = to_canonical(original)
        restored = from_canonical(canonical, expected_type=DV_TEXT)

        assert restored.value == original.value

    def test_dv_quantity_round_trip(self) -> None:
        """Test DV_QUANTITY round-trip."""
        term_id = TERMINOLOGY_ID(value="openehr")
        property_code = CODE_PHRASE(terminology_id=term_id, code_string="382")

        original = DV_QUANTITY(
            magnitude=120.0,
            units="mm[Hg]",
            property=property_code,
            precision=0,
        )

        canonical = to_canonical(original)
        restored = from_canonical(canonical, expected_type=DV_QUANTITY)

        assert restored.magnitude == original.magnitude
        assert restored.units == original.units
        assert restored.precision == original.precision

    def test_dv_coded_text_round_trip(self) -> None:
        """Test DV_CODED_TEXT round-trip."""
        term_id = TERMINOLOGY_ID(value="local")
        code = CODE_PHRASE(terminology_id=term_id, code_string="at0001")

        original = DV_CODED_TEXT(value="Systolic", defining_code=code)

        canonical = to_canonical(original)
        restored = from_canonical(canonical, expected_type=DV_CODED_TEXT)

        assert restored.value == original.value
        assert restored.defining_code.code_string == original.defining_code.code_string
