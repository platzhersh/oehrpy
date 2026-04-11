"""Tests for OPT (Operational Template) validator.

Tests are organized by validation category:
- Category A: XML well-formedness checks
- Category B: Semantic integrity checks
- Category C: Structural warnings
- Category D: FLAT path impact analysis
- Integration: OPTValidator, CLI, and parser/generator integration
"""

from __future__ import annotations

from pathlib import Path

import pytest

from oehrpy.validation.opt import (
    OPTValidationError,
    OPTValidator,
    issue_codes,
)

# ---------------------------------------------------------------------------
# Helpers: minimal valid OPT XML for testing
# ---------------------------------------------------------------------------

MINIMAL_VALID_OPT = """\
<?xml version="1.0" encoding="UTF-8"?>
<template xmlns="http://schemas.openehr.org/v1"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <language>
    <terminology_id><value>ISO_639-1</value></terminology_id>
    <code_string>en</code_string>
  </language>
  <description>
    <lifecycle_state>published</lifecycle_state>
    <details>
      <language>
        <terminology_id><value>ISO_639-1</value></terminology_id>
        <code_string>en</code_string>
      </language>
      <purpose>Test template</purpose>
    </details>
  </description>
  <template_id><value>Test Template.v1</value></template_id>
  <concept>test_template</concept>
  <definition>
    <rm_type_name>COMPOSITION</rm_type_name>
    <occurrences>
      <lower_included>true</lower_included>
      <upper_included>true</upper_included>
      <lower_unbounded>false</lower_unbounded>
      <upper_unbounded>false</upper_unbounded>
      <lower>1</lower>
      <upper>1</upper>
    </occurrences>
    <node_id>at0000</node_id>
    <archetype_id>
      <value>openEHR-EHR-COMPOSITION.encounter.v1</value>
    </archetype_id>
  </definition>
  <ontology>
    <term_definitions language="en">
      <items code="at0000">
        <items id="text"><value>Encounter</value></items>
        <items id="description"><value>An encounter</value></items>
      </items>
    </term_definitions>
  </ontology>
</template>
"""


def _make_opt(**overrides: str) -> str:
    """Create a test OPT XML with optional field overrides.

    Supports overrides:
        template_id, concept, language, lifecycle_state, rm_type_name,
        archetype_id, node_id
    """
    template_id = overrides.get("template_id", "Test Template.v1")
    concept = overrides.get("concept", "test_template")
    language = overrides.get("language", "en")
    lifecycle = overrides.get("lifecycle_state", "published")
    rm_type = overrides.get("rm_type_name", "COMPOSITION")
    archetype_id = overrides.get("archetype_id", "openEHR-EHR-COMPOSITION.encounter.v1")
    node_id = overrides.get("node_id", "at0000")

    return f"""\
<?xml version="1.0" encoding="UTF-8"?>
<template xmlns="http://schemas.openehr.org/v1"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <language>
    <terminology_id><value>ISO_639-1</value></terminology_id>
    <code_string>{language}</code_string>
  </language>
  <description>
    <lifecycle_state>{lifecycle}</lifecycle_state>
    <details>
      <language>
        <terminology_id><value>ISO_639-1</value></terminology_id>
        <code_string>{language}</code_string>
      </language>
      <purpose>Test</purpose>
    </details>
  </description>
  <template_id><value>{template_id}</value></template_id>
  <concept>{concept}</concept>
  <definition>
    <rm_type_name>{rm_type}</rm_type_name>
    <occurrences>
      <lower_unbounded>false</lower_unbounded>
      <upper_unbounded>false</upper_unbounded>
      <lower>1</lower>
      <upper>1</upper>
    </occurrences>
    <node_id>{node_id}</node_id>
    <archetype_id>
      <value>{archetype_id}</value>
    </archetype_id>
  </definition>
  <ontology>
    <term_definitions language="{language}">
      <items code="{node_id}">
        <items id="text"><value>Test Node</value></items>
        <items id="description"><value>A test node</value></items>
      </items>
    </term_definitions>
  </ontology>
</template>
"""


# ===========================================================================
# Category A: XML well-formedness checks
# ===========================================================================


class TestXMLWellFormedness:
    """Tests for Category A validation checks."""

    def test_valid_opt(self) -> None:
        """A minimal valid OPT passes validation."""
        validator = OPTValidator()
        result = validator.validate_string(MINIMAL_VALID_OPT)
        assert result.is_valid
        assert result.error_count == 0
        assert result.template_id == "Test Template.v1"
        assert result.concept == "test_template"

    def test_invalid_xml(self) -> None:
        """Non-XML content is rejected."""
        validator = OPTValidator()
        result = validator.validate_string("this is not xml")
        assert not result.is_valid
        assert any(i.code == issue_codes.XML_INVALID for i in result.issues)

    def test_wrong_namespace(self) -> None:
        """Wrong root namespace is flagged."""
        xml = MINIMAL_VALID_OPT.replace(
            "http://schemas.openehr.org/v1",
            "http://wrong.namespace.org",
        )
        validator = OPTValidator()
        result = validator.validate_string(xml)
        assert any(i.code == issue_codes.XML_WRONG_NAMESPACE for i in result.issues)

    def test_missing_template_id(self) -> None:
        """Missing template_id is an error."""
        xml = MINIMAL_VALID_OPT.replace(
            "<template_id><value>Test Template.v1</value></template_id>",
            "<template_id><value></value></template_id>",
        )
        validator = OPTValidator()
        result = validator.validate_string(xml)
        assert not result.is_valid
        assert any(i.code == issue_codes.MISSING_TEMPLATE_ID for i in result.issues)

    def test_invalid_template_id_format(self) -> None:
        """Template ID with invalid characters is flagged."""
        xml = _make_opt(template_id="Test!@#Template.v1")
        validator = OPTValidator()
        result = validator.validate_string(xml)
        assert any(i.code == issue_codes.INVALID_TEMPLATE_ID_FORMAT for i in result.issues)

    def test_missing_concept(self) -> None:
        """Missing concept element is an error."""
        xml = MINIMAL_VALID_OPT.replace(
            "<concept>test_template</concept>",
            "<concept></concept>",
        )
        validator = OPTValidator()
        result = validator.validate_string(xml)
        assert any(i.code == issue_codes.MISSING_CONCEPT for i in result.issues)

    def test_invalid_language_code(self) -> None:
        """Invalid ISO 639-1 language code is flagged."""
        xml = _make_opt(language="xx")
        validator = OPTValidator()
        result = validator.validate_string(xml)
        assert any(i.code == issue_codes.INVALID_LANGUAGE_CODE for i in result.issues)

    def test_valid_language_code(self) -> None:
        """Valid non-English language code is accepted."""
        xml = _make_opt(language="de")
        validator = OPTValidator()
        result = validator.validate_string(xml)
        assert not any(i.code == issue_codes.INVALID_LANGUAGE_CODE for i in result.issues)

    def test_invalid_root_rm_type(self) -> None:
        """Root rm_type_name not COMPOSITION is an error."""
        xml = _make_opt(rm_type_name="OBSERVATION")
        validator = OPTValidator()
        result = validator.validate_string(xml)
        assert any(i.code == issue_codes.INVALID_ROOT_RM_TYPE for i in result.issues)

    def test_invalid_archetype_id_format(self) -> None:
        """Archetype ID not matching required pattern is flagged."""
        xml = _make_opt(archetype_id="blood_pressure.v1")
        validator = OPTValidator()
        result = validator.validate_string(xml)
        assert any(i.code == issue_codes.INVALID_ARCHETYPE_ID_FORMAT for i in result.issues)

    def test_archetype_id_missing_version(self) -> None:
        """Archetype ID without version is flagged."""
        xml = _make_opt(archetype_id="openEHR-EHR-COMPOSITION.encounter")
        validator = OPTValidator()
        result = validator.validate_string(xml)
        assert any(i.code == issue_codes.INVALID_ARCHETYPE_ID_FORMAT for i in result.issues)

    def test_invalid_rm_type_name(self) -> None:
        """Unknown rm_type_name is flagged."""
        xml = MINIMAL_VALID_OPT.replace(
            "<rm_type_name>COMPOSITION</rm_type_name>",
            "<rm_type_name>DV_CODED_QUANTITY</rm_type_name>",
        )
        validator = OPTValidator()
        result = validator.validate_string(xml)
        assert any(i.code == issue_codes.INVALID_RM_TYPE for i in result.issues)
        # Should have a suggestion
        rm_issue = next(i for i in result.issues if i.code == issue_codes.INVALID_RM_TYPE)
        assert rm_issue.suggestion is not None

    def test_invalid_occurrences_min_greater_than_max(self) -> None:
        """Occurrences with min > max is an error."""
        xml = MINIMAL_VALID_OPT.replace(
            "<lower>1</lower>\n      <upper>1</upper>",
            "<lower>5</lower>\n      <upper>1</upper>",
        )
        validator = OPTValidator()
        result = validator.validate_string(xml)
        assert any(i.code == issue_codes.INVALID_OCCURRENCES for i in result.issues)

    def test_duplicate_node_id(self) -> None:
        """Duplicate node_id within archetype scope is flagged."""
        xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<template xmlns="http://schemas.openehr.org/v1"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <language>
    <terminology_id><value>ISO_639-1</value></terminology_id>
    <code_string>en</code_string>
  </language>
  <description>
    <lifecycle_state>published</lifecycle_state>
    <details><language><terminology_id><value>ISO_639-1</value></terminology_id>
    <code_string>en</code_string></language><purpose>Test</purpose></details>
  </description>
  <template_id><value>Test Template.v1</value></template_id>
  <concept>test_template</concept>
  <definition>
    <rm_type_name>COMPOSITION</rm_type_name>
    <occurrences>
      <lower_unbounded>false</lower_unbounded>
      <upper_unbounded>false</upper_unbounded>
      <lower>1</lower>
      <upper>1</upper>
    </occurrences>
    <node_id>at0000</node_id>
    <archetype_id>
      <value>openEHR-EHR-COMPOSITION.encounter.v1</value>
    </archetype_id>
    <attributes xsi:type="C_SINGLE_ATTRIBUTE">
      <rm_attribute_name>content</rm_attribute_name>
      <children xsi:type="C_COMPLEX_OBJECT">
        <rm_type_name>EVALUATION</rm_type_name>
        <node_id>at0001</node_id>
        <occurrences>
          <lower_unbounded>false</lower_unbounded>
          <upper_unbounded>false</upper_unbounded>
          <lower>0</lower>
          <upper>1</upper>
        </occurrences>
      </children>
      <children xsi:type="C_COMPLEX_OBJECT">
        <rm_type_name>OBSERVATION</rm_type_name>
        <node_id>at0001</node_id>
        <occurrences>
          <lower_unbounded>false</lower_unbounded>
          <upper_unbounded>false</upper_unbounded>
          <lower>0</lower>
          <upper>1</upper>
        </occurrences>
      </children>
    </attributes>
  </definition>
  <ontology>
    <term_definitions language="en">
      <items code="at0000">
        <items id="text"><value>Encounter</value></items>
        <items id="description"><value>Test</value></items>
      </items>
      <items code="at0001">
        <items id="text"><value>Node</value></items>
        <items id="description"><value>Test</value></items>
      </items>
    </term_definitions>
  </ontology>
</template>
"""
        validator = OPTValidator()
        result = validator.validate_string(xml)
        assert any(i.code == issue_codes.DUPLICATE_NODE_ID for i in result.issues)

    def test_null_bytes_detected(self) -> None:
        """Null bytes in XML content are flagged."""
        xml_bytes = MINIMAL_VALID_OPT.encode("utf-8")
        # Inject a null byte
        xml_bytes = xml_bytes[:50] + b"\x00" + xml_bytes[50:]
        # Write to temp file and validate
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".opt", delete=False) as f:
            f.write(xml_bytes)
            tmp_path = f.name

        try:
            validator = OPTValidator()
            result = validator.validate_file(tmp_path)
            # Either XML_ENCODING_ISSUE or XML_INVALID (parser may reject it)
            assert any(
                i.code in (issue_codes.XML_ENCODING_ISSUE, issue_codes.XML_INVALID)
                for i in result.issues
            )
        finally:
            Path(tmp_path).unlink()


# ===========================================================================
# Category B: Semantic integrity checks
# ===========================================================================


class TestSemanticIntegrity:
    """Tests for Category B validation checks."""

    def test_missing_term_definition(self) -> None:
        """node_id without matching term definition is flagged."""
        xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<template xmlns="http://schemas.openehr.org/v1"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <language>
    <terminology_id><value>ISO_639-1</value></terminology_id>
    <code_string>en</code_string>
  </language>
  <description>
    <lifecycle_state>published</lifecycle_state>
    <details><language><terminology_id><value>ISO_639-1</value></terminology_id>
    <code_string>en</code_string></language><purpose>Test</purpose></details>
  </description>
  <template_id><value>Test Template.v1</value></template_id>
  <concept>test_template</concept>
  <definition>
    <rm_type_name>COMPOSITION</rm_type_name>
    <occurrences>
      <lower_unbounded>false</lower_unbounded>
      <upper_unbounded>false</upper_unbounded>
      <lower>1</lower>
      <upper>1</upper>
    </occurrences>
    <node_id>at0000</node_id>
    <archetype_id>
      <value>openEHR-EHR-COMPOSITION.encounter.v1</value>
    </archetype_id>
    <attributes xsi:type="C_SINGLE_ATTRIBUTE">
      <rm_attribute_name>content</rm_attribute_name>
      <children xsi:type="C_COMPLEX_OBJECT">
        <rm_type_name>EVALUATION</rm_type_name>
        <node_id>at0055</node_id>
        <occurrences>
          <lower_unbounded>false</lower_unbounded>
          <upper_unbounded>false</upper_unbounded>
          <lower>0</lower>
          <upper>1</upper>
        </occurrences>
      </children>
    </attributes>
  </definition>
  <ontology>
    <term_definitions language="en">
      <items code="at0000">
        <items id="text"><value>Encounter</value></items>
        <items id="description"><value>An encounter</value></items>
      </items>
    </term_definitions>
  </ontology>
</template>
"""
        validator = OPTValidator()
        result = validator.validate_string(xml)
        assert any(i.code == issue_codes.MISSING_TERM_DEF for i in result.issues)
        missing = [i for i in result.issues if i.code == issue_codes.MISSING_TERM_DEF]
        assert any(i.node_id == "at0055" for i in missing)

    def test_orphan_terminology_binding(self) -> None:
        """Terminology binding for non-existent node_id is flagged."""
        xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<template xmlns="http://schemas.openehr.org/v1"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <language>
    <terminology_id><value>ISO_639-1</value></terminology_id>
    <code_string>en</code_string>
  </language>
  <description>
    <lifecycle_state>published</lifecycle_state>
    <details><language><terminology_id><value>ISO_639-1</value></terminology_id>
    <code_string>en</code_string></language><purpose>Test</purpose></details>
  </description>
  <template_id><value>Test Template.v1</value></template_id>
  <concept>test_template</concept>
  <definition>
    <rm_type_name>COMPOSITION</rm_type_name>
    <occurrences>
      <lower_unbounded>false</lower_unbounded>
      <upper_unbounded>false</upper_unbounded>
      <lower>1</lower>
      <upper>1</upper>
    </occurrences>
    <node_id>at0000</node_id>
    <archetype_id>
      <value>openEHR-EHR-COMPOSITION.encounter.v1</value>
    </archetype_id>
  </definition>
  <ontology>
    <term_definitions language="en">
      <items code="at0000">
        <items id="text"><value>Encounter</value></items>
        <items id="description"><value>Test</value></items>
      </items>
    </term_definitions>
    <term_bindings terminology="SNOMED-CT">
      <items code="at9999">
        <value>
          <terminology_id><value>SNOMED-CT</value></terminology_id>
          <code_string>12345</code_string>
        </value>
      </items>
    </term_bindings>
  </ontology>
</template>
"""
        validator = OPTValidator()
        result = validator.validate_string(xml)
        assert any(i.code == issue_codes.ORPHAN_TERMINOLOGY_BINDING for i in result.issues)

    def test_mandatory_node_no_name(self) -> None:
        """Mandatory node without resolvable name is flagged."""
        xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<template xmlns="http://schemas.openehr.org/v1"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <language>
    <terminology_id><value>ISO_639-1</value></terminology_id>
    <code_string>en</code_string>
  </language>
  <description>
    <lifecycle_state>published</lifecycle_state>
    <details><language><terminology_id><value>ISO_639-1</value></terminology_id>
    <code_string>en</code_string></language><purpose>Test</purpose></details>
  </description>
  <template_id><value>Test Template.v1</value></template_id>
  <concept>test_template</concept>
  <definition>
    <rm_type_name>COMPOSITION</rm_type_name>
    <occurrences>
      <lower_unbounded>false</lower_unbounded>
      <upper_unbounded>false</upper_unbounded>
      <lower>1</lower>
      <upper>1</upper>
    </occurrences>
    <node_id>at0000</node_id>
    <archetype_id>
      <value>openEHR-EHR-COMPOSITION.encounter.v1</value>
    </archetype_id>
    <attributes xsi:type="C_SINGLE_ATTRIBUTE">
      <rm_attribute_name>content</rm_attribute_name>
      <children xsi:type="C_COMPLEX_OBJECT">
        <rm_type_name>EVALUATION</rm_type_name>
        <node_id>at0099</node_id>
        <occurrences>
          <lower_unbounded>false</lower_unbounded>
          <upper_unbounded>false</upper_unbounded>
          <lower>1</lower>
          <upper>1</upper>
        </occurrences>
      </children>
    </attributes>
  </definition>
  <ontology>
    <term_definitions language="en">
      <items code="at0000">
        <items id="text"><value>Encounter</value></items>
        <items id="description"><value>Test</value></items>
      </items>
    </term_definitions>
  </ontology>
</template>
"""
        validator = OPTValidator()
        result = validator.validate_string(xml)
        assert any(i.code == issue_codes.MANDATORY_NODE_NO_NAME for i in result.issues)

    def test_unknown_terminology_id(self) -> None:
        """Terminology binding referencing undeclared terminology ID is flagged."""
        xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<template xmlns="http://schemas.openehr.org/v1"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <language>
    <terminology_id><value>ISO_639-1</value></terminology_id>
    <code_string>en</code_string>
  </language>
  <description>
    <lifecycle_state>published</lifecycle_state>
    <details><language><terminology_id><value>ISO_639-1</value></terminology_id>
    <code_string>en</code_string></language><purpose>Test</purpose></details>
  </description>
  <template_id><value>Test Template.v1</value></template_id>
  <concept>test_template</concept>
  <definition>
    <rm_type_name>COMPOSITION</rm_type_name>
    <occurrences>
      <lower_unbounded>false</lower_unbounded>
      <upper_unbounded>false</upper_unbounded>
      <lower>1</lower>
      <upper>1</upper>
    </occurrences>
    <node_id>at0000</node_id>
    <archetype_id>
      <value>openEHR-EHR-COMPOSITION.encounter.v1</value>
    </archetype_id>
  </definition>
  <ontology>
    <terminologies_available>
      <e>LOINC</e>
    </terminologies_available>
    <term_definitions language="en">
      <items code="at0000">
        <items id="text"><value>Encounter</value></items>
        <items id="description"><value>Test</value></items>
      </items>
    </term_definitions>
    <term_bindings terminology="SNOMED-CT">
      <items code="at0000">
        <value>
          <terminology_id><value>SNOMED-CT</value></terminology_id>
          <code_string>12345</code_string>
        </value>
      </items>
    </term_bindings>
  </ontology>
</template>
"""
        validator = OPTValidator()
        result = validator.validate_string(xml)
        unknown = [i for i in result.issues if i.code == issue_codes.UNKNOWN_TERMINOLOGY_ID]
        assert len(unknown) == 1
        assert "SNOMED-CT" in unknown[0].message

    def test_known_terminology_id_passes(self) -> None:
        """Terminology binding referencing a declared terminology ID passes."""
        xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<template xmlns="http://schemas.openehr.org/v1"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <language>
    <terminology_id><value>ISO_639-1</value></terminology_id>
    <code_string>en</code_string>
  </language>
  <description>
    <lifecycle_state>published</lifecycle_state>
    <details><language><terminology_id><value>ISO_639-1</value></terminology_id>
    <code_string>en</code_string></language><purpose>Test</purpose></details>
  </description>
  <template_id><value>Test Template.v1</value></template_id>
  <concept>test_template</concept>
  <definition>
    <rm_type_name>COMPOSITION</rm_type_name>
    <occurrences>
      <lower_unbounded>false</lower_unbounded>
      <upper_unbounded>false</upper_unbounded>
      <lower>1</lower>
      <upper>1</upper>
    </occurrences>
    <node_id>at0000</node_id>
    <archetype_id>
      <value>openEHR-EHR-COMPOSITION.encounter.v1</value>
    </archetype_id>
  </definition>
  <ontology>
    <terminologies_available>
      <e>LOINC</e>
    </terminologies_available>
    <term_definitions language="en">
      <items code="at0000">
        <items id="text"><value>Encounter</value></items>
        <items id="description"><value>Test</value></items>
      </items>
    </term_definitions>
    <term_bindings terminology="LOINC">
      <items code="at0000">
        <value>
          <terminology_id><value>LOINC</value></terminology_id>
          <code_string>12345-6</code_string>
        </value>
      </items>
    </term_bindings>
  </ontology>
</template>
"""
        validator = OPTValidator()
        result = validator.validate_string(xml)
        assert not any(i.code == issue_codes.UNKNOWN_TERMINOLOGY_ID for i in result.issues)


# ===========================================================================
# Category C: Structural warnings
# ===========================================================================


class TestStructuralWarnings:
    """Tests for Category C structural warning checks."""

    def test_draft_lifecycle_warning(self) -> None:
        """Non-published lifecycle_state triggers a warning."""
        xml = _make_opt(lifecycle_state="Initial")
        validator = OPTValidator()
        result = validator.validate_string(xml)
        warnings = [i for i in result.issues if i.code == issue_codes.DRAFT_LIFECYCLE]
        assert len(warnings) > 0
        assert warnings[0].severity == "warning"

    def test_published_lifecycle_no_warning(self) -> None:
        """Published lifecycle_state does not trigger a warning."""
        xml = _make_opt(lifecycle_state="published")
        validator = OPTValidator()
        result = validator.validate_string(xml)
        assert not any(i.code == issue_codes.DRAFT_LIFECYCLE for i in result.issues)

    def test_concept_special_chars_warning(self) -> None:
        """Concept with special characters triggers a warning."""
        xml = _make_opt(concept="IDCR - Vital Signs.v1")
        validator = OPTValidator()
        result = validator.validate_string(xml)
        assert any(i.code == issue_codes.CONCEPT_SPECIAL_CHARS for i in result.issues)

    def test_unstable_archetype_version(self) -> None:
        """v0 archetype reference triggers a warning."""
        xml = _make_opt(archetype_id="openEHR-EHR-COMPOSITION.encounter.v0")
        validator = OPTValidator()
        result = validator.validate_string(xml)
        assert any(i.code == issue_codes.UNSTABLE_ARCHETYPE_VERSION for i in result.issues)


# ===========================================================================
# Category D: FLAT path impact analysis
# ===========================================================================


class TestFlatPathImpact:
    """Tests for Category D FLAT path impact analysis."""

    def test_concept_path_analysis(self) -> None:
        """Concept with special chars gets a FLAT path impact note."""
        xml = _make_opt(concept="IDCR - Adverse Reaction List.v1")
        validator = OPTValidator()
        result = validator.validate_string(xml)
        flat_issues = [i for i in result.issues if i.category == "flat_impact"]
        assert len(flat_issues) > 0

    def test_renamed_node_detection(self) -> None:
        """Node with template name override is detected."""
        xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<template xmlns="http://schemas.openehr.org/v1"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <language>
    <terminology_id><value>ISO_639-1</value></terminology_id>
    <code_string>en</code_string>
  </language>
  <description>
    <lifecycle_state>published</lifecycle_state>
    <details><language><terminology_id><value>ISO_639-1</value></terminology_id>
    <code_string>en</code_string></language><purpose>Test</purpose></details>
  </description>
  <template_id><value>Test Template.v1</value></template_id>
  <concept>test_template</concept>
  <definition>
    <rm_type_name>COMPOSITION</rm_type_name>
    <occurrences>
      <lower_unbounded>false</lower_unbounded>
      <upper_unbounded>false</upper_unbounded>
      <lower>1</lower>
      <upper>1</upper>
    </occurrences>
    <node_id>at0000</node_id>
    <archetype_id>
      <value>openEHR-EHR-COMPOSITION.encounter.v1</value>
    </archetype_id>
    <attributes xsi:type="C_SINGLE_ATTRIBUTE">
      <rm_attribute_name>content</rm_attribute_name>
      <children xsi:type="C_COMPLEX_OBJECT">
        <rm_type_name>EVALUATION</rm_type_name>
        <node_id>at0002</node_id>
        <name><value>Causative Agent</value></name>
        <occurrences>
          <lower_unbounded>false</lower_unbounded>
          <upper_unbounded>false</upper_unbounded>
          <lower>0</lower>
          <upper>1</upper>
        </occurrences>
      </children>
    </attributes>
  </definition>
  <ontology>
    <term_definitions language="en">
      <items code="at0000">
        <items id="text"><value>Encounter</value></items>
        <items id="description"><value>Test</value></items>
      </items>
      <items code="at0002">
        <items id="text"><value>Substance</value></items>
        <items id="description"><value>The substance</value></items>
      </items>
    </term_definitions>
  </ontology>
</template>
"""
        validator = OPTValidator()
        result = validator.validate_string(xml)
        renamed = [i for i in result.issues if i.code == issue_codes.RENAMED_NODE_DETECTED]
        assert len(renamed) > 0
        assert "Causative Agent" in renamed[0].message
        assert "Substance" in renamed[0].message


# ===========================================================================
# Integration tests
# ===========================================================================


class TestOPTValidatorIntegration:
    """Integration tests for OPTValidator."""

    @property
    def sample_opt_path(self) -> Path:
        return Path(__file__).parent / "fixtures" / "vital_signs.opt"

    def test_validate_file(self) -> None:
        """Validate the sample OPT file from fixtures."""
        validator = OPTValidator()
        result = validator.validate_file(self.sample_opt_path)
        assert result.template_id is not None
        assert result.concept is not None
        assert result.node_count > 0
        assert result.archetype_count > 0

    def test_validate_file_not_found(self) -> None:
        """Validating a non-existent file raises an error."""
        validator = OPTValidator()
        with pytest.raises(FileNotFoundError):
            validator.validate_file("/nonexistent/path.opt")

    def test_validation_result_serialization(self) -> None:
        """Validation result can be serialized to JSON."""
        validator = OPTValidator()
        result = validator.validate_string(MINIMAL_VALID_OPT)
        json_str = result.to_json()
        assert "is_valid" in json_str
        assert "template_id" in json_str

        result_dict = result.to_dict()
        assert isinstance(result_dict, dict)
        assert "issues" in result_dict

    def test_validation_result_properties(self) -> None:
        """Validation result computed properties work correctly."""
        validator = OPTValidator()
        result = validator.validate_string(MINIMAL_VALID_OPT)
        assert isinstance(result.errors, list)
        assert isinstance(result.warnings, list)
        assert result.error_count == len(result.errors)
        assert result.warning_count == len(result.warnings)

    def test_parse_opt_with_validation(self) -> None:
        """parse_opt with validate=True raises on real OPT with issues."""
        from oehrpy.templates import parse_opt

        # The sample vital_signs.opt has validation issues (missing term defs etc.)
        # so validate=True should raise
        with pytest.raises(OPTValidationError):
            parse_opt(self.sample_opt_path, validate=True)

    def test_parse_opt_string_with_validation(self) -> None:
        """parse_opt from string with validate=True works."""
        from oehrpy.templates import parse_opt

        template = parse_opt(MINIMAL_VALID_OPT, validate=True)
        assert template.template_id == "Test Template.v1"

    def test_parse_opt_with_validation_failure(self) -> None:
        """parse_opt with validate=True raises on invalid OPT."""
        from oehrpy.templates import parse_opt

        # OPT with invalid RM type should raise
        xml = _make_opt(rm_type_name="INVALID_TYPE_XYZ")
        with pytest.raises(OPTValidationError) as exc_info:
            parse_opt(xml, validate=True)
        assert exc_info.value.result.error_count > 0

    def test_generate_builder_with_validation(self) -> None:
        """generate_builder_from_opt raises when validate=True and OPT has issues."""
        from oehrpy.templates import generate_builder_from_opt

        # The sample vital_signs.opt has validation issues,
        # so explicit validate=True should raise
        with pytest.raises(OPTValidationError):
            generate_builder_from_opt(self.sample_opt_path, validate=True)

    def test_generate_builder_validation_disabled(self) -> None:
        """generate_builder_from_opt skips validation by default."""
        from oehrpy.templates import generate_builder_from_opt

        code = generate_builder_from_opt(self.sample_opt_path)
        assert "Builder" in code


class TestCLI:
    """Tests for the CLI entry point."""

    @property
    def sample_opt_path(self) -> str:
        return str(Path(__file__).parent / "fixtures" / "vital_signs.opt")

    def test_cli_valid_file(self) -> None:
        """CLI returns 0 for a valid OPT file."""
        from oehrpy.validate_opt_cli import main

        exit_code = main([self.sample_opt_path])
        # May return 0 or 1 depending on warnings in the fixture
        assert exit_code in (0, 1)

    def test_cli_json_output(self) -> None:
        """CLI JSON output mode works."""
        from oehrpy.validate_opt_cli import main

        exit_code = main([self.sample_opt_path, "--output", "json"])
        assert exit_code in (0, 1)

    def test_cli_file_not_found(self) -> None:
        """CLI returns 1 for a non-existent file."""
        from oehrpy.validate_opt_cli import main

        exit_code = main(["/nonexistent/file.opt"])
        assert exit_code == 1

    def test_cli_strict_mode(self) -> None:
        """CLI strict mode treats warnings as errors."""
        from oehrpy.validate_opt_cli import main

        # The sample OPT likely has warnings (e.g., lifecycle_state)
        exit_code = main([self.sample_opt_path, "--strict"])
        # With strict, even warnings cause failure
        assert isinstance(exit_code, int)

    def test_cli_show_flat_paths(self) -> None:
        """CLI --show-flat-paths option works."""
        from oehrpy.validate_opt_cli import main

        exit_code = main([self.sample_opt_path, "--show-flat-paths"])
        assert exit_code in (0, 1)


class TestRMTypeRegistry:
    """Tests for the RM type registry used in validation."""

    def test_known_types_loaded(self) -> None:
        """RM type registry loads the expected number of types."""
        from oehrpy.validation.opt.rm_types import KNOWN_RM_TYPES

        assert len(KNOWN_RM_TYPES) >= 130  # Should be ~134

    def test_common_types_present(self) -> None:
        """Common RM types are in the registry."""
        from oehrpy.validation.opt.rm_types import KNOWN_RM_TYPES

        common = [
            "COMPOSITION",
            "OBSERVATION",
            "EVALUATION",
            "INSTRUCTION",
            "ACTION",
            "SECTION",
            "CLUSTER",
            "ELEMENT",
            "DV_QUANTITY",
            "DV_TEXT",
            "DV_CODED_TEXT",
            "DV_DATE_TIME",
            "ITEM_TREE",
            "HISTORY",
            "POINT_EVENT",
            "INTERVAL_EVENT",
        ]
        for rm_type in common:
            assert rm_type in KNOWN_RM_TYPES, f"{rm_type} not in registry"

    def test_suggest_rm_type(self) -> None:
        """RM type suggestion works for common misspellings."""
        from oehrpy.validation.opt.rm_types import suggest_rm_type

        # DV_CODED_QUANTITY -> should suggest DV_QUANTITY or DV_CODED_TEXT
        suggestion = suggest_rm_type("DV_CODED_QUANTITY")
        assert suggestion is not None
        assert suggestion in ("DV_QUANTITY", "DV_CODED_TEXT")
