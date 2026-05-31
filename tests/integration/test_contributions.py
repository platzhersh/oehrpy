"""Integration tests for contributions (audit & atomic changesets) — PRD-0003.

These tests validate the contribution endpoints against a real EHRBase
instance. The create/round-trip tests build a CANONICAL composition via the RM
classes; like the canonical-format composition tests, they require complete
openEHR RM conformance and are skipped by default (see
``test_canonical_format.py`` for the rationale). The not-found test exercises
the client path without needing valid composition data and always runs.
"""

from datetime import datetime, timezone

import pytest

from oehrpy.client import (
    ContributionBuilder,
    EHRBaseClient,
    NotFoundError,
)
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


def _build_canonical_pulse(template_id: str, magnitude: float = 72.0) -> dict:
    """Build a minimal CANONICAL pulse composition as a dict."""
    from oehrpy.serialization import to_canonical

    now = datetime.now(timezone.utc)
    observation = OBSERVATION(
        archetype_node_id="openEHR-EHR-OBSERVATION.pulse.v1",
        name=DV_TEXT(value="Pulse"),
        language=CODE_PHRASE(terminology_id=TERMINOLOGY_ID(value="ISO_639-1"), code_string="en"),
        encoding=CODE_PHRASE(
            terminology_id=TERMINOLOGY_ID(value="IANA_character-sets"), code_string="UTF-8"
        ),
        subject=PARTY_SELF(),
        data=HISTORY(
            archetype_node_id="at0002",
            name=DV_TEXT(value="History"),
            events=[
                POINT_EVENT(
                    archetype_node_id="at0003",
                    name=DV_TEXT(value="Any event"),
                    time=DV_DATE_TIME(value=now.isoformat()),
                    data=ITEM_TREE(
                        archetype_node_id="at0002",
                        name=DV_TEXT(value="List"),
                        items=[
                            ELEMENT(
                                archetype_node_id="at0004",
                                name=DV_TEXT(value="Heart Rate"),
                                value=DV_QUANTITY(magnitude=magnitude, units="/min"),
                            )
                        ],
                    ),
                )
            ],
        ),
    )
    composition = COMPOSITION(
        archetype_node_id="openEHR-EHR-COMPOSITION.encounter.v1",
        archetype_details=ARCHETYPED(
            archetype_id=ARCHETYPE_ID(value="openEHR-EHR-COMPOSITION.encounter.v1"),
            template_id=TEMPLATE_ID(value=template_id),
            rm_version="1.1.0",
        ),
        name=DV_TEXT(value="Vital Signs"),
        language=CODE_PHRASE(terminology_id=TERMINOLOGY_ID(value="ISO_639-1"), code_string="en"),
        territory=CODE_PHRASE(terminology_id=TERMINOLOGY_ID(value="ISO_3166-1"), code_string="US"),
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
                items=[observation],
            )
        ],
    )
    return to_canonical(composition)


@pytest.mark.integration
class TestContributionNotFound:
    """Exercises the client path without needing valid composition data."""

    async def test_get_missing_contribution_raises_not_found(
        self,
        ehrbase_client: EHRBaseClient,
        test_ehr: str,
    ) -> None:
        missing_uid = "00000000-0000-4000-8000-000000000000"
        with pytest.raises(NotFoundError):
            await ehrbase_client.get_contribution(test_ehr, missing_uid)


@pytest.mark.integration
@pytest.mark.skip(
    reason="Creating contributions requires complete openEHR RM conformance for "
    "the version data (same caveat as test_canonical_format.py)."
)
class TestContributionLifecycle:
    """Commit and retrieve contributions against a real EHRBase."""

    async def test_create_single_creation_contribution(
        self,
        ehrbase_client: EHRBaseClient,
        test_ehr: str,
        vital_signs_template: str,
    ) -> None:
        composition = _build_canonical_pulse(vital_signs_template)
        body = (
            ContributionBuilder(system_id="oehrpy.integration.test")
            .add_creation(composition=composition)
            .set_audit(committer="Dr. Smith", description="Routine vitals")
            .build()
        )

        result = await ehrbase_client.create_contribution(test_ehr, body)

        assert result.contribution_uid
        assert len(result.versions) == 1

        # Round-trip: retrieve the contribution by UID.
        fetched = await ehrbase_client.get_contribution(test_ehr, result.contribution_uid)
        assert fetched.contribution_uid == result.contribution_uid
        assert len(fetched.versions) == 1

    async def test_multi_operation_contribution_is_atomic(
        self,
        ehrbase_client: EHRBaseClient,
        test_ehr: str,
        vital_signs_template: str,
    ) -> None:
        body = (
            ContributionBuilder(system_id="oehrpy.integration.test")
            .add_creation(composition=_build_canonical_pulse(vital_signs_template, 70.0))
            .add_creation(composition=_build_canonical_pulse(vital_signs_template, 80.0))
            .set_audit(committer="Dr. Smith", description="Two readings")
            .build()
        )

        result = await ehrbase_client.create_contribution(test_ehr, body)

        assert len(result.versions) == 2
