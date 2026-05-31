"""Builder for openEHR CONTRIBUTION request bodies.

A CONTRIBUTION groups one or more versioned-object changes (compositions) into a
single atomic changeset with shared audit metadata. The EHRBase contribution
endpoint consumes a CANONICAL ``CONTRIBUTION`` whose ``versions`` array holds
``ORIGINAL_VERSION`` wrappers. Assembling those nested structures by hand is
error-prone, so :class:`ContributionBuilder` provides a fluent API.

Example::

    from oehrpy.client import ContributionBuilder

    contribution = (
        ContributionBuilder()
        .add_creation(composition=vitals_canonical)
        .add_amendment(
            preceding_version_uid="abc::ehrbase::1",
            composition=updated_canonical,
            description="Corrected systolic value",
        )
        .set_audit(committer="Dr. Smith", description="Routine vitals and correction")
        .build()
    )

    result = await client.create_contribution(ehr_id, contribution)

See PRD-0003 (Audit & Contributions) for the full specification.
"""

from __future__ import annotations

from typing import Any

# openEHR change-type terminology codes (terminology id "openehr").
_CHANGE_TYPE_CODES: dict[str, str] = {
    "creation": "249",
    "amendment": "250",
    "modification": "251",
    "deleted": "523",
}


def _coded_text(value: str, code_string: str) -> dict[str, Any]:
    """Build a DV_CODED_TEXT block using the ``openehr`` terminology."""
    return {
        "_type": "DV_CODED_TEXT",
        "value": value,
        "defining_code": {
            "_type": "CODE_PHRASE",
            "terminology_id": {"_type": "TERMINOLOGY_ID", "value": "openehr"},
            "code_string": code_string,
        },
    }


def _audit_details(
    change_type: str,
    *,
    committer: str | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    """Build an AUDIT_DETAILS block.

    ``committer`` and ``time_committed`` may be omitted so the server can fill
    them in from the authenticated principal.
    """
    audit: dict[str, Any] = {
        "_type": "AUDIT_DETAILS",
        "change_type": _coded_text(change_type, _CHANGE_TYPE_CODES[change_type]),
    }
    if committer is not None:
        audit["committer"] = {"_type": "PARTY_IDENTIFIED", "name": committer}
    if description is not None:
        audit["description"] = {"_type": "DV_TEXT", "value": description}
    return audit


def _lifecycle_state(state: str) -> dict[str, Any]:
    """Build a DV_CODED_TEXT lifecycle_state block.

    openEHR ``version lifecycle states`` terminology (group 273):
    ``532`` complete, ``531`` incomplete, ``533`` deleted.
    """
    codes = {"complete": "532", "incomplete": "531", "deleted": "533"}
    return _coded_text(state, codes.get(state, "532"))


class ContributionBuilder:
    """Fluent builder for a CANONICAL openEHR CONTRIBUTION request body.

    Compositions are accepted as already-CANONICAL dicts (the
    ``oehrpy.serialization.canonical`` layer can produce these from RM objects).
    Call ``add_*`` for each change, optionally ``set_audit`` for contribution-
    level audit, then ``build()`` to obtain the request body.
    """

    def __init__(self) -> None:
        self._versions: list[dict[str, Any]] = []
        self._audit: dict[str, Any] | None = None

    def _add_version(
        self,
        change_type: str,
        *,
        composition: dict[str, Any] | None,
        preceding_version_uid: str | None,
        lifecycle_state: str,
        description: str | None,
    ) -> ContributionBuilder:
        version: dict[str, Any] = {
            "_type": "ORIGINAL_VERSION",
            "commit_audit": _audit_details(change_type, description=description),
            "lifecycle_state": _lifecycle_state(lifecycle_state),
        }
        if preceding_version_uid is not None:
            version["preceding_version_uid"] = {
                "_type": "OBJECT_VERSION_ID",
                "value": preceding_version_uid,
            }
        if composition is not None:
            version["data"] = composition
        self._versions.append(version)
        return self

    def add_creation(
        self,
        composition: dict[str, Any],
        *,
        lifecycle_state: str = "complete",
        description: str | None = None,
    ) -> ContributionBuilder:
        """Append a ``creation`` version for a brand-new composition."""
        return self._add_version(
            "creation",
            composition=composition,
            preceding_version_uid=None,
            lifecycle_state=lifecycle_state,
            description=description,
        )

    def add_amendment(
        self,
        preceding_version_uid: str,
        composition: dict[str, Any],
        *,
        lifecycle_state: str = "complete",
        description: str | None = None,
    ) -> ContributionBuilder:
        """Append an ``amendment`` version updating an existing composition."""
        return self._add_version(
            "amendment",
            composition=composition,
            preceding_version_uid=preceding_version_uid,
            lifecycle_state=lifecycle_state,
            description=description,
        )

    def add_modification(
        self,
        preceding_version_uid: str,
        composition: dict[str, Any],
        *,
        lifecycle_state: str = "complete",
        description: str | None = None,
    ) -> ContributionBuilder:
        """Append a ``modification`` version updating an existing composition."""
        return self._add_version(
            "modification",
            composition=composition,
            preceding_version_uid=preceding_version_uid,
            lifecycle_state=lifecycle_state,
            description=description,
        )

    def add_deletion(
        self,
        preceding_version_uid: str,
        *,
        description: str | None = None,
    ) -> ContributionBuilder:
        """Append a ``deleted`` version (logical deletion; no ``data``)."""
        return self._add_version(
            "deleted",
            composition=None,
            preceding_version_uid=preceding_version_uid,
            lifecycle_state="deleted",
            description=description,
        )

    def set_audit(
        self,
        *,
        committer: str | None = None,
        description: str | None = None,
        change_type: str = "creation",
    ) -> ContributionBuilder:
        """Set the contribution-level AUDIT_DETAILS.

        Both ``committer`` and ``description`` are optional; when omitted the
        server fills in the committer from the authenticated principal.
        """
        self._audit = _audit_details(change_type, committer=committer, description=description)
        return self

    def build(self) -> dict[str, Any]:
        """Assemble and return the CANONICAL CONTRIBUTION request body.

        Raises:
            ValueError: If no versions have been added.
        """
        if not self._versions:
            raise ValueError("A contribution must contain at least one version.")
        body: dict[str, Any] = {
            "_type": "CONTRIBUTION",
            "versions": list(self._versions),
        }
        if self._audit is not None:
            body["audit"] = self._audit
        return body
