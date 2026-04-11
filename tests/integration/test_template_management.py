"""Integration tests for template management operations (PRD-0013).

Tests get_template_opt(), update_template(), and delete_template()
against a real EHRBase instance.
"""

import contextlib
from pathlib import Path

import pytest

from openehr_sdk.client import EHRBaseClient, NotFoundError, ValidationError


@pytest.fixture
def vital_signs_opt_xml(vital_signs_opt_path: Path) -> str:
    """Read the Vital Signs OPT XML as a string."""
    return vital_signs_opt_path.read_text(encoding="utf-8")


@pytest.mark.integration
class TestGetTemplateOpt:
    """Tests for get_template_opt()."""

    async def test_upload_and_get_opt_round_trip(
        self,
        ehrbase_client: EHRBaseClient,
        vital_signs_template: str,
    ) -> None:
        """Upload OPT then get_template_opt() returns valid XML."""
        opt_xml = await ehrbase_client.get_template_opt(vital_signs_template)

        assert opt_xml is not None
        assert len(opt_xml) > 0
        assert "<?xml" in opt_xml or "<template" in opt_xml

    async def test_get_opt_not_found(
        self,
        ehrbase_client: EHRBaseClient,
    ) -> None:
        """get_template_opt() for non-existent template raises NotFoundError."""
        with pytest.raises(NotFoundError):
            await ehrbase_client.get_template_opt("nonexistent-template-id")

    async def test_opt_xml_can_be_parsed(
        self,
        ehrbase_client: EHRBaseClient,
        vital_signs_template: str,
    ) -> None:
        """Downloaded OPT XML can be parsed by OPTParser."""
        from openehr_sdk.templates.opt_parser import OPTParser

        opt_xml = await ehrbase_client.get_template_opt(vital_signs_template)

        parser = OPTParser()
        template_def = parser.parse_string(opt_xml)
        assert template_def.template_id == vital_signs_template


@pytest.mark.integration
class TestDeleteTemplate:
    """Tests for delete_template()."""

    async def test_delete_template(
        self,
        ehrbase_client: EHRBaseClient,
        vital_signs_opt_xml: str,
    ) -> None:
        """Upload then delete — template should no longer appear in list."""
        # Upload a fresh template (may already exist — ignore errors)
        with contextlib.suppress(Exception):
            await ehrbase_client.upload_template(vital_signs_opt_xml)

        templates_before = await ehrbase_client.list_templates()
        template_ids_before = {t.template_id for t in templates_before}

        if not any("vital" in tid.lower() for tid in template_ids_before):
            pytest.skip("Vital signs template not available for delete test")

        # Find the vital signs template ID
        vital_id = next(tid for tid in template_ids_before if "vital" in tid.lower())

        # Delete it — may fail with 409/422 if compositions exist
        # (standard API returns 409, admin API returns 422)
        try:
            await ehrbase_client.delete_template(vital_id)
        except ValidationError as e:
            if e.status_code in (409, 422):
                pytest.skip("Cannot delete: compositions reference this template")
            raise

        templates_after = await ehrbase_client.list_templates()
        template_ids_after = {t.template_id for t in templates_after}
        assert vital_id not in template_ids_after

    async def test_delete_not_found(
        self,
        ehrbase_client: EHRBaseClient,
    ) -> None:
        """Deleting a non-existent template raises NotFoundError."""
        with pytest.raises(NotFoundError):
            await ehrbase_client.delete_template("nonexistent-template-id")

    async def test_delete_invalidates_cache(
        self,
        ehrbase_client: EHRBaseClient,
        vital_signs_template: str,
        vital_signs_opt_xml: str,
    ) -> None:
        """delete_template() clears the web template cache entry."""
        # Prime the cache
        try:
            await ehrbase_client.get_web_template(vital_signs_template)
        except Exception:
            pytest.skip("Could not fetch web template")

        assert vital_signs_template in ehrbase_client._web_template_cache

        # Delete (may fail with 409)
        try:
            await ehrbase_client.delete_template(vital_signs_template)
        except ValidationError as e:
            if e.status_code in (409, 422):
                pytest.skip("Cannot delete: compositions reference this template")
            raise

        assert vital_signs_template not in ehrbase_client._web_template_cache


@pytest.mark.integration
class TestUpdateTemplate:
    """Tests for update_template()."""

    async def test_update_template(
        self,
        ehrbase_client: EHRBaseClient,
        vital_signs_template: str,
        vital_signs_opt_xml: str,
    ) -> None:
        """Upload, update, then get_template_opt() returns content."""
        # Update with the same XML (content hasn't changed, but tests the flow)
        try:
            result = await ehrbase_client.update_template(vital_signs_template, vital_signs_opt_xml)
        except ValidationError as e:
            if e.status_code in (409, 422):
                pytest.skip("Cannot update: compositions reference this template")
            raise

        assert result.template_id == vital_signs_template

    async def test_update_invalidates_web_template_cache(
        self,
        ehrbase_client: EHRBaseClient,
        vital_signs_template: str,
        vital_signs_opt_xml: str,
    ) -> None:
        """get_web_template() after update returns fresh data."""
        # Prime the cache
        try:
            await ehrbase_client.get_web_template(vital_signs_template)
        except Exception:
            pytest.skip("Could not fetch web template")

        assert vital_signs_template in ehrbase_client._web_template_cache

        # Update
        try:
            await ehrbase_client.update_template(vital_signs_template, vital_signs_opt_xml)
        except ValidationError as e:
            if e.status_code in (409, 422):
                pytest.skip("Cannot update: compositions reference this template")
            raise

        # Cache should be cleared (the delete step in fallback clears it)
        assert vital_signs_template not in ehrbase_client._web_template_cache
