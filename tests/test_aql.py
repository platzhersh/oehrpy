"""Tests for AQL query builder."""

from openehr_sdk.aql import AQLBuilder


class TestAQLBuilder:
    """Tests for AQLBuilder."""

    def test_simple_select(self) -> None:
        """Test simple SELECT query."""
        query = AQLBuilder().select("c").from_ehr().contains_composition().build()
        sql = query.to_string()

        assert "SELECT c" in sql
        assert "FROM EHR e" in sql
        assert "CONTAINS COMPOSITION c" in sql

    def test_select_with_alias(self) -> None:
        """Test SELECT with alias."""
        query = (
            AQLBuilder()
            .select("c/uid/value", alias="composition_id")
            .from_ehr()
            .contains_composition()
            .build()
        )
        sql = query.to_string()

        assert "c/uid/value AS composition_id" in sql

    def test_select_multiple(self) -> None:
        """Test multiple SELECT items."""
        query = (
            AQLBuilder()
            .select("c/uid/value", alias="uid")
            .select("c/context/start_time/value", alias="time")
            .from_ehr()
            .contains_composition()
            .build()
        )
        sql = query.to_string()

        assert "c/uid/value AS uid" in sql
        assert "c/context/start_time/value AS time" in sql

    def test_select_count(self) -> None:
        """Test COUNT aggregate."""
        query = (
            AQLBuilder().select_count("c", alias="total").from_ehr().contains_composition().build()
        )
        sql = query.to_string()

        assert "COUNT(c) AS total" in sql

    def test_where_clause(self) -> None:
        """Test WHERE clause."""
        query = (
            AQLBuilder()
            .select("c")
            .from_ehr()
            .contains_composition()
            .where("e/ehr_id/value = '123'")
            .build()
        )
        sql = query.to_string()

        assert "WHERE e/ehr_id/value = '123'" in sql

    def test_where_multiple(self) -> None:
        """Test multiple WHERE conditions."""
        query = (
            AQLBuilder()
            .select("c")
            .from_ehr()
            .contains_composition()
            .where("e/ehr_id/value = '123'")
            .where("c/name/value = 'Test'")
            .build()
        )
        sql = query.to_string()

        assert "WHERE" in sql
        assert "AND" in sql

    def test_where_ehr_id(self) -> None:
        """Test WHERE for EHR ID."""
        query = AQLBuilder().select("c").from_ehr().contains_composition().where_ehr_id().build()
        sql = query.to_string()

        assert "e/ehr_id/value = $ehr_id" in sql

    def test_order_by(self) -> None:
        """Test ORDER BY clause."""
        query = (
            AQLBuilder()
            .select("c")
            .from_ehr()
            .contains_composition()
            .order_by("c/context/start_time/value")
            .build()
        )
        sql = query.to_string()

        assert "ORDER BY c/context/start_time/value ASC" in sql

    def test_order_by_descending(self) -> None:
        """Test ORDER BY DESC."""
        query = (
            AQLBuilder()
            .select("c")
            .from_ehr()
            .contains_composition()
            .order_by("c/context/start_time/value", descending=True)
            .build()
        )
        sql = query.to_string()

        assert "ORDER BY c/context/start_time/value DESC" in sql

    def test_limit(self) -> None:
        """Test LIMIT clause."""
        query = AQLBuilder().select("c").from_ehr().contains_composition().limit(10).build()
        sql = query.to_string()

        assert "LIMIT 10" in sql

    def test_offset(self) -> None:
        """Test OFFSET clause."""
        query = (
            AQLBuilder().select("c").from_ehr().contains_composition().limit(10).offset(20).build()
        )
        sql = query.to_string()

        assert "LIMIT 10" in sql
        assert "OFFSET 20" in sql

    def test_paginate(self) -> None:
        """Test pagination helper."""
        query = (
            AQLBuilder()
            .select("c")
            .from_ehr()
            .contains_composition()
            .paginate(page=3, page_size=10)
            .build()
        )
        sql = query.to_string()

        assert "LIMIT 10" in sql
        assert "OFFSET 20" in sql  # (3-1) * 10

    def test_contains_observation(self) -> None:
        """Test CONTAINS OBSERVATION."""
        query = (
            AQLBuilder()
            .select("o")
            .from_ehr()
            .contains_composition()
            .contains_observation("o", "openEHR-EHR-OBSERVATION.blood_pressure.v1")
            .build()
        )
        sql = query.to_string()

        assert "CONTAINS COMPOSITION c" in sql
        assert "CONTAINS OBSERVATION o" in sql
        assert "$o_archetype_id" in sql  # Parameterized
        assert query.parameters["o_archetype_id"] == "openEHR-EHR-OBSERVATION.blood_pressure.v1"

    def test_full_query(self) -> None:
        """Test complete query with all clauses."""
        query = (
            AQLBuilder()
            .select("c/uid/value", alias="uid")
            .select("c/context/start_time/value", alias="time")
            .from_ehr()
            .contains_composition()
            .where_ehr_id()
            .order_by_time()
            .limit(100)
            .build()
        )
        sql = query.to_string()

        assert sql.startswith("SELECT")
        assert "FROM EHR e" in sql
        assert "WHERE" in sql
        assert "ORDER BY" in sql
        assert "LIMIT 100" in sql


class TestAQLQuery:
    """Tests for AQLQuery object."""

    def test_to_string(self) -> None:
        """Test query string generation."""
        query = AQLBuilder().select("c").from_ehr().contains_composition().build()
        assert isinstance(query.to_string(), str)

    def test_str_conversion(self) -> None:
        """Test __str__ method."""
        query = AQLBuilder().select("c").from_ehr().contains_composition().build()
        assert str(query) == query.to_string()

    def test_with_parameters(self) -> None:
        """Test adding parameters."""
        query = (
            AQLBuilder()
            .select("c")
            .from_ehr()
            .contains_composition()
            .where_ehr_id()
            .param("ehr_id", "test-123")
            .build()
        )

        assert query.parameters["ehr_id"] == "test-123"

        # Test with_parameters returns new query
        new_query = query.with_parameters(limit=10)
        assert new_query.parameters["ehr_id"] == "test-123"
        assert new_query.parameters["limit"] == 10
