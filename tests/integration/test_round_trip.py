"""Integration tests for end-to-end round-trip workflows with EHRBase."""

from datetime import datetime, timezone

import pytest

from openehr_sdk.client import CompositionFormat, EHRBaseClient, EHRBaseError
from openehr_sdk.templates import VitalSignsBuilder


@pytest.mark.integration
class TestRoundTripWorkflows:
    """Test complete end-to-end workflows with EHRBase."""

    async def test_create_retrieve_composition_round_trip(
        self,
        ehrbase_client: EHRBaseClient,
        test_ehr: str,
        vital_signs_template: str,
    ) -> None:
        """Test creating and retrieving a composition maintains data integrity."""
        # Create composition with known values
        systolic = 125
        diastolic = 82
        pulse = 73
        composer = "Dr. Round Trip Test"

        builder = VitalSignsBuilder(composer_name=composer)
        builder.add_blood_pressure(systolic=systolic, diastolic=diastolic)
        builder.add_pulse(rate=pulse)
        original_flat = builder.build()

        # Submit to EHRBase
        created = await ehrbase_client.create_composition(
            ehr_id=test_ehr,
            template_id=vital_signs_template,
            composition=original_flat,
            format=CompositionFormat.FLAT,
        )

        # Retrieve in FLAT format
        retrieved = await ehrbase_client.get_composition(
            ehr_id=test_ehr,
            composition_uid=created.uid,
            format=CompositionFormat.FLAT,
        )

        # Verify data integrity
        flat_data = retrieved.composition
        assert flat_data is not None

        # Check context preserved
        assert flat_data.get("ctx/composer_name") == composer
        assert flat_data.get("ctx/language") == "en"
        assert flat_data.get("ctx/territory") == "US"

        # Check vital signs data preserved
        # Note: Exact paths may vary based on EHRBase version
        systolic_keys = [k for k in flat_data if "systolic" in k and "magnitude" in k]
        assert len(systolic_keys) > 0
        assert flat_data[systolic_keys[0]] == systolic

        diastolic_keys = [k for k in flat_data if "diastolic" in k and "magnitude" in k]
        assert len(diastolic_keys) > 0
        assert flat_data[diastolic_keys[0]] == diastolic

    async def test_create_query_workflow(
        self,
        ehrbase_client: EHRBaseClient,
        test_ehr: str,
        vital_signs_template: str,
    ) -> None:
        """Test complete workflow: EHR creation, composition creation, and AQL query."""
        # Build and create composition
        temperature = 38.2
        spo2 = 96

        builder = VitalSignsBuilder(composer_name="Dr. Workflow Test")
        builder.add_temperature(temperature, unit="°C")
        builder.add_oxygen_saturation(spo2=spo2)
        flat_data = builder.build()

        composition = await ehrbase_client.create_composition(
            ehr_id=test_ehr,
            template_id=vital_signs_template,
            composition=flat_data,
            format=CompositionFormat.FLAT,
        )

        # Query back the data
        aql = f"""
        SELECT c/uid/value AS uid
        FROM EHR e[ehr_id/value='{test_ehr}']
        CONTAINS COMPOSITION c
        """

        result = await ehrbase_client.query(aql)

        # Verify our composition is in results
        results_dict = result.as_dicts()
        composition_uids = [r["uid"].split("::")[0] for r in results_dict if r.get("uid")]
        assert composition.uid.split("::")[0] in composition_uids

    async def test_update_retrieve_workflow(
        self,
        ehrbase_client: EHRBaseClient,
        test_ehr: str,
        vital_signs_template: str,
    ) -> None:
        """Test updating a composition and verifying the new version."""
        # Create initial version
        builder_v1 = VitalSignsBuilder(composer_name="Dr. Update Workflow V1")
        builder_v1.add_blood_pressure(systolic=120, diastolic=80)
        flat_v1 = builder_v1.build()

        created = await ehrbase_client.create_composition(
            ehr_id=test_ehr,
            template_id=vital_signs_template,
            composition=flat_v1,
            format=CompositionFormat.FLAT,
        )

        # Update with new values
        new_systolic = 130
        new_diastolic = 85

        builder_v2 = VitalSignsBuilder(composer_name="Dr. Update Workflow V2")
        builder_v2.add_blood_pressure(systolic=new_systolic, diastolic=new_diastolic)
        builder_v2.add_pulse(rate=75)  # Add pulse in v2
        flat_v2 = builder_v2.build()

        updated = await ehrbase_client.update_composition(
            ehr_id=test_ehr,
            composition_uid=created.uid,
            composition=flat_v2,
            template_id=vital_signs_template,
            format=CompositionFormat.FLAT,
        )

        # Retrieve updated version
        retrieved = await ehrbase_client.get_composition(
            ehr_id=test_ehr,
            composition_uid=updated.uid,
            format=CompositionFormat.FLAT,
        )

        # Verify new values
        flat_data = retrieved.composition
        systolic_keys = [k for k in flat_data if "systolic" in k and "magnitude" in k]
        assert flat_data[systolic_keys[0]] == new_systolic

        diastolic_keys = [k for k in flat_data if "diastolic" in k and "magnitude" in k]
        assert flat_data[diastolic_keys[0]] == new_diastolic

        # Verify pulse was added
        pulse_keys = [
            k for k in flat_data if "pulse" in k.lower() and "rate" in k and "magnitude" in k
        ]
        assert len(pulse_keys) > 0

        # Verify composer updated
        assert flat_data.get("ctx/composer_name") == "Dr. Update Workflow V2"

    async def test_multiple_compositions_query_workflow(
        self,
        ehrbase_client: EHRBaseClient,
        test_ehr: str,
        vital_signs_template: str,
    ) -> None:
        """Test creating multiple compositions and querying across them."""
        # Create multiple compositions over time
        test_data = [
            {"systolic": 120, "diastolic": 80, "pulse": 70},
            {"systolic": 125, "diastolic": 82, "pulse": 72},
            {"systolic": 118, "diastolic": 78, "pulse": 68},
        ]

        created_uids = []

        for i, data in enumerate(test_data):
            builder = VitalSignsBuilder(composer_name=f"Dr. Multi Test {i}")
            builder.add_blood_pressure(
                systolic=data["systolic"],
                diastolic=data["diastolic"],
            )
            builder.add_pulse(rate=data["pulse"])
            flat_data = builder.build()

            composition = await ehrbase_client.create_composition(
                ehr_id=test_ehr,
                template_id=vital_signs_template,
                composition=flat_data,
                format=CompositionFormat.FLAT,
            )
            created_uids.append(composition.uid)

        # Query all compositions
        aql = f"""
        SELECT c/uid/value AS uid, c/context/start_time/value AS start_time
        FROM EHR e[ehr_id/value='{test_ehr}']
        CONTAINS COMPOSITION c
        ORDER BY c/context/start_time/value DESC
        """

        result = await ehrbase_client.query(aql)

        # Verify all compositions are present
        assert len(result.rows) >= len(test_data)

        results_dict = result.as_dicts()
        result_base_uids = [r["uid"].split("::")[0] for r in results_dict if r.get("uid")]

        for created_uid in created_uids:
            created_base_uid = created_uid.split("::")[0]
            assert created_base_uid in result_base_uids

    async def test_template_upload_composition_workflow(
        self,
        ehrbase_client: EHRBaseClient,
        test_ehr: str,
        vital_signs_opt_path,
    ) -> None:
        """Test uploading template, then creating composition with it."""
        # Upload template (may already exist from other tests)
        template_xml = vital_signs_opt_path.read_text(encoding="utf-8")
        try:
            template_response = await ehrbase_client.upload_template(template_xml)
        except EHRBaseError as e:
            if e.status_code == 409:
                # Template already exists, extract ID from XML
                import xml.etree.ElementTree as ET

                root = ET.fromstring(template_xml)
                ns = "{http://schemas.openehr.org/v1}"
                elem = root.find(f".//{ns}template_id/{ns}value")
                if elem is None:
                    elem = root.find(".//template_id/value")
                from openehr_sdk.client.ehrbase import TemplateResponse

                template_response = TemplateResponse(
                    template_id=elem.text if elem is not None else ""
                )
            else:
                raise

        assert template_response.template_id is not None

        # List templates to verify it's there
        templates = await ehrbase_client.list_templates()
        template_ids = [t.template_id for t in templates]
        assert template_response.template_id in template_ids

        # Create composition with uploaded template
        builder = VitalSignsBuilder(composer_name="Dr. Template Upload Test")
        builder.add_respiration(rate=16)
        flat_data = builder.build()

        composition = await ehrbase_client.create_composition(
            ehr_id=test_ehr,
            template_id=template_response.template_id,
            composition=flat_data,
            format=CompositionFormat.FLAT,
        )

        assert composition.uid is not None
        assert "::" in composition.uid

    async def test_canonical_to_flat_format_conversion(
        self,
        ehrbase_client: EHRBaseClient,
        test_ehr: str,
        vital_signs_template: str,
    ) -> None:
        """Test creating in FLAT, retrieving in both FLAT and CANONICAL."""
        # Create in FLAT format
        builder = VitalSignsBuilder(composer_name="Dr. Format Test")
        builder.add_blood_pressure(systolic=115, diastolic=75)
        flat_data = builder.build()

        composition = await ehrbase_client.create_composition(
            ehr_id=test_ehr,
            template_id=vital_signs_template,
            composition=flat_data,
            format=CompositionFormat.FLAT,
        )

        # Retrieve in FLAT
        flat_retrieved = await ehrbase_client.get_composition(
            ehr_id=test_ehr,
            composition_uid=composition.uid,
            format=CompositionFormat.FLAT,
        )
        assert flat_retrieved.composition is not None
        # FLAT has pipe-separated keys
        assert any("|" in str(key) for key in flat_retrieved.composition)

        # Retrieve in CANONICAL
        canonical_retrieved = await ehrbase_client.get_composition(
            ehr_id=test_ehr,
            composition_uid=composition.uid,
            format=CompositionFormat.CANONICAL,
        )
        assert canonical_retrieved.composition is not None
        # Canonical has _type fields
        assert "_type" in canonical_retrieved.composition

    async def test_timestamp_preservation(
        self,
        ehrbase_client: EHRBaseClient,
        test_ehr: str,
        vital_signs_template: str,
    ) -> None:
        """Test that custom timestamps are preserved in round-trip."""
        # Create composition with specific time
        specific_time = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)

        builder = VitalSignsBuilder(composer_name="Dr. Timestamp Test")
        builder.add_blood_pressure(
            systolic=120,
            diastolic=80,
            time=specific_time,
        )
        flat_data = builder.build()

        # Create composition
        composition = await ehrbase_client.create_composition(
            ehr_id=test_ehr,
            template_id=vital_signs_template,
            composition=flat_data,
            format=CompositionFormat.FLAT,
        )

        # Retrieve and check timestamp
        retrieved = await ehrbase_client.get_composition(
            ehr_id=test_ehr,
            composition_uid=composition.uid,
            format=CompositionFormat.FLAT,
        )

        flat_data = retrieved.composition
        time_keys = [k for k in flat_data if k.endswith("/time") and "blood_pressure" in k]

        assert len(time_keys) > 0
        # Check that the timestamp is preserved (allowing for formatting differences)
        assert "2024-01-15" in flat_data[time_keys[0]]
        assert "10:30" in flat_data[time_keys[0]]
