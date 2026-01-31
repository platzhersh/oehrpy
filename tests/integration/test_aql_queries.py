"""Integration tests for AQL queries with EHRBase."""

import pytest

from openehr_sdk.aql import AQLBuilder
from openehr_sdk.client import EHRBaseClient
from openehr_sdk.templates import VitalSignsBuilder


@pytest.mark.integration
class TestAQLQueries:
    """Test AQL query execution against real EHRBase with data."""

    async def test_simple_composition_query(
        self,
        ehrbase_client: EHRBaseClient,
        test_ehr: str,
        vital_signs_template: str,
    ) -> None:
        """Test simple AQL query for compositions."""
        # Create a composition first
        builder = VitalSignsBuilder(composer_name="Dr. AQL Test")
        builder.add_blood_pressure(systolic=120, diastolic=80)
        flat_data = builder.build()

        await ehrbase_client.create_composition(
            ehr_id=test_ehr,
            template_id=vital_signs_template,
            composition=flat_data,
            format="FLAT",
        )

        # Query for all compositions in this EHR
        aql = f"SELECT c FROM EHR e[ehr_id/value='{test_ehr}'] CONTAINS COMPOSITION c"

        result = await ehrbase_client.query(aql)

        assert result.rows is not None
        assert len(result.rows) >= 1
        assert result.columns is not None
        assert len(result.columns) >= 1

    async def test_query_with_aql_builder(
        self,
        ehrbase_client: EHRBaseClient,
        test_ehr: str,
        vital_signs_template: str,
    ) -> None:
        """Test AQL query built with AQLBuilder."""
        # Create test data
        builder = VitalSignsBuilder(composer_name="Dr. Builder Test")
        builder.add_pulse(rate=75)
        flat_data = builder.build()

        composition = await ehrbase_client.create_composition(
            ehr_id=test_ehr,
            template_id=vital_signs_template,
            composition=flat_data,
            format="FLAT",
        )

        # Build query using AQLBuilder
        query = (
            AQLBuilder()
            .select("c/uid/value", alias="composition_id")
            .select("c/context/start_time/value", alias="time")
            .from_ehr()
            .contains_composition()
            .where_ehr_id()
            .build()
        )

        # Execute with parameter
        result = await ehrbase_client.query(
            aql=query.to_string(),
            query_parameters={"ehr_id": test_ehr},
        )

        assert result.rows is not None
        assert len(result.rows) >= 1

        # Verify we got our composition
        results_dict = result.as_dicts()
        composition_ids = [r.get("composition_id") for r in results_dict]
        base_uid = composition.uid.split("::")[0]
        result_base_uids = [cid.split("::")[0] for cid in composition_ids if cid]
        assert base_uid in result_base_uids

    async def test_query_observation_data(
        self,
        ehrbase_client: EHRBaseClient,
        test_ehr: str,
        vital_signs_template: str,
    ) -> None:
        """Test querying specific observation data (blood pressure)."""
        # Create composition with known BP values
        systolic_value = 135
        diastolic_value = 88

        builder = VitalSignsBuilder(composer_name="Dr. Observation Test")
        builder.add_blood_pressure(systolic=systolic_value, diastolic=diastolic_value)
        flat_data = builder.build()

        await ehrbase_client.create_composition(
            ehr_id=test_ehr,
            template_id=vital_signs_template,
            composition=flat_data,
            format="FLAT",
        )

        # Query for blood pressure observations
        aql = f"""
        SELECT
            o/data[at0001]/events[at0006]/data[at0003]/items[at0004]/value/magnitude AS systolic,
            o/data[at0001]/events[at0006]/data[at0003]/items[at0005]/value/magnitude AS diastolic
        FROM EHR e[ehr_id/value='{test_ehr}']
        CONTAINS COMPOSITION c
        CONTAINS OBSERVATION o[openEHR-EHR-OBSERVATION.blood_pressure.v1]
        """

        result = await ehrbase_client.query(aql)

        assert len(result.rows) >= 1

        # Check we got our values
        results_dict = result.as_dicts()
        found = False
        for row in results_dict:
            if row.get("systolic") == systolic_value and row.get("diastolic") == diastolic_value:
                found = True
                break

        assert found, f"Expected BP {systolic_value}/{diastolic_value} not found in results"

    async def test_query_with_parameters(
        self,
        ehrbase_client: EHRBaseClient,
        test_ehr: str,
        vital_signs_template: str,
    ) -> None:
        """Test AQL query with query parameters."""
        # Create composition
        builder = VitalSignsBuilder(composer_name="Dr. Params Test")
        builder.add_temperature(37.5)
        flat_data = builder.build()

        await ehrbase_client.create_composition(
            ehr_id=test_ehr,
            template_id=vital_signs_template,
            composition=flat_data,
            format="FLAT",
        )

        # Query using parameters
        aql = "SELECT c FROM EHR e CONTAINS COMPOSITION c WHERE e/ehr_id/value = $ehr_id"

        result = await ehrbase_client.query(
            aql=aql,
            query_parameters={"ehr_id": test_ehr},
        )

        assert len(result.rows) >= 1

    async def test_query_get_method(
        self,
        ehrbase_client: EHRBaseClient,
        test_ehr: str,
        vital_signs_template: str,
    ) -> None:
        """Test AQL query via GET method."""
        # Create data
        builder = VitalSignsBuilder(composer_name="Dr. GET Test")
        builder.add_respiration(rate=16)
        flat_data = builder.build()

        await ehrbase_client.create_composition(
            ehr_id=test_ehr,
            template_id=vital_signs_template,
            composition=flat_data,
            format="FLAT",
        )

        # Query using GET
        aql = f"SELECT c/uid/value FROM EHR e[ehr_id/value='{test_ehr}'] CONTAINS COMPOSITION c"

        result = await ehrbase_client.query_get(aql=aql)

        assert len(result.rows) >= 1

    async def test_query_with_pagination(
        self,
        ehrbase_client: EHRBaseClient,
        test_ehr: str,
        vital_signs_template: str,
    ) -> None:
        """Test AQL query with pagination parameters."""
        # Create multiple compositions
        for i in range(3):
            builder = VitalSignsBuilder(composer_name=f"Dr. Pagination Test {i}")
            builder.add_pulse(rate=70 + i)
            flat_data = builder.build()

            await ehrbase_client.create_composition(
                ehr_id=test_ehr,
                template_id=vital_signs_template,
                composition=flat_data,
                format="FLAT",
            )

        # Query with limit
        aql = f"SELECT c FROM EHR e[ehr_id/value='{test_ehr}'] CONTAINS COMPOSITION c"

        result = await ehrbase_client.query_get(
            aql=aql,
            offset=0,
            fetch=2,  # Only fetch 2 results
        )

        assert len(result.rows) == 2

    async def test_query_with_order_by(
        self,
        ehrbase_client: EHRBaseClient,
        test_ehr: str,
        vital_signs_template: str,
    ) -> None:
        """Test AQL query with ORDER BY clause."""
        # Create compositions at different times
        for i in range(2):
            builder = VitalSignsBuilder(composer_name=f"Dr. Order Test {i}")
            builder.add_pulse(rate=60 + i * 5)
            flat_data = builder.build()

            await ehrbase_client.create_composition(
                ehr_id=test_ehr,
                template_id=vital_signs_template,
                composition=flat_data,
                format="FLAT",
            )

        # Query with order by
        aql = f"""
        SELECT c/uid/value AS uid, c/context/start_time/value AS time
        FROM EHR e[ehr_id/value='{test_ehr}']
        CONTAINS COMPOSITION c
        ORDER BY c/context/start_time/value DESC
        """

        result = await ehrbase_client.query(aql)

        assert len(result.rows) >= 2

        # Verify results are ordered (times should be descending)
        results_dict = result.as_dicts()
        if len(results_dict) >= 2:
            assert results_dict[0]["time"] >= results_dict[1]["time"]

    async def test_query_count_aggregation(
        self,
        ehrbase_client: EHRBaseClient,
        test_ehr: str,
        vital_signs_template: str,
    ) -> None:
        """Test AQL query with COUNT aggregation."""
        # Create known number of compositions
        num_compositions = 3
        for i in range(num_compositions):
            builder = VitalSignsBuilder(composer_name=f"Dr. Count Test {i}")
            builder.add_temperature(37.0 + i * 0.1)
            flat_data = builder.build()

            await ehrbase_client.create_composition(
                ehr_id=test_ehr,
                template_id=vital_signs_template,
                composition=flat_data,
                format="FLAT",
            )

        # Query with COUNT
        aql = f"""
        SELECT COUNT(c) AS composition_count
        FROM EHR e[ehr_id/value='{test_ehr}']
        CONTAINS COMPOSITION c
        """

        result = await ehrbase_client.query(aql)

        assert len(result.rows) == 1
        results_dict = result.as_dicts()
        assert results_dict[0]["composition_count"] == num_compositions

    async def test_query_empty_result(
        self,
        ehrbase_client: EHRBaseClient,
        test_ehr: str,
    ) -> None:
        """Test AQL query that returns no results."""
        # Query for a non-existent archetype
        aql = f"""
        SELECT c
        FROM EHR e[ehr_id/value='{test_ehr}']
        CONTAINS COMPOSITION c
        CONTAINS OBSERVATION o[openEHR-EHR-OBSERVATION.nonexistent.v1]
        """

        result = await ehrbase_client.query(aql)

        assert result.rows is not None
        assert len(result.rows) == 0
