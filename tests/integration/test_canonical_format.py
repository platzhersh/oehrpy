"""Integration tests for CANONICAL format compositions with EHRBase.

These tests use the openEHR Reference Model classes directly to create
compositions in CANONICAL JSON format, which is more reliable than FLAT
format and doesn't require web template knowledge.
"""

from datetime import datetime, timezone

import pytest

from openehr_sdk.client import CompositionFormat, EHRBaseClient
from openehr_sdk.rm import (
    CODE_PHRASE,
    COMPOSITION,
    DV_CODED_TEXT,
    DV_DATE_TIME,
    DV_QUANTITY,
    DV_TEXT,
    EVENT_CONTEXT,
    HISTORY,
    ITEM_TREE,
    OBSERVATION,
    PARTY_IDENTIFIED,
    PARTY_REF,
    POINT_EVENT,
    SECTION,
)


@pytest.mark.integration
class TestCanonicalFormat:
    """Test CANONICAL format composition creation and retrieval."""

    async def test_create_canonical_blood_pressure(
        self,
        ehrbase_client: EHRBaseClient,
        test_ehr: str,
        vital_signs_template: str,
    ) -> None:
        """Test creating a composition using CANONICAL format with RM classes."""
        # Create a blood pressure observation using RM classes
        now = datetime.now(timezone.utc)

        # Build the blood pressure observation
        systolic = DV_QUANTITY(magnitude=120.0, units="mm[Hg]")
        diastolic = DV_QUANTITY(magnitude=80.0, units="mm[Hg]")

        bp_data = ITEM_TREE(
            archetype_node_id="at0003",
            name=DV_TEXT(value="Blood pressure"),
            items=[
                {"name": DV_TEXT(value="Systolic"), "value": systolic},
                {"name": DV_TEXT(value="Diastolic"), "value": diastolic},
            ],
        )

        bp_event = POINT_EVENT(
            time=DV_DATE_TIME(value=now.isoformat()),
            data=bp_data,
        )

        bp_history = HISTORY(events=[bp_event])

        bp_observation = OBSERVATION(
            name=DV_TEXT(value="Blood Pressure"),
            language=CODE_PHRASE(terminology_id="ISO_639-1", code_string="en"),
            encoding=CODE_PHRASE(terminology_id="IANA_character-sets", code_string="UTF-8"),
            subject=PARTY_REF(namespace="local", type="PERSON", id="patient-1"),
            data=bp_history,
        )

        # Create vital signs section
        vital_signs_section = SECTION(
            name=DV_TEXT(value="Vital Signs"),
            items=[bp_observation],
        )

        # Create composition
        composition = COMPOSITION(
            name=DV_TEXT(value="Vital Signs Observation"),
            language=CODE_PHRASE(terminology_id="ISO_639-1", code_string="en"),
            territory=CODE_PHRASE(terminology_id="ISO_3166-1", code_string="US"),
            category=DV_CODED_TEXT(
                value="event",
                defining_code=CODE_PHRASE(terminology_id="openehr", code_string="433"),
            ),
            composer=PARTY_IDENTIFIED(name="Dr. Test"),
            context=EVENT_CONTEXT(
                start_time=DV_DATE_TIME(value=now.isoformat()),
                setting=DV_CODED_TEXT(
                    value="other care",
                    defining_code=CODE_PHRASE(terminology_id="openehr", code_string="238"),
                ),
            ),
            content=[vital_signs_section],
        )

        # Convert to dict for submission
        from openehr_sdk.serialization import to_canonical

        canonical_data = to_canonical(composition)

        # Submit to EHRBase
        result = await ehrbase_client.create_composition(
            ehr_id=test_ehr,
            template_id=vital_signs_template,
            composition=canonical_data,
            format=CompositionFormat.JSON,  # CANONICAL is sent as JSON
        )

        assert result.uid is not None
        assert "::" in result.uid

    async def test_retrieve_canonical_composition(
        self,
        ehrbase_client: EHRBaseClient,
        test_ehr: str,
        vital_signs_template: str,
    ) -> None:
        """Test retrieving a composition in CANONICAL format."""
        # First create a simple composition using RM classes
        now = datetime.now(timezone.utc)

        pulse_rate = DV_QUANTITY(magnitude=72.0, units="/min")
        pulse_data = ITEM_TREE(
            archetype_node_id="at0002",
            name=DV_TEXT(value="Event Series"),
            items=[{"name": DV_TEXT(value="Heart Rate"), "value": pulse_rate}],
        )

        pulse_event = POINT_EVENT(
            time=DV_DATE_TIME(value=now.isoformat()),
            data=pulse_data,
        )

        pulse_observation = OBSERVATION(
            name=DV_TEXT(value="Pulse"),
            language=CODE_PHRASE(terminology_id="ISO_639-1", code_string="en"),
            encoding=CODE_PHRASE(terminology_id="IANA_character-sets", code_string="UTF-8"),
            subject=PARTY_REF(namespace="local", type="PERSON", id="patient-1"),
            data=HISTORY(events=[pulse_event]),
        )

        composition = COMPOSITION(
            name=DV_TEXT(value="Vital Signs"),
            language=CODE_PHRASE(terminology_id="ISO_639-1", code_string="en"),
            territory=CODE_PHRASE(terminology_id="ISO_3166-1", code_string="US"),
            category=DV_CODED_TEXT(
                value="event",
                defining_code=CODE_PHRASE(terminology_id="openehr", code_string="433"),
            ),
            composer=PARTY_IDENTIFIED(name="Dr. Test"),
            context=EVENT_CONTEXT(
                start_time=DV_DATE_TIME(value=now.isoformat()),
                setting=DV_CODED_TEXT(
                    value="other care",
                    defining_code=CODE_PHRASE(terminology_id="openehr", code_string="238"),
                ),
            ),
            content=[
                SECTION(
                    name=DV_TEXT(value="Vital Signs"),
                    items=[pulse_observation],
                )
            ],
        )

        from openehr_sdk.serialization import to_canonical

        canonical_data = to_canonical(composition)

        # Create composition
        created = await ehrbase_client.create_composition(
            ehr_id=test_ehr,
            template_id=vital_signs_template,
            composition=canonical_data,
            format=CompositionFormat.JSON,
        )

        # Retrieve in CANONICAL format
        retrieved = await ehrbase_client.get_composition(
            ehr_id=test_ehr,
            composition_uid=created.uid,
            format=CompositionFormat.CANONICAL,
        )

        assert retrieved.composition is not None
        assert "_type" in retrieved.composition
        assert retrieved.composition["_type"] == "COMPOSITION"

    async def test_canonical_round_trip(
        self,
        ehrbase_client: EHRBaseClient,
        test_ehr: str,
        vital_signs_template: str,
    ) -> None:
        """Test round-trip: create with RM, retrieve as CANONICAL, parse back to RM."""
        now = datetime.now(timezone.utc)

        # Create simple temperature observation
        temp = DV_QUANTITY(magnitude=37.2, units="°C")
        temp_data = ITEM_TREE(
            archetype_node_id="at0003",
            name=DV_TEXT(value="Any event"),
            items=[{"name": DV_TEXT(value="Temperature"), "value": temp}],
        )

        temp_event = POINT_EVENT(
            time=DV_DATE_TIME(value=now.isoformat()),
            data=temp_data,
        )

        temp_observation = OBSERVATION(
            name=DV_TEXT(value="Body Temperature"),
            language=CODE_PHRASE(terminology_id="ISO_639-1", code_string="en"),
            encoding=CODE_PHRASE(terminology_id="IANA_character-sets", code_string="UTF-8"),
            subject=PARTY_REF(namespace="local", type="PERSON", id="patient-1"),
            data=HISTORY(events=[temp_event]),
        )

        original_composition = COMPOSITION(
            name=DV_TEXT(value="Vital Signs"),
            language=CODE_PHRASE(terminology_id="ISO_639-1", code_string="en"),
            territory=CODE_PHRASE(terminology_id="ISO_3166-1", code_string="US"),
            category=DV_CODED_TEXT(
                value="event",
                defining_code=CODE_PHRASE(terminology_id="openehr", code_string="433"),
            ),
            composer=PARTY_IDENTIFIED(name="Dr. Test"),
            context=EVENT_CONTEXT(
                start_time=DV_DATE_TIME(value=now.isoformat()),
                setting=DV_CODED_TEXT(
                    value="other care",
                    defining_code=CODE_PHRASE(terminology_id="openehr", code_string="238"),
                ),
            ),
            content=[
                SECTION(
                    name=DV_TEXT(value="Vital Signs"),
                    items=[temp_observation],
                )
            ],
        )

        from openehr_sdk.serialization import from_canonical, to_canonical

        # Create
        canonical_data = to_canonical(original_composition)
        created = await ehrbase_client.create_composition(
            ehr_id=test_ehr,
            template_id=vital_signs_template,
            composition=canonical_data,
            format=CompositionFormat.JSON,
        )

        # Retrieve
        retrieved = await ehrbase_client.get_composition(
            ehr_id=test_ehr,
            composition_uid=created.uid,
            format=CompositionFormat.CANONICAL,
        )

        # Parse back to RM
        parsed_composition = from_canonical(retrieved.composition, COMPOSITION)

        assert parsed_composition is not None
        assert parsed_composition.name.value == "Vital Signs"
        assert len(parsed_composition.content) > 0
