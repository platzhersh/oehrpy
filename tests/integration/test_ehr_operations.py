"""Integration tests for EHR operations with EHRBase."""

import pytest

from openehr_sdk.client import EHRBaseClient, NotFoundError


@pytest.mark.integration
class TestEHROperations:
    """Test EHR CRUD operations against real EHRBase."""

    async def test_create_ehr(self, ehrbase_client: EHRBaseClient) -> None:
        """Test creating a new EHR."""
        ehr = await ehrbase_client.create_ehr()

        assert ehr.ehr_id is not None
        assert len(ehr.ehr_id) > 0
        assert ehr.system_id is not None
        assert ehr.time_created is not None

    async def test_create_ehr_with_subject(self, ehrbase_client: EHRBaseClient) -> None:
        """Test creating an EHR with subject ID."""
        subject_id = "patient-123"
        subject_namespace = "test-namespace"

        ehr = await ehrbase_client.create_ehr(
            subject_id=subject_id,
            subject_namespace=subject_namespace,
        )

        assert ehr.ehr_id is not None
        # Verify subject info in ehr_status
        assert ehr.ehr_status is not None
        subject = ehr.ehr_status.get("subject")
        assert subject is not None
        external_ref = subject.get("external_ref")
        assert external_ref is not None
        assert external_ref.get("id", {}).get("value") == subject_id
        assert external_ref.get("namespace") == subject_namespace

    async def test_get_ehr(self, ehrbase_client: EHRBaseClient, test_ehr: str) -> None:
        """Test retrieving an existing EHR."""
        ehr = await ehrbase_client.get_ehr(test_ehr)

        assert ehr.ehr_id == test_ehr
        assert ehr.ehr_status is not None
        assert ehr.system_id is not None
        assert ehr.time_created is not None

    async def test_get_nonexistent_ehr(self, ehrbase_client: EHRBaseClient) -> None:
        """Test retrieving a non-existent EHR raises NotFoundError."""
        fake_ehr_id = "00000000-0000-0000-0000-000000000000"

        with pytest.raises(NotFoundError):
            await ehrbase_client.get_ehr(fake_ehr_id)

    async def test_get_ehr_by_subject(self, ehrbase_client: EHRBaseClient) -> None:
        """Test retrieving an EHR by subject ID."""
        subject_id = "patient-456"
        subject_namespace = "test-ns"

        # Create EHR with subject
        created_ehr = await ehrbase_client.create_ehr(
            subject_id=subject_id,
            subject_namespace=subject_namespace,
        )

        # Retrieve by subject
        retrieved_ehr = await ehrbase_client.get_ehr_by_subject(
            subject_id=subject_id,
            subject_namespace=subject_namespace,
        )

        assert retrieved_ehr.ehr_id == created_ehr.ehr_id

    async def test_get_ehr_by_nonexistent_subject(self, ehrbase_client: EHRBaseClient) -> None:
        """Test retrieving EHR by non-existent subject raises NotFoundError."""
        with pytest.raises(NotFoundError):
            await ehrbase_client.get_ehr_by_subject(
                subject_id="nonexistent-patient",
                subject_namespace="test-ns",
            )

    async def test_health_check(self, ehrbase_client: EHRBaseClient) -> None:
        """Test EHRBase health check endpoint."""
        is_healthy = await ehrbase_client.health_check()
        assert is_healthy is True
