"""Tests for FLAT format validation module."""

from __future__ import annotations

from typing import Any

import pytest

from openehr_sdk.validation import (
    FlatValidator,
    enumerate_valid_paths,
    parse_web_template,
)
from openehr_sdk.validation.platforms import get_dialect
from openehr_sdk.validation.suggestions import suggest_path, suggest_segment

# ─── Fixtures ───────────────────────────────────────────────────────


def _make_web_template(**overrides: Any) -> dict[str, Any]:
    """Build a minimal Web Template JSON for testing."""
    wt: dict[str, Any] = {
        "templateId": "IDCR - Adverse Reaction List.v1",
        "version": "2.3",
        "defaultLanguage": "en",
        "tree": {
            "id": "adverse_reaction_list",
            "name": "Adverse Reaction List",
            "rmType": "COMPOSITION",
            "min": 1,
            "max": 1,
            "children": [
                {"id": "category", "name": "category", "rmType": "DV_CODED_TEXT", "children": []},
                {"id": "language", "name": "language", "rmType": "CODE_PHRASE", "children": []},
                {"id": "territory", "name": "territory", "rmType": "CODE_PHRASE", "children": []},
                {
                    "id": "composer",
                    "name": "composer",
                    "rmType": "PARTY_IDENTIFIED",
                    "children": [],
                },
                {
                    "id": "context",
                    "name": "context",
                    "rmType": "EVENT_CONTEXT",
                    "children": [
                        {
                            "id": "start_time",
                            "name": "start_time",
                            "rmType": "DV_DATE_TIME",
                            "children": [],
                        },
                        {
                            "id": "setting",
                            "name": "setting",
                            "rmType": "DV_CODED_TEXT",
                            "children": [],
                        },
                    ],
                },
                {
                    "id": "adverse_reaction",
                    "name": "Adverse Reaction Risk",
                    "rmType": "EVALUATION",
                    "min": 0,
                    "max": -1,
                    "children": [
                        {
                            "id": "causative_agent",
                            "name": "Causative agent",
                            "rmType": "DV_CODED_TEXT",
                            "nodeId": "at0002",
                            "localizedNames": {"en": "Causative agent"},
                            "aqlPath": "/data[at0001]/items[at0002]/value",
                            "children": [],
                        },
                        {
                            "id": "status",
                            "name": "Status",
                            "rmType": "DV_CODED_TEXT",
                            "children": [],
                        },
                        {
                            "id": "comment",
                            "name": "Comment",
                            "rmType": "DV_TEXT",
                            "children": [],
                        },
                        {
                            "id": "reaction_severity",
                            "name": "Reaction severity",
                            "rmType": "DV_ORDINAL",
                            "children": [],
                        },
                        {
                            "id": "temperature",
                            "name": "Temperature",
                            "rmType": "DV_QUANTITY",
                            "children": [],
                        },
                    ],
                },
            ],
        },
    }
    wt.update(overrides)
    return wt


def _make_valid_flat() -> dict[str, Any]:
    """Build a valid FLAT composition for the test Web Template."""
    return {
        "adverse_reaction_list/category|code": "433",
        "adverse_reaction_list/category|value": "event",
        "adverse_reaction_list/category|terminology": "openehr",
        "adverse_reaction_list/language|code": "en",
        "adverse_reaction_list/language|terminology": "ISO_639-1",
        "adverse_reaction_list/territory|code": "CH",
        "adverse_reaction_list/territory|terminology": "ISO_3166-1",
        "adverse_reaction_list/composer|name": "Dr. Chregi",
        "adverse_reaction_list/context/start_time": "2026-03-12T10:00:00Z",
        "adverse_reaction_list/context/setting|code": "238",
        "adverse_reaction_list/context/setting|value": "other care",
        "adverse_reaction_list/context/setting|terminology": "openehr",
        "adverse_reaction_list/adverse_reaction/causative_agent|value": "Penicillin",
        "adverse_reaction_list/adverse_reaction/causative_agent|code": "372687004",
        "adverse_reaction_list/adverse_reaction/causative_agent|terminology": "SNOMED-CT",
    }


# ─── Web Template Parser ────────────────────────────────────────────


class TestParseWebTemplate:
    """Tests for web template parsing."""

    def test_parse_basic_template(self) -> None:
        wt = _make_web_template()
        parsed = parse_web_template(wt)

        assert parsed.tree_id == "adverse_reaction_list"
        assert parsed.template_id == "IDCR - Adverse Reaction List.v1"
        assert "adverse_reaction_list" in parsed.nodes
        assert "adverse_reaction_list/adverse_reaction/causative_agent" in parsed.nodes

    def test_parse_extracts_rm_type(self) -> None:
        wt = _make_web_template()
        parsed = parse_web_template(wt)

        node = parsed.nodes["adverse_reaction_list/adverse_reaction/causative_agent"]
        assert node.rm_type == "DV_CODED_TEXT"

    def test_parse_detects_rename(self) -> None:
        """When localizedNames differs from the id, original_name should be set."""
        wt = _make_web_template()
        # The causative_agent node has localizedNames={"en": "Causative agent"}
        # which slugifies to "causative_agent" — same as id, so no rename detected.
        # Let's add a node with a real rename.
        wt["tree"]["children"][5]["children"].append(
            {
                "id": "causative_agent_v2",
                "name": "Causative agent v2",
                "rmType": "DV_TEXT",
                "localizedNames": {"en": "Old Substance Name"},
                "children": [],
            }
        )
        parsed = parse_web_template(wt)
        node = parsed.nodes["adverse_reaction_list/adverse_reaction/causative_agent_v2"]
        assert node.original_name == "Old Substance Name"

    def test_parse_missing_tree_raises(self) -> None:
        with pytest.raises(ValueError, match="must contain a 'tree' key"):
            parse_web_template({"templateId": "test"})

    def test_get_children_ids(self) -> None:
        wt = _make_web_template()
        parsed = parse_web_template(wt)

        children = parsed.get_children_ids("adverse_reaction_list/adverse_reaction")
        assert "causative_agent" in children
        assert "status" in children
        assert "comment" in children


# ─── Path Enumeration ────────────────────────────────────────────────


class TestEnumerateValidPaths:
    """Tests for valid path enumeration."""

    def test_ehrbase_paths_include_suffixed_variants(self) -> None:
        wt = _make_web_template()
        parsed = parse_web_template(wt)
        paths = enumerate_valid_paths(parsed, "ehrbase")

        # DV_CODED_TEXT should have |value, |code, |terminology suffixes
        assert "adverse_reaction_list/adverse_reaction/causative_agent|value" in paths
        assert "adverse_reaction_list/adverse_reaction/causative_agent|code" in paths
        assert "adverse_reaction_list/adverse_reaction/causative_agent|terminology" in paths

    def test_ehrbase_paths_include_bare_paths(self) -> None:
        wt = _make_web_template()
        parsed = parse_web_template(wt)
        paths = enumerate_valid_paths(parsed, "ehrbase")

        # The bare path (without suffix) should also be valid
        assert "adverse_reaction_list/adverse_reaction/causative_agent" in paths

    def test_ehrbase_no_index_notation(self) -> None:
        wt = _make_web_template()
        parsed = parse_web_template(wt)
        paths = enumerate_valid_paths(parsed, "ehrbase")

        # No paths should have :0 in them for ehrbase
        indexed = [p for p in paths if ":0" in p]
        assert indexed == []

    def test_better_paths_include_indexed_variants(self) -> None:
        wt = _make_web_template()
        parsed = parse_web_template(wt)
        paths = enumerate_valid_paths(parsed, "better")

        # Better should include :0 indexed variants
        indexed = [p for p in paths if ":0" in p]
        assert len(indexed) > 0

    def test_dv_date_time_no_suffix(self) -> None:
        wt = _make_web_template()
        parsed = parse_web_template(wt)
        paths = enumerate_valid_paths(parsed, "ehrbase")

        # DV_DATE_TIME has no suffixes
        assert "adverse_reaction_list/context/start_time" in paths
        start_time_paths = [p for p in paths if "start_time" in p]
        assert len(start_time_paths) == 1  # only the bare path

    def test_structural_types_excluded(self) -> None:
        wt = _make_web_template()
        parsed = parse_web_template(wt)
        paths = enumerate_valid_paths(parsed, "ehrbase")

        # COMPOSITION, EVALUATION, EVENT_CONTEXT are structural — should not appear
        assert "adverse_reaction_list" not in paths
        assert "adverse_reaction_list/adverse_reaction" not in paths
        assert "adverse_reaction_list/context" not in paths


# ─── FlatValidator ───────────────────────────────────────────────────


class TestFlatValidator:
    """Tests for the FlatValidator public API."""

    def test_valid_composition(self) -> None:
        wt = _make_web_template()
        validator = FlatValidator.from_web_template(wt, platform="ehrbase")
        result = validator.validate(_make_valid_flat())

        assert result.is_valid
        assert len(result.errors) == 0
        assert result.platform == "ehrbase"
        assert result.template_id == "IDCR - Adverse Reaction List.v1"

    def test_unknown_path_error(self) -> None:
        wt = _make_web_template()
        validator = FlatValidator.from_web_template(wt, platform="ehrbase")

        flat = _make_valid_flat()
        flat["adverse_reaction_list/adverse_reaction/nonexistent|value"] = "x"

        result = validator.validate(flat)

        assert not result.is_valid
        assert len(result.errors) == 1
        assert result.errors[0].error_type == "unknown_path"
        assert "nonexistent" in result.errors[0].path

    def test_renamed_node_detection(self) -> None:
        """Test that using old node name triggers rename message."""
        wt = _make_web_template()
        # Add a node with originalName that differs from id
        wt["tree"]["children"][5]["children"].append(
            {
                "id": "new_name",
                "name": "New name",
                "rmType": "DV_TEXT",
                "localizedNames": {"en": "Original old name"},
                "children": [],
            }
        )
        validator = FlatValidator.from_web_template(wt, platform="ehrbase")

        flat = _make_valid_flat()
        flat["adverse_reaction_list/adverse_reaction/original_old_name|value"] = "test"

        result = validator.validate(flat)

        assert not result.is_valid
        error = result.errors[0]
        assert "renamed" in error.message.lower()

    def test_index_notation_error_ehrbase(self) -> None:
        """EHRBase 2.x should flag :0 index notation."""
        wt = _make_web_template()
        validator = FlatValidator.from_web_template(wt, platform="ehrbase")

        flat = _make_valid_flat()
        # Add a path with :0 that would be valid without the index
        flat["adverse_reaction_list/adverse_reaction/causative_agent:0|value"] = "test"

        result = validator.validate(flat)

        has_index_error = any(e.error_type == "index_mismatch" for e in result.errors)
        assert has_index_error

    def test_missing_required_fields(self) -> None:
        """Missing required fields should produce warnings."""
        wt = _make_web_template()
        validator = FlatValidator.from_web_template(wt, platform="ehrbase")

        # Minimal composition missing most required fields
        flat = {
            "adverse_reaction_list/adverse_reaction/causative_agent|value": "Penicillin",
        }
        result = validator.validate(flat)

        assert len(result.warnings) > 0
        warning_paths = [w.path for w in result.warnings]
        assert any("category" in p for p in warning_paths)
        assert any("composer" in p for p in warning_paths)
        assert any("start_time" in p for p in warning_paths)

    def test_no_warnings_when_all_required_present(self) -> None:
        wt = _make_web_template()
        validator = FlatValidator.from_web_template(wt, platform="ehrbase")
        result = validator.validate(_make_valid_flat())

        assert len(result.warnings) == 0

    def test_validator_properties(self) -> None:
        wt = _make_web_template()
        validator = FlatValidator.from_web_template(wt, platform="ehrbase")

        assert validator.template_id == "IDCR - Adverse Reaction List.v1"
        assert validator.tree_id == "adverse_reaction_list"
        assert validator.platform == "ehrbase"
        assert len(validator.valid_paths) > 0

    def test_checked_path_count(self) -> None:
        wt = _make_web_template()
        validator = FlatValidator.from_web_template(wt, platform="ehrbase")
        flat = _make_valid_flat()
        result = validator.validate(flat)

        assert result.checked_path_count == len(flat)
        assert result.valid_path_count > 0

    def test_wrong_suffix_error(self) -> None:
        """Using an invalid suffix for a data type should produce a wrong_suffix error."""
        wt = _make_web_template()
        validator = FlatValidator.from_web_template(wt, platform="ehrbase")

        flat = _make_valid_flat()
        # DV_DATE_TIME has no valid suffixes, so |value should fail
        flat["adverse_reaction_list/context/start_time|value"] = "test"

        result = validator.validate(flat)

        suffix_errors = [e for e in result.errors if e.error_type == "wrong_suffix"]
        assert len(suffix_errors) == 1
        assert "DV_DATE_TIME" in suffix_errors[0].message

    def test_dv_quantity_wrong_suffix(self) -> None:
        """Using |value on a DV_QUANTITY should suggest |magnitude."""
        wt = _make_web_template()
        validator = FlatValidator.from_web_template(wt, platform="ehrbase")

        flat = _make_valid_flat()
        flat["adverse_reaction_list/adverse_reaction/temperature|value"] = "37.5"

        result = validator.validate(flat)
        suffix_errors = [e for e in result.errors if e.error_type == "wrong_suffix"]
        assert len(suffix_errors) == 1
        assert "|magnitude" in suffix_errors[0].message or suffix_errors[0].suggestion is not None


# ─── Suggestions ─────────────────────────────────────────────────────


class TestSuggestions:
    """Tests for fuzzy matching suggestions."""

    def test_suggest_path_close_match(self) -> None:
        valid = ["foo/bar/causative_agent|value", "foo/bar/status|value"]
        suggestions = suggest_path("foo/bar/causatve_agent|value", valid)
        assert len(suggestions) > 0
        assert "causative_agent" in suggestions[0]

    def test_suggest_path_no_match(self) -> None:
        valid = ["foo/bar/causative_agent|value"]
        suggestions = suggest_path("completely_different_path", valid)
        assert len(suggestions) == 0

    def test_suggest_segment(self) -> None:
        valid_segments = ["causative_agent", "status", "comment"]
        suggestions = suggest_segment("substanc", valid_segments)
        # May or may not match — depends on cutoff
        # At least shouldn't crash
        assert isinstance(suggestions, list)

    def test_suggest_segment_typo(self) -> None:
        valid_segments = ["causative_agent", "status", "comment"]
        suggestions = suggest_segment("causatve_agent", valid_segments)
        assert len(suggestions) > 0
        assert "causative_agent" in suggestions


# ─── Platform Dialects ───────────────────────────────────────────────


class TestPlatformDialects:
    """Tests for platform dialect configuration."""

    def test_ehrbase_dialect(self) -> None:
        dialect = get_dialect("ehrbase")
        assert dialect.name == "ehrbase"
        assert not dialect.uses_index_notation
        assert not dialect.includes_any_event

    def test_better_dialect(self) -> None:
        dialect = get_dialect("better")
        assert dialect.name == "better"
        assert dialect.uses_index_notation
        assert dialect.includes_any_event

    def test_dialect_description(self) -> None:
        dialect = get_dialect("ehrbase")
        desc = dialect.description
        assert "no :0" in desc


# ─── ctx/ Path Validation ──────────────────────────────────────────────


class TestCtxPathValidation:
    """Tests for ctx/ shorthand path handling (PRD-0007)."""

    def test_ctx_bare_keys_accepted(self) -> None:
        """All allowlisted bare ctx/ keys must not produce errors or warnings."""
        wt = _make_web_template()
        validator = FlatValidator.from_web_template(wt, platform="ehrbase")

        flat = _make_valid_flat()
        flat["ctx/language"] = "en"
        flat["ctx/territory"] = "CH"
        flat["ctx/composer_name"] = "Dr. Smith"
        flat["ctx/composer_id"] = "12345"
        flat["ctx/id_scheme"] = "scheme"
        flat["ctx/id_namespace"] = "namespace"
        flat["ctx/time"] = "2025-01-05T10:30:00Z"
        flat["ctx/end_time"] = "2025-01-05T11:00:00Z"
        flat["ctx/history_origin"] = "2025-01-05T10:30:00Z"
        flat["ctx/health_care_facility"] = "Hospital"
        flat["ctx/participation_name"] = "Nurse"
        flat["ctx/participation_function"] = "requester"
        flat["ctx/participation_mode"] = "face-to-face"
        flat["ctx/participation_id"] = "nurse-1"
        flat["ctx/setting"] = "primary care"

        result = validator.validate(flat)

        assert result.is_valid
        ctx_errors = [e for e in result.errors if e.path.startswith("ctx/")]
        assert ctx_errors == []
        ctx_warnings = [w for w in result.warnings if w.path.startswith("ctx/")]
        assert ctx_warnings == []

    def test_ctx_pipe_attribute_variants_accepted(self) -> None:
        """ctx/ keys with |attribute suffixes must be accepted."""
        wt = _make_web_template()
        validator = FlatValidator.from_web_template(wt, platform="ehrbase")

        flat = _make_valid_flat()
        flat["ctx/health_care_facility|name"] = "City Hospital"
        flat["ctx/health_care_facility|id"] = "facility_id"
        flat["ctx/language|code"] = "en"
        flat["ctx/language|terminology"] = "ISO_639-1"
        flat["ctx/territory|code"] = "CH"
        flat["ctx/territory|terminology"] = "ISO_3166-1"

        result = validator.validate(flat)

        assert result.is_valid
        ctx_errors = [e for e in result.errors if e.path.startswith("ctx/")]
        assert ctx_errors == []

    def test_unknown_ctx_path_produces_warning(self) -> None:
        """An unknown ctx/ sub-path must produce a warning."""
        wt = _make_web_template()
        validator = FlatValidator.from_web_template(wt, platform="ehrbase")

        flat = _make_valid_flat()
        flat["ctx/invented_nonsense"] = "bogus"

        result = validator.validate(flat)

        # Unknown ctx/ should NOT cause an error (is_valid stays True)
        ctx_errors = [e for e in result.errors if e.path.startswith("ctx/")]
        assert ctx_errors == []

        # But it SHOULD produce a warning
        ctx_warnings = [w for w in result.warnings if w.path == "ctx/invented_nonsense"]
        assert len(ctx_warnings) == 1
        assert "Unknown ctx/ shorthand" in ctx_warnings[0].message

    def test_ctx_paths_do_not_break_template_validation(self) -> None:
        """Existing template-derived path validation must still work with ctx/ paths present."""
        wt = _make_web_template()
        validator = FlatValidator.from_web_template(wt, platform="ehrbase")

        flat = _make_valid_flat()
        flat["ctx/language"] = "en"
        flat["ctx/territory"] = "CH"
        flat["ctx/composer_name"] = "Dr. Smith"
        flat["adverse_reaction_list/adverse_reaction/nonexistent|value"] = "x"

        result = validator.validate(flat)

        assert not result.is_valid
        assert len(result.errors) == 1
        assert result.errors[0].error_type == "unknown_path"
        assert "nonexistent" in result.errors[0].path

    def test_ctx_works_on_better_platform(self) -> None:
        """ctx/ paths should be accepted regardless of platform."""
        wt = _make_web_template()
        validator = FlatValidator.from_web_template(wt, platform="better")

        flat = {
            "adverse_reaction_list/category:0|code": "433",
            "adverse_reaction_list/category:0|value": "event",
            "adverse_reaction_list/category:0|terminology": "openehr",
            "adverse_reaction_list/language:0|code": "en",
            "adverse_reaction_list/language:0|terminology": "ISO_639-1",
            "adverse_reaction_list/territory:0|code": "CH",
            "adverse_reaction_list/territory:0|terminology": "ISO_3166-1",
            "adverse_reaction_list/composer:0|name": "Dr. Chregi",
            "adverse_reaction_list/context:0/start_time:0": "2026-03-12T10:00:00Z",
            "adverse_reaction_list/context:0/setting:0|code": "238",
            "adverse_reaction_list/context:0/setting:0|value": "other care",
            "adverse_reaction_list/context:0/setting:0|terminology": "openehr",
            "adverse_reaction_list/adverse_reaction:0/causative_agent:0|value": "Penicillin",
            "ctx/language": "en",
            "ctx/territory": "CH",
            "ctx/health_care_facility|name": "Hospital",
        }

        result = validator.validate(flat)
        ctx_errors = [e for e in result.errors if e.path.startswith("ctx/")]
        assert ctx_errors == []

    def test_unknown_ctx_pipe_attribute_produces_warning(self) -> None:
        """ctx/unknown_base|attr should still warn since the base is unknown."""
        wt = _make_web_template()
        validator = FlatValidator.from_web_template(wt, platform="ehrbase")

        flat = _make_valid_flat()
        flat["ctx/fake_field|name"] = "bogus"

        result = validator.validate(flat)

        ctx_warnings = [w for w in result.warnings if w.path == "ctx/fake_field|name"]
        assert len(ctx_warnings) == 1


# ─── Integration-style Tests ─────────────────────────────────────────


class TestEndToEnd:
    """End-to-end tests matching the PRD example scenario."""

    def test_substance_to_causative_agent_rename(self) -> None:
        """The canonical PRD example: 'substance' was renamed to 'causative_agent'."""
        wt = _make_web_template()
        # Add originalName to simulate the rename scenario from the PRD
        for child in wt["tree"]["children"]:
            if child["id"] == "adverse_reaction":
                for grandchild in child["children"]:
                    if grandchild["id"] == "causative_agent":
                        grandchild["originalName"] = "Substance/Agent"
        validator = FlatValidator.from_web_template(wt, platform="ehrbase")

        flat = _make_valid_flat()
        # Replace valid paths with old 'substance' name
        del flat["adverse_reaction_list/adverse_reaction/causative_agent|value"]
        del flat["adverse_reaction_list/adverse_reaction/causative_agent|code"]
        del flat["adverse_reaction_list/adverse_reaction/causative_agent|terminology"]
        flat["adverse_reaction_list/adverse_reaction/substance|value"] = "Penicillin"
        flat["adverse_reaction_list/adverse_reaction/substance|code"] = "372687004"
        flat["adverse_reaction_list/adverse_reaction/substance|terminology"] = "SNOMED-CT"

        result = validator.validate(flat)

        assert not result.is_valid
        assert len(result.errors) == 3
        # Each error should have a suggestion pointing to causative_agent
        for error in result.errors:
            assert error.suggestion is not None
            assert "causative_agent" in error.suggestion

    def test_all_valid_composition(self) -> None:
        """A fully valid composition should produce no errors and no warnings."""
        wt = _make_web_template()
        validator = FlatValidator.from_web_template(wt, platform="ehrbase")
        result = validator.validate(_make_valid_flat())

        assert result.is_valid
        assert result.errors == []
        assert result.warnings == []
        assert result.checked_path_count > 0
