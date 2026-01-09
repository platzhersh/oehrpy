"""Pytest fixtures for integration tests."""

import os
from pathlib import Path

import pytest

from openehr_sdk.client import EHRBaseClient, EHRBaseError, ValidationError


@pytest.fixture
def ehrbase_url() -> str:
    """Get EHRBase URL from environment or use default."""
    return os.getenv("EHRBASE_URL", "http://localhost:8080/ehrbase")


@pytest.fixture
def ehrbase_user() -> str:
    """Get EHRBase username from environment or use default."""
    return os.getenv("EHRBASE_USER", "ehrbase-user")


@pytest.fixture
def ehrbase_password() -> str:
    """Get EHRBase password from environment or use default."""
    return os.getenv("EHRBASE_PASSWORD", "SuperSecretPassword")


@pytest.fixture
async def ehrbase_client(
    ehrbase_url: str,
    ehrbase_user: str,
    ehrbase_password: str,
) -> EHRBaseClient:
    """Provide authenticated EHRBase client.

    This fixture creates a connected client and ensures proper cleanup.
    """
    async with EHRBaseClient(
        base_url=ehrbase_url,
        username=ehrbase_user,
        password=ehrbase_password,
    ) as client:
        # Verify connection before running tests
        healthy = await client.health_check()
        if not healthy:
            pytest.skip("EHRBase is not healthy or not running")

        yield client


@pytest.fixture
async def test_ehr(ehrbase_client: EHRBaseClient) -> str:
    """Create a test EHR and return its ID.

    This fixture creates a fresh EHR for each test that needs one.
    """
    ehr = await ehrbase_client.create_ehr()
    return ehr.ehr_id


@pytest.fixture
def vital_signs_opt_path() -> Path:
    """Get path to Vital Signs OPT template."""
    fixtures_dir = Path(__file__).parent.parent / "fixtures"
    opt_path = fixtures_dir / "vital_signs.opt"

    if not opt_path.exists():
        pytest.skip(f"Vital Signs OPT template not found at {opt_path}")

    return opt_path


@pytest.fixture
async def vital_signs_template(
    ehrbase_client: EHRBaseClient,
    vital_signs_opt_path: Path,
) -> str:
    """Upload Vital Signs template and return template ID.

    This fixture uploads the template once per test that needs it.
    """
    # Read template XML
    template_xml = vital_signs_opt_path.read_text(encoding="utf-8")

    # Upload to EHRBase
    try:
        response = await ehrbase_client.upload_template(template_xml)
        return response.template_id
    except (ValidationError, EHRBaseError) as e:
        # Template might already exist (409 Conflict) or have validation issues
        # Try to extract template ID from XML if we got a 409
        if isinstance(e, EHRBaseError) and e.status_code == 409:
            # Extract template_id from the XML
            import xml.etree.ElementTree as ET

            root = ET.fromstring(template_xml)
            template_id_elem = root.find(
                ".//{http://schemas.openehr.org/v1}template_id/{http://schemas.openehr.org/v1}value"
            )
            if template_id_elem is None:
                template_id_elem = root.find(".//template_id/value")
            if template_id_elem is not None and template_id_elem.text:
                return template_id_elem.text

        # Otherwise, try to list and find it
        templates = await ehrbase_client.list_templates()
        vital_signs_templates = [
            t
            for t in templates
            if "vital" in t.template_id.lower() or "vital" in (t.concept or "").lower()
        ]

        if vital_signs_templates:
            return vital_signs_templates[0].template_id

        # Re-raise if we couldn't find it
        raise
