"""Tests for template builders."""


from openehr_sdk.templates import VitalSignsBuilder


class TestVitalSignsBuilder:
    """Tests for VitalSignsBuilder."""

    def test_basic_creation(self) -> None:
        """Test creating a builder."""
        builder = VitalSignsBuilder(composer_name="Dr. Smith")
        result = builder.build()

        assert result["ctx/language"] == "en"
        assert result["ctx/territory"] == "US"
        assert result["ctx/composer_name"] == "Dr. Smith"

    def test_add_blood_pressure(self) -> None:
        """Test adding blood pressure reading."""
        builder = VitalSignsBuilder(composer_name="Dr. Smith")
        builder.add_blood_pressure(systolic=120, diastolic=80)
        result = builder.build()

        assert "vital_signs/blood_pressure:0/any_event:0/systolic|magnitude" in result
        assert result["vital_signs/blood_pressure:0/any_event:0/systolic|magnitude"] == 120
        assert result["vital_signs/blood_pressure:0/any_event:0/systolic|unit"] == "mm[Hg]"
        assert result["vital_signs/blood_pressure:0/any_event:0/diastolic|magnitude"] == 80

    def test_add_pulse(self) -> None:
        """Test adding pulse reading."""
        builder = VitalSignsBuilder(composer_name="Dr. Smith")
        builder.add_pulse(rate=72)
        result = builder.build()

        assert "vital_signs/pulse_heart_beat:0/any_event:0/rate|magnitude" in result
        assert result["vital_signs/pulse_heart_beat:0/any_event:0/rate|magnitude"] == 72
        assert result["vital_signs/pulse_heart_beat:0/any_event:0/rate|unit"] == "/min"

    def test_add_temperature(self) -> None:
        """Test adding temperature reading."""
        builder = VitalSignsBuilder(composer_name="Dr. Smith")
        builder.add_temperature(temperature=37.2)
        result = builder.build()

        assert "vital_signs/body_temperature:0/any_event:0/temperature|magnitude" in result
        assert result["vital_signs/body_temperature:0/any_event:0/temperature|magnitude"] == 37.2
        assert result["vital_signs/body_temperature:0/any_event:0/temperature|unit"] == "Cel"

    def test_add_respiration(self) -> None:
        """Test adding respiration reading."""
        builder = VitalSignsBuilder(composer_name="Dr. Smith")
        builder.add_respiration(rate=16)
        result = builder.build()

        assert "vital_signs/respirations:0/any_event:0/rate|magnitude" in result
        assert result["vital_signs/respirations:0/any_event:0/rate|magnitude"] == 16

    def test_add_oxygen_saturation(self) -> None:
        """Test adding SpO2 reading."""
        builder = VitalSignsBuilder(composer_name="Dr. Smith")
        builder.add_oxygen_saturation(spo2=98)
        result = builder.build()

        assert "vital_signs/indirect_oximetry:0/any_event:0/spo2|magnitude" in result
        assert result["vital_signs/indirect_oximetry:0/any_event:0/spo2|magnitude"] == 98
        assert result["vital_signs/indirect_oximetry:0/any_event:0/spo2|unit"] == "%"

    def test_add_all_vitals(self) -> None:
        """Test adding all vitals at once."""
        builder = VitalSignsBuilder(composer_name="Dr. Smith")
        builder.add_all_vitals(
            systolic=120,
            diastolic=80,
            pulse=72,
            temperature=37.0,
            respiration=16,
            spo2=98,
        )
        result = builder.build()

        # Check all vitals are present
        assert "vital_signs/blood_pressure:0/any_event:0/systolic|magnitude" in result
        assert "vital_signs/pulse_heart_beat:0/any_event:0/rate|magnitude" in result
        assert "vital_signs/body_temperature:0/any_event:0/temperature|magnitude" in result
        assert "vital_signs/respirations:0/any_event:0/rate|magnitude" in result
        assert "vital_signs/indirect_oximetry:0/any_event:0/spo2|magnitude" in result

    def test_method_chaining(self) -> None:
        """Test that methods return self for chaining."""
        builder = VitalSignsBuilder(composer_name="Dr. Smith")
        result = (
            builder
            .add_blood_pressure(120, 80)
            .add_pulse(72)
            .add_temperature(37.0)
            .build()
        )

        assert len(result) > 3  # Context + vitals

    def test_multiple_readings(self) -> None:
        """Test adding multiple readings of same type."""
        builder = VitalSignsBuilder(composer_name="Dr. Smith")
        builder.add_blood_pressure(120, 80)
        builder.add_blood_pressure(118, 78)
        result = builder.build()

        # Should have two BP readings with different indices
        assert "vital_signs/blood_pressure:0/any_event:0/systolic|magnitude" in result
        assert "vital_signs/blood_pressure:1/any_event:1/systolic|magnitude" in result

    def test_custom_time(self) -> None:
        """Test setting custom measurement time."""
        time_str = "2026-01-05T10:30:00"
        builder = VitalSignsBuilder(composer_name="Dr. Smith")
        builder.add_blood_pressure(120, 80, time=time_str)
        result = builder.build()

        assert result["vital_signs/blood_pressure:0/any_event:0/time"] == time_str
