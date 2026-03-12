"""Required composition-level fields for FLAT format validation."""

from __future__ import annotations

# Each group represents a set of fields where at least one must be present
# to satisfy the requirement. Groups are checked independently.
REQUIRED_FIELD_GROUPS: list[list[str]] = [
    ["category|code"],
    ["category|value"],
    ["category|terminology"],
    ["language|code"],
    ["language|terminology"],
    ["territory|code"],
    ["territory|terminology"],
    ["composer|name"],
    ["context/start_time"],
    ["context/setting|code"],
    ["context/setting|value"],
    ["context/setting|terminology"],
]

# Valid suffixes per RM data type.
# An empty list means the path itself (no suffix) is the only valid form.
VALID_SUFFIXES: dict[str, list[str]] = {
    "DV_QUANTITY": ["|magnitude", "|unit", "|precision", "|normal_range", "|normal_status"],
    "DV_CODED_TEXT": ["|value", "|code", "|terminology", "|preferred_term"],
    "DV_TEXT": ["|value"],
    "DV_DATE_TIME": [],
    "DV_DATE": [],
    "DV_TIME": [],
    "DV_BOOLEAN": [],
    "DV_COUNT": ["|magnitude", "|accuracy", "|accuracy_is_percent"],
    "DV_ORDINAL": ["|value", "|code", "|terminology", "|ordinal"],
    "DV_SCALE": ["|value", "|code", "|terminology", "|symbol_value"],
    "DV_PROPORTION": ["|numerator", "|denominator", "|type", "|precision"],
    "DV_DURATION": [],
    "DV_IDENTIFIER": ["|id", "|type", "|issuer", "|assigner"],
    "DV_URI": [],
    "DV_EHR_URI": [],
    "DV_MULTIMEDIA": ["|mediatype", "|alternatetext", "|uri", "|size"],
    "DV_PARSABLE": ["|value", "|formalism"],
    "CODE_PHRASE": ["|code", "|terminology"],
    "PARTY_IDENTIFIED": ["|name", "|id"],
    "PARTY_RELATED": ["|name", "|id", "|relationship"],
    "PARTY_SELF": [],
}

# Structural RM types that are not leaf data types —
# paths through these are intermediate, not validated for suffixes.
STRUCTURAL_RM_TYPES: set[str] = {
    "COMPOSITION",
    "SECTION",
    "OBSERVATION",
    "EVALUATION",
    "INSTRUCTION",
    "ACTION",
    "ADMIN_ENTRY",
    "CLUSTER",
    "HISTORY",
    "EVENT",
    "POINT_EVENT",
    "INTERVAL_EVENT",
    "ITEM_TREE",
    "ITEM_LIST",
    "ITEM_SINGLE",
    "ITEM_TABLE",
    "ELEMENT",
    "EVENT_CONTEXT",
    "ACTIVITY",
    "ISM_TRANSITION",
    "INSTRUCTION_DETAILS",
}
