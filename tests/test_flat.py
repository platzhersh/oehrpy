"""Tests for FLAT format serialization."""

from openehr_sdk.serialization.flat import (
    FlatBuilder,
    FlatContext,
    FlatPath,
    flatten_dict,
    unflatten_dict,
)


class TestFlatPath:
    """Tests for FlatPath parsing."""

    def test_simple_path(self) -> None:
        """Test parsing simple path."""
        path = FlatPath.parse("ctx/language")
        assert path.segments == ["ctx", "language"]
        assert path.index is None
        assert path.attribute is None

    def test_path_with_index(self) -> None:
        """Test parsing path with index."""
        path = FlatPath.parse("vital_signs/bp:0/systolic")
        assert "bp" in path.segments
        assert path.index == 0

    def test_path_with_attribute(self) -> None:
        """Test parsing path with attribute."""
        path = FlatPath.parse("vital_signs/bp:0/systolic|magnitude")
        assert path.attribute == "magnitude"


class TestFlatContext:
    """Tests for FlatContext."""

    def test_default_context(self) -> None:
        """Test default context values."""
        ctx = FlatContext()
        flat = ctx.to_flat()  # Uses default "ctx" prefix

        assert flat["ctx/language|code"] == "en"
        assert flat["ctx/language|terminology"] == "ISO_639-1"
        assert flat["ctx/territory|code"] == "US"
        assert flat["ctx/territory|terminology"] == "ISO_3166-1"

    def test_custom_context(self) -> None:
        """Test custom context values."""
        ctx = FlatContext(
            language="de",
            territory="DE",
            composer_name="Dr. Mueller",
        )
        flat = ctx.to_flat()

        assert flat["ctx/language|code"] == "de"
        assert flat["ctx/territory|code"] == "DE"
        assert flat["ctx/composer|name"] == "Dr. Mueller"

    def test_from_flat(self) -> None:
        """Test creating context from flat data."""
        data = {
            "ctx/language": "fr",
            "ctx/territory": "FR",
            "ctx/composer_name": "Dr. Dupont",
        }

        ctx = FlatContext.from_flat(data)

        assert ctx.language == "fr"
        assert ctx.territory == "FR"
        assert ctx.composer_name == "Dr. Dupont"


class TestFlatBuilder:
    """Tests for FlatBuilder."""

    def test_basic_builder(self) -> None:
        """Test basic builder usage."""
        builder = FlatBuilder()  # Uses default "ctx" prefix
        builder.context(language="en", territory="US")
        builder.set("test/path", "value")

        result = builder.build()

        assert result["ctx/language|code"] == "en"
        assert result["test/path"] == "value"

    def test_set_quantity(self) -> None:
        """Test setting a quantity."""
        builder = FlatBuilder()
        builder.set_quantity("vital_signs/bp/systolic", 120.0, "mm[Hg]")

        result = builder.build()

        assert result["vital_signs/bp/systolic|magnitude"] == 120.0
        assert result["vital_signs/bp/systolic|unit"] == "mm[Hg]"

    def test_set_coded_text(self) -> None:
        """Test setting a coded text."""
        builder = FlatBuilder()
        builder.set_coded_text(
            "vital_signs/status",
            value="Normal",
            code="at0001",
            terminology="local",
        )

        result = builder.build()

        assert result["vital_signs/status|value"] == "Normal"
        assert result["vital_signs/status|code"] == "at0001"
        assert result["vital_signs/status|terminology"] == "local"


class TestFlattenUnflatten:
    """Tests for flatten/unflatten functions."""

    def test_flatten_simple(self) -> None:
        """Test flattening a simple nested dict."""
        data = {
            "ctx": {
                "language": "en",
                "territory": "US",
            }
        }

        flat = flatten_dict(data)

        assert flat["ctx/language"] == "en"
        assert flat["ctx/territory"] == "US"

    def test_flatten_list(self) -> None:
        """Test flattening a dict with lists."""
        data = {
            "events": [
                {"value": 120},
                {"value": 80},
            ]
        }

        flat = flatten_dict(data)

        assert flat["events:0/value"] == 120
        assert flat["events:1/value"] == 80

    def test_unflatten_simple(self) -> None:
        """Test unflattening a simple dict."""
        flat = {
            "ctx/language": "en",
            "ctx/territory": "US",
        }

        nested = unflatten_dict(flat)

        assert nested["ctx"]["language"] == "en"
        assert nested["ctx"]["territory"] == "US"
