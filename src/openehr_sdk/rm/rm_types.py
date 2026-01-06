"""
Generated Pydantic models for openEHR Reference Model 1.1.0.

Auto-generated from specifications-ITS-JSON.
DO NOT EDIT MANUALLY.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

# RM 1.1.0 Types


class ACTION(BaseModel):
    """ACTION."""

    type: str = Field(default="ACTION", alias="_type")
    uid: Optional[Any] = None
    archetype_node_id: str
    name: Optional[Any]
    archetype_details: Optional["ARCHETYPED"] = None
    feeder_audit: Optional["FEEDER_AUDIT"] = None
    links: Optional[list["LINK"]] = None
    language: Optional["CODE_PHRASE"]
    encoding: Optional["CODE_PHRASE"]
    subject: Optional[Any]
    provider: Optional[Any] = None
    other_participations: Optional[list["PARTICIPATION"]] = None
    workflow_id: Optional[Any] = None
    protocol: Optional[Any] = None
    guideline_id: Optional[Any] = None
    time: Optional["DV_DATE_TIME"]
    description: Optional[Any]
    ism_transition: Optional["ISM_TRANSITION"]
    instruction_details: Optional["INSTRUCTION_DETAILS"] = None

    model_config = ConfigDict(populate_by_name=True)


class ACTIVITY(BaseModel):
    """ACTIVITY."""

    type: str = Field(default="ACTIVITY", alias="_type")
    uid: Optional[Any] = None
    archetype_node_id: str
    name: Optional[Any]
    archetype_details: Optional["ARCHETYPED"] = None
    feeder_audit: Optional["FEEDER_AUDIT"] = None
    links: Optional[list["LINK"]] = None
    description: Optional[Any]
    timing: Optional["DV_PARSABLE"] = None
    action_archetype_id: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class ADDRESS(BaseModel):
    """ADDRESS."""

    type: str = Field(default="ADDRESS", alias="_type")
    uid: Optional[Any] = None
    archetype_node_id: str
    name: Optional[Any]
    archetype_details: Optional["ARCHETYPED"] = None
    feeder_audit: Optional["FEEDER_AUDIT"] = None
    links: Optional[list["LINK"]] = None
    details: Optional[Any]

    model_config = ConfigDict(populate_by_name=True)


class ADDRESSED_MESSAGE(BaseModel):
    """ADDRESSED_MESSAGE."""

    type: str = Field(default="ADDRESSED_MESSAGE", alias="_type")
    sender: str
    sender_reference: str
    addressees: Optional[list] = None
    urgency: Optional[int] = None
    message: Optional["MESSAGE"] = None

    model_config = ConfigDict(populate_by_name=True)


class ADMIN_ENTRY(BaseModel):
    """ADMIN_ENTRY."""

    type: str = Field(default="ADMIN_ENTRY", alias="_type")
    uid: Optional[Any] = None
    archetype_node_id: str
    name: Optional[Any]
    archetype_details: Optional["ARCHETYPED"] = None
    feeder_audit: Optional["FEEDER_AUDIT"] = None
    links: Optional[list["LINK"]] = None
    language: Optional["CODE_PHRASE"]
    encoding: Optional["CODE_PHRASE"]
    subject: Optional[Any]
    provider: Optional[Any] = None
    other_participations: Optional[list["PARTICIPATION"]] = None
    workflow_id: Optional[Any] = None
    data: Optional[Any]

    model_config = ConfigDict(populate_by_name=True)


class AGENT(BaseModel):
    """AGENT."""

    type: str = Field(default="AGENT", alias="_type")
    uid: Optional[Any]
    archetype_node_id: str
    name: Optional[Any]
    archetype_details: Optional["ARCHETYPED"] = None
    feeder_audit: Optional["FEEDER_AUDIT"] = None
    links: Optional[list["LINK"]] = None
    details: Optional[Any] = None
    identities: Optional[list["PARTY_IDENTITY"]]
    contacts: Optional[list["CONTACT"]] = None
    relationships: Optional[list["PARTY_RELATIONSHIP"]] = None
    reverse_relationships: Optional[list["LOCATABLE_REF"]] = None
    roles: Optional[list["PARTY_REF"]] = None
    languages: Optional[list] = None

    model_config = ConfigDict(populate_by_name=True)


class ARCHETYPED(BaseModel):
    """ARCHETYPED."""

    type: str = Field(default="ARCHETYPED", alias="_type")
    archetype_id: Optional["ARCHETYPE_ID"]
    template_id: Optional["TEMPLATE_ID"] = None
    rm_version: str

    model_config = ConfigDict(populate_by_name=True)


class ATTESTATION(BaseModel):
    """ATTESTATION."""

    type: str = Field(default="ATTESTATION", alias="_type")
    system_id: str
    time_committed: Optional["DV_DATE_TIME"]
    change_type: Optional["DV_CODED_TEXT"]
    description: Optional[Any] = None
    committer: Optional[Any]
    attested_view: Optional["DV_MULTIMEDIA"] = None
    proof: Optional[str] = None
    items: Optional[list["DV_EHR_URI"]] = None
    reason: Optional[Any]
    is_pending: bool

    model_config = ConfigDict(populate_by_name=True)


class AUDIT_DETAILS(BaseModel):
    """AUDIT_DETAILS."""

    type: str = Field(default="AUDIT_DETAILS", alias="_type")
    system_id: str
    time_committed: Optional["DV_DATE_TIME"]
    change_type: Optional["DV_CODED_TEXT"]
    description: Optional[Any] = None
    committer: Optional[Any]

    model_config = ConfigDict(populate_by_name=True)


class CAPABILITY(BaseModel):
    """CAPABILITY."""

    type: str = Field(default="CAPABILITY", alias="_type")
    uid: Optional[Any] = None
    archetype_node_id: str
    name: Optional[Any]
    archetype_details: Optional["ARCHETYPED"] = None
    feeder_audit: Optional["FEEDER_AUDIT"] = None
    links: Optional[list["LINK"]] = None
    credentials: Optional[Any]
    time_validity: Optional["DV_INTERVAL"] = None

    model_config = ConfigDict(populate_by_name=True)


class CLUSTER(BaseModel):
    """CLUSTER."""

    type: str = Field(default="CLUSTER", alias="_type")
    uid: Optional[Any] = None
    archetype_node_id: str
    name: Optional[Any]
    archetype_details: Optional["ARCHETYPED"] = None
    feeder_audit: Optional["FEEDER_AUDIT"] = None
    links: Optional[list["LINK"]] = None
    items: list

    model_config = ConfigDict(populate_by_name=True)


class CODE_PHRASE(BaseModel):
    """CODE_PHRASE."""

    type: str = Field(default="CODE_PHRASE", alias="_type")
    terminology_id: Optional["TERMINOLOGY_ID"]
    code_string: str
    preferred_term: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class COMPOSITION(BaseModel):
    """COMPOSITION."""

    type: str = Field(default="COMPOSITION", alias="_type")
    uid: Optional[Any] = None
    archetype_node_id: str
    name: Optional[Any]
    archetype_details: Optional["ARCHETYPED"] = None
    feeder_audit: Optional["FEEDER_AUDIT"] = None
    links: Optional[list["LINK"]] = None
    language: Optional["CODE_PHRASE"]
    territory: Optional["CODE_PHRASE"]
    category: Optional["DV_CODED_TEXT"]
    composer: Optional[Any]
    context: Optional["EVENT_CONTEXT"] = None
    content: Optional[list] = None

    model_config = ConfigDict(populate_by_name=True)


class CONTACT(BaseModel):
    """CONTACT."""

    type: str = Field(default="CONTACT", alias="_type")
    uid: Optional[Any] = None
    archetype_node_id: str
    name: Optional[Any]
    archetype_details: Optional["ARCHETYPED"] = None
    feeder_audit: Optional["FEEDER_AUDIT"] = None
    links: Optional[list["LINK"]] = None
    time_validity: Optional["DV_INTERVAL"] = None
    addresses: Optional[list["ADDRESS"]] = None

    model_config = ConfigDict(populate_by_name=True)


class CONTRIBUTION(BaseModel):
    """CONTRIBUTION."""

    type: str = Field(default="CONTRIBUTION", alias="_type")
    uid: Optional["HIER_OBJECT_ID"]
    audit: Optional[Any]
    versions: list

    model_config = ConfigDict(populate_by_name=True)


class DV_BOOLEAN(BaseModel):
    """DV_BOOLEAN."""

    type: str = Field(default="DV_BOOLEAN", alias="_type")
    value: bool

    model_config = ConfigDict(populate_by_name=True)


class DV_CODED_TEXT(BaseModel):
    """DV_CODED_TEXT."""

    type: str = Field(default="DV_CODED_TEXT", alias="_type")
    value: str
    hyperlink: Optional[Any] = None
    language: Optional["CODE_PHRASE"] = None
    encoding: Optional["CODE_PHRASE"] = None
    formatting: Optional[str] = None
    mappings: Optional[list["TERM_MAPPING"]] = None
    defining_code: Optional["CODE_PHRASE"]

    model_config = ConfigDict(populate_by_name=True)


class DV_COUNT(BaseModel):
    """DV_COUNT."""

    type: str = Field(default="DV_COUNT", alias="_type")
    normal_status: Optional["CODE_PHRASE"] = None
    normal_range: Optional["DV_INTERVAL"] = None
    other_reference_ranges: Optional[list["REFERENCE_RANGE"]] = None
    magnitude_status: Optional[str] = None
    accuracy: Optional[float] = None
    accuracy_is_percent: Optional[bool] = None
    magnitude: int

    model_config = ConfigDict(populate_by_name=True)


class DV_DATE(BaseModel):
    """DV_DATE."""

    type: str = Field(default="DV_DATE", alias="_type")
    normal_status: Optional["CODE_PHRASE"] = None
    normal_range: Optional["DV_INTERVAL"] = None
    other_reference_ranges: Optional[list["REFERENCE_RANGE"]] = None
    magnitude_status: Optional[str] = None
    accuracy: Optional["DV_DURATION"] = None
    value: str

    model_config = ConfigDict(populate_by_name=True)


class DV_DATE_TIME(BaseModel):
    """DV_DATE_TIME."""

    type: str = Field(default="DV_DATE_TIME", alias="_type")
    normal_status: Optional["CODE_PHRASE"] = None
    normal_range: Optional["DV_INTERVAL"] = None
    other_reference_ranges: Optional[list["REFERENCE_RANGE"]] = None
    magnitude_status: Optional[str] = None
    accuracy: Optional["DV_DURATION"] = None
    value: str

    model_config = ConfigDict(populate_by_name=True)


class DV_DURATION(BaseModel):
    """DV_DURATION."""

    type: str = Field(default="DV_DURATION", alias="_type")
    normal_status: Optional["CODE_PHRASE"] = None
    normal_range: Optional["DV_INTERVAL"] = None
    other_reference_ranges: Optional[list["REFERENCE_RANGE"]] = None
    magnitude_status: Optional[str] = None
    accuracy: Optional[float] = None
    accuracy_is_percent: Optional[bool] = None
    value: str

    model_config = ConfigDict(populate_by_name=True)


class DV_EHR_URI(BaseModel):
    """DV_EHR_URI."""

    type: str = Field(default="DV_EHR_URI", alias="_type")
    value: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class DV_GENERAL_TIME_SPECIFICATION(BaseModel):
    """DV_GENERAL_TIME_SPECIFICATION."""

    type: str = Field(default="DV_GENERAL_TIME_SPECIFICATION", alias="_type")
    value: Optional["DV_PARSABLE"]

    model_config = ConfigDict(populate_by_name=True)


class DV_IDENTIFIER(BaseModel):
    """DV_IDENTIFIER."""

    type: str = Field(default="DV_IDENTIFIER", alias="_type")
    issuer: Optional[str] = None
    id: str
    type: Optional[str] = None
    assigner: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class DV_INTERVAL(BaseModel):
    """DV_INTERVAL."""

    type: str = Field(default="DV_INTERVAL", alias="_type")
    lower_unbounded: bool
    upper_unbounded: bool
    lower_included: bool
    upper_included: bool

    model_config = ConfigDict(populate_by_name=True)


class DV_MULTIMEDIA(BaseModel):
    """DV_MULTIMEDIA."""

    type: str = Field(default="DV_MULTIMEDIA", alias="_type")
    charset: Optional["CODE_PHRASE"] = None
    language: Optional["CODE_PHRASE"] = None
    alternate_text: Optional[str] = None
    uri: Optional[Any] = None
    data: Optional[str] = None
    media_type: Optional["CODE_PHRASE"]
    compression_algorithm: Optional["CODE_PHRASE"] = None
    integrity_check: Optional[str] = None
    integrity_check_algorithm: Optional["CODE_PHRASE"] = None
    thumbnail: Optional["DV_MULTIMEDIA"] = None
    size: int

    model_config = ConfigDict(populate_by_name=True)


class DV_ORDINAL(BaseModel):
    """DV_ORDINAL."""

    type: str = Field(default="DV_ORDINAL", alias="_type")
    normal_status: Optional["CODE_PHRASE"] = None
    normal_range: Optional["DV_INTERVAL"] = None
    other_reference_ranges: Optional[list["REFERENCE_RANGE"]] = None
    value: int
    symbol: Optional["DV_CODED_TEXT"]

    model_config = ConfigDict(populate_by_name=True)


class DV_PARAGRAPH(BaseModel):
    """DV_PARAGRAPH."""

    type: str = Field(default="DV_PARAGRAPH", alias="_type")
    items: list

    model_config = ConfigDict(populate_by_name=True)


class DV_PARSABLE(BaseModel):
    """DV_PARSABLE."""

    type: str = Field(default="DV_PARSABLE", alias="_type")
    charset: Optional["CODE_PHRASE"] = None
    language: Optional["CODE_PHRASE"] = None
    value: str
    formalism: str

    model_config = ConfigDict(populate_by_name=True)


class DV_PERIODIC_TIME_SPECIFICATION(BaseModel):
    """DV_PERIODIC_TIME_SPECIFICATION."""

    type: str = Field(default="DV_PERIODIC_TIME_SPECIFICATION", alias="_type")
    value: Optional["DV_PARSABLE"]

    model_config = ConfigDict(populate_by_name=True)


class DV_PROPORTION(BaseModel):
    """DV_PROPORTION."""

    type: str = Field(default="DV_PROPORTION", alias="_type")
    normal_status: Optional["CODE_PHRASE"] = None
    normal_range: Optional["DV_INTERVAL"] = None
    other_reference_ranges: Optional[list["REFERENCE_RANGE"]] = None
    magnitude_status: Optional[str] = None
    accuracy: Optional[float] = None
    accuracy_is_percent: Optional[bool] = None
    numerator: float
    denominator: float
    type: int
    precision: Optional[int] = None

    model_config = ConfigDict(populate_by_name=True)


class DV_QUANTITY(BaseModel):
    """DV_QUANTITY."""

    type: str = Field(default="DV_QUANTITY", alias="_type")
    normal_status: Optional["CODE_PHRASE"] = None
    normal_range: Optional["DV_INTERVAL"] = None
    other_reference_ranges: Optional[list["REFERENCE_RANGE"]] = None
    magnitude_status: Optional[str] = None
    accuracy: Optional[float] = None
    accuracy_is_percent: Optional[bool] = None
    magnitude: float
    property: Optional["CODE_PHRASE"] = None
    units: str
    units_system: Optional[str] = None
    units_display_name: Optional[str] = None
    precision: Optional[int] = None

    model_config = ConfigDict(populate_by_name=True)


class DV_SCALE(BaseModel):
    """DV_SCALE - New in RM 1.1.0.

    Data type for scales/scores with decimal values.
    Extends DV_ORDINAL for non-integer scale values.
    """

    type: str = Field(default="DV_SCALE", alias="_type")
    normal_status: Optional["CODE_PHRASE"] = None
    normal_range: Optional["DV_INTERVAL"] = None
    other_reference_ranges: Optional[list["REFERENCE_RANGE"]] = None
    value: float
    symbol: Optional["DV_CODED_TEXT"]

    model_config = ConfigDict(populate_by_name=True)


class DV_STATE(BaseModel):
    """DV_STATE."""

    type: str = Field(default="DV_STATE", alias="_type")
    value: Optional["DV_CODED_TEXT"]
    is_terminal: bool

    model_config = ConfigDict(populate_by_name=True)


class DV_TEXT(BaseModel):
    """DV_TEXT."""

    type: str = Field(default="DV_TEXT", alias="_type")
    value: str
    hyperlink: Optional[Any] = None
    language: Optional["CODE_PHRASE"] = None
    encoding: Optional["CODE_PHRASE"] = None
    formatting: Optional[str] = None
    mappings: Optional[list["TERM_MAPPING"]] = None

    model_config = ConfigDict(populate_by_name=True)


class DV_TIME(BaseModel):
    """DV_TIME."""

    type: str = Field(default="DV_TIME", alias="_type")
    normal_status: Optional["CODE_PHRASE"] = None
    normal_range: Optional["DV_INTERVAL"] = None
    other_reference_ranges: Optional[list["REFERENCE_RANGE"]] = None
    magnitude_status: Optional[str] = None
    accuracy: Optional["DV_DURATION"] = None
    value: str

    model_config = ConfigDict(populate_by_name=True)


class DV_URI(BaseModel):
    """DV_URI."""

    type: str = Field(default="DV_URI", alias="_type")
    value: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class EHR(BaseModel):
    """EHR."""

    type: str = Field(default="EHR", alias="_type")
    system_id: Optional["HIER_OBJECT_ID"]
    ehr_id: Optional["HIER_OBJECT_ID"]
    time_created: Optional["DV_DATE_TIME"]
    ehr_access: Optional[Any]
    ehr_status: Optional[Any]
    directory: Optional[Any] = None
    folders: Optional[list] = None
    compositions: Optional[list] = None
    contributions: list

    model_config = ConfigDict(populate_by_name=True)


class EHR_ACCESS(BaseModel):
    """EHR_ACCESS."""

    type: str = Field(default="EHR_ACCESS", alias="_type")
    uid: Optional[Any] = None
    archetype_node_id: str
    name: Optional[Any]
    archetype_details: Optional["ARCHETYPED"] = None
    feeder_audit: Optional["FEEDER_AUDIT"] = None
    links: Optional[list["LINK"]] = None

    model_config = ConfigDict(populate_by_name=True)


class EHR_STATUS(BaseModel):
    """EHR_STATUS."""

    type: str = Field(default="EHR_STATUS", alias="_type")
    uid: Optional[Any] = None
    archetype_node_id: str
    name: Optional[Any]
    archetype_details: Optional["ARCHETYPED"] = None
    feeder_audit: Optional["FEEDER_AUDIT"] = None
    links: Optional[list["LINK"]] = None
    subject: Optional["PARTY_SELF"]
    is_queryable: bool
    is_modifiable: bool
    other_details: Optional[Any] = None

    model_config = ConfigDict(populate_by_name=True)


class ELEMENT(BaseModel):
    """ELEMENT."""

    type: str = Field(default="ELEMENT", alias="_type")
    uid: Optional[Any] = None
    archetype_node_id: str
    name: Optional[Any]
    archetype_details: Optional["ARCHETYPED"] = None
    feeder_audit: Optional["FEEDER_AUDIT"] = None
    links: Optional[list["LINK"]] = None
    null_flavour: Optional["DV_CODED_TEXT"] = None
    value: Optional[Any] = None
    null_reason: Optional[Any] = None

    model_config = ConfigDict(populate_by_name=True)


class EVALUATION(BaseModel):
    """EVALUATION."""

    type: str = Field(default="EVALUATION", alias="_type")
    uid: Optional[Any] = None
    archetype_node_id: str
    name: Optional[Any]
    archetype_details: Optional["ARCHETYPED"] = None
    feeder_audit: Optional["FEEDER_AUDIT"] = None
    links: Optional[list["LINK"]] = None
    language: Optional["CODE_PHRASE"]
    encoding: Optional["CODE_PHRASE"]
    subject: Optional[Any]
    provider: Optional[Any] = None
    other_participations: Optional[list["PARTICIPATION"]] = None
    workflow_id: Optional[Any] = None
    protocol: Optional[Any] = None
    guideline_id: Optional[Any] = None
    data: Optional[Any]

    model_config = ConfigDict(populate_by_name=True)


class EVENT_CONTEXT(BaseModel):
    """EVENT_CONTEXT."""

    type: str = Field(default="EVENT_CONTEXT", alias="_type")
    health_care_facility: Optional[Any] = None
    start_time: Optional["DV_DATE_TIME"]
    end_time: Optional["DV_DATE_TIME"] = None
    participations: Optional[list["PARTICIPATION"]] = None
    location: Optional[str] = None
    setting: Optional["DV_CODED_TEXT"]
    other_context: Optional[Any] = None

    model_config = ConfigDict(populate_by_name=True)


class EXTRACT(BaseModel):
    """EXTRACT."""

    type: str = Field(default="EXTRACT", alias="_type")
    uid: Optional[Any] = None
    archetype_node_id: str
    name: Optional[Any]
    archetype_details: Optional["ARCHETYPED"] = None
    feeder_audit: Optional["FEEDER_AUDIT"] = None
    links: Optional[list["LINK"]] = None
    request_id: Optional["HIER_OBJECT_ID"] = None
    time_created: Optional["DV_DATE_TIME"]
    system_id: Optional["HIER_OBJECT_ID"]
    sequence_nr: int
    specification: Optional["EXTRACT_SPEC"] = None
    chapters: Optional[list] = None
    participations: Optional[list["EXTRACT_PARTICIPATION"]] = None

    model_config = ConfigDict(populate_by_name=True)


class EXTRACT_ACTION_REQUEST(BaseModel):
    """EXTRACT_ACTION_REQUEST."""

    type: str = Field(default="EXTRACT_ACTION_REQUEST", alias="_type")
    uid: Optional["HIER_OBJECT_ID"]
    archetype_node_id: str
    name: Optional[Any]
    archetype_details: Optional["ARCHETYPED"] = None
    feeder_audit: Optional["FEEDER_AUDIT"] = None
    links: Optional[list["LINK"]] = None
    request_id: Optional[Any]
    action: Optional["DV_CODED_TEXT"]

    model_config = ConfigDict(populate_by_name=True)


class EXTRACT_CHAPTER(BaseModel):
    """EXTRACT_CHAPTER."""

    type: str = Field(default="EXTRACT_CHAPTER", alias="_type")
    uid: Optional[Any] = None
    archetype_node_id: str
    name: Optional[Any]
    archetype_details: Optional["ARCHETYPED"] = None
    feeder_audit: Optional["FEEDER_AUDIT"] = None
    links: Optional[list["LINK"]] = None
    items: Optional[list] = None

    model_config = ConfigDict(populate_by_name=True)


class EXTRACT_ENTITY_CHAPTER(BaseModel):
    """EXTRACT_ENTITY_CHAPTER."""

    type: str = Field(default="EXTRACT_ENTITY_CHAPTER", alias="_type")
    uid: Optional[Any] = None
    archetype_node_id: str
    name: Optional[Any]
    archetype_details: Optional["ARCHETYPED"] = None
    feeder_audit: Optional["FEEDER_AUDIT"] = None
    links: Optional[list["LINK"]] = None
    items: Optional[list] = None
    extract_id_key: str

    model_config = ConfigDict(populate_by_name=True)


class EXTRACT_ENTITY_MANIFEST(BaseModel):
    """EXTRACT_ENTITY_MANIFEST."""

    type: str = Field(default="EXTRACT_ENTITY_MANIFEST", alias="_type")
    extract_id_key: str
    ehr_id: Optional[str] = None
    subject_id: Optional[str] = None
    other_ids: Optional[list] = None
    item_list: Optional[list] = None

    model_config = ConfigDict(populate_by_name=True)


class EXTRACT_FOLDER(BaseModel):
    """EXTRACT_FOLDER."""

    type: str = Field(default="EXTRACT_FOLDER", alias="_type")
    uid: Optional[Any] = None
    archetype_node_id: str
    name: Optional[Any]
    archetype_details: Optional["ARCHETYPED"] = None
    feeder_audit: Optional["FEEDER_AUDIT"] = None
    links: Optional[list["LINK"]] = None
    items: Optional[list] = None

    model_config = ConfigDict(populate_by_name=True)


class EXTRACT_MANIFEST(BaseModel):
    """EXTRACT_MANIFEST."""

    type: str = Field(default="EXTRACT_MANIFEST", alias="_type")
    entities: Optional[list["EXTRACT_ENTITY_MANIFEST"]] = None

    model_config = ConfigDict(populate_by_name=True)


class EXTRACT_PARTICIPATION(BaseModel):
    """EXTRACT_PARTICIPATION."""

    type: str = Field(default="EXTRACT_PARTICIPATION", alias="_type")
    performer: str
    function: Optional[Any]
    mode: Optional["DV_CODED_TEXT"] = None
    time: Optional["DV_INTERVAL"] = None

    model_config = ConfigDict(populate_by_name=True)


class EXTRACT_REQUEST(BaseModel):
    """EXTRACT_REQUEST."""

    type: str = Field(default="EXTRACT_REQUEST", alias="_type")
    uid: Optional["HIER_OBJECT_ID"]
    archetype_node_id: str
    name: Optional[Any]
    archetype_details: Optional["ARCHETYPED"] = None
    feeder_audit: Optional["FEEDER_AUDIT"] = None
    links: Optional[list["LINK"]] = None
    extract_spec: Optional["EXTRACT_SPEC"]
    update_spec: Optional["EXTRACT_UPDATE_SPEC"] = None

    model_config = ConfigDict(populate_by_name=True)


class EXTRACT_SPEC(BaseModel):
    """EXTRACT_SPEC."""

    type: str = Field(default="EXTRACT_SPEC", alias="_type")
    extract_type: Optional["DV_CODED_TEXT"]
    include_multimedia: bool
    priority: int
    link_depth: int
    criteria: Optional[list["DV_PARSABLE"]] = None
    manifest: Optional["EXTRACT_MANIFEST"]
    version_spec: Optional["EXTRACT_VERSION_SPEC"] = None
    other_details: Optional[Any] = None

    model_config = ConfigDict(populate_by_name=True)


class EXTRACT_UPDATE_SPEC(BaseModel):
    """EXTRACT_UPDATE_SPEC."""

    type: str = Field(default="EXTRACT_UPDATE_SPEC", alias="_type")
    persist_in_server: bool
    trigger_events: Optional[list["DV_CODED_TEXT"]] = None
    repeat_period: Optional["DV_DURATION"] = None
    update_method: Optional["CODE_PHRASE"]

    model_config = ConfigDict(populate_by_name=True)


class EXTRACT_VERSION_SPEC(BaseModel):
    """EXTRACT_VERSION_SPEC."""

    type: str = Field(default="EXTRACT_VERSION_SPEC", alias="_type")
    include_all_versions: bool
    commit_time_interval: Optional["DV_INTERVAL"] = None
    include_revision_history: bool
    include_data: bool

    model_config = ConfigDict(populate_by_name=True)


class FEEDER_AUDIT(BaseModel):
    """FEEDER_AUDIT."""

    type: str = Field(default="FEEDER_AUDIT", alias="_type")
    originating_system_item_ids: Optional[list["DV_IDENTIFIER"]] = None
    feeder_system_item_ids: Optional[list["DV_IDENTIFIER"]] = None
    original_content: Optional[Any] = None
    originating_system_audit: Optional["FEEDER_AUDIT_DETAILS"]
    feeder_system_audit: Optional["FEEDER_AUDIT_DETAILS"] = None

    model_config = ConfigDict(populate_by_name=True)


class FEEDER_AUDIT_DETAILS(BaseModel):
    """FEEDER_AUDIT_DETAILS."""

    type: str = Field(default="FEEDER_AUDIT_DETAILS", alias="_type")
    system_id: str
    location: Optional[Any] = None
    provider: Optional[Any] = None
    subject: Optional[Any] = None
    time: Optional["DV_DATE_TIME"] = None
    version_id: Optional[str] = None
    other_details: Optional[Any] = None

    model_config = ConfigDict(populate_by_name=True)


class FOLDER(BaseModel):
    """FOLDER."""

    type: str = Field(default="FOLDER", alias="_type")
    uid: Optional[Any] = None
    archetype_node_id: str
    name: Optional[Any]
    archetype_details: Optional["ARCHETYPED"] = None
    feeder_audit: Optional["FEEDER_AUDIT"] = None
    links: Optional[list["LINK"]] = None
    folders: Optional[list["FOLDER"]] = None
    items: Optional[list] = None
    details: Optional[Any] = None

    model_config = ConfigDict(populate_by_name=True)


class GENERIC_CONTENT_ITEM(BaseModel):
    """GENERIC_CONTENT_ITEM."""

    type: str = Field(default="GENERIC_CONTENT_ITEM", alias="_type")
    uid: Optional[Any] = None
    archetype_node_id: str
    name: Optional[Any]
    archetype_details: Optional["ARCHETYPED"] = None
    feeder_audit: Optional["FEEDER_AUDIT"] = None
    links: Optional[list["LINK"]] = None
    is_primary: bool
    is_changed: Optional[bool] = None
    is_masked: Optional[bool] = None
    item: Optional[Any] = None
    item_type: Optional["DV_CODED_TEXT"] = None
    item_type_version: Optional[str] = None
    author: Optional[str] = None
    creation_time: Optional[str] = None
    authoriser: Optional[str] = None
    authorisation_time: Optional[str] = None
    item_status: Optional["DV_CODED_TEXT"] = None
    version_id: Optional[str] = None
    version_set_id: Optional[str] = None
    system_id: Optional[str] = None
    other_details: Optional[list] = None

    model_config = ConfigDict(populate_by_name=True)


class GENERIC_ENTRY(BaseModel):
    """GENERIC_ENTRY."""

    type: str = Field(default="GENERIC_ENTRY", alias="_type")
    uid: Optional[Any] = None
    archetype_node_id: str
    name: Optional[Any]
    archetype_details: Optional["ARCHETYPED"] = None
    feeder_audit: Optional["FEEDER_AUDIT"] = None
    links: Optional[list["LINK"]] = None
    data: Optional["ITEM_TREE"]

    model_config = ConfigDict(populate_by_name=True)


class GROUP(BaseModel):
    """GROUP."""

    type: str = Field(default="GROUP", alias="_type")
    uid: Optional[Any]
    archetype_node_id: str
    name: Optional[Any]
    archetype_details: Optional["ARCHETYPED"] = None
    feeder_audit: Optional["FEEDER_AUDIT"] = None
    links: Optional[list["LINK"]] = None
    details: Optional[Any] = None
    identities: Optional[list["PARTY_IDENTITY"]]
    contacts: Optional[list["CONTACT"]] = None
    relationships: Optional[list["PARTY_RELATIONSHIP"]] = None
    reverse_relationships: Optional[list["LOCATABLE_REF"]] = None
    roles: Optional[list["PARTY_REF"]] = None
    languages: Optional[list] = None

    model_config = ConfigDict(populate_by_name=True)


class HISTORY(BaseModel):
    """HISTORY."""

    type: str = Field(default="HISTORY", alias="_type")
    uid: Optional[Any] = None
    archetype_node_id: str
    name: Optional[Any]
    archetype_details: Optional["ARCHETYPED"] = None
    feeder_audit: Optional["FEEDER_AUDIT"] = None
    links: Optional[list["LINK"]] = None
    origin: Optional["DV_DATE_TIME"]
    period: Optional["DV_DURATION"] = None
    duration: Optional["DV_DURATION"] = None
    summary: Optional[Any] = None
    events: Optional[list] = None

    model_config = ConfigDict(populate_by_name=True)


class IMPORTED_VERSION(BaseModel):
    """IMPORTED_VERSION."""

    type: str = Field(default="IMPORTED_VERSION", alias="_type")
    contribution: Optional[Any]
    commit_audit: Optional[Any]
    signature: Optional[str] = None
    item: Optional["ORIGINAL_VERSION"]

    model_config = ConfigDict(populate_by_name=True)


class INSTRUCTION(BaseModel):
    """INSTRUCTION."""

    type: str = Field(default="INSTRUCTION", alias="_type")
    uid: Optional[Any] = None
    archetype_node_id: str
    name: Optional[Any]
    archetype_details: Optional["ARCHETYPED"] = None
    feeder_audit: Optional["FEEDER_AUDIT"] = None
    links: Optional[list["LINK"]] = None
    language: Optional["CODE_PHRASE"]
    encoding: Optional["CODE_PHRASE"]
    subject: Optional[Any]
    provider: Optional[Any] = None
    other_participations: Optional[list["PARTICIPATION"]] = None
    workflow_id: Optional[Any] = None
    protocol: Optional[Any] = None
    guideline_id: Optional[Any] = None
    narrative: Optional[Any]
    expiry_time: Optional["DV_DATE_TIME"] = None
    wf_definition: Optional["DV_PARSABLE"] = None
    activities: Optional[list["ACTIVITY"]] = None

    model_config = ConfigDict(populate_by_name=True)


class INSTRUCTION_DETAILS(BaseModel):
    """INSTRUCTION_DETAILS."""

    type: str = Field(default="INSTRUCTION_DETAILS", alias="_type")
    instruction_id: Optional["LOCATABLE_REF"]
    wf_details: Optional[Any] = None
    activity_id: str

    model_config = ConfigDict(populate_by_name=True)


class INTERVAL_EVENT(BaseModel):
    """INTERVAL_EVENT."""

    type: str = Field(default="INTERVAL_EVENT", alias="_type")
    uid: Optional[Any] = None
    archetype_node_id: str
    name: Optional[Any]
    archetype_details: Optional["ARCHETYPED"] = None
    feeder_audit: Optional["FEEDER_AUDIT"] = None
    links: Optional[list["LINK"]] = None
    time: Optional["DV_DATE_TIME"]
    state: Optional[Any] = None
    data: Optional[Any]
    width: Optional["DV_DURATION"]
    sample_count: Optional[int] = None
    math_function: Optional["DV_CODED_TEXT"]

    model_config = ConfigDict(populate_by_name=True)


class ISM_TRANSITION(BaseModel):
    """ISM_TRANSITION."""

    type: str = Field(default="ISM_TRANSITION", alias="_type")
    current_state: Optional["DV_CODED_TEXT"]
    transition: Optional["DV_CODED_TEXT"] = None
    careflow_step: Optional["DV_CODED_TEXT"] = None
    reason: Optional[list] = None

    model_config = ConfigDict(populate_by_name=True)


class ITEM_LIST(BaseModel):
    """ITEM_LIST."""

    type: str = Field(default="ITEM_LIST", alias="_type")
    uid: Optional[Any] = None
    archetype_node_id: str
    name: Optional[Any]
    archetype_details: Optional["ARCHETYPED"] = None
    feeder_audit: Optional["FEEDER_AUDIT"] = None
    links: Optional[list["LINK"]] = None
    items: Optional[list["ELEMENT"]] = None

    model_config = ConfigDict(populate_by_name=True)


class ITEM_SINGLE(BaseModel):
    """ITEM_SINGLE."""

    type: str = Field(default="ITEM_SINGLE", alias="_type")
    uid: Optional[Any] = None
    archetype_node_id: str
    name: Optional[Any]
    archetype_details: Optional["ARCHETYPED"] = None
    feeder_audit: Optional["FEEDER_AUDIT"] = None
    links: Optional[list["LINK"]] = None
    item: Optional["ELEMENT"]

    model_config = ConfigDict(populate_by_name=True)


class ITEM_TABLE(BaseModel):
    """ITEM_TABLE."""

    type: str = Field(default="ITEM_TABLE", alias="_type")
    uid: Optional[Any] = None
    archetype_node_id: str
    name: Optional[Any]
    archetype_details: Optional["ARCHETYPED"] = None
    feeder_audit: Optional["FEEDER_AUDIT"] = None
    links: Optional[list["LINK"]] = None
    rows: Optional[list["CLUSTER"]] = None

    model_config = ConfigDict(populate_by_name=True)


class ITEM_TREE(BaseModel):
    """ITEM_TREE."""

    type: str = Field(default="ITEM_TREE", alias="_type")
    uid: Optional[Any] = None
    archetype_node_id: str
    name: Optional[Any]
    archetype_details: Optional["ARCHETYPED"] = None
    feeder_audit: Optional["FEEDER_AUDIT"] = None
    links: Optional[list["LINK"]] = None
    items: Optional[list] = None

    model_config = ConfigDict(populate_by_name=True)


class LINK(BaseModel):
    """LINK."""

    type: str = Field(default="LINK", alias="_type")
    meaning: Optional[Any]
    type: Optional[Any]
    target: Optional["DV_EHR_URI"]

    model_config = ConfigDict(populate_by_name=True)


class MESSAGE(BaseModel):
    """MESSAGE."""

    type: str = Field(default="MESSAGE", alias="_type")
    author: Optional[Any]
    audit: Optional[Any]
    content: Optional[Any]
    signature: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class OBSERVATION(BaseModel):
    """OBSERVATION."""

    type: str = Field(default="OBSERVATION", alias="_type")
    uid: Optional[Any] = None
    archetype_node_id: str
    name: Optional[Any]
    archetype_details: Optional["ARCHETYPED"] = None
    feeder_audit: Optional["FEEDER_AUDIT"] = None
    links: Optional[list["LINK"]] = None
    language: Optional["CODE_PHRASE"]
    encoding: Optional["CODE_PHRASE"]
    subject: Optional[Any]
    provider: Optional[Any] = None
    other_participations: Optional[list["PARTICIPATION"]] = None
    workflow_id: Optional[Any] = None
    protocol: Optional[Any] = None
    guideline_id: Optional[Any] = None
    data: Optional["HISTORY"]
    state: Optional["HISTORY"] = None

    model_config = ConfigDict(populate_by_name=True)


class OPENEHR_CONTENT_ITEM(BaseModel):
    """OPENEHR_CONTENT_ITEM."""

    type: str = Field(default="OPENEHR_CONTENT_ITEM", alias="_type")
    uid: Optional[Any] = None
    archetype_node_id: str
    name: Optional[Any]
    archetype_details: Optional["ARCHETYPED"] = None
    feeder_audit: Optional["FEEDER_AUDIT"] = None
    links: Optional[list["LINK"]] = None
    is_primary: bool
    is_changed: Optional[bool] = None
    is_masked: Optional[bool] = None
    item: Optional[Any] = None

    model_config = ConfigDict(populate_by_name=True)


class ORGANISATION(BaseModel):
    """ORGANISATION."""

    type: str = Field(default="ORGANISATION", alias="_type")
    uid: Optional[Any]
    archetype_node_id: str
    name: Optional[Any]
    archetype_details: Optional["ARCHETYPED"] = None
    feeder_audit: Optional["FEEDER_AUDIT"] = None
    links: Optional[list["LINK"]] = None
    details: Optional[Any] = None
    identities: Optional[list["PARTY_IDENTITY"]]
    contacts: Optional[list["CONTACT"]] = None
    relationships: Optional[list["PARTY_RELATIONSHIP"]] = None
    reverse_relationships: Optional[list["LOCATABLE_REF"]] = None
    roles: Optional[list["PARTY_REF"]] = None
    languages: Optional[list] = None

    model_config = ConfigDict(populate_by_name=True)


class ORIGINAL_VERSION(BaseModel):
    """ORIGINAL_VERSION."""

    type: str = Field(default="ORIGINAL_VERSION", alias="_type")
    contribution: Optional[Any]
    commit_audit: Optional[Any]
    signature: Optional[str] = None
    uid: Optional["OBJECT_VERSION_ID"]
    preceding_version_uid: Optional["OBJECT_VERSION_ID"] = None
    other_input_version_uids: Optional[list["OBJECT_VERSION_ID"]] = None
    attestations: Optional[list["ATTESTATION"]] = None
    lifecycle_state: Optional["DV_CODED_TEXT"]

    model_config = ConfigDict(populate_by_name=True)


class PARTICIPATION(BaseModel):
    """PARTICIPATION."""

    type: str = Field(default="PARTICIPATION", alias="_type")
    function: Optional[Any]
    time: Optional["DV_INTERVAL"] = None
    mode: Optional["DV_CODED_TEXT"] = None
    performer: Optional[Any]

    model_config = ConfigDict(populate_by_name=True)


class PARTY_IDENTIFIED(BaseModel):
    """PARTY_IDENTIFIED."""

    type: str = Field(default="PARTY_IDENTIFIED", alias="_type")
    external_ref: Optional["PARTY_REF"] = None
    name: Optional[str] = None
    identifiers: Optional[list["DV_IDENTIFIER"]] = None

    model_config = ConfigDict(populate_by_name=True)


class PARTY_IDENTITY(BaseModel):
    """PARTY_IDENTITY."""

    type: str = Field(default="PARTY_IDENTITY", alias="_type")
    uid: Optional[Any] = None
    archetype_node_id: str
    name: Optional[Any]
    archetype_details: Optional["ARCHETYPED"] = None
    feeder_audit: Optional["FEEDER_AUDIT"] = None
    links: Optional[list["LINK"]] = None
    details: Optional[Any]

    model_config = ConfigDict(populate_by_name=True)


class PARTY_RELATED(BaseModel):
    """PARTY_RELATED."""

    type: str = Field(default="PARTY_RELATED", alias="_type")
    external_ref: Optional["PARTY_REF"] = None
    name: Optional[str] = None
    identifiers: Optional[list["DV_IDENTIFIER"]] = None
    relationship: Optional["DV_CODED_TEXT"]

    model_config = ConfigDict(populate_by_name=True)


class PARTY_RELATIONSHIP(BaseModel):
    """PARTY_RELATIONSHIP."""

    type: str = Field(default="PARTY_RELATIONSHIP", alias="_type")
    uid: Optional[Any] = None
    archetype_node_id: str
    name: Optional[Any]
    archetype_details: Optional["ARCHETYPED"] = None
    feeder_audit: Optional["FEEDER_AUDIT"] = None
    links: Optional[list["LINK"]] = None
    source: Optional["PARTY_REF"]
    target: Optional["PARTY_REF"]
    details: Optional[Any] = None
    time_validity: Optional["DV_INTERVAL"] = None

    model_config = ConfigDict(populate_by_name=True)


class PARTY_SELF(BaseModel):
    """PARTY_SELF."""

    type: str = Field(default="PARTY_SELF", alias="_type")
    external_ref: Optional["PARTY_REF"] = None

    model_config = ConfigDict(populate_by_name=True)


class PERSON(BaseModel):
    """PERSON."""

    type: str = Field(default="PERSON", alias="_type")
    uid: Optional[Any]
    archetype_node_id: str
    name: Optional[Any]
    archetype_details: Optional["ARCHETYPED"] = None
    feeder_audit: Optional["FEEDER_AUDIT"] = None
    links: Optional[list["LINK"]] = None
    details: Optional[Any] = None
    identities: Optional[list["PARTY_IDENTITY"]]
    contacts: Optional[list["CONTACT"]] = None
    relationships: Optional[list["PARTY_RELATIONSHIP"]] = None
    reverse_relationships: Optional[list["LOCATABLE_REF"]] = None
    roles: Optional[list["PARTY_REF"]] = None
    languages: Optional[list] = None

    model_config = ConfigDict(populate_by_name=True)


class POINT_EVENT(BaseModel):
    """POINT_EVENT."""

    type: str = Field(default="POINT_EVENT", alias="_type")
    uid: Optional[Any] = None
    archetype_node_id: str
    name: Optional[Any]
    archetype_details: Optional["ARCHETYPED"] = None
    feeder_audit: Optional["FEEDER_AUDIT"] = None
    links: Optional[list["LINK"]] = None
    time: Optional["DV_DATE_TIME"]
    state: Optional[Any] = None
    data: Optional[Any]

    model_config = ConfigDict(populate_by_name=True)


class REFERENCE_RANGE(BaseModel):
    """REFERENCE_RANGE."""

    type: str = Field(default="REFERENCE_RANGE", alias="_type")
    range: Optional["DV_INTERVAL"]
    meaning: Optional[Any]

    model_config = ConfigDict(populate_by_name=True)


class REVISION_HISTORY(BaseModel):
    """REVISION_HISTORY."""

    type: str = Field(default="REVISION_HISTORY", alias="_type")
    items: Optional[list["REVISION_HISTORY_ITEM"]]

    model_config = ConfigDict(populate_by_name=True)


class REVISION_HISTORY_ITEM(BaseModel):
    """REVISION_HISTORY_ITEM."""

    type: str = Field(default="REVISION_HISTORY_ITEM", alias="_type")
    version_id: Optional["OBJECT_VERSION_ID"]
    audits: list

    model_config = ConfigDict(populate_by_name=True)


class ROLE(BaseModel):
    """ROLE."""

    type: str = Field(default="ROLE", alias="_type")
    uid: Optional[Any]
    archetype_node_id: str
    name: Optional[Any]
    archetype_details: Optional["ARCHETYPED"] = None
    feeder_audit: Optional["FEEDER_AUDIT"] = None
    links: Optional[list["LINK"]] = None
    details: Optional[Any] = None
    identities: Optional[list["PARTY_IDENTITY"]]
    contacts: Optional[list["CONTACT"]] = None
    relationships: Optional[list["PARTY_RELATIONSHIP"]] = None
    reverse_relationships: Optional[list["LOCATABLE_REF"]] = None
    performer: Optional["PARTY_REF"]
    capabilities: Optional[list["CAPABILITY"]] = None
    time_validity: Optional["DV_INTERVAL"] = None

    model_config = ConfigDict(populate_by_name=True)


class SECTION(BaseModel):
    """SECTION."""

    type: str = Field(default="SECTION", alias="_type")
    uid: Optional[Any] = None
    archetype_node_id: str
    name: Optional[Any]
    archetype_details: Optional["ARCHETYPED"] = None
    feeder_audit: Optional["FEEDER_AUDIT"] = None
    links: Optional[list["LINK"]] = None
    items: Optional[list] = None

    model_config = ConfigDict(populate_by_name=True)


class SYNC_EXTRACT(BaseModel):
    """SYNC_EXTRACT."""

    type: str = Field(default="SYNC_EXTRACT", alias="_type")
    uid: Optional[Any] = None
    archetype_node_id: str
    name: Optional[Any]
    archetype_details: Optional["ARCHETYPED"] = None
    feeder_audit: Optional["FEEDER_AUDIT"] = None
    links: Optional[list["LINK"]] = None
    specification: Optional["SYNC_EXTRACT_SPEC"]
    items: Optional[list["X_CONTRIBUTION"]] = None

    model_config = ConfigDict(populate_by_name=True)


class SYNC_EXTRACT_REQUEST(BaseModel):
    """SYNC_EXTRACT_REQUEST."""

    type: str = Field(default="SYNC_EXTRACT_REQUEST", alias="_type")
    uid: Optional[Any] = None
    archetype_node_id: str
    name: Optional[Any]
    archetype_details: Optional["ARCHETYPED"] = None
    feeder_audit: Optional["FEEDER_AUDIT"] = None
    links: Optional[list["LINK"]] = None
    specification: Optional["SYNC_EXTRACT_SPEC"]

    model_config = ConfigDict(populate_by_name=True)


class SYNC_EXTRACT_SPEC(BaseModel):
    """SYNC_EXTRACT_SPEC."""

    type: str = Field(default="SYNC_EXTRACT_SPEC", alias="_type")
    includes_versions: bool
    contribution_list: Optional[list["HIER_OBJECT_ID"]] = None
    contributions_since: Optional["DV_DATE_TIME"] = None
    all_contributions: Optional[bool] = None

    model_config = ConfigDict(populate_by_name=True)


class TERM_MAPPING(BaseModel):
    """TERM_MAPPING."""

    type: str = Field(default="TERM_MAPPING", alias="_type")
    match: str
    purpose: Optional["DV_CODED_TEXT"] = None
    target: Optional["CODE_PHRASE"]

    model_config = ConfigDict(populate_by_name=True)


class VERSIONED_OBJECT(BaseModel):
    """VERSIONED_OBJECT."""

    type: str = Field(default="VERSIONED_OBJECT", alias="_type")
    uid: Optional["HIER_OBJECT_ID"]
    owner_id: Optional[Any]
    time_created: Optional["DV_DATE_TIME"]

    model_config = ConfigDict(populate_by_name=True)


class X_CONTRIBUTION(BaseModel):
    """X_CONTRIBUTION."""

    type: str = Field(default="X_CONTRIBUTION", alias="_type")
    uid: Optional["HIER_OBJECT_ID"]
    audit: Optional[Any]
    versions: Optional[list] = None

    model_config = ConfigDict(populate_by_name=True)


class X_VERSIONED_COMPOSITION(BaseModel):
    """X_VERSIONED_COMPOSITION."""

    type: str = Field(default="X_VERSIONED_COMPOSITION", alias="_type")
    uid: Optional["HIER_OBJECT_ID"]
    owner_id: Optional[Any]
    time_created: Optional["DV_DATE_TIME"]
    total_version_count: int
    extract_version_count: int
    revision_history: Optional["REVISION_HISTORY"] = None
    versions: Optional[list["ORIGINAL_VERSION"]] = None

    model_config = ConfigDict(populate_by_name=True)


class X_VERSIONED_EHR_ACCESS(BaseModel):
    """X_VERSIONED_EHR_ACCESS."""

    type: str = Field(default="X_VERSIONED_EHR_ACCESS", alias="_type")
    uid: Optional["HIER_OBJECT_ID"]
    owner_id: Optional[Any]
    time_created: Optional["DV_DATE_TIME"]
    total_version_count: int
    extract_version_count: int
    revision_history: Optional["REVISION_HISTORY"] = None
    versions: Optional[list["ORIGINAL_VERSION"]] = None

    model_config = ConfigDict(populate_by_name=True)


class X_VERSIONED_EHR_STATUS(BaseModel):
    """X_VERSIONED_EHR_STATUS."""

    type: str = Field(default="X_VERSIONED_EHR_STATUS", alias="_type")
    uid: Optional["HIER_OBJECT_ID"]
    owner_id: Optional[Any]
    time_created: Optional["DV_DATE_TIME"]
    total_version_count: int
    extract_version_count: int
    revision_history: Optional["REVISION_HISTORY"] = None
    versions: Optional[list["ORIGINAL_VERSION"]] = None

    model_config = ConfigDict(populate_by_name=True)


class X_VERSIONED_FOLDER(BaseModel):
    """X_VERSIONED_FOLDER."""

    type: str = Field(default="X_VERSIONED_FOLDER", alias="_type")
    uid: Optional["HIER_OBJECT_ID"]
    owner_id: Optional[Any]
    time_created: Optional["DV_DATE_TIME"]
    total_version_count: int
    extract_version_count: int
    revision_history: Optional["REVISION_HISTORY"] = None
    versions: Optional[list["ORIGINAL_VERSION"]] = None

    model_config = ConfigDict(populate_by_name=True)


class X_VERSIONED_OBJECT(BaseModel):
    """X_VERSIONED_OBJECT."""

    type: str = Field(default="X_VERSIONED_OBJECT", alias="_type")
    uid: Optional["HIER_OBJECT_ID"]
    owner_id: Optional[Any]
    time_created: Optional["DV_DATE_TIME"]
    total_version_count: int
    extract_version_count: int
    revision_history: Optional["REVISION_HISTORY"] = None
    versions: Optional[list["ORIGINAL_VERSION"]] = None

    model_config = ConfigDict(populate_by_name=True)


class X_VERSIONED_PARTY(BaseModel):
    """X_VERSIONED_PARTY."""

    type: str = Field(default="X_VERSIONED_PARTY", alias="_type")
    uid: Optional["HIER_OBJECT_ID"]
    owner_id: Optional[Any]
    time_created: Optional["DV_DATE_TIME"]
    total_version_count: int
    extract_version_count: int
    revision_history: Optional["REVISION_HISTORY"] = None
    versions: Optional[list["ORIGINAL_VERSION"]] = None

    model_config = ConfigDict(populate_by_name=True)


# Rebuild all models to resolve forward references
import sys as _sys
_module = _sys.modules[__name__]
for _name in dir(_module):
    _obj = getattr(_module, _name)
    if isinstance(_obj, type) and issubclass(_obj, BaseModel) and _obj is not BaseModel:
        try:
            _obj.model_rebuild()
        except Exception:
            pass  # Skip if rebuild fails
