"""
AQL (Archetype Query Language) query builder.

This module provides a fluent API for building type-safe AQL queries
for openEHR Clinical Data Repositories.

Example:
    >>> from openehr_sdk.aql import AQLBuilder
    >>>
    >>> query = (
    ...     AQLBuilder()
    ...     .select("c/uid/value", alias="composition_id")
    ...     .select("c/context/start_time/value", alias="start_time")
    ...     .from_ehr("e")
    ...     .contains_composition("c", "IDCR - Vital Signs Encounter.v1")
    ...     .where("e/ehr_id/value = :ehr_id")
    ...     .order_by("c/context/start_time/value", descending=True)
    ...     .limit(10)
    ...     .build()
    ... )
    >>> print(query.to_string())
"""

from .builder import (
    AQLBuilder,
    AQLQuery,
    FromClause,
    OrderByClause,
    SelectClause,
    WhereClause,
)

__all__ = [
    "AQLBuilder",
    "AQLQuery",
    "SelectClause",
    "FromClause",
    "WhereClause",
    "OrderByClause",
]
