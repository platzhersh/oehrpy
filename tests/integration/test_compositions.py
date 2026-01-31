"""Integration tests for composition operations with EHRBase."""

import pytest

from openehr_sdk.client import CompositionFormat, EHRBaseClient, NotFoundError, ValidationError
from openehr_sdk.templates import VitalSignsBuilder


@pytest.mark.integration
class TestCompositionOperations:
    """Test composition CRUD operations against real EHRBase."""

    async def test_create_composition_with_builder(
        self,
        ehrbase_client: EHRBaseClient,
        test_ehr: str,
        vital_signs_template: str,
    ) -> None:
        """Test creating a composition using VitalSignsBuilder."""
        # Build composition using builder
        builder = VitalSignsBuilder(composer_name="Dr. Integration Test")
        builder.add_blood_pressure(systolic=120, diastolic=80)
        builder.add_pulse(rate=72)
        flat_data = builder.build()

        # Submit to EHRBase
        composition = await ehrbase_client.create_composition(
            ehr_id=test_ehr,
            template_id=vital_signs_template,
            composition=flat_data,
            format=CompositionFormat.FLAT,
        )

        assert composition.uid is not None
        assert "::" in composition.uid  # Versioned UID format
        assert composition.ehr_id == test_ehr

    async def test_create_composition_all_vitals(
        self,
        ehrbase_client: EHRBaseClient,
        test_ehr: str,
        vital_signs_template: str,
    ) -> None:
        """Test creating a composition with all vital signs."""
        builder = VitalSignsBuilder(composer_name="Dr. Complete Test")
        builder.add_all_vitals(
            systolic=125,
            diastolic=85,
            pulse=75,
            temperature=37.2,
            respiration=16,
            spo2=98,
        )
        flat_data = builder.build()

        composition = await ehrbase_client.create_composition(
            ehr_id=test_ehr,
            template_id=vital_signs_template,
            composition=flat_data,
            format=CompositionFormat.FLAT,
        )

        assert composition.uid is not None
        assert "::" in composition.uid  # Versioned UID format

    async def test_get_composition(
        self,
        ehrbase_client: EHRBaseClient,
        test_ehr: str,
        vital_signs_template: str,
    ) -> None:
        """Test retrieving a composition by UID."""
        # Create a composition first
        builder = VitalSignsBuilder(composer_name="Dr. Get Test")
        builder.add_blood_pressure(systolic=130, diastolic=90)
        flat_data = builder.build()

        created = await ehrbase_client.create_composition(
            ehr_id=test_ehr,
            template_id=vital_signs_template,
            composition=flat_data,
            format=CompositionFormat.FLAT,
        )

        # Retrieve it
        retrieved = await ehrbase_client.get_composition(
            ehr_id=test_ehr,
            composition_uid=created.uid,
            format=CompositionFormat.FLAT,
        )

        assert retrieved.uid == created.uid
        assert retrieved.composition is not None

        # Check that blood pressure values are present in FLAT format
        flat_composition = retrieved.composition
        assert any("systolic" in str(key) for key in flat_composition)
        assert any("diastolic" in str(key) for key in flat_composition)

    async def test_get_composition_canonical_format(
        self,
        ehrbase_client: EHRBaseClient,
        test_ehr: str,
        vital_signs_template: str,
    ) -> None:
        """Test retrieving a composition in canonical JSON format."""
        # Create composition
        builder = VitalSignsBuilder(composer_name="Dr. Canonical Test")
        builder.add_pulse(rate=80)
        flat_data = builder.build()

        created = await ehrbase_client.create_composition(
            ehr_id=test_ehr,
            template_id=vital_signs_template,
            composition=flat_data,
            format=CompositionFormat.FLAT,
        )

        # Retrieve in canonical format
        retrieved = await ehrbase_client.get_composition(
            ehr_id=test_ehr,
            composition_uid=created.uid,
            format=CompositionFormat.CANONICAL,
        )

        assert retrieved.composition is not None
        # Canonical format should have _type fields
        assert "_type" in retrieved.composition

    async def test_update_composition(
        self,
        ehrbase_client: EHRBaseClient,
        test_ehr: str,
        vital_signs_template: str,
    ) -> None:
        """Test updating an existing composition."""
        # Create initial composition
        builder = VitalSignsBuilder(composer_name="Dr. Update Test")
        builder.add_blood_pressure(systolic=120, diastolic=80)
        flat_data = builder.build()

        created = await ehrbase_client.create_composition(
            ehr_id=test_ehr,
            template_id=vital_signs_template,
            composition=flat_data,
            format=CompositionFormat.FLAT,
        )

        # Update with new values
        updated_builder = VitalSignsBuilder(composer_name="Dr. Update Test")
        updated_builder.add_blood_pressure(systolic=125, diastolic=85)
        updated_builder.add_pulse(rate=75)
        updated_flat_data = updated_builder.build()

        updated = await ehrbase_client.update_composition(
            ehr_id=test_ehr,
            composition_uid=created.uid,
            composition=updated_flat_data,
            template_id=vital_signs_template,
            format=CompositionFormat.FLAT,
        )

        assert updated.uid != created.uid  # New version
        assert updated.uid.startswith(created.uid.split("::")[0])  # Same base UID

    async def test_delete_composition(
        self,
        ehrbase_client: EHRBaseClient,
        test_ehr: str,
        vital_signs_template: str,
    ) -> None:
        """Test deleting a composition."""
        # Create a composition
        builder = VitalSignsBuilder(composer_name="Dr. Delete Test")
        builder.add_temperature(37.0)
        flat_data = builder.build()

        created = await ehrbase_client.create_composition(
            ehr_id=test_ehr,
            template_id=vital_signs_template,
            composition=flat_data,
            format=CompositionFormat.FLAT,
        )

        # Delete it
        await ehrbase_client.delete_composition(
            ehr_id=test_ehr,
            composition_uid=created.uid,
        )

        # Verify it's deleted by trying to retrieve it
        # Note: EHRBase might return 404 or a deleted marker depending on version
        with pytest.raises((NotFoundError, Exception)):
            await ehrbase_client.get_composition(
                ehr_id=test_ehr,
                composition_uid=created.uid,
            )

    async def test_get_nonexistent_composition(
        self,
        ehrbase_client: EHRBaseClient,
        test_ehr: str,
    ) -> None:
        """Test retrieving a non-existent composition raises error."""
        fake_uid = "00000000-0000-0000-0000-000000000000::local.ehrbase.org::1"

        with pytest.raises(NotFoundError):
            await ehrbase_client.get_composition(
                ehr_id=test_ehr,
                composition_uid=fake_uid,
                format=CompositionFormat.FLAT,
            )

    async def test_create_composition_without_template_fails(
        self,
        ehrbase_client: EHRBaseClient,
        test_ehr: str,
    ) -> None:
        """Test that creating composition without template ID fails."""
        flat_data = {
            "ctx/language": "en",
            "ctx/territory": "US",
        }

        # Should fail because template_id is required for FLAT format
        with pytest.raises((ValidationError, Exception)):
            await ehrbase_client.create_composition(
                ehr_id=test_ehr,
                composition=flat_data,
                template_id=None,
                format=CompositionFormat.FLAT,
            )

    async def test_multiple_events_same_observation(
        self,
        ehrbase_client: EHRBaseClient,
        test_ehr: str,
        vital_signs_template: str,
    ) -> None:
        """Test adding multiple blood pressure readings in one composition."""
        builder = VitalSignsBuilder(composer_name="Dr. Multi Event Test")

        # Add multiple BP readings
        builder.add_blood_pressure(systolic=120, diastolic=80)
        builder.add_blood_pressure(systolic=125, diastolic=82)
        builder.add_blood_pressure(systolic=118, diastolic=78)

        flat_data = builder.build()

        composition = await ehrbase_client.create_composition(
            ehr_id=test_ehr,
            template_id=vital_signs_template,
            composition=flat_data,
            format=CompositionFormat.FLAT,
        )

        assert composition.uid is not None

        # Retrieve and verify multiple events
        retrieved = await ehrbase_client.get_composition(
            ehr_id=test_ehr,
            composition_uid=composition.uid,
            format=CompositionFormat.FLAT,
        )

        flat_composition = retrieved.composition
        # Should have blood_pressure:0, blood_pressure:1, blood_pressure:2
        assert any("blood_pressure:0" in str(key) for key in flat_composition)
        assert any("blood_pressure:1" in str(key) for key in flat_composition)
        assert any("blood_pressure:2" in str(key) for key in flat_composition)
