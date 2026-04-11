"""Integration tests for CANONICAL format compositions with EHRBase.

These tests use the openEHR Reference Model classes directly to create
compositions in CANONICAL JSON format, which is more reliable than FLAT
format and doesn't require web template knowledge.
"""

from datetime import datetime, timezone

import pytest

from oehrpy.client import CompositionFormat, EHRBaseClient
from oehrpy.rm import (
    ARCHETYPE_ID,
    ARCHETYPED,
    CODE_PHRASE,
    COMPOSITION,
    DV_CODED_TEXT,
    DV_DATE_TIME,
    DV_QUANTITY,
    DV_TEXT,
    ELEMENT,
    EVENT_CONTEXT,
    HISTORY,
    ITEM_TREE,
    OBSERVATION,
    PARTY_IDENTIFIED,
    PARTY_SELF,
    POINT_EVENT,
    SECTION,
    TEMPLATE_ID,
    TERMINOLOGY_ID,
)


@pytest.mark.integration
@pytest.mark.skip(
    reason="Canonical JSON format requires complete openEHR RM conformance "
    "(archetype_details on all archetypes, origin on HISTORY, etc.). "
    "Use FLAT format via VitalSignsBuilder for simpler composition creation."
)
class TestCanonicalFormat:
    """Test CANONICAL format composition creation and retrieval.

    NOTE: These tests are skipped because creating valid canonical JSON
    compositions requires complete openEHR RM conformance including:
    - archetype_details on COMPOSITION and all OBSERVATION entries
    - origin attribute on all HISTORY objects
    - Proper archetype root invariants

    For production use, prefer FLAT format via VitalSignsBuilder which
    handles these details automatically.
    """

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
                ELEMENT(
                    archetype_node_id="at0004",
                    name=DV_TEXT(value="Systolic"),
                    value=systolic,
                ),
                ELEMENT(
                    archetype_node_id="at0005",
                    name=DV_TEXT(value="Diastolic"),
                    value=diastolic,
                ),
            ],
        )

        bp_event = POINT_EVENT(
            archetype_node_id="at0006",
            time=DV_DATE_TIME(value=now.isoformat()),
            data=bp_data,
            name=DV_TEXT(value="Any event"),
        )

        bp_history = HISTORY(
            archetype_node_id="at0002", name=DV_TEXT(value="Event Series"), events=[bp_event]
        )

        bp_observation = OBSERVATION(
            archetype_node_id="openEHR-EHR-OBSERVATION.blood_pressure.v1",
            name=DV_TEXT(value="Blood Pressure"),
            language=CODE_PHRASE(
                terminology_id=TERMINOLOGY_ID(value="ISO_639-1"), code_string="en"
            ),
            encoding=CODE_PHRASE(
                terminology_id=TERMINOLOGY_ID(value="IANA_character-sets"),
                code_string="UTF-8",
            ),
            subject=PARTY_SELF(),
            data=bp_history,
        )

        # Create vital signs section
        vital_signs_section = SECTION(
            archetype_node_id="openEHR-EHR-SECTION.vital_signs.v1",
            name=DV_TEXT(value="Vital Signs"),
            items=[bp_observation],
        )

        # Create composition
        composition = COMPOSITION(
            archetype_node_id="openEHR-EHR-COMPOSITION.encounter.v1",
            archetype_details=ARCHETYPED(
                archetype_id=ARCHETYPE_ID(value="openEHR-EHR-COMPOSITION.encounter.v1"),
                template_id=TEMPLATE_ID(value=vital_signs_template),
                rm_version="1.1.0",
            ),
            name=DV_TEXT(value="Vital Signs Observation"),
            language=CODE_PHRASE(
                terminology_id=TERMINOLOGY_ID(value="ISO_639-1"), code_string="en"
            ),
            territory=CODE_PHRASE(
                terminology_id=TERMINOLOGY_ID(value="ISO_3166-1"), code_string="US"
            ),
            category=DV_CODED_TEXT(
                value="event",
                defining_code=CODE_PHRASE(
                    terminology_id=TERMINOLOGY_ID(value="openehr"), code_string="433"
                ),
            ),
            composer=PARTY_IDENTIFIED(name="Dr. Test"),
            context=EVENT_CONTEXT(
                start_time=DV_DATE_TIME(value=now.isoformat()),
                setting=DV_CODED_TEXT(
                    value="other care",
                    defining_code=CODE_PHRASE(
                        terminology_id=TERMINOLOGY_ID(value="openehr"), code_string="238"
                    ),
                ),
            ),
            content=[vital_signs_section],
        )

        # Convert to dict for submission
        from oehrpy.serialization import to_canonical

        canonical_data = to_canonical(composition)

        # Submit to EHRBase (use JSON format - EHRBase 2.0 uses JSON instead of CANONICAL)
        result = await ehrbase_client.create_composition(
            ehr_id=test_ehr,
            template_id=vital_signs_template,
            composition=canonical_data,
            format=CompositionFormat.JSON,
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
            name=DV_TEXT(value="List"),
            items=[
                ELEMENT(
                    archetype_node_id="at0004",
                    name=DV_TEXT(value="Heart Rate"),
                    value=pulse_rate,
                )
            ],
        )

        pulse_event = POINT_EVENT(
            archetype_node_id="at0003",
            name=DV_TEXT(value="Any event"),
            time=DV_DATE_TIME(value=now.isoformat()),
            data=pulse_data,
        )

        pulse_observation = OBSERVATION(
            archetype_node_id="openEHR-EHR-OBSERVATION.pulse.v1",
            name=DV_TEXT(value="Pulse"),
            language=CODE_PHRASE(
                terminology_id=TERMINOLOGY_ID(value="ISO_639-1"), code_string="en"
            ),
            encoding=CODE_PHRASE(
                terminology_id=TERMINOLOGY_ID(value="IANA_character-sets"),
                code_string="UTF-8",
            ),
            subject=PARTY_SELF(),
            data=HISTORY(
                archetype_node_id="at0002",
                name=DV_TEXT(value="History"),
                events=[pulse_event],
            ),
        )

        composition = COMPOSITION(
            archetype_node_id="openEHR-EHR-COMPOSITION.encounter.v1",
            archetype_details=ARCHETYPED(
                archetype_id=ARCHETYPE_ID(value="openEHR-EHR-COMPOSITION.encounter.v1"),
                template_id=TEMPLATE_ID(value=vital_signs_template),
                rm_version="1.1.0",
            ),
            name=DV_TEXT(value="Vital Signs"),
            language=CODE_PHRASE(
                terminology_id=TERMINOLOGY_ID(value="ISO_639-1"), code_string="en"
            ),
            territory=CODE_PHRASE(
                terminology_id=TERMINOLOGY_ID(value="ISO_3166-1"), code_string="US"
            ),
            category=DV_CODED_TEXT(
                value="event",
                defining_code=CODE_PHRASE(
                    terminology_id=TERMINOLOGY_ID(value="openehr"), code_string="433"
                ),
            ),
            composer=PARTY_IDENTIFIED(name="Dr. Test"),
            context=EVENT_CONTEXT(
                start_time=DV_DATE_TIME(value=now.isoformat()),
                setting=DV_CODED_TEXT(
                    value="other care",
                    defining_code=CODE_PHRASE(
                        terminology_id=TERMINOLOGY_ID(value="openehr"), code_string="238"
                    ),
                ),
            ),
            content=[
                SECTION(
                    archetype_node_id="openEHR-EHR-SECTION.vital_signs.v1",
                    name=DV_TEXT(value="Vital Signs"),
                    items=[pulse_observation],
                )
            ],
        )

        from oehrpy.serialization import to_canonical

        canonical_data = to_canonical(composition)

        # Create composition (use JSON format - EHRBase 2.0 uses JSON instead of CANONICAL)
        created = await ehrbase_client.create_composition(
            ehr_id=test_ehr,
            template_id=vital_signs_template,
            composition=canonical_data,
            format=CompositionFormat.JSON,
        )

        # Retrieve in JSON format (EHRBase 2.0 canonical JSON format)
        retrieved = await ehrbase_client.get_composition(
            ehr_id=test_ehr,
            composition_uid=created.uid,
            format=CompositionFormat.JSON,
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
            name=DV_TEXT(value="Single"),
            items=[
                ELEMENT(
                    archetype_node_id="at0004",
                    name=DV_TEXT(value="Temperature"),
                    value=temp,
                )
            ],
        )

        temp_event = POINT_EVENT(
            archetype_node_id="at0003",
            name=DV_TEXT(value="Any event"),
            time=DV_DATE_TIME(value=now.isoformat()),
            data=temp_data,
        )

        temp_observation = OBSERVATION(
            archetype_node_id="openEHR-EHR-OBSERVATION.body_temperature.v1",
            name=DV_TEXT(value="Body Temperature"),
            language=CODE_PHRASE(
                terminology_id=TERMINOLOGY_ID(value="ISO_639-1"), code_string="en"
            ),
            encoding=CODE_PHRASE(
                terminology_id=TERMINOLOGY_ID(value="IANA_character-sets"),
                code_string="UTF-8",
            ),
            subject=PARTY_SELF(),
            data=HISTORY(
                archetype_node_id="at0002",
                name=DV_TEXT(value="History"),
                events=[temp_event],
            ),
        )

        original_composition = COMPOSITION(
            archetype_node_id="openEHR-EHR-COMPOSITION.encounter.v1",
            archetype_details=ARCHETYPED(
                archetype_id=ARCHETYPE_ID(value="openEHR-EHR-COMPOSITION.encounter.v1"),
                template_id=TEMPLATE_ID(value=vital_signs_template),
                rm_version="1.1.0",
            ),
            name=DV_TEXT(value="Vital Signs"),
            language=CODE_PHRASE(
                terminology_id=TERMINOLOGY_ID(value="ISO_639-1"), code_string="en"
            ),
            territory=CODE_PHRASE(
                terminology_id=TERMINOLOGY_ID(value="ISO_3166-1"), code_string="US"
            ),
            category=DV_CODED_TEXT(
                value="event",
                defining_code=CODE_PHRASE(
                    terminology_id=TERMINOLOGY_ID(value="openehr"), code_string="433"
                ),
            ),
            composer=PARTY_IDENTIFIED(name="Dr. Test"),
            context=EVENT_CONTEXT(
                start_time=DV_DATE_TIME(value=now.isoformat()),
                setting=DV_CODED_TEXT(
                    value="other care",
                    defining_code=CODE_PHRASE(
                        terminology_id=TERMINOLOGY_ID(value="openehr"), code_string="238"
                    ),
                ),
            ),
            content=[
                SECTION(
                    archetype_node_id="openEHR-EHR-SECTION.vital_signs.v1",
                    name=DV_TEXT(value="Vital Signs"),
                    items=[temp_observation],
                )
            ],
        )

        from oehrpy.serialization import from_canonical, to_canonical

        # Create (use JSON format - EHRBase 2.0 uses JSON instead of CANONICAL)
        canonical_data = to_canonical(original_composition)
        created = await ehrbase_client.create_composition(
            ehr_id=test_ehr,
            template_id=vital_signs_template,
            composition=canonical_data,
            format=CompositionFormat.JSON,
        )

        # Retrieve in JSON format (EHRBase 2.0 canonical JSON format)
        retrieved = await ehrbase_client.get_composition(
            ehr_id=test_ehr,
            composition_uid=created.uid,
            format=CompositionFormat.JSON,
        )

        # Parse back to RM
        parsed_composition = from_canonical(retrieved.composition, expected_type=COMPOSITION)

        assert parsed_composition is not None
        assert parsed_composition.name.value == "Vital Signs"
        assert len(parsed_composition.content) > 0
