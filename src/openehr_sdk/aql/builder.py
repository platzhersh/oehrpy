"""
AQL Query Builder implementation.

This module provides a fluent API for constructing AQL queries
with proper escaping and parameterization.

AQL Syntax Reference:
    SELECT <select_clause>
    FROM <from_clause>
    [WHERE <where_clause>]
    [ORDER BY <order_by_clause>]
    [LIMIT <limit> [OFFSET <offset>]]

Example:
    >>> query = (
    ...     AQLBuilder()
    ...     .select("c/uid/value")
    ...     .from_ehr()
    ...     .contains_composition("c")
    ...     .build()
    ... )
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SortOrder(str, Enum):
    """Sort order for ORDER BY clause."""

    ASC = "ASC"
    DESC = "DESC"


@dataclass
class SelectClause:
    """Represents a SELECT clause item."""

    path: str
    alias: str | None = None
    aggregate: str | None = None  # COUNT, MAX, MIN, etc.

    def to_string(self) -> str:
        """Convert to AQL string."""
        expr = f"{self.aggregate}({self.path})" if self.aggregate else self.path

        if self.alias:
            return f"{expr} AS {self.alias}"
        return expr


@dataclass
class FromClause:
    """Represents a FROM clause with containments."""

    ehr_alias: str = "e"
    ehr_id_param: str | None = None  # Parameter name for EHR ID (not the value)
    containments: list[str] = field(default_factory=list)

    def to_string(self) -> str:
        """Convert to AQL string."""
        parts = []

        # EHR clause
        if self.ehr_id_param:
            parts.append(f"EHR {self.ehr_alias}[ehr_id/value=${self.ehr_id_param}]")
        else:
            parts.append(f"EHR {self.ehr_alias}")

        # Containments
        for containment in self.containments:
            parts.append(f"CONTAINS {containment}")

        return " ".join(parts)


@dataclass
class WhereClause:
    """Represents a WHERE clause."""

    conditions: list[str] = field(default_factory=list)
    logic: str = "AND"  # AND or OR

    def to_string(self) -> str:
        """Convert to AQL string."""
        if not self.conditions:
            return ""
        return f" {self.logic} ".join(self.conditions)

    def add(self, condition: str) -> None:
        """Add a condition."""
        self.conditions.append(condition)


@dataclass
class OrderByClause:
    """Represents an ORDER BY clause item."""

    path: str
    order: SortOrder = SortOrder.ASC

    def to_string(self) -> str:
        """Convert to AQL string."""
        return f"{self.path} {self.order.value}"


@dataclass
class AQLQuery:
    """Represents a complete AQL query."""

    select_clauses: list[SelectClause] = field(default_factory=list)
    from_clause: FromClause | None = None
    where_clause: WhereClause | None = None
    order_by_clauses: list[OrderByClause] = field(default_factory=list)
    limit_value: int | None = None
    offset_value: int | None = None
    parameters: dict[str, Any] = field(default_factory=dict)

    def to_string(self) -> str:
        """Convert to AQL query string."""
        parts = []

        # SELECT
        if self.select_clauses:
            select_items = ", ".join(s.to_string() for s in self.select_clauses)
            parts.append(f"SELECT {select_items}")
        else:
            parts.append("SELECT *")

        # FROM
        if self.from_clause:
            parts.append(f"FROM {self.from_clause.to_string()}")

        # WHERE
        if self.where_clause and self.where_clause.conditions:
            parts.append(f"WHERE {self.where_clause.to_string()}")

        # ORDER BY
        if self.order_by_clauses:
            order_items = ", ".join(o.to_string() for o in self.order_by_clauses)
            parts.append(f"ORDER BY {order_items}")

        # LIMIT and OFFSET
        if self.limit_value is not None:
            parts.append(f"LIMIT {self.limit_value}")
            if self.offset_value is not None:
                parts.append(f"OFFSET {self.offset_value}")

        return " ".join(parts)

    def __str__(self) -> str:
        return self.to_string()

    def with_parameters(self, **params: Any) -> AQLQuery:
        """Return a new query with additional parameters."""
        new_params = {**self.parameters, **params}
        return AQLQuery(
            select_clauses=self.select_clauses,
            from_clause=self.from_clause,
            where_clause=self.where_clause,
            order_by_clauses=self.order_by_clauses,
            limit_value=self.limit_value,
            offset_value=self.offset_value,
            parameters=new_params,
        )


class AQLBuilder:
    """Fluent builder for AQL queries.

    Example:
        >>> query = (
        ...     AQLBuilder()
        ...     .select("c/uid/value", alias="uid")
        ...     .select("c/context/start_time/value", alias="time")
        ...     .from_ehr("e")
        ...     .contains_composition("c", "IDCR - Vital Signs Encounter.v1")
        ...     .where("e/ehr_id/value = $ehr_id")
        ...     .order_by("c/context/start_time/value", descending=True)
        ...     .limit(10)
        ...     .build()
        ... )
    """

    def __init__(self) -> None:
        self._select_clauses: list[SelectClause] = []
        self._from_clause: FromClause | None = None
        self._where_clause: WhereClause = WhereClause()
        self._order_by_clauses: list[OrderByClause] = []
        self._limit: int | None = None
        self._offset: int | None = None
        self._parameters: dict[str, Any] = {}

    def select(
        self,
        path: str,
        alias: str | None = None,
        aggregate: str | None = None,
    ) -> AQLBuilder:
        """Add a SELECT clause item.

        Args:
            path: The AQL path expression (e.g., "c/uid/value").
            alias: Optional alias for the result column.
            aggregate: Optional aggregate function (COUNT, MAX, MIN, SUM, AVG).

        Returns:
            Self for method chaining.
        """
        self._select_clauses.append(SelectClause(path, alias, aggregate))
        return self

    def select_count(self, path: str = "*", alias: str | None = None) -> AQLBuilder:
        """Add a COUNT aggregate."""
        return self.select(path, alias, "COUNT")

    def select_max(self, path: str, alias: str | None = None) -> AQLBuilder:
        """Add a MAX aggregate."""
        return self.select(path, alias, "MAX")

    def select_min(self, path: str, alias: str | None = None) -> AQLBuilder:
        """Add a MIN aggregate."""
        return self.select(path, alias, "MIN")

    def from_ehr(
        self,
        alias: str = "e",
        ehr_id: str | None = None,
        ehr_id_param: str = "ehr_id_from",
    ) -> AQLBuilder:
        """Set the FROM EHR clause.

        Args:
            alias: Alias for the EHR (default: "e").
            ehr_id: Optional specific EHR ID to query (registered as parameter).
            ehr_id_param: Parameter name for the EHR ID.

        Returns:
            Self for method chaining.
        """
        if ehr_id is not None:
            self._from_clause = FromClause(ehr_alias=alias, ehr_id_param=ehr_id_param)
            self._parameters[ehr_id_param] = ehr_id
        else:
            self._from_clause = FromClause(ehr_alias=alias)
        return self

    def contains(
        self,
        rm_type: str,
        alias: str,
        archetype_id: str | None = None,
    ) -> AQLBuilder:
        """Add a CONTAINS clause.

        Args:
            rm_type: The RM type (COMPOSITION, OBSERVATION, etc.).
            alias: Alias for the contained item.
            archetype_id: Optional archetype ID filter (parameterized).

        Returns:
            Self for method chaining.
        """
        if self._from_clause is None:
            self._from_clause = FromClause()

        if archetype_id:
            param_name = f"{alias}_archetype_id"
            containment = f"{rm_type} {alias}[archetype_id/value=${param_name}]"
            self._parameters[param_name] = archetype_id
        else:
            containment = f"{rm_type} {alias}"

        self._from_clause.containments.append(containment)
        return self

    def contains_composition(
        self,
        alias: str = "c",
        template_id: str | None = None,
        archetype_id: str | None = None,
        template_id_param: str = "template_id",
    ) -> AQLBuilder:
        """Add a CONTAINS COMPOSITION clause.

        Args:
            alias: Alias for the composition.
            template_id: Optional template ID filter (added as parameterized WHERE).
            archetype_id: Optional archetype ID filter.
            template_id_param: Parameter name for template ID.

        Returns:
            Self for method chaining.
        """
        if self._from_clause is None:
            self._from_clause = FromClause()

        if archetype_id:
            containment = f"COMPOSITION {alias}[archetype_id/value=${alias}_archetype_id]"
            self._parameters[f"{alias}_archetype_id"] = archetype_id
        else:
            containment = f"COMPOSITION {alias}"

        self._from_clause.containments.append(containment)

        # Add template_id filter as parameterized WHERE clause
        if template_id:
            self._where_clause.add(
                f"{alias}/archetype_details/template_id/value = ${template_id_param}"
            )
            self._parameters[template_id_param] = template_id

        return self

    def contains_observation(
        self,
        alias: str = "o",
        archetype_id: str | None = None,
    ) -> AQLBuilder:
        """Add a CONTAINS OBSERVATION clause."""
        return self.contains("OBSERVATION", alias, archetype_id)

    def contains_evaluation(
        self,
        alias: str = "e",
        archetype_id: str | None = None,
    ) -> AQLBuilder:
        """Add a CONTAINS EVALUATION clause."""
        return self.contains("EVALUATION", alias, archetype_id)

    def contains_instruction(
        self,
        alias: str = "i",
        archetype_id: str | None = None,
    ) -> AQLBuilder:
        """Add a CONTAINS INSTRUCTION clause."""
        return self.contains("INSTRUCTION", alias, archetype_id)

    def contains_action(
        self,
        alias: str = "a",
        archetype_id: str | None = None,
    ) -> AQLBuilder:
        """Add a CONTAINS ACTION clause."""
        return self.contains("ACTION", alias, archetype_id)

    def where(self, condition: str) -> AQLBuilder:
        """Add a WHERE condition.

        Args:
            condition: The condition expression.

        Returns:
            Self for method chaining.
        """
        self._where_clause.add(condition)
        return self

    def and_where(self, condition: str) -> AQLBuilder:
        """Add an AND condition."""
        return self.where(condition)

    def where_ehr_id(self, ehr_alias: str = "e", param_name: str = "ehr_id") -> AQLBuilder:
        """Add a WHERE condition for EHR ID.

        Args:
            ehr_alias: Alias for the EHR.
            param_name: Parameter name for the EHR ID.

        Returns:
            Self for method chaining.
        """
        return self.where(f"{ehr_alias}/ehr_id/value = ${param_name}")

    def where_template(
        self,
        composition_alias: str = "c",
        template_id: str | None = None,
        param_name: str = "template_id",
    ) -> AQLBuilder:
        """Add a WHERE condition for template ID.

        Args:
            composition_alias: Alias for the composition.
            template_id: The template ID value (registered as parameter if provided).
            param_name: Parameter name for the template ID.

        Returns:
            Self for method chaining.
        """
        self.where(f"{composition_alias}/archetype_details/template_id/value = ${param_name}")
        if template_id:
            self._parameters[param_name] = template_id
        return self

    def where_time_range(
        self,
        path: str,
        start: str | None = None,
        end: str | None = None,
        start_param: str = "start_time",
        end_param: str = "end_time",
    ) -> AQLBuilder:
        """Add WHERE conditions for a time range.

        Args:
            path: Path to the datetime field.
            start: Start time (ISO format). If provided, registers as parameter.
            end: End time (ISO format). If provided, registers as parameter.
            start_param: Parameter name for start time.
            end_param: Parameter name for end time.

        Returns:
            Self for method chaining.
        """
        if start:
            self.where(f"{path} >= ${start_param}")
            self._parameters[start_param] = start
        if end:
            self.where(f"{path} <= ${end_param}")
            self._parameters[end_param] = end
        return self

    def order_by(
        self,
        path: str,
        descending: bool = False,
    ) -> AQLBuilder:
        """Add an ORDER BY clause.

        Args:
            path: The path to order by.
            descending: Whether to sort descending.

        Returns:
            Self for method chaining.
        """
        order = SortOrder.DESC if descending else SortOrder.ASC
        self._order_by_clauses.append(OrderByClause(path, order))
        return self

    def order_by_time(
        self,
        path: str = "c/context/start_time/value",
        descending: bool = True,
    ) -> AQLBuilder:
        """Add ORDER BY for a time field (newest first by default)."""
        return self.order_by(path, descending)

    def limit(self, count: int) -> AQLBuilder:
        """Set the LIMIT.

        Args:
            count: Maximum number of results.

        Returns:
            Self for method chaining.
        """
        self._limit = count
        return self

    def offset(self, count: int) -> AQLBuilder:
        """Set the OFFSET.

        Args:
            count: Number of results to skip.

        Returns:
            Self for method chaining.
        """
        self._offset = count
        return self

    def paginate(self, page: int, page_size: int) -> AQLBuilder:
        """Set pagination.

        Args:
            page: Page number (1-based).
            page_size: Number of results per page.

        Returns:
            Self for method chaining.
        """
        self._limit = page_size
        self._offset = (page - 1) * page_size
        return self

    def param(self, name: str, value: Any) -> AQLBuilder:
        """Set a query parameter.

        Args:
            name: Parameter name.
            value: Parameter value.

        Returns:
            Self for method chaining.
        """
        self._parameters[name] = value
        return self

    def build(self) -> AQLQuery:
        """Build the AQL query.

        Returns:
            The constructed AQLQuery object.
        """
        return AQLQuery(
            select_clauses=self._select_clauses,
            from_clause=self._from_clause,
            where_clause=self._where_clause if self._where_clause.conditions else None,
            order_by_clauses=self._order_by_clauses,
            limit_value=self._limit,
            offset_value=self._offset,
            parameters=self._parameters,
        )

    def to_string(self) -> str:
        """Build and return the query string."""
        return self.build().to_string()


# Convenience functions for common queries


def select_compositions(
    ehr_id: str | None = None,
    template_id: str | None = None,
    limit: int = 100,
) -> AQLQuery:
    """Build a query to select compositions.

    Args:
        ehr_id: Optional EHR ID filter.
        template_id: Optional template ID filter.
        limit: Maximum results.

    Returns:
        AQLQuery for compositions.
    """
    builder = (
        AQLBuilder()
        .select("c/uid/value", alias="uid")
        .select("c/archetype_details/template_id/value", alias="template_id")
        .select("c/context/start_time/value", alias="start_time")
        .select("c/composer/name", alias="composer")
        .from_ehr()
        .contains_composition()
    )

    if ehr_id:
        builder.where_ehr_id()
        builder.param("ehr_id", ehr_id)
    if template_id:
        builder.where_template(template_id=template_id)

    return builder.order_by_time().limit(limit).build()


def select_observations(
    archetype_id: str,
    ehr_id: str | None = None,
    limit: int = 100,
) -> AQLQuery:
    """Build a query to select observations.

    Args:
        archetype_id: Observation archetype ID.
        ehr_id: Optional EHR ID filter.
        limit: Maximum results.

    Returns:
        AQLQuery for observations.
    """
    builder = (
        AQLBuilder()
        .select("o")
        .from_ehr()
        .contains_composition()
        .contains_observation(archetype_id=archetype_id)
    )

    if ehr_id:
        builder.where_ehr_id()
        builder.param("ehr_id", ehr_id)

    return builder.limit(limit).build()
