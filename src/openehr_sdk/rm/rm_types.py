"""
openEHR Reference Model - Rm Types classes.

Auto-generated from openEHR BMM specifications.
Do not edit manually.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, Optional

from pydantic import BaseModel, ConfigDict, Field


class EHR(BaseModel):
    """openEHR RM type: EHR."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "EHR"
    system_id: "HIER_OBJECT_ID"
    ehr_id: "HIER_OBJECT_ID"
    time_created: "DV_DATE_TIME"
    ehr_access: "OBJECT_REF"
    ehr_status: "OBJECT_REF"
    directory: Optional["OBJECT_REF"] = Field(default=None)
    compositions: Optional[list["OBJECT_REF"]] = Field(default=None)
    contributions: list["OBJECT_REF"]
    most_recent_composition: Optional["COMPOSITION"] = Field(default=None)


class PATHABLE(BaseModel):
    """openEHR RM type: PATHABLE."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "PATHABLE"


class LOCATABLE(PATHABLE):
    """openEHR RM type: LOCATABLE."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "LOCATABLE"
    uid: Optional["UID_BASED_ID"] = Field(default=None)
    archetype_node_id: str
    name: "DV_TEXT"
    archetype_details: Optional["ARCHETYPED"] = Field(default=None)
    feeder_audit: Optional["FEEDER_AUDIT"] = Field(default=None)
    links: Optional[list["LINK"]] = Field(default=None)


class EHR_ACCESS(LOCATABLE):
    """openEHR RM type: EHR_ACCESS."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "EHR_ACCESS"
    settings: Optional["ACCESS_CONTROL_SETTINGS"] = Field(default=None)


class ACCESS_CONTROL_SETTINGS(BaseModel):
    """openEHR RM type: ACCESS_CONTROL_SETTINGS."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "ACCESS_CONTROL_SETTINGS"


class EHR_STATUS(LOCATABLE):
    """openEHR RM type: EHR_STATUS."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "EHR_STATUS"
    subject: "PARTY_SELF"
    is_queryable: bool
    is_modifiable: bool
    other_details: Optional["ITEM_STRUCTURE"] = Field(default=None)


class COMPOSITION(LOCATABLE):
    """openEHR RM type: COMPOSITION."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "COMPOSITION"
    language: "CODE_PHRASE"
    territory: "CODE_PHRASE"
    category: "DV_CODED_TEXT"
    composer: "PARTY_PROXY"
    context: Optional["EVENT_CONTEXT"] = Field(default=None)
    content: Optional[list["CONTENT_ITEM"]] = Field(default=None)


class EVENT_CONTEXT(PATHABLE):
    """openEHR RM type: EVENT_CONTEXT."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "EVENT_CONTEXT"
    health_care_facility: Optional["PARTY_IDENTIFIED"] = Field(default=None)
    start_time: "DV_DATE_TIME"
    end_time: Optional["DV_DATE_TIME"] = Field(default=None)
    participations: Optional[list["PARTICIPATION"]] = Field(default=None)
    location: str | None = Field(default=None)
    setting: "DV_CODED_TEXT"
    other_context: Optional["ITEM_STRUCTURE"] = Field(default=None)


class CONTENT_ITEM(LOCATABLE):
    """openEHR RM type: CONTENT_ITEM."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "CONTENT_ITEM"


class SECTION(CONTENT_ITEM):
    """openEHR RM type: SECTION."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "SECTION"
    items: Optional[list["CONTENT_ITEM"]] = Field(default=None)


class ENTRY(CONTENT_ITEM):
    """openEHR RM type: ENTRY."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "ENTRY"
    language: "CODE_PHRASE"
    encoding: "CODE_PHRASE"
    subject: "PARTY_PROXY"
    provider: Optional["PARTY_PROXY"] = Field(default=None)
    other_participations: Optional[list["PARTICIPATION"]] = Field(default=None)
    workflow_id: Optional["OBJECT_REF"] = Field(default=None)


class ADMIN_ENTRY(ENTRY):
    """openEHR RM type: ADMIN_ENTRY."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "ADMIN_ENTRY"
    data: "ITEM_STRUCTURE"


class CARE_ENTRY(ENTRY):
    """Abstract ENTRY subtype corresponding to any type of ENTRY in the clinical care cycle."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "CARE_ENTRY"
    protocol: Optional["ITEM_STRUCTURE"] = Field(default=None)
    guideline_id: Optional["OBJECT_REF"] = Field(default=None)


class OBSERVATION(CARE_ENTRY):
    """ENTRY subtype used to represent observation information in time, as either a single or multiple samples."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "OBSERVATION"
    data: "HISTORY" = Field(description="Data of the observation, in the form of a HISTORY of EVENTs.")
    state: Optional["HISTORY"] = Field(default=None)


class EVALUATION(CARE_ENTRY):
    """openEHR RM type: EVALUATION."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "EVALUATION"
    data: "ITEM_STRUCTURE"


class INSTRUCTION(CARE_ENTRY):
    """openEHR RM type: INSTRUCTION."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "INSTRUCTION"
    narrative: "DV_TEXT"
    expiry_time: Optional["DV_DATE_TIME"] = Field(default=None)
    wf_definition: Optional["DV_PARSABLE"] = Field(default=None)
    activities: Optional[list["ACTIVITY"]] = Field(default=None)


class ACTIVITY(LOCATABLE):
    """openEHR RM type: ACTIVITY."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "ACTIVITY"
    description: "ITEM_STRUCTURE"
    timing: Optional["DV_PARSABLE"] = Field(default=None)
    action_archetype_id: str


class ACTION(CARE_ENTRY):
    """openEHR RM type: ACTION."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "ACTION"
    time: "DV_DATE_TIME"
    description: "ITEM_STRUCTURE"
    ism_transition: "ISM_TRANSITION"
    instruction_details: Optional["INSTRUCTION_DETAILS"] = Field(default=None)


class INSTRUCTION_DETAILS(PATHABLE):
    """openEHR RM type: INSTRUCTION_DETAILS."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "INSTRUCTION_DETAILS"
    instruction_id: "LOCATABLE_REF"
    wf_details: Optional["ITEM_STRUCTURE"] = Field(default=None)
    activity_id: str


class ISM_TRANSITION(PATHABLE):
    """openEHR RM type: ISM_TRANSITION."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "ISM_TRANSITION"
    current_state: "DV_CODED_TEXT"
    transition: Optional["DV_CODED_TEXT"] = Field(default=None)
    careflow_step: Optional["DV_CODED_TEXT"] = Field(default=None)
    reason: Optional[list["DV_TEXT"]] = Field(default=None)


class GENERIC_ENTRY(CONTENT_ITEM):
    """openEHR RM type: GENERIC_ENTRY."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "GENERIC_ENTRY"
    data: "ITEM_TREE"


class DATA_STRUCTURE(LOCATABLE):
    """openEHR RM type: DATA_STRUCTURE."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "DATA_STRUCTURE"


class ITEM_STRUCTURE(DATA_STRUCTURE):
    """openEHR RM type: ITEM_STRUCTURE."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "ITEM_STRUCTURE"


class ITEM_SINGLE(ITEM_STRUCTURE):
    """openEHR RM type: ITEM_SINGLE."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "ITEM_SINGLE"
    item: "ELEMENT"


class ITEM_LIST(ITEM_STRUCTURE):
    """openEHR RM type: ITEM_LIST."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "ITEM_LIST"
    items: Optional[list["ELEMENT"]] = Field(default=None)


class ITEM_TABLE(ITEM_STRUCTURE):
    """openEHR RM type: ITEM_TABLE."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "ITEM_TABLE"
    rows: Optional[list["CLUSTER"]] = Field(default=None)


class ITEM_TREE(ITEM_STRUCTURE):
    """openEHR RM type: ITEM_TREE."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "ITEM_TREE"
    items: Optional[list["ITEM"]] = Field(default=None)


class ITEM(LOCATABLE):
    """openEHR RM type: ITEM."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "ITEM"


class CLUSTER(ITEM):
    """openEHR RM type: CLUSTER."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "CLUSTER"
    items: list["ITEM"]


class ELEMENT(ITEM):
    """openEHR RM type: ELEMENT."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "ELEMENT"
    null_flavour: Optional["DV_CODED_TEXT"] = Field(default=None)
    value: Optional["DATA_VALUE"] = Field(default=None)


class HISTORY(DATA_STRUCTURE):
    """openEHR RM type: HISTORY."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "HISTORY"
    origin: "DV_DATE_TIME"
    period: Optional["DV_DURATION"] = Field(default=None)
    duration: Optional["DV_DURATION"] = Field(default=None)
    summary: Optional["ITEM_STRUCTURE"] = Field(default=None)
    events: Optional[list["EVENT"]] = Field(default=None)


class EVENT(LOCATABLE):
    """openEHR RM type: EVENT."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "EVENT"
    time: "DV_DATE_TIME"
    state: Optional["ITEM_STRUCTURE"] = Field(default=None)
    data: Any
    offset: Optional["DV_DURATION"] = Field(default=None)


class POINT_EVENT(EVENT):
    """openEHR RM type: POINT_EVENT."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "POINT_EVENT"
    pass


class INTERVAL_EVENT(EVENT):
    """openEHR RM type: INTERVAL_EVENT."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "INTERVAL_EVENT"
    width: "DV_DURATION"
    sample_count: int | None = Field(default=None)
    math_function: "DV_CODED_TEXT"


class REVISION_HISTORY(BaseModel):
    """openEHR RM type: REVISION_HISTORY."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "REVISION_HISTORY"
    items: list["REVISION_HISTORY_ITEM"]


class REVISION_HISTORY_ITEM(BaseModel):
    """openEHR RM type: REVISION_HISTORY_ITEM."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "REVISION_HISTORY_ITEM"
    version_id: "OBJECT_VERSION_ID"
    audits: list["AUDIT_DETAILS"]


class AUDIT_DETAILS(BaseModel):
    """openEHR RM type: AUDIT_DETAILS."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "AUDIT_DETAILS"
    system_id: str
    time_committed: "DV_DATE_TIME"
    change_type: "DV_CODED_TEXT"
    description: Optional["DV_TEXT"] = Field(default=None)
    committer: "PARTY_PROXY"


class ATTESTATION(AUDIT_DETAILS):
    """openEHR RM type: ATTESTATION."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "ATTESTATION"
    attested_view: Optional["DV_MULTIMEDIA"] = Field(default=None)
    proof: str | None = Field(default=None)
    items: Optional[list["DV_EHR_URI"]] = Field(default=None)
    reason: "DV_TEXT"
    is_pending: bool


class PARTICIPATION(BaseModel):
    """openEHR RM type: PARTICIPATION."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "PARTICIPATION"
    function: "DV_TEXT"
    time: Optional["DV_INTERVAL"] = Field(default=None)
    mode: Optional["DV_CODED_TEXT"] = Field(default=None)
    performer: "PARTY_PROXY"


class PARTY_PROXY(BaseModel):
    """openEHR RM type: PARTY_PROXY."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "PARTY_PROXY"
    external_ref: Optional["PARTY_REF"] = Field(default=None)


class PARTY_IDENTIFIED(PARTY_PROXY):
    """openEHR RM type: PARTY_IDENTIFIED."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "PARTY_IDENTIFIED"
    name: str | None = Field(default=None)
    identifiers: Optional[list["DV_IDENTIFIER"]] = Field(default=None)


class PARTY_RELATED(PARTY_IDENTIFIED):
    """openEHR RM type: PARTY_RELATED."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "PARTY_RELATED"
    relationship: "DV_CODED_TEXT"


class PARTY_SELF(PARTY_PROXY):
    """openEHR RM type: PARTY_SELF."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "PARTY_SELF"
    pass


class LINK(BaseModel):
    """openEHR RM type: LINK."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "LINK"
    meaning: "DV_TEXT"
    type: "DV_TEXT"
    target: "DV_EHR_URI"


class ARCHETYPED(BaseModel):
    """openEHR RM type: ARCHETYPED."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "ARCHETYPED"
    archetype_id: "ARCHETYPE_ID"
    template_id: Optional["TEMPLATE_ID"] = Field(default=None)
    rm_version: str


class FEEDER_AUDIT(BaseModel):
    """openEHR RM type: FEEDER_AUDIT."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "FEEDER_AUDIT"
    originating_system_item_ids: Optional[list["DV_IDENTIFIER"]] = Field(default=None)
    feeder_system_item_ids: Optional[list["DV_IDENTIFIER"]] = Field(default=None)
    original_content: Optional["DV_ENCAPSULATED"] = Field(default=None)
    originating_system_audit: "FEEDER_AUDIT_DETAILS"
    feeder_system_audit: Optional["FEEDER_AUDIT_DETAILS"] = Field(default=None)


class FEEDER_AUDIT_DETAILS(BaseModel):
    """openEHR RM type: FEEDER_AUDIT_DETAILS."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "FEEDER_AUDIT_DETAILS"
    system_id: str
    location: Optional["PARTY_IDENTIFIED"] = Field(default=None)
    provider: Optional["PARTY_IDENTIFIED"] = Field(default=None)
    subject: Optional["PARTY_PROXY"] = Field(default=None)
    time: Optional["DV_DATE_TIME"] = Field(default=None)
    version_id: str | None = Field(default=None)


class FOLDER(LOCATABLE):
    """openEHR RM type: FOLDER."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "FOLDER"
    folders: Optional[list["FOLDER"]] = Field(default=None)
    items: Optional[list["OBJECT_REF"]] = Field(default=None)


class CONTRIBUTION(BaseModel):
    """openEHR RM type: CONTRIBUTION."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "CONTRIBUTION"
    uid: "HIER_OBJECT_ID"
    audit: "AUDIT_DETAILS"
    versions: list["OBJECT_REF"]


class VERSIONED_OBJECT(BaseModel):
    """openEHR RM type: VERSIONED_OBJECT."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "VERSIONED_OBJECT"
    uid: "HIER_OBJECT_ID"
    owner_id: "OBJECT_REF"
    time_created: "DV_DATE_TIME"


class VERSION(BaseModel):
    """openEHR RM type: VERSION."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "VERSION"
    contribution: "OBJECT_REF"
    commit_audit: "AUDIT_DETAILS"
    signature: str | None = Field(default=None)


class ORIGINAL_VERSION(VERSION):
    """openEHR RM type: ORIGINAL_VERSION."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "ORIGINAL_VERSION"
    uid: "OBJECT_VERSION_ID"
    preceding_version_uid: Optional["OBJECT_VERSION_ID"] = Field(default=None)
    other_input_version_uids: Optional[list["OBJECT_VERSION_ID"]] = Field(default=None)
    attestations: Optional[list["ATTESTATION"]] = Field(default=None)
    lifecycle_state: "DV_CODED_TEXT"
    data: Any | None = Field(default=None)


class IMPORTED_VERSION(VERSION):
    """openEHR RM type: IMPORTED_VERSION."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "IMPORTED_VERSION"
    item: "ORIGINAL_VERSION"


class DATA_VALUE(BaseModel):
    """openEHR RM type: DATA_VALUE."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "DATA_VALUE"


class DV_BOOLEAN(DATA_VALUE):
    """openEHR RM type: DV_BOOLEAN."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "DV_BOOLEAN"
    value: bool


class DV_IDENTIFIER(DATA_VALUE):
    """openEHR RM type: DV_IDENTIFIER."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "DV_IDENTIFIER"
    issuer: str | None = Field(default=None)
    id: str
    type: str | None = Field(default=None)
    assigner: str | None = Field(default=None)


class DV_STATE(DATA_VALUE):
    """openEHR RM type: DV_STATE."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "DV_STATE"
    value: "DV_CODED_TEXT"
    is_terminal: bool


class TERM_MAPPING(BaseModel):
    """openEHR RM type: TERM_MAPPING."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "TERM_MAPPING"
    match: str
    purpose: Optional["DV_CODED_TEXT"] = Field(default=None)
    target: "CODE_PHRASE"


class DV_TEXT(DATA_VALUE):
    """openEHR RM type: DV_TEXT."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "DV_TEXT"
    value: str
    hyperlink: Optional["DV_URI"] = Field(default=None)
    language: Optional["CODE_PHRASE"] = Field(default=None)
    encoding: Optional["CODE_PHRASE"] = Field(default=None)
    formatting: str | None = Field(default=None)
    mappings: Optional[list["TERM_MAPPING"]] = Field(default=None)


class DV_CODED_TEXT(DV_TEXT):
    """openEHR RM type: DV_CODED_TEXT."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "DV_CODED_TEXT"
    defining_code: "CODE_PHRASE"


class CODE_PHRASE(BaseModel):
    """openEHR RM type: CODE_PHRASE."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "CODE_PHRASE"
    terminology_id: "TERMINOLOGY_ID"
    code_string: str


class DV_PARAGRAPH(DATA_VALUE):
    """openEHR RM type: DV_PARAGRAPH."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "DV_PARAGRAPH"
    items: list["DV_TEXT"]


class DV_INTERVAL(DATA_VALUE):
    """openEHR RM type: DV_INTERVAL."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "DV_INTERVAL"
    pass


class REFERENCE_RANGE(BaseModel):
    """openEHR RM type: REFERENCE_RANGE."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "REFERENCE_RANGE"
    range: "DV_INTERVAL"
    meaning: "DV_TEXT"


class DV_ORDERED(DATA_VALUE):
    """openEHR RM type: DV_ORDERED."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "DV_ORDERED"
    normal_status: Optional["CODE_PHRASE"] = Field(default=None)
    normal_range: Optional["DV_INTERVAL"] = Field(default=None)
    other_reference_ranges: Optional[list["REFERENCE_RANGE"]] = Field(default=None)


class DV_QUANTIFIED(DV_ORDERED):
    """openEHR RM type: DV_QUANTIFIED."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "DV_QUANTIFIED"
    magnitude_status: str | None = Field(default=None)
    accuracy: Any | None = Field(default=None)


class DV_ORDINAL(DV_ORDERED):
    """openEHR RM type: DV_ORDINAL."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "DV_ORDINAL"
    value: int
    symbol: "DV_CODED_TEXT"


class DV_AMOUNT(DV_QUANTIFIED):
    """openEHR RM type: DV_AMOUNT."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "DV_AMOUNT"
    accuracy: float | None = Field(default=None)
    accuracy_is_percent: bool | None = Field(default=None)


class DV_ABSOLUTE_QUANTITY(DV_QUANTIFIED):
    """openEHR RM type: DV_ABSOLUTE_QUANTITY."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "DV_ABSOLUTE_QUANTITY"
    accuracy: Optional["DV_AMOUNT"] = Field(default=None)


class DV_QUANTITY(DV_AMOUNT):
    """openEHR RM type: DV_QUANTITY."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "DV_QUANTITY"
    magnitude: float
    property: "CODE_PHRASE"
    units: str
    precision: int | None = Field(default=None)
    normal_range: Optional["DV_INTERVAL"] = Field(default=None)
    other_reference_ranges: Optional[list["REFERENCE_RANGE"]] = Field(default=None)


class DV_COUNT(DV_AMOUNT):
    """openEHR RM type: DV_COUNT."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "DV_COUNT"
    magnitude: int
    normal_range: Optional["DV_INTERVAL"] = Field(default=None)
    other_reference_ranges: Optional[list["REFERENCE_RANGE"]] = Field(default=None)


class DV_PROPORTION(DV_AMOUNT):
    """openEHR RM type: DV_PROPORTION."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "DV_PROPORTION"
    numerator: float
    denominator: float
    type: "PROPORTION_KIND"
    precision: int | None = Field(default=None)
    is_integral: bool | None = Field(default=None)
    normal_range: Optional["DV_INTERVAL"] = Field(default=None)
    other_reference_ranges: Optional[list["REFERENCE_RANGE"]] = Field(default=None)


class PROPORTION_KIND(BaseModel):
    """openEHR RM type: PROPORTION_KIND."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "PROPORTION_KIND"
    pass


class DV_TEMPORAL(DV_ABSOLUTE_QUANTITY):
    """openEHR RM type: DV_TEMPORAL."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "DV_TEMPORAL"
    accuracy: Optional["DV_DURATION"] = Field(default=None)


class DV_DATE(DV_TEMPORAL):
    """openEHR RM type: DV_DATE."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "DV_DATE"
    value: str


class DV_TIME(DV_TEMPORAL):
    """openEHR RM type: DV_TIME."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "DV_TIME"
    value: str


class DV_DATE_TIME(DV_TEMPORAL):
    """openEHR RM type: DV_DATE_TIME."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "DV_DATE_TIME"
    value: str


class DV_DURATION(DV_AMOUNT):
    """openEHR RM type: DV_DURATION."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "DV_DURATION"
    value: str


class DV_ENCAPSULATED(DATA_VALUE):
    """openEHR RM type: DV_ENCAPSULATED."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "DV_ENCAPSULATED"
    charset: Optional["CODE_PHRASE"] = Field(default=None)
    language: Optional["CODE_PHRASE"] = Field(default=None)


class DV_MULTIMEDIA(DV_ENCAPSULATED):
    """openEHR RM type: DV_MULTIMEDIA."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "DV_MULTIMEDIA"
    alternate_text: str | None = Field(default=None)
    uri: Optional["DV_URI"] = Field(default=None)
    data: Optional[list[bytes]] = Field(default=None)
    media_type: "CODE_PHRASE"
    compression_algorithm: Optional["CODE_PHRASE"] = Field(default=None)
    integrity_check: Optional[list[bytes]] = Field(default=None)
    integrity_check_algorithm: Optional["CODE_PHRASE"] = Field(default=None)
    thumbnail: Optional["DV_MULTIMEDIA"] = Field(default=None)
    size: int


class DV_PARSABLE(DV_ENCAPSULATED):
    """openEHR RM type: DV_PARSABLE."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "DV_PARSABLE"
    value: str
    formalism: str


class DV_URI(DATA_VALUE):
    """openEHR RM type: DV_URI."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "DV_URI"
    value: str


class DV_EHR_URI(DV_URI):
    """openEHR RM type: DV_EHR_URI."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "DV_EHR_URI"
    pass


class DV_TIME_SPECIFICATION(DATA_VALUE):
    """openEHR RM type: DV_TIME_SPECIFICATION."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "DV_TIME_SPECIFICATION"
    value: "DV_PARSABLE"


class DV_PERIODIC_TIME_SPECIFICATION(DV_TIME_SPECIFICATION):
    """openEHR RM type: DV_PERIODIC_TIME_SPECIFICATION."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "DV_PERIODIC_TIME_SPECIFICATION"
    pass


class DV_GENERAL_TIME_SPECIFICATION(DV_TIME_SPECIFICATION):
    """openEHR RM type: DV_GENERAL_TIME_SPECIFICATION."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "DV_GENERAL_TIME_SPECIFICATION"
    pass


class OBJECT_REF(BaseModel):
    """openEHR RM type: OBJECT_REF."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "OBJECT_REF"
    id: "OBJECT_ID"
    namespace: str
    type: str


class LOCATABLE_REF(OBJECT_REF):
    """openEHR RM type: LOCATABLE_REF."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "LOCATABLE_REF"
    id: "UID_BASED_ID"
    path: str | None = Field(default=None)


class PARTY_REF(OBJECT_REF):
    """openEHR RM type: PARTY_REF."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "PARTY_REF"
    pass


class ACCESS_GROUP_REF(OBJECT_REF):
    """openEHR RM type: ACCESS_GROUP_REF."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "ACCESS_GROUP_REF"
    pass


class OBJECT_ID(BaseModel):
    """openEHR RM type: OBJECT_ID."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "OBJECT_ID"
    value: str


class TERMINOLOGY_ID(OBJECT_ID):
    """openEHR RM type: TERMINOLOGY_ID."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "TERMINOLOGY_ID"
    pass


class UID_BASED_ID(OBJECT_ID):
    """openEHR RM type: UID_BASED_ID."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "UID_BASED_ID"


class GENERIC_ID(OBJECT_ID):
    """openEHR RM type: GENERIC_ID."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "GENERIC_ID"
    scheme: str


class ARCHETYPE_ID(OBJECT_ID):
    """openEHR RM type: ARCHETYPE_ID."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "ARCHETYPE_ID"
    pass


class ARCHETYPE_HRID(BaseModel):
    """openEHR RM type: ARCHETYPE_HRID."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "ARCHETYPE_HRID"
    namespace: str
    rm_publisher: str
    rm_package: str
    rm_class: str
    concept_id: str
    release_version: str
    version_status: "VERSION_STATUS"
    build_count: str


class TEMPLATE_ID(OBJECT_ID):
    """openEHR RM type: TEMPLATE_ID."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "TEMPLATE_ID"
    pass


class OBJECT_VERSION_ID(UID_BASED_ID):
    """openEHR RM type: OBJECT_VERSION_ID."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "OBJECT_VERSION_ID"
    pass


class HIER_OBJECT_ID(UID_BASED_ID):
    """openEHR RM type: HIER_OBJECT_ID."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "HIER_OBJECT_ID"
    pass


class VERSION_TREE_ID(BaseModel):
    """openEHR RM type: VERSION_TREE_ID."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "VERSION_TREE_ID"
    value: str


class UID(BaseModel):
    """openEHR RM type: UID."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "UID"
    value: str


class INTERNET_ID(UID):
    """openEHR RM type: INTERNET_ID."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "INTERNET_ID"
    pass


class UUID(UID):
    """openEHR RM type: UUID."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "UUID"
    pass


class ISO_OID(UID):
    """openEHR RM type: ISO_OID."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "ISO_OID"
    pass


class VALIDITY_KIND(BaseModel):
    """openEHR RM type: VALIDITY_KIND."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "VALIDITY_KIND"
    pass


class VERSION_STATUS(BaseModel):
    """openEHR RM type: VERSION_STATUS."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "VERSION_STATUS"
    pass


class AUTHORED_RESOURCE(BaseModel):
    """openEHR RM type: AUTHORED_RESOURCE."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "AUTHORED_RESOURCE"
    original_language: Any
    is_controlled: bool | None = Field(default=None)
    translations: Optional[list["TRANSLATION_DETAILS"]] = Field(default=None)
    description: Optional["RESOURCE_DESCRIPTION"] = Field(default=None)


class TRANSLATION_DETAILS(BaseModel):
    """openEHR RM type: TRANSLATION_DETAILS."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "TRANSLATION_DETAILS"
    language: Any
    author: Any
    accreditation: str | None = Field(default=None)
    other_details: Any | None = Field(default=None)


class RESOURCE_DESCRIPTION(BaseModel):
    """openEHR RM type: RESOURCE_DESCRIPTION."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "RESOURCE_DESCRIPTION"
    original_author: Any
    other_contributors: Optional[list[str]] = Field(default=None)
    lifecycle_state: str
    resource_package_uri: str | None = Field(default=None)
    other_details: Any | None = Field(default=None)
    parent_resource: "AUTHORED_RESOURCE"
    details: list["RESOURCE_DESCRIPTION_ITEM"]


class RESOURCE_DESCRIPTION_ITEM(BaseModel):
    """openEHR RM type: RESOURCE_DESCRIPTION_ITEM."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    _type_: ClassVar[str] = "RESOURCE_DESCRIPTION_ITEM"
    language: Any
    purpose: str
    keywords: Optional[list[str]] = Field(default=None)
    use: str | None = Field(default=None)
    misuse: str | None = Field(default=None)
    copyright: str | None = Field(default=None)
    original_resource_uri: Optional[list[Any]] = Field(default=None)
    other_details: Any


