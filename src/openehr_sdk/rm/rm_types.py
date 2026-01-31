"""
Generated Pydantic models for openEHR Reference Model 1.1.0.

Includes both RM and BASE types from specifications-ITS-JSON.
Auto-generated - DO NOT EDIT MANUALLY.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# openEHR RM 1.1.0 and BASE Types


class ACCESS_GROUP_REF(BaseModel):
    """ACCESS_GROUP_REF."""

    type: str = Field(default="ACCESS_GROUP_REF", alias="_type")
    id: Any | None
    namespace: str

    model_config = ConfigDict(populate_by_name=True)


class ACTION(BaseModel):
    """ACTION."""

    type: str = Field(default="ACTION", alias="_type")
    uid: Any | None = None
    archetype_node_id: str
    name: Any | None
    archetype_details: ARCHETYPED | None = None
    feeder_audit: FEEDER_AUDIT | None = None
    links: list[LINK] | None = None
    language: CODE_PHRASE | None
    encoding: CODE_PHRASE | None
    subject: Any | None
    provider: Any | None = None
    other_participations: list[PARTICIPATION] | None = None
    workflow_id: Any | None = None
    protocol: Any | None = None
    guideline_id: Any | None = None
    time: DV_DATE_TIME | None
    description: Any | None
    ism_transition: ISM_TRANSITION | None
    instruction_details: INSTRUCTION_DETAILS | None = None

    model_config = ConfigDict(populate_by_name=True)


class ACTIVITY(BaseModel):
    """ACTIVITY."""

    type: str = Field(default="ACTIVITY", alias="_type")
    uid: Any | None = None
    archetype_node_id: str
    name: Any | None
    archetype_details: ARCHETYPED | None = None
    feeder_audit: FEEDER_AUDIT | None = None
    links: list[LINK] | None = None
    description: Any | None
    timing: DV_PARSABLE | None = None
    action_archetype_id: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class ADDRESS(BaseModel):
    """ADDRESS."""

    type: str = Field(default="ADDRESS", alias="_type")
    uid: Any | None = None
    archetype_node_id: str
    name: Any | None
    archetype_details: ARCHETYPED | None = None
    feeder_audit: FEEDER_AUDIT | None = None
    links: list[LINK] | None = None
    details: Any | None

    model_config = ConfigDict(populate_by_name=True)


class ADDRESSED_MESSAGE(BaseModel):
    """ADDRESSED_MESSAGE."""

    type: str = Field(default="ADDRESSED_MESSAGE", alias="_type")
    sender: str
    sender_reference: str
    addressees: list | None = None
    urgency: int | None = None
    message: MESSAGE | None = None

    model_config = ConfigDict(populate_by_name=True)


class ADMIN_ENTRY(BaseModel):
    """ADMIN_ENTRY."""

    type: str = Field(default="ADMIN_ENTRY", alias="_type")
    uid: Any | None = None
    archetype_node_id: str
    name: Any | None
    archetype_details: ARCHETYPED | None = None
    feeder_audit: FEEDER_AUDIT | None = None
    links: list[LINK] | None = None
    language: CODE_PHRASE | None
    encoding: CODE_PHRASE | None
    subject: Any | None
    provider: Any | None = None
    other_participations: list[PARTICIPATION] | None = None
    workflow_id: Any | None = None
    data: Any | None

    model_config = ConfigDict(populate_by_name=True)


class AGENT(BaseModel):
    """AGENT."""

    type: str = Field(default="AGENT", alias="_type")
    uid: Any | None
    archetype_node_id: str
    name: Any | None
    archetype_details: ARCHETYPED | None = None
    feeder_audit: FEEDER_AUDIT | None = None
    links: list[LINK] | None = None
    details: Any | None = None
    identities: list[PARTY_IDENTITY] | None
    contacts: list[CONTACT] | None = None
    relationships: list[PARTY_RELATIONSHIP] | None = None
    reverse_relationships: list[LOCATABLE_REF] | None = None
    roles: list[PARTY_REF] | None = None
    languages: list | None = None

    model_config = ConfigDict(populate_by_name=True)


class ARCHETYPED(BaseModel):
    """ARCHETYPED."""

    type: str = Field(default="ARCHETYPED", alias="_type")
    archetype_id: ARCHETYPE_ID | None
    template_id: TEMPLATE_ID | None = None
    rm_version: str

    model_config = ConfigDict(populate_by_name=True)


class ARCHETYPE_HRID(BaseModel):
    """ARCHETYPE_HRID."""

    type: str = Field(default="ARCHETYPE_HRID", alias="_type")
    namespace: str
    rm_publisher: str
    rm_package: str
    rm_class: str
    concept_id: str
    release_version: str
    version_status: VERSION_STATUS | None
    build_count: str

    model_config = ConfigDict(populate_by_name=True)


class ARCHETYPE_ID(BaseModel):
    """ARCHETYPE_ID."""

    type: str = Field(default="ARCHETYPE_ID", alias="_type")
    value: str

    model_config = ConfigDict(populate_by_name=True)


class ARRAY(BaseModel):
    """ARRAY."""

    type: str = Field(default="ARRAY", alias="_type")

    model_config = ConfigDict(populate_by_name=True)


class ATTESTATION(BaseModel):
    """ATTESTATION."""

    type: str = Field(default="ATTESTATION", alias="_type")
    system_id: str
    time_committed: DV_DATE_TIME | None
    change_type: DV_CODED_TEXT | None
    description: Any | None = None
    committer: Any | None
    attested_view: DV_MULTIMEDIA | None = None
    proof: str | None = None
    items: list[DV_EHR_URI] | None = None
    reason: Any | None
    is_pending: bool

    model_config = ConfigDict(populate_by_name=True)


class AUDIT_DETAILS(BaseModel):
    """AUDIT_DETAILS."""

    type: str = Field(default="AUDIT_DETAILS", alias="_type")
    system_id: str
    time_committed: DV_DATE_TIME | None
    change_type: DV_CODED_TEXT | None
    description: Any | None = None
    committer: Any | None

    model_config = ConfigDict(populate_by_name=True)


class CAPABILITY(BaseModel):
    """CAPABILITY."""

    type: str = Field(default="CAPABILITY", alias="_type")
    uid: Any | None = None
    archetype_node_id: str
    name: Any | None
    archetype_details: ARCHETYPED | None = None
    feeder_audit: FEEDER_AUDIT | None = None
    links: list[LINK] | None = None
    credentials: Any | None
    time_validity: DV_INTERVAL | None = None

    model_config = ConfigDict(populate_by_name=True)


class CLUSTER(BaseModel):
    """CLUSTER."""

    type: str = Field(default="CLUSTER", alias="_type")
    uid: Any | None = None
    archetype_node_id: str
    name: Any | None
    archetype_details: ARCHETYPED | None = None
    feeder_audit: FEEDER_AUDIT | None = None
    links: list[LINK] | None = None
    items: list

    model_config = ConfigDict(populate_by_name=True)


class CODE_PHRASE(BaseModel):
    """CODE_PHRASE."""

    type: str = Field(default="CODE_PHRASE", alias="_type")
    terminology_id: TERMINOLOGY_ID | None
    code_string: str
    preferred_term: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class COMPOSITION(BaseModel):
    """COMPOSITION."""

    type: str = Field(default="COMPOSITION", alias="_type")
    uid: Any | None = None
    archetype_node_id: str
    name: Any | None
    archetype_details: ARCHETYPED | None = None
    feeder_audit: FEEDER_AUDIT | None = None
    links: list[LINK] | None = None
    language: CODE_PHRASE | None
    territory: CODE_PHRASE | None
    category: DV_CODED_TEXT | None
    composer: Any | None
    context: EVENT_CONTEXT | None = None
    content: list | None = None

    model_config = ConfigDict(populate_by_name=True)


class CONTACT(BaseModel):
    """CONTACT."""

    type: str = Field(default="CONTACT", alias="_type")
    uid: Any | None = None
    archetype_node_id: str
    name: Any | None
    archetype_details: ARCHETYPED | None = None
    feeder_audit: FEEDER_AUDIT | None = None
    links: list[LINK] | None = None
    time_validity: DV_INTERVAL | None = None
    addresses: list[ADDRESS] | None = None

    model_config = ConfigDict(populate_by_name=True)


class CONTRIBUTION(BaseModel):
    """CONTRIBUTION."""

    type: str = Field(default="CONTRIBUTION", alias="_type")
    uid: HIER_OBJECT_ID | None
    audit: Any | None
    versions: list

    model_config = ConfigDict(populate_by_name=True)


class DATE(BaseModel):
    """DATE."""

    type: str = Field(default="DATE", alias="_type")
    value: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class DATE_TIME(BaseModel):
    """DATE_TIME."""

    type: str = Field(default="DATE_TIME", alias="_type")
    value: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class DURATION(BaseModel):
    """DURATION."""

    type: str = Field(default="DURATION", alias="_type")
    value: str | None = None

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
    hyperlink: Any | None = None
    language: CODE_PHRASE | None = None
    encoding: CODE_PHRASE | None = None
    formatting: str | None = None
    mappings: list[TERM_MAPPING] | None = None
    defining_code: CODE_PHRASE | None

    model_config = ConfigDict(populate_by_name=True)


class DV_COUNT(BaseModel):
    """DV_COUNT."""

    type: str = Field(default="DV_COUNT", alias="_type")
    normal_status: CODE_PHRASE | None = None
    normal_range: DV_INTERVAL | None = None
    other_reference_ranges: list[REFERENCE_RANGE] | None = None
    magnitude_status: str | None = None
    accuracy: float | None = None
    accuracy_is_percent: bool | None = None
    magnitude: int

    model_config = ConfigDict(populate_by_name=True)


class DV_DATE(BaseModel):
    """DV_DATE."""

    type: str = Field(default="DV_DATE", alias="_type")
    normal_status: CODE_PHRASE | None = None
    normal_range: DV_INTERVAL | None = None
    other_reference_ranges: list[REFERENCE_RANGE] | None = None
    magnitude_status: str | None = None
    accuracy: DV_DURATION | None = None
    value: str

    model_config = ConfigDict(populate_by_name=True)


class DV_DATE_TIME(BaseModel):
    """DV_DATE_TIME."""

    type: str = Field(default="DV_DATE_TIME", alias="_type")
    normal_status: CODE_PHRASE | None = None
    normal_range: DV_INTERVAL | None = None
    other_reference_ranges: list[REFERENCE_RANGE] | None = None
    magnitude_status: str | None = None
    accuracy: DV_DURATION | None = None
    value: str

    model_config = ConfigDict(populate_by_name=True)


class DV_DURATION(BaseModel):
    """DV_DURATION."""

    type: str = Field(default="DV_DURATION", alias="_type")
    normal_status: CODE_PHRASE | None = None
    normal_range: DV_INTERVAL | None = None
    other_reference_ranges: list[REFERENCE_RANGE] | None = None
    magnitude_status: str | None = None
    accuracy: float | None = None
    accuracy_is_percent: bool | None = None
    value: str

    model_config = ConfigDict(populate_by_name=True)


class DV_EHR_URI(BaseModel):
    """DV_EHR_URI."""

    type: str = Field(default="DV_EHR_URI", alias="_type")
    value: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class DV_GENERAL_TIME_SPECIFICATION(BaseModel):
    """DV_GENERAL_TIME_SPECIFICATION."""

    type: str = Field(default="DV_GENERAL_TIME_SPECIFICATION", alias="_type")
    value: DV_PARSABLE | None

    model_config = ConfigDict(populate_by_name=True)


class DV_IDENTIFIER(BaseModel):
    """DV_IDENTIFIER."""

    type: str = Field(default="DV_IDENTIFIER", alias="_type")
    issuer: str | None = None
    id: str
    assigner: str | None = None

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
    charset: CODE_PHRASE | None = None
    language: CODE_PHRASE | None = None
    alternate_text: str | None = None
    uri: Any | None = None
    data: str | None = None
    media_type: CODE_PHRASE | None
    compression_algorithm: CODE_PHRASE | None = None
    integrity_check: str | None = None
    integrity_check_algorithm: CODE_PHRASE | None = None
    thumbnail: DV_MULTIMEDIA | None = None
    size: int

    model_config = ConfigDict(populate_by_name=True)


class DV_ORDINAL(BaseModel):
    """DV_ORDINAL."""

    type: str = Field(default="DV_ORDINAL", alias="_type")
    normal_status: CODE_PHRASE | None = None
    normal_range: DV_INTERVAL | None = None
    other_reference_ranges: list[REFERENCE_RANGE] | None = None
    value: int
    symbol: DV_CODED_TEXT | None

    model_config = ConfigDict(populate_by_name=True)


class DV_PARAGRAPH(BaseModel):
    """DV_PARAGRAPH."""

    type: str = Field(default="DV_PARAGRAPH", alias="_type")
    items: list

    model_config = ConfigDict(populate_by_name=True)


class DV_PARSABLE(BaseModel):
    """DV_PARSABLE."""

    type: str = Field(default="DV_PARSABLE", alias="_type")
    charset: CODE_PHRASE | None = None
    language: CODE_PHRASE | None = None
    value: str
    formalism: str

    model_config = ConfigDict(populate_by_name=True)


class DV_PERIODIC_TIME_SPECIFICATION(BaseModel):
    """DV_PERIODIC_TIME_SPECIFICATION."""

    type: str = Field(default="DV_PERIODIC_TIME_SPECIFICATION", alias="_type")
    value: DV_PARSABLE | None

    model_config = ConfigDict(populate_by_name=True)


class DV_PROPORTION(BaseModel):
    """DV_PROPORTION."""

    type: str = Field(default="DV_PROPORTION", alias="_type")
    normal_status: CODE_PHRASE | None = None
    normal_range: DV_INTERVAL | None = None
    other_reference_ranges: list[REFERENCE_RANGE] | None = None
    magnitude_status: str | None = None
    accuracy: float | None = None
    accuracy_is_percent: bool | None = None
    numerator: float
    denominator: float
    precision: int | None = None

    model_config = ConfigDict(populate_by_name=True)


class DV_QUANTITY(BaseModel):
    """DV_QUANTITY."""

    type: str = Field(default="DV_QUANTITY", alias="_type")
    normal_status: CODE_PHRASE | None = None
    normal_range: DV_INTERVAL | None = None
    other_reference_ranges: list[REFERENCE_RANGE] | None = None
    magnitude_status: str | None = None
    accuracy: float | None = None
    accuracy_is_percent: bool | None = None
    magnitude: float
    property: CODE_PHRASE | None = None
    units: str
    units_system: str | None = None
    units_display_name: str | None = None
    precision: int | None = None

    model_config = ConfigDict(populate_by_name=True)


class DV_SCALE(BaseModel):
    """DV_SCALE - New in RM 1.1.0.

    Data type for scales/scores with decimal values.
    Extends DV_ORDINAL for non-integer scale values.
    """

    type: str = Field(default="DV_SCALE", alias="_type")
    normal_status: CODE_PHRASE | None = None
    normal_range: DV_INTERVAL | None = None
    other_reference_ranges: list[REFERENCE_RANGE] | None = None
    value: float
    symbol: DV_CODED_TEXT | None

    model_config = ConfigDict(populate_by_name=True)


class DV_STATE(BaseModel):
    """DV_STATE."""

    type: str = Field(default="DV_STATE", alias="_type")
    value: DV_CODED_TEXT | None
    is_terminal: bool

    model_config = ConfigDict(populate_by_name=True)


class DV_TEXT(BaseModel):
    """DV_TEXT."""

    type: str = Field(default="DV_TEXT", alias="_type")
    value: str
    hyperlink: Any | None = None
    language: CODE_PHRASE | None = None
    encoding: CODE_PHRASE | None = None
    formatting: str | None = None
    mappings: list[TERM_MAPPING] | None = None

    model_config = ConfigDict(populate_by_name=True)


class DV_TIME(BaseModel):
    """DV_TIME."""

    type: str = Field(default="DV_TIME", alias="_type")
    normal_status: CODE_PHRASE | None = None
    normal_range: DV_INTERVAL | None = None
    other_reference_ranges: list[REFERENCE_RANGE] | None = None
    magnitude_status: str | None = None
    accuracy: DV_DURATION | None = None
    value: str

    model_config = ConfigDict(populate_by_name=True)


class DV_URI(BaseModel):
    """DV_URI."""

    type: str = Field(default="DV_URI", alias="_type")
    value: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class EHR(BaseModel):
    """EHR."""

    type: str = Field(default="EHR", alias="_type")
    system_id: HIER_OBJECT_ID | None
    ehr_id: HIER_OBJECT_ID | None
    time_created: DV_DATE_TIME | None
    ehr_access: Any | None
    ehr_status: Any | None
    directory: Any | None = None
    folders: list | None = None
    compositions: list | None = None
    contributions: list

    model_config = ConfigDict(populate_by_name=True)


class EHR_ACCESS(BaseModel):
    """EHR_ACCESS."""

    type: str = Field(default="EHR_ACCESS", alias="_type")
    uid: Any | None = None
    archetype_node_id: str
    name: Any | None
    archetype_details: ARCHETYPED | None = None
    feeder_audit: FEEDER_AUDIT | None = None
    links: list[LINK] | None = None

    model_config = ConfigDict(populate_by_name=True)


class EHR_STATUS(BaseModel):
    """EHR_STATUS."""

    type: str = Field(default="EHR_STATUS", alias="_type")
    uid: Any | None = None
    archetype_node_id: str
    name: Any | None
    archetype_details: ARCHETYPED | None = None
    feeder_audit: FEEDER_AUDIT | None = None
    links: list[LINK] | None = None
    subject: PARTY_SELF | None
    is_queryable: bool
    is_modifiable: bool
    other_details: Any | None = None

    model_config = ConfigDict(populate_by_name=True)


class ELEMENT(BaseModel):
    """ELEMENT."""

    type: str = Field(default="ELEMENT", alias="_type")
    uid: Any | None = None
    archetype_node_id: str
    name: Any | None
    archetype_details: ARCHETYPED | None = None
    feeder_audit: FEEDER_AUDIT | None = None
    links: list[LINK] | None = None
    null_flavour: DV_CODED_TEXT | None = None
    value: Any | None = None
    null_reason: Any | None = None

    model_config = ConfigDict(populate_by_name=True)


class EVALUATION(BaseModel):
    """EVALUATION."""

    type: str = Field(default="EVALUATION", alias="_type")
    uid: Any | None = None
    archetype_node_id: str
    name: Any | None
    archetype_details: ARCHETYPED | None = None
    feeder_audit: FEEDER_AUDIT | None = None
    links: list[LINK] | None = None
    language: CODE_PHRASE | None
    encoding: CODE_PHRASE | None
    subject: Any | None
    provider: Any | None = None
    other_participations: list[PARTICIPATION] | None = None
    workflow_id: Any | None = None
    protocol: Any | None = None
    guideline_id: Any | None = None
    data: Any | None

    model_config = ConfigDict(populate_by_name=True)


class EVENT_CONTEXT(BaseModel):
    """EVENT_CONTEXT."""

    type: str = Field(default="EVENT_CONTEXT", alias="_type")
    health_care_facility: Any | None = None
    start_time: DV_DATE_TIME | None
    end_time: DV_DATE_TIME | None = None
    participations: list[PARTICIPATION] | None = None
    location: str | None = None
    setting: DV_CODED_TEXT | None
    other_context: Any | None = None

    model_config = ConfigDict(populate_by_name=True)


class EXTRACT(BaseModel):
    """EXTRACT."""

    type: str = Field(default="EXTRACT", alias="_type")
    uid: Any | None = None
    archetype_node_id: str
    name: Any | None
    archetype_details: ARCHETYPED | None = None
    feeder_audit: FEEDER_AUDIT | None = None
    links: list[LINK] | None = None
    request_id: HIER_OBJECT_ID | None = None
    time_created: DV_DATE_TIME | None
    system_id: HIER_OBJECT_ID | None
    sequence_nr: int
    specification: EXTRACT_SPEC | None = None
    chapters: list | None = None
    participations: list[EXTRACT_PARTICIPATION] | None = None

    model_config = ConfigDict(populate_by_name=True)


class EXTRACT_ACTION_REQUEST(BaseModel):
    """EXTRACT_ACTION_REQUEST."""

    type: str = Field(default="EXTRACT_ACTION_REQUEST", alias="_type")
    uid: HIER_OBJECT_ID | None
    archetype_node_id: str
    name: Any | None
    archetype_details: ARCHETYPED | None = None
    feeder_audit: FEEDER_AUDIT | None = None
    links: list[LINK] | None = None
    request_id: Any | None
    action: DV_CODED_TEXT | None

    model_config = ConfigDict(populate_by_name=True)


class EXTRACT_CHAPTER(BaseModel):
    """EXTRACT_CHAPTER."""

    type: str = Field(default="EXTRACT_CHAPTER", alias="_type")
    uid: Any | None = None
    archetype_node_id: str
    name: Any | None
    archetype_details: ARCHETYPED | None = None
    feeder_audit: FEEDER_AUDIT | None = None
    links: list[LINK] | None = None
    items: list | None = None

    model_config = ConfigDict(populate_by_name=True)


class EXTRACT_ENTITY_CHAPTER(BaseModel):
    """EXTRACT_ENTITY_CHAPTER."""

    type: str = Field(default="EXTRACT_ENTITY_CHAPTER", alias="_type")
    uid: Any | None = None
    archetype_node_id: str
    name: Any | None
    archetype_details: ARCHETYPED | None = None
    feeder_audit: FEEDER_AUDIT | None = None
    links: list[LINK] | None = None
    items: list | None = None
    extract_id_key: str

    model_config = ConfigDict(populate_by_name=True)


class EXTRACT_ENTITY_MANIFEST(BaseModel):
    """EXTRACT_ENTITY_MANIFEST."""

    type: str = Field(default="EXTRACT_ENTITY_MANIFEST", alias="_type")
    extract_id_key: str
    ehr_id: str | None = None
    subject_id: str | None = None
    other_ids: list | None = None
    item_list: list | None = None

    model_config = ConfigDict(populate_by_name=True)


class EXTRACT_FOLDER(BaseModel):
    """EXTRACT_FOLDER."""

    type: str = Field(default="EXTRACT_FOLDER", alias="_type")
    uid: Any | None = None
    archetype_node_id: str
    name: Any | None
    archetype_details: ARCHETYPED | None = None
    feeder_audit: FEEDER_AUDIT | None = None
    links: list[LINK] | None = None
    items: list | None = None

    model_config = ConfigDict(populate_by_name=True)


class EXTRACT_MANIFEST(BaseModel):
    """EXTRACT_MANIFEST."""

    type: str = Field(default="EXTRACT_MANIFEST", alias="_type")
    entities: list[EXTRACT_ENTITY_MANIFEST] | None = None

    model_config = ConfigDict(populate_by_name=True)


class EXTRACT_PARTICIPATION(BaseModel):
    """EXTRACT_PARTICIPATION."""

    type: str = Field(default="EXTRACT_PARTICIPATION", alias="_type")
    performer: str
    function: Any | None
    mode: DV_CODED_TEXT | None = None
    time: DV_INTERVAL | None = None

    model_config = ConfigDict(populate_by_name=True)


class EXTRACT_REQUEST(BaseModel):
    """EXTRACT_REQUEST."""

    type: str = Field(default="EXTRACT_REQUEST", alias="_type")
    uid: HIER_OBJECT_ID | None
    archetype_node_id: str
    name: Any | None
    archetype_details: ARCHETYPED | None = None
    feeder_audit: FEEDER_AUDIT | None = None
    links: list[LINK] | None = None
    extract_spec: EXTRACT_SPEC | None
    update_spec: EXTRACT_UPDATE_SPEC | None = None

    model_config = ConfigDict(populate_by_name=True)


class EXTRACT_SPEC(BaseModel):
    """EXTRACT_SPEC."""

    type: str = Field(default="EXTRACT_SPEC", alias="_type")
    extract_type: DV_CODED_TEXT | None
    include_multimedia: bool
    priority: int
    link_depth: int
    criteria: list[DV_PARSABLE] | None = None
    manifest: EXTRACT_MANIFEST | None
    version_spec: EXTRACT_VERSION_SPEC | None = None
    other_details: Any | None = None

    model_config = ConfigDict(populate_by_name=True)


class EXTRACT_UPDATE_SPEC(BaseModel):
    """EXTRACT_UPDATE_SPEC."""

    type: str = Field(default="EXTRACT_UPDATE_SPEC", alias="_type")
    persist_in_server: bool
    trigger_events: list[DV_CODED_TEXT] | None = None
    repeat_period: DV_DURATION | None = None
    update_method: CODE_PHRASE | None

    model_config = ConfigDict(populate_by_name=True)


class EXTRACT_VERSION_SPEC(BaseModel):
    """EXTRACT_VERSION_SPEC."""

    type: str = Field(default="EXTRACT_VERSION_SPEC", alias="_type")
    include_all_versions: bool
    commit_time_interval: DV_INTERVAL | None = None
    include_revision_history: bool
    include_data: bool

    model_config = ConfigDict(populate_by_name=True)


class FEEDER_AUDIT(BaseModel):
    """FEEDER_AUDIT."""

    type: str = Field(default="FEEDER_AUDIT", alias="_type")
    originating_system_item_ids: list[DV_IDENTIFIER] | None = None
    feeder_system_item_ids: list[DV_IDENTIFIER] | None = None
    original_content: Any | None = None
    originating_system_audit: FEEDER_AUDIT_DETAILS | None
    feeder_system_audit: FEEDER_AUDIT_DETAILS | None = None

    model_config = ConfigDict(populate_by_name=True)


class FEEDER_AUDIT_DETAILS(BaseModel):
    """FEEDER_AUDIT_DETAILS."""

    type: str = Field(default="FEEDER_AUDIT_DETAILS", alias="_type")
    system_id: str
    location: Any | None = None
    provider: Any | None = None
    subject: Any | None = None
    time: DV_DATE_TIME | None = None
    version_id: str | None = None
    other_details: Any | None = None

    model_config = ConfigDict(populate_by_name=True)


class FOLDER(BaseModel):
    """FOLDER."""

    type: str = Field(default="FOLDER", alias="_type")
    uid: Any | None = None
    archetype_node_id: str
    name: Any | None
    archetype_details: ARCHETYPED | None = None
    feeder_audit: FEEDER_AUDIT | None = None
    links: list[LINK] | None = None
    folders: list[FOLDER] | None = None
    items: list | None = None
    details: Any | None = None

    model_config = ConfigDict(populate_by_name=True)


class GENERIC_CONTENT_ITEM(BaseModel):
    """GENERIC_CONTENT_ITEM."""

    type: str = Field(default="GENERIC_CONTENT_ITEM", alias="_type")
    uid: Any | None = None
    archetype_node_id: str
    name: Any | None
    archetype_details: ARCHETYPED | None = None
    feeder_audit: FEEDER_AUDIT | None = None
    links: list[LINK] | None = None
    is_primary: bool
    is_changed: bool | None = None
    is_masked: bool | None = None
    item: Any | None = None
    item_type: DV_CODED_TEXT | None = None
    item_type_version: str | None = None
    author: str | None = None
    creation_time: str | None = None
    authoriser: str | None = None
    authorisation_time: str | None = None
    item_status: DV_CODED_TEXT | None = None
    version_id: str | None = None
    version_set_id: str | None = None
    system_id: str | None = None
    other_details: list | None = None

    model_config = ConfigDict(populate_by_name=True)


class GENERIC_ENTRY(BaseModel):
    """GENERIC_ENTRY."""

    type: str = Field(default="GENERIC_ENTRY", alias="_type")
    uid: Any | None = None
    archetype_node_id: str
    name: Any | None
    archetype_details: ARCHETYPED | None = None
    feeder_audit: FEEDER_AUDIT | None = None
    links: list[LINK] | None = None
    data: ITEM_TREE | None

    model_config = ConfigDict(populate_by_name=True)


class GENERIC_ID(BaseModel):
    """GENERIC_ID."""

    type: str = Field(default="GENERIC_ID", alias="_type")
    value: str
    scheme: str

    model_config = ConfigDict(populate_by_name=True)


class GROUP(BaseModel):
    """GROUP."""

    type: str = Field(default="GROUP", alias="_type")
    uid: Any | None
    archetype_node_id: str
    name: Any | None
    archetype_details: ARCHETYPED | None = None
    feeder_audit: FEEDER_AUDIT | None = None
    links: list[LINK] | None = None
    details: Any | None = None
    identities: list[PARTY_IDENTITY] | None
    contacts: list[CONTACT] | None = None
    relationships: list[PARTY_RELATIONSHIP] | None = None
    reverse_relationships: list[LOCATABLE_REF] | None = None
    roles: list[PARTY_REF] | None = None
    languages: list | None = None

    model_config = ConfigDict(populate_by_name=True)


class HIER_OBJECT_ID(BaseModel):
    """HIER_OBJECT_ID."""

    type: str = Field(default="HIER_OBJECT_ID", alias="_type")
    value: str

    model_config = ConfigDict(populate_by_name=True)


class HISTORY(BaseModel):
    """HISTORY."""

    type: str = Field(default="HISTORY", alias="_type")
    uid: Any | None = None
    archetype_node_id: str
    name: Any | None
    archetype_details: ARCHETYPED | None = None
    feeder_audit: FEEDER_AUDIT | None = None
    links: list[LINK] | None = None
    origin: DV_DATE_TIME | None = None
    period: DV_DURATION | None = None
    duration: DV_DURATION | None = None
    summary: Any | None = None
    events: list | None = None

    model_config = ConfigDict(populate_by_name=True)


class IMPORTED_VERSION(BaseModel):
    """IMPORTED_VERSION."""

    type: str = Field(default="IMPORTED_VERSION", alias="_type")
    contribution: Any | None
    commit_audit: Any | None
    signature: str | None = None
    item: ORIGINAL_VERSION | None

    model_config = ConfigDict(populate_by_name=True)


class INSTRUCTION(BaseModel):
    """INSTRUCTION."""

    type: str = Field(default="INSTRUCTION", alias="_type")
    uid: Any | None = None
    archetype_node_id: str
    name: Any | None
    archetype_details: ARCHETYPED | None = None
    feeder_audit: FEEDER_AUDIT | None = None
    links: list[LINK] | None = None
    language: CODE_PHRASE | None
    encoding: CODE_PHRASE | None
    subject: Any | None
    provider: Any | None = None
    other_participations: list[PARTICIPATION] | None = None
    workflow_id: Any | None = None
    protocol: Any | None = None
    guideline_id: Any | None = None
    narrative: Any | None
    expiry_time: DV_DATE_TIME | None = None
    wf_definition: DV_PARSABLE | None = None
    activities: list[ACTIVITY] | None = None

    model_config = ConfigDict(populate_by_name=True)


class INSTRUCTION_DETAILS(BaseModel):
    """INSTRUCTION_DETAILS."""

    type: str = Field(default="INSTRUCTION_DETAILS", alias="_type")
    instruction_id: LOCATABLE_REF | None
    wf_details: Any | None = None
    activity_id: str

    model_config = ConfigDict(populate_by_name=True)


class INTERNET_ID(BaseModel):
    """INTERNET_ID."""

    type: str = Field(default="INTERNET_ID", alias="_type")
    value: str

    model_config = ConfigDict(populate_by_name=True)


class INTERVAL(BaseModel):
    """INTERVAL."""

    type: str = Field(default="INTERVAL", alias="_type")
    lower_unbounded: bool
    upper_unbounded: bool
    lower_included: bool
    upper_included: bool

    model_config = ConfigDict(populate_by_name=True)


class INTERVAL_EVENT(BaseModel):
    """INTERVAL_EVENT."""

    type: str = Field(default="INTERVAL_EVENT", alias="_type")
    uid: Any | None = None
    archetype_node_id: str
    name: Any | None
    archetype_details: ARCHETYPED | None = None
    feeder_audit: FEEDER_AUDIT | None = None
    links: list[LINK] | None = None
    time: DV_DATE_TIME | None
    state: Any | None = None
    data: Any | None
    width: DV_DURATION | None
    sample_count: int | None = None
    math_function: DV_CODED_TEXT | None

    model_config = ConfigDict(populate_by_name=True)


class ISM_TRANSITION(BaseModel):
    """ISM_TRANSITION."""

    type: str = Field(default="ISM_TRANSITION", alias="_type")
    current_state: DV_CODED_TEXT | None
    transition: DV_CODED_TEXT | None = None
    careflow_step: DV_CODED_TEXT | None = None
    reason: list | None = None

    model_config = ConfigDict(populate_by_name=True)


class ISO8601_TYPE(BaseModel):
    """ISO8601_TYPE."""

    type: str = Field(default="ISO8601_TYPE", alias="_type")
    value: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class ISO_OID(BaseModel):
    """ISO_OID."""

    type: str = Field(default="ISO_OID", alias="_type")
    value: str

    model_config = ConfigDict(populate_by_name=True)


class ITEM_LIST(BaseModel):
    """ITEM_LIST."""

    type: str = Field(default="ITEM_LIST", alias="_type")
    uid: Any | None = None
    archetype_node_id: str
    name: Any | None
    archetype_details: ARCHETYPED | None = None
    feeder_audit: FEEDER_AUDIT | None = None
    links: list[LINK] | None = None
    items: list[ELEMENT] | None = None

    model_config = ConfigDict(populate_by_name=True)


class ITEM_SINGLE(BaseModel):
    """ITEM_SINGLE."""

    type: str = Field(default="ITEM_SINGLE", alias="_type")
    uid: Any | None = None
    archetype_node_id: str
    name: Any | None
    archetype_details: ARCHETYPED | None = None
    feeder_audit: FEEDER_AUDIT | None = None
    links: list[LINK] | None = None
    item: ELEMENT | None

    model_config = ConfigDict(populate_by_name=True)


class ITEM_TABLE(BaseModel):
    """ITEM_TABLE."""

    type: str = Field(default="ITEM_TABLE", alias="_type")
    uid: Any | None = None
    archetype_node_id: str
    name: Any | None
    archetype_details: ARCHETYPED | None = None
    feeder_audit: FEEDER_AUDIT | None = None
    links: list[LINK] | None = None
    rows: list[CLUSTER] | None = None

    model_config = ConfigDict(populate_by_name=True)


class ITEM_TREE(BaseModel):
    """ITEM_TREE."""

    type: str = Field(default="ITEM_TREE", alias="_type")
    uid: Any | None = None
    archetype_node_id: str
    name: Any | None
    archetype_details: ARCHETYPED | None = None
    feeder_audit: FEEDER_AUDIT | None = None
    links: list[LINK] | None = None
    items: list | None = None

    model_config = ConfigDict(populate_by_name=True)


class LINK(BaseModel):
    """LINK."""

    type: str = Field(default="LINK", alias="_type")
    meaning: Any | None
    target: DV_EHR_URI | None

    model_config = ConfigDict(populate_by_name=True)


class LIST(BaseModel):
    """LIST."""

    type: str = Field(default="LIST", alias="_type")

    model_config = ConfigDict(populate_by_name=True)


class LOCATABLE_REF(BaseModel):
    """LOCATABLE_REF."""

    type: str = Field(default="LOCATABLE_REF", alias="_type")
    id: Any | None
    namespace: str
    path: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class MESSAGE(BaseModel):
    """MESSAGE."""

    type: str = Field(default="MESSAGE", alias="_type")
    author: Any | None
    audit: Any | None
    content: Any | None
    signature: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class OBJECT_REF(BaseModel):
    """OBJECT_REF."""

    type: str = Field(default="OBJECT_REF", alias="_type")
    id: Any | None
    namespace: str

    model_config = ConfigDict(populate_by_name=True)


class OBJECT_VERSION_ID(BaseModel):
    """OBJECT_VERSION_ID."""

    type: str = Field(default="OBJECT_VERSION_ID", alias="_type")
    value: str

    model_config = ConfigDict(populate_by_name=True)


class OBSERVATION(BaseModel):
    """OBSERVATION."""

    type: str = Field(default="OBSERVATION", alias="_type")
    uid: Any | None = None
    archetype_node_id: str
    name: Any | None
    archetype_details: ARCHETYPED | None = None
    feeder_audit: FEEDER_AUDIT | None = None
    links: list[LINK] | None = None
    language: CODE_PHRASE | None
    encoding: CODE_PHRASE | None
    subject: Any | None
    provider: Any | None = None
    other_participations: list[PARTICIPATION] | None = None
    workflow_id: Any | None = None
    protocol: Any | None = None
    guideline_id: Any | None = None
    data: HISTORY | None
    state: HISTORY | None = None

    model_config = ConfigDict(populate_by_name=True)


class OPENEHR_CONTENT_ITEM(BaseModel):
    """OPENEHR_CONTENT_ITEM."""

    type: str = Field(default="OPENEHR_CONTENT_ITEM", alias="_type")
    uid: Any | None = None
    archetype_node_id: str
    name: Any | None
    archetype_details: ARCHETYPED | None = None
    feeder_audit: FEEDER_AUDIT | None = None
    links: list[LINK] | None = None
    is_primary: bool
    is_changed: bool | None = None
    is_masked: bool | None = None
    item: Any | None = None

    model_config = ConfigDict(populate_by_name=True)


class ORGANISATION(BaseModel):
    """ORGANISATION."""

    type: str = Field(default="ORGANISATION", alias="_type")
    uid: Any | None
    archetype_node_id: str
    name: Any | None
    archetype_details: ARCHETYPED | None = None
    feeder_audit: FEEDER_AUDIT | None = None
    links: list[LINK] | None = None
    details: Any | None = None
    identities: list[PARTY_IDENTITY] | None
    contacts: list[CONTACT] | None = None
    relationships: list[PARTY_RELATIONSHIP] | None = None
    reverse_relationships: list[LOCATABLE_REF] | None = None
    roles: list[PARTY_REF] | None = None
    languages: list | None = None

    model_config = ConfigDict(populate_by_name=True)


class ORIGINAL_VERSION(BaseModel):
    """ORIGINAL_VERSION."""

    type: str = Field(default="ORIGINAL_VERSION", alias="_type")
    contribution: Any | None
    commit_audit: Any | None
    signature: str | None = None
    uid: OBJECT_VERSION_ID | None
    preceding_version_uid: OBJECT_VERSION_ID | None = None
    other_input_version_uids: list[OBJECT_VERSION_ID] | None = None
    attestations: list[ATTESTATION] | None = None
    lifecycle_state: DV_CODED_TEXT | None

    model_config = ConfigDict(populate_by_name=True)


class PARTICIPATION(BaseModel):
    """PARTICIPATION."""

    type: str = Field(default="PARTICIPATION", alias="_type")
    function: Any | None
    time: DV_INTERVAL | None = None
    mode: DV_CODED_TEXT | None = None
    performer: Any | None

    model_config = ConfigDict(populate_by_name=True)


class PARTY_IDENTIFIED(BaseModel):
    """PARTY_IDENTIFIED."""

    type: str = Field(default="PARTY_IDENTIFIED", alias="_type")
    external_ref: PARTY_REF | None = None
    name: str | None = None
    identifiers: list[DV_IDENTIFIER] | None = None

    model_config = ConfigDict(populate_by_name=True)


class PARTY_IDENTITY(BaseModel):
    """PARTY_IDENTITY."""

    type: str = Field(default="PARTY_IDENTITY", alias="_type")
    uid: Any | None = None
    archetype_node_id: str
    name: Any | None
    archetype_details: ARCHETYPED | None = None
    feeder_audit: FEEDER_AUDIT | None = None
    links: list[LINK] | None = None
    details: Any | None

    model_config = ConfigDict(populate_by_name=True)


class PARTY_REF(BaseModel):
    """PARTY_REF."""

    type: str = Field(default="PARTY_REF", alias="_type")
    id: Any | None
    namespace: str

    model_config = ConfigDict(populate_by_name=True)


class PARTY_RELATED(BaseModel):
    """PARTY_RELATED."""

    type: str = Field(default="PARTY_RELATED", alias="_type")
    external_ref: PARTY_REF | None = None
    name: str | None = None
    identifiers: list[DV_IDENTIFIER] | None = None
    relationship: DV_CODED_TEXT | None

    model_config = ConfigDict(populate_by_name=True)


class PARTY_RELATIONSHIP(BaseModel):
    """PARTY_RELATIONSHIP."""

    type: str = Field(default="PARTY_RELATIONSHIP", alias="_type")
    uid: Any | None = None
    archetype_node_id: str
    name: Any | None
    archetype_details: ARCHETYPED | None = None
    feeder_audit: FEEDER_AUDIT | None = None
    links: list[LINK] | None = None
    source: PARTY_REF | None
    target: PARTY_REF | None
    details: Any | None = None
    time_validity: DV_INTERVAL | None = None

    model_config = ConfigDict(populate_by_name=True)


class PARTY_SELF(BaseModel):
    """PARTY_SELF."""

    type: str = Field(default="PARTY_SELF", alias="_type")
    external_ref: PARTY_REF | None = None

    model_config = ConfigDict(populate_by_name=True)


class PERSON(BaseModel):
    """PERSON."""

    type: str = Field(default="PERSON", alias="_type")
    uid: Any | None
    archetype_node_id: str
    name: Any | None
    archetype_details: ARCHETYPED | None = None
    feeder_audit: FEEDER_AUDIT | None = None
    links: list[LINK] | None = None
    details: Any | None = None
    identities: list[PARTY_IDENTITY] | None
    contacts: list[CONTACT] | None = None
    relationships: list[PARTY_RELATIONSHIP] | None = None
    reverse_relationships: list[LOCATABLE_REF] | None = None
    roles: list[PARTY_REF] | None = None
    languages: list | None = None

    model_config = ConfigDict(populate_by_name=True)


class POINT_EVENT(BaseModel):
    """POINT_EVENT."""

    type: str = Field(default="POINT_EVENT", alias="_type")
    uid: Any | None = None
    archetype_node_id: str
    name: Any | None
    archetype_details: ARCHETYPED | None = None
    feeder_audit: FEEDER_AUDIT | None = None
    links: list[LINK] | None = None
    time: DV_DATE_TIME | None
    state: Any | None = None
    data: Any | None

    model_config = ConfigDict(populate_by_name=True)


class REFERENCE_RANGE(BaseModel):
    """REFERENCE_RANGE."""

    type: str = Field(default="REFERENCE_RANGE", alias="_type")
    range: DV_INTERVAL | None
    meaning: Any | None

    model_config = ConfigDict(populate_by_name=True)


class RESOURCE_DESCRIPTION(BaseModel):
    """RESOURCE_DESCRIPTION."""

    type: str = Field(default="RESOURCE_DESCRIPTION", alias="_type")
    other_contributors: list | None = None
    lifecycle_state: str
    resource_package_uri: str | None = None
    details: list[RESOURCE_DESCRIPTION_ITEM] | None

    model_config = ConfigDict(populate_by_name=True)


class RESOURCE_DESCRIPTION_ITEM(BaseModel):
    """RESOURCE_DESCRIPTION_ITEM."""

    type: str = Field(default="RESOURCE_DESCRIPTION_ITEM", alias="_type")
    language: TERMINOLOGY_CODE | None
    purpose: str
    keywords: list | None = None
    use: str | None = None
    misuse: str | None = None
    copyright: str | None = None
    original_resource_uri: list | None = None

    model_config = ConfigDict(populate_by_name=True)


class REVISION_HISTORY(BaseModel):
    """REVISION_HISTORY."""

    type: str = Field(default="REVISION_HISTORY", alias="_type")
    items: list[REVISION_HISTORY_ITEM] | None

    model_config = ConfigDict(populate_by_name=True)


class REVISION_HISTORY_ITEM(BaseModel):
    """REVISION_HISTORY_ITEM."""

    type: str = Field(default="REVISION_HISTORY_ITEM", alias="_type")
    version_id: OBJECT_VERSION_ID | None
    audits: list

    model_config = ConfigDict(populate_by_name=True)


class ROLE(BaseModel):
    """ROLE."""

    type: str = Field(default="ROLE", alias="_type")
    uid: Any | None
    archetype_node_id: str
    name: Any | None
    archetype_details: ARCHETYPED | None = None
    feeder_audit: FEEDER_AUDIT | None = None
    links: list[LINK] | None = None
    details: Any | None = None
    identities: list[PARTY_IDENTITY] | None
    contacts: list[CONTACT] | None = None
    relationships: list[PARTY_RELATIONSHIP] | None = None
    reverse_relationships: list[LOCATABLE_REF] | None = None
    performer: PARTY_REF | None
    capabilities: list[CAPABILITY] | None = None
    time_validity: DV_INTERVAL | None = None

    model_config = ConfigDict(populate_by_name=True)


class SECTION(BaseModel):
    """SECTION."""

    type: str = Field(default="SECTION", alias="_type")
    uid: Any | None = None
    archetype_node_id: str
    name: Any | None
    archetype_details: ARCHETYPED | None = None
    feeder_audit: FEEDER_AUDIT | None = None
    links: list[LINK] | None = None
    items: list | None = None

    model_config = ConfigDict(populate_by_name=True)


class SET(BaseModel):
    """SET."""

    type: str = Field(default="SET", alias="_type")

    model_config = ConfigDict(populate_by_name=True)


class SYNC_EXTRACT(BaseModel):
    """SYNC_EXTRACT."""

    type: str = Field(default="SYNC_EXTRACT", alias="_type")
    uid: Any | None = None
    archetype_node_id: str
    name: Any | None
    archetype_details: ARCHETYPED | None = None
    feeder_audit: FEEDER_AUDIT | None = None
    links: list[LINK] | None = None
    specification: SYNC_EXTRACT_SPEC | None
    items: list[X_CONTRIBUTION] | None = None

    model_config = ConfigDict(populate_by_name=True)


class SYNC_EXTRACT_REQUEST(BaseModel):
    """SYNC_EXTRACT_REQUEST."""

    type: str = Field(default="SYNC_EXTRACT_REQUEST", alias="_type")
    uid: Any | None = None
    archetype_node_id: str
    name: Any | None
    archetype_details: ARCHETYPED | None = None
    feeder_audit: FEEDER_AUDIT | None = None
    links: list[LINK] | None = None
    specification: SYNC_EXTRACT_SPEC | None

    model_config = ConfigDict(populate_by_name=True)


class SYNC_EXTRACT_SPEC(BaseModel):
    """SYNC_EXTRACT_SPEC."""

    type: str = Field(default="SYNC_EXTRACT_SPEC", alias="_type")
    includes_versions: bool
    contribution_list: list[HIER_OBJECT_ID] | None = None
    contributions_since: DV_DATE_TIME | None = None
    all_contributions: bool | None = None

    model_config = ConfigDict(populate_by_name=True)


class TEMPLATE_ID(BaseModel):
    """TEMPLATE_ID."""

    type: str = Field(default="TEMPLATE_ID", alias="_type")
    value: str

    model_config = ConfigDict(populate_by_name=True)


class TERMINOLOGY_CODE(BaseModel):
    """TERMINOLOGY_CODE."""

    type: str = Field(default="TERMINOLOGY_CODE", alias="_type")
    terminology_id: str
    terminology_version: str | None = None
    code_string: str
    uri: URI | None

    model_config = ConfigDict(populate_by_name=True)


class TERMINOLOGY_ID(BaseModel):
    """TERMINOLOGY_ID."""

    type: str = Field(default="TERMINOLOGY_ID", alias="_type")
    value: str

    model_config = ConfigDict(populate_by_name=True)


class TERMINOLOGY_TERM(BaseModel):
    """TERMINOLOGY_TERM."""

    type: str = Field(default="TERMINOLOGY_TERM", alias="_type")
    text: str
    concept: TERMINOLOGY_CODE | None

    model_config = ConfigDict(populate_by_name=True)


class TERM_MAPPING(BaseModel):
    """TERM_MAPPING."""

    type: str = Field(default="TERM_MAPPING", alias="_type")
    match: str
    purpose: DV_CODED_TEXT | None = None
    target: CODE_PHRASE | None

    model_config = ConfigDict(populate_by_name=True)


class TIME(BaseModel):
    """TIME."""

    type: str = Field(default="TIME", alias="_type")
    value: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class TRANSLATION_DETAILS(BaseModel):
    """TRANSLATION_DETAILS."""

    type: str = Field(default="TRANSLATION_DETAILS", alias="_type")
    language: TERMINOLOGY_CODE | None
    accreditation: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class URI(BaseModel):
    """URI."""

    type: str = Field(default="URI", alias="_type")

    model_config = ConfigDict(populate_by_name=True)


class UUID(BaseModel):
    """UUID."""

    type: str = Field(default="UUID", alias="_type")
    value: str

    model_config = ConfigDict(populate_by_name=True)


class VALIDITY_KIND(BaseModel):
    """VALIDITY_KIND."""

    type: str = Field(default="VALIDITY_KIND", alias="_type")

    model_config = ConfigDict(populate_by_name=True)


class VERSIONED_OBJECT(BaseModel):
    """VERSIONED_OBJECT."""

    type: str = Field(default="VERSIONED_OBJECT", alias="_type")
    uid: HIER_OBJECT_ID | None
    owner_id: Any | None
    time_created: DV_DATE_TIME | None

    model_config = ConfigDict(populate_by_name=True)


class VERSION_STATUS(BaseModel):
    """VERSION_STATUS."""

    type: str = Field(default="VERSION_STATUS", alias="_type")

    model_config = ConfigDict(populate_by_name=True)


class VERSION_TREE_ID(BaseModel):
    """VERSION_TREE_ID."""

    type: str = Field(default="VERSION_TREE_ID", alias="_type")
    value: str

    model_config = ConfigDict(populate_by_name=True)


class X_CONTRIBUTION(BaseModel):
    """X_CONTRIBUTION."""

    type: str = Field(default="X_CONTRIBUTION", alias="_type")
    uid: HIER_OBJECT_ID | None
    audit: Any | None
    versions: list | None = None

    model_config = ConfigDict(populate_by_name=True)


class X_VERSIONED_COMPOSITION(BaseModel):
    """X_VERSIONED_COMPOSITION."""

    type: str = Field(default="X_VERSIONED_COMPOSITION", alias="_type")
    uid: HIER_OBJECT_ID | None
    owner_id: Any | None
    time_created: DV_DATE_TIME | None
    total_version_count: int
    extract_version_count: int
    revision_history: REVISION_HISTORY | None = None
    versions: list[ORIGINAL_VERSION] | None = None

    model_config = ConfigDict(populate_by_name=True)


class X_VERSIONED_EHR_ACCESS(BaseModel):
    """X_VERSIONED_EHR_ACCESS."""

    type: str = Field(default="X_VERSIONED_EHR_ACCESS", alias="_type")
    uid: HIER_OBJECT_ID | None
    owner_id: Any | None
    time_created: DV_DATE_TIME | None
    total_version_count: int
    extract_version_count: int
    revision_history: REVISION_HISTORY | None = None
    versions: list[ORIGINAL_VERSION] | None = None

    model_config = ConfigDict(populate_by_name=True)


class X_VERSIONED_EHR_STATUS(BaseModel):
    """X_VERSIONED_EHR_STATUS."""

    type: str = Field(default="X_VERSIONED_EHR_STATUS", alias="_type")
    uid: HIER_OBJECT_ID | None
    owner_id: Any | None
    time_created: DV_DATE_TIME | None
    total_version_count: int
    extract_version_count: int
    revision_history: REVISION_HISTORY | None = None
    versions: list[ORIGINAL_VERSION] | None = None

    model_config = ConfigDict(populate_by_name=True)


class X_VERSIONED_FOLDER(BaseModel):
    """X_VERSIONED_FOLDER."""

    type: str = Field(default="X_VERSIONED_FOLDER", alias="_type")
    uid: HIER_OBJECT_ID | None
    owner_id: Any | None
    time_created: DV_DATE_TIME | None
    total_version_count: int
    extract_version_count: int
    revision_history: REVISION_HISTORY | None = None
    versions: list[ORIGINAL_VERSION] | None = None

    model_config = ConfigDict(populate_by_name=True)


class X_VERSIONED_OBJECT(BaseModel):
    """X_VERSIONED_OBJECT."""

    type: str = Field(default="X_VERSIONED_OBJECT", alias="_type")
    uid: HIER_OBJECT_ID | None
    owner_id: Any | None
    time_created: DV_DATE_TIME | None
    total_version_count: int
    extract_version_count: int
    revision_history: REVISION_HISTORY | None = None
    versions: list[ORIGINAL_VERSION] | None = None

    model_config = ConfigDict(populate_by_name=True)


class X_VERSIONED_PARTY(BaseModel):
    """X_VERSIONED_PARTY."""

    type: str = Field(default="X_VERSIONED_PARTY", alias="_type")
    uid: HIER_OBJECT_ID | None
    owner_id: Any | None
    time_created: DV_DATE_TIME | None
    total_version_count: int
    extract_version_count: int
    revision_history: REVISION_HISTORY | None = None
    versions: list[ORIGINAL_VERSION] | None = None

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
