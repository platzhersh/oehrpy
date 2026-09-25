"""Pytest fixtures for integration tests.

The suite runs against one CDR at a time, selected with ``OEHRPY_CDR``:

- ``ehrbase`` (default): ``EHRBASE_URL``, ``EHRBASE_USER``, ``EHRBASE_PASSWORD``,
  ``EHRBASE_ADMIN_USER``, ``EHRBASE_ADMIN_PASSWORD``
- ``ferroehr``: ``FERROEHR_URL``, ``FERROEHR_USER``, ``FERROEHR_PASSWORD``,
  ``FERROEHR_ADMIN_USER``, ``FERROEHR_ADMIN_PASSWORD``,
  ``FERROEHR_READONLY_USER``, ``FERROEHR_HMAC_SECRET`` (defaults match the
  ``ferroehr`` profile in ``docker-compose.yml``)

Tests hitting a known FerroEHR server bug are marked
``@pytest.mark.ferroehr_xfail(reason=...)`` and become non-strict xfails when
running against FerroEHR.
"""

import os
from collections.abc import AsyncIterator
from pathlib import Path

import pytest

from oehrpy.client import (
    EHRBaseError,
    OpenEHRClient,
    ServerType,
    ValidationError,
    create_client,
)

CDR = ServerType(os.getenv("OEHRPY_CDR", ServerType.EHRBASE.value))


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Turn ``ferroehr_xfail`` markers into xfails when testing FerroEHR."""
    for item in items:
        marker = item.get_closest_marker("ferroehr_xfail")
        if marker is None:
            continue
        if CDR is ServerType.FERROEHR:
            reason = marker.kwargs.get("reason", "known FerroEHR server issue")
            item.add_marker(pytest.mark.xfail(reason=reason, strict=False))


@pytest.fixture
def cdr_server_type() -> ServerType:
    """The CDR vendor under test."""
    return CDR


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
def ehrbase_admin_user() -> str:
    """Get EHRBase admin username from environment or use default."""
    return os.getenv("EHRBASE_ADMIN_USER", "ehrbase-admin")


@pytest.fixture
def ehrbase_admin_password() -> str:
    """Get EHRBase admin password from environment or use default."""
    return os.getenv("EHRBASE_ADMIN_PASSWORD", "EvenMoreSecretPassword")


@pytest.fixture
def ferroehr_settings() -> dict[str, str]:
    """FerroEHR connection settings from environment or docker-compose defaults."""
    return {
        "url": os.getenv("FERROEHR_URL", "http://localhost:8081/ferroehr"),
        "user": os.getenv("FERROEHR_USER", "ferroehr"),
        "password": os.getenv("FERROEHR_PASSWORD", "ferroehr"),
        "admin_user": os.getenv("FERROEHR_ADMIN_USER", "ferroehr-admin"),
        "admin_password": os.getenv("FERROEHR_ADMIN_PASSWORD", "ferroehr"),
        "readonly_user": os.getenv("FERROEHR_READONLY_USER", "ferroehr-readonly"),
        "hmac_secret": os.getenv(
            "FERROEHR_HMAC_SECRET", "oehrpy-dev-hmac-secret-not-for-production"
        ),
        "issuer": os.getenv("FERROEHR_OIDC_ISSUER", "http://oehrpy.test"),
        "audience": os.getenv("FERROEHR_OIDC_AUDIENCE", "ferroehr"),
    }


@pytest.fixture
async def ehrbase_client(
    ehrbase_url: str,
    ehrbase_user: str,
    ehrbase_password: str,
    ehrbase_admin_user: str,
    ehrbase_admin_password: str,
    ferroehr_settings: dict[str, str],
) -> AsyncIterator[OpenEHRClient]:
    """Provide an authenticated client for the CDR under test.

    Named ``ehrbase_client`` for historical reasons; with ``OEHRPY_CDR=ferroehr``
    it is a :class:`~oehrpy.client.FerroEHRClient`.
    """
    if CDR is ServerType.FERROEHR:
        client = create_client(
            CDR,
            base_url=ferroehr_settings["url"],
            username=ferroehr_settings["user"],
            password=ferroehr_settings["password"],
            admin_username=ferroehr_settings["admin_user"],
            admin_password=ferroehr_settings["admin_password"],
        )
    else:
        client = create_client(
            CDR,
            base_url=ehrbase_url,
            username=ehrbase_user,
            password=ehrbase_password,
            admin_username=ehrbase_admin_user,
            admin_password=ehrbase_admin_password,
        )
    async with client:
        # Verify connection before running tests
        healthy = await client.health_check()
        if not healthy:
            pytest.skip(f"{CDR.value} is not healthy or not running")

        yield client


@pytest.fixture
async def cdr_client(ehrbase_client: OpenEHRClient) -> OpenEHRClient:
    """Vendor-neutral alias of :func:`ehrbase_client`."""
    return ehrbase_client


@pytest.fixture
async def test_ehr(ehrbase_client: OpenEHRClient) -> str:
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
    ehrbase_client: OpenEHRClient,
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
