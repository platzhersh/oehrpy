"""Integration tests for composition lifecycle (update & versioning) — PRD-0002."""

from __future__ import annotations

import pytest

from openehr_sdk.client import (
    CompositionFormat,
    CompositionVersionResponse,
    EHRBaseClient,
    PreconditionFailedError,
    VersionedCompositionResponse,
)
from openehr_sdk.templates import VitalSignsBuilder


@pytest.mark.integration
class TestCompositionLifecycle:
    """End-to-end composition lifecycle tests against EHRBase."""

    async def _create_composition(
        self,
        client: EHRBaseClient,
        ehr_id: str,
        template_id: str,
        systolic: int = 120,
        diastolic: int = 80,
    ) -> str:
        """Helper: create a composition and return its full version UID."""
        builder = VitalSignsBuilder(composer_name="Dr. Lifecycle Test")
        builder.add_blood_pressure(systolic=systolic, diastolic=diastolic)
        flat_data = builder.build()
        result = await client.create_composition(
            ehr_id=ehr_id,
            template_id=template_id,
            composition=flat_data,
            format=CompositionFormat.FLAT,
        )
        return result.uid

    # ── FR-1: Update composition ─────────────────────────────────────────

    async def test_update_composition_returns_new_version(
        self,
        ehrbase_client: EHRBaseClient,
        test_ehr: str,
        vital_signs_template: str,
    ) -> None:
        v1_uid = await self._create_composition(
            ehrbase_client, test_ehr, vital_signs_template, systolic=120, diastolic=80
        )
        versioned_object_uid = v1_uid.split("::")[0]

        builder = VitalSignsBuilder(composer_name="Dr. Lifecycle Test")
        builder.add_blood_pressure(systolic=130, diastolic=90)
        updated_data = builder.build()

        result = await ehrbase_client.update_composition(
            ehr_id=test_ehr,
            versioned_object_uid=versioned_object_uid,
            preceding_version_uid=v1_uid,
            composition=updated_data,
            template_id=vital_signs_template,
            format=CompositionFormat.FLAT,
        )

        assert result.uid != v1_uid
        assert result.uid.startswith(versioned_object_uid)

    async def test_update_with_stale_version_raises_412(
        self,
        ehrbase_client: EHRBaseClient,
        test_ehr: str,
        vital_signs_template: str,
    ) -> None:
        v1_uid = await self._create_composition(ehrbase_client, test_ehr, vital_signs_template)
        versioned_object_uid = v1_uid.split("::")[0]

        # First update succeeds
        builder = VitalSignsBuilder(composer_name="Dr. Lifecycle Test")
        builder.add_blood_pressure(systolic=125, diastolic=85)
        await ehrbase_client.update_composition(
            ehr_id=test_ehr,
            versioned_object_uid=versioned_object_uid,
            preceding_version_uid=v1_uid,
            composition=builder.build(),
            template_id=vital_signs_template,
            format=CompositionFormat.FLAT,
        )

        # Second update with stale v1 should fail
        builder2 = VitalSignsBuilder(composer_name="Dr. Lifecycle Test")
        builder2.add_blood_pressure(systolic=140, diastolic=95)
        with pytest.raises(PreconditionFailedError):
            await ehrbase_client.update_composition(
                ehr_id=test_ehr,
                versioned_object_uid=versioned_object_uid,
                preceding_version_uid=v1_uid,  # stale!
                composition=builder2.build(),
                template_id=vital_signs_template,
                format=CompositionFormat.FLAT,
            )

    # ── FR-2: get_composition_at_time ────────────────────────────────────

    async def test_get_composition_at_time(
        self,
        ehrbase_client: EHRBaseClient,
        test_ehr: str,
        vital_signs_template: str,
    ) -> None:
        v1_uid = await self._create_composition(
            ehrbase_client, test_ehr, vital_signs_template, systolic=110, diastolic=70
        )
        versioned_object_uid = v1_uid.split("::")[0]

        # Use a far-future timestamp to get the latest version
        result = await ehrbase_client.get_composition_at_time(
            ehr_id=test_ehr,
            versioned_object_uid=versioned_object_uid,
            version_at_time="2099-12-31T23:59:59Z",
            format=CompositionFormat.FLAT,
        )

        assert result.uid is not None
        assert result.composition is not None

    # ── FR-3: get_versioned_composition ──────────────────────────────────

    async def test_get_versioned_composition_metadata(
        self,
        ehrbase_client: EHRBaseClient,
        test_ehr: str,
        vital_signs_template: str,
    ) -> None:
        v1_uid = await self._create_composition(ehrbase_client, test_ehr, vital_signs_template)
        versioned_object_uid = v1_uid.split("::")[0]

        result = await ehrbase_client.get_versioned_composition(
            ehr_id=test_ehr,
            versioned_object_uid=versioned_object_uid,
        )

        assert isinstance(result, VersionedCompositionResponse)
        assert result.uid == versioned_object_uid
        assert result.time_created is not None

    # ── FR-4: get_composition_version ────────────────────────────────────

    async def test_get_specific_version(
        self,
        ehrbase_client: EHRBaseClient,
        test_ehr: str,
        vital_signs_template: str,
    ) -> None:
        v1_uid = await self._create_composition(ehrbase_client, test_ehr, vital_signs_template)
        versioned_object_uid = v1_uid.split("::")[0]

        result = await ehrbase_client.get_composition_version(
            ehr_id=test_ehr,
            versioned_object_uid=versioned_object_uid,
            version_uid=v1_uid,
        )

        assert isinstance(result, CompositionVersionResponse)
        assert result.version_uid == v1_uid

    # ── Round-trip: create → update → retrieve both versions ─────────────

    async def test_round_trip_create_update_retrieve_versions(
        self,
        ehrbase_client: EHRBaseClient,
        test_ehr: str,
        vital_signs_template: str,
    ) -> None:
        # Create v1
        v1_uid = await self._create_composition(
            ehrbase_client, test_ehr, vital_signs_template, systolic=120, diastolic=80
        )
        versioned_object_uid = v1_uid.split("::")[0]

        # Update to v2
        builder = VitalSignsBuilder(composer_name="Dr. Lifecycle Test")
        builder.add_blood_pressure(systolic=140, diastolic=95)
        v2_result = await ehrbase_client.update_composition(
            ehr_id=test_ehr,
            versioned_object_uid=versioned_object_uid,
            preceding_version_uid=v1_uid,
            composition=builder.build(),
            template_id=vital_signs_template,
            format=CompositionFormat.FLAT,
        )
        v2_uid = v2_result.uid

        # Retrieve v1 and v2 separately
        comp_v1 = await ehrbase_client.get_composition(
            ehr_id=test_ehr,
            composition_uid=v1_uid,
            format=CompositionFormat.FLAT,
        )
        comp_v2 = await ehrbase_client.get_composition(
            ehr_id=test_ehr,
            composition_uid=v2_uid,
            format=CompositionFormat.FLAT,
        )

        assert comp_v1.uid != comp_v2.uid
        assert comp_v1.composition != comp_v2.composition
