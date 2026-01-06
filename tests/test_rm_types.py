"""Tests for openEHR RM type classes."""

import pytest
from pydantic import ValidationError

from openehr_sdk.rm import (
    CODE_PHRASE,
    COMPOSITION,
    DV_BOOLEAN,
    DV_CODED_TEXT,
    DV_COUNT,
    DV_IDENTIFIER,
    DV_QUANTITY,
    DV_TEXT,
    OBSERVATION,
    TERMINOLOGY_ID,
)


class TestDataTypes:
    """Tests for data type classes."""

    def test_dv_text_creation(self) -> None:
        """Test creating a DV_TEXT instance."""
        text = DV_TEXT(value="Hello World")
        assert text.value == "Hello World"
        assert text.hyperlink is None
        assert text.language is None

    def test_dv_text_requires_value(self) -> None:
        """Test that DV_TEXT requires a value."""
        with pytest.raises(ValidationError):
            DV_TEXT()  # type: ignore

    def test_dv_boolean_creation(self) -> None:
        """Test creating a DV_BOOLEAN instance."""
        dv_true = DV_BOOLEAN(value=True)
        dv_false = DV_BOOLEAN(value=False)
        assert dv_true.value is True
        assert dv_false.value is False

    def test_dv_identifier_creation(self) -> None:
        """Test creating a DV_IDENTIFIER instance."""
        identifier = DV_IDENTIFIER(
            id="12345",
            issuer="Hospital",
            assigner="Lab",
            type="MRN",
        )
        assert identifier.id == "12345"
        assert identifier.issuer == "Hospital"

    def test_dv_count_creation(self) -> None:
        """Test creating a DV_COUNT instance."""
        count = DV_COUNT(magnitude=42)
        assert count.magnitude == 42

    def test_dv_quantity_creation(self) -> None:
        """Test creating a DV_QUANTITY instance."""
        term_id = TERMINOLOGY_ID(value="openehr")
        property_code = CODE_PHRASE(terminology_id=term_id, code_string="382")

        quantity = DV_QUANTITY(
            magnitude=120.0,
            units="mm[Hg]",
            property=property_code,
        )

        assert quantity.magnitude == 120.0
        assert quantity.units == "mm[Hg]"
        assert quantity.property.code_string == "382"

    def test_dv_coded_text_creation(self) -> None:
        """Test creating a DV_CODED_TEXT instance."""
        term_id = TERMINOLOGY_ID(value="local")
        code = CODE_PHRASE(terminology_id=term_id, code_string="at0001")

        coded_text = DV_CODED_TEXT(value="Systolic", defining_code=code)

        assert coded_text.value == "Systolic"
        assert coded_text.defining_code.code_string == "at0001"

    def test_code_phrase_creation(self) -> None:
        """Test creating a CODE_PHRASE instance."""
        term_id = TERMINOLOGY_ID(value="local")
        code = CODE_PHRASE(terminology_id=term_id, code_string="at0001")

        assert code.terminology_id.value == "local"
        assert code.code_string == "at0001"


class TestInheritance:
    """Tests for class inheritance."""

    def test_dv_coded_text_inherits_from_dv_text(self) -> None:
        """Test that DV_CODED_TEXT has text-like properties.

        Note: RM 1.1.0 JSON Schema uses flat classes rather than inheritance,
        but DV_CODED_TEXT still has all required text fields.
        """
        # Check that DV_CODED_TEXT has the same core field as DV_TEXT
        assert "value" in DV_CODED_TEXT.model_fields
        assert "value" in DV_TEXT.model_fields

    def test_dv_quantity_inherits_properly(self) -> None:
        """Test DV_QUANTITY inheritance chain."""
        # Should have all fields from parent classes
        fields = DV_QUANTITY.model_fields
        assert "magnitude" in fields  # Direct field
        assert "units" in fields  # Direct field
        assert "normal_status" in fields  # From DV_ORDERED


class TestModelDump:
    """Tests for model serialization."""

    def test_dv_text_model_dump(self) -> None:
        """Test DV_TEXT model_dump with canonical JSON format.

        Tests serialization using by_alias=True to produce openEHR canonical JSON
        with _type discriminator field.
        """
        text = DV_TEXT(value="Test")
        data = text.model_dump(by_alias=True, exclude_none=True)

        assert data == {"_type": "DV_TEXT", "value": "Test"}

    def test_dv_quantity_model_dump(self) -> None:
        """Test DV_QUANTITY model_dump."""
        term_id = TERMINOLOGY_ID(value="openehr")
        property_code = CODE_PHRASE(terminology_id=term_id, code_string="382")

        quantity = DV_QUANTITY(
            magnitude=120.0,
            units="mm[Hg]",
            property=property_code,
            precision=0,
        )

        data = quantity.model_dump(exclude_none=True)

        assert data["magnitude"] == 120.0
        assert data["units"] == "mm[Hg]"
        assert data["precision"] == 0
        assert "property" in data


class TestCompositionTypes:
    """Tests for composition-related types."""

    def test_composition_fields(self) -> None:
        """Test COMPOSITION has expected fields."""
        fields = COMPOSITION.model_fields
        assert "language" in fields
        assert "territory" in fields
        assert "category" in fields
        assert "composer" in fields
        assert "content" in fields

    def test_observation_fields(self) -> None:
        """Test OBSERVATION has expected fields."""
        fields = OBSERVATION.model_fields
        assert "data" in fields
        assert "state" in fields
        # Inherited from LOCATABLE
        assert "archetype_node_id" in fields
        assert "name" in fields
