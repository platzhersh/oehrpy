"""Tests for the ``python -m oehrpy.validation`` command-line interface."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from oehrpy import __version__
from oehrpy.validation.__main__ import main

# ─── Fixtures ───────────────────────────────────────────────────────


def _make_web_template() -> dict[str, Any]:
    """Build a minimal Web Template JSON for testing."""
    return {
        "templateId": "IDCR - Adverse Reaction List.v1",
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


def _make_valid_flat() -> dict[str, Any]:
    """Build a valid FLAT composition for the test Web Template."""
    return {
        "adverse_reaction_list/category|code": "433",
        "adverse_reaction_list/language|code": "en",
        "adverse_reaction_list/territory|code": "CH",
        "adverse_reaction_list/composer|name": "Dr. Chregi",
        "adverse_reaction_list/context/start_time": "2026-03-12T10:00:00Z",
        "adverse_reaction_list/context/setting|code": "238",
        "adverse_reaction_list/adverse_reaction/causative_agent|value": "Penicillin",
    }


@pytest.fixture
def wt_file(tmp_path: Path) -> str:
    """Write the test Web Template to a temp file and return its path."""
    path = tmp_path / "web_template.json"
    path.write_text(json.dumps(_make_web_template()), encoding="utf-8")
    return str(path)


def _write_composition(tmp_path: Path, composition: dict[str, Any]) -> str:
    path = tmp_path / "composition.flat.json"
    path.write_text(json.dumps(composition), encoding="utf-8")
    return str(path)


# ─── --version ──────────────────────────────────────────────────────


class TestVersion:
    """The --version flag works without a subcommand."""

    def test_version_prints_and_exits_zero(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(SystemExit) as exc:
            main(["--version"])
        assert exc.value.code == 0
        out = capsys.readouterr().out
        assert __version__ in out

    def test_no_command_returns_usage_error(self) -> None:
        assert main([]) == 2


# ─── validate-flat ──────────────────────────────────────────────────


class TestValidateFlat:
    """The validate-flat subcommand."""

    def test_valid_composition_exits_zero(
        self, tmp_path: Path, wt_file: str, capsys: pytest.CaptureFixture[str]
    ) -> None:
        comp = _write_composition(tmp_path, _make_valid_flat())
        code = main(
            ["validate-flat", "--web-template", wt_file, "--composition", comp, "--output", "json"]
        )
        assert code == 0
        result = json.loads(capsys.readouterr().out)
        assert result["is_valid"] is True
        assert result["errors"] == []
        assert result["template_id"] == "IDCR - Adverse Reaction List.v1"
        assert result["platform"] == "ehrbase"
        assert result["valid_path_count"] > 0

    def test_unknown_path_reports_error_with_suggestion(
        self, tmp_path: Path, wt_file: str, capsys: pytest.CaptureFixture[str]
    ) -> None:
        comp = _write_composition(
            tmp_path,
            {"adverse_reaction_list/adverse_reaction/causative_agnt|value": "Penicillin"},
        )
        code = main(
            ["validate-flat", "--web-template", wt_file, "--composition", comp, "--output", "json"]
        )
        assert code == 1
        result = json.loads(capsys.readouterr().out)
        assert result["is_valid"] is False
        errors = result["errors"]
        assert any(e["error_type"] == "unknown_path" for e in errors)
        # The typo'd "causative_agnt" should suggest "causative_agent".
        typo = next(e for e in errors if "causative_agnt" in e["path"])
        assert typo["suggestion"] is not None
        assert "causative_agent" in typo["suggestion"]

    def test_wrong_suffix_reports_error(
        self, tmp_path: Path, wt_file: str, capsys: pytest.CaptureFixture[str]
    ) -> None:
        comp = _write_composition(
            tmp_path,
            {"adverse_reaction_list/adverse_reaction/temperature|bogus": 37.5},
        )
        code = main(
            ["validate-flat", "--web-template", wt_file, "--composition", comp, "--output", "json"]
        )
        assert code == 1
        result = json.loads(capsys.readouterr().out)
        assert any(e["error_type"] == "wrong_suffix" for e in result["errors"])

    def test_text_output_human_readable(
        self, tmp_path: Path, wt_file: str, capsys: pytest.CaptureFixture[str]
    ) -> None:
        comp = _write_composition(tmp_path, _make_valid_flat())
        code = main(["validate-flat", "--web-template", wt_file, "--composition", comp])
        assert code == 0
        assert "Valid" in capsys.readouterr().out

    def test_non_object_composition_errors(self, tmp_path: Path, wt_file: str) -> None:
        bad = tmp_path / "bad.json"
        bad.write_text("[1, 2, 3]", encoding="utf-8")
        with pytest.raises(SystemExit):
            main(["validate-flat", "--web-template", wt_file, "--composition", str(bad)])

    def test_missing_file_errors(self, tmp_path: Path, wt_file: str) -> None:
        with pytest.raises(SystemExit):
            main(
                [
                    "validate-flat",
                    "--web-template",
                    wt_file,
                    "--composition",
                    str(tmp_path / "does_not_exist.json"),
                ]
            )


# ─── web-template inspect ───────────────────────────────────────────


class TestWebTemplateInspect:
    """The web-template inspect subcommand."""

    def test_inspect_known_path(self, wt_file: str, capsys: pytest.CaptureFixture[str]) -> None:
        code = main(
            [
                "web-template",
                "inspect",
                "--web-template",
                wt_file,
                "--path",
                "adverse_reaction_list/adverse_reaction/temperature",
            ]
        )
        assert code == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["id"] == "temperature"
        assert payload["rm_type"] == "DV_QUANTITY"
        assert "|magnitude" in payload["valid_suffixes"]

    def test_inspect_strips_suffix_and_index(
        self, wt_file: str, capsys: pytest.CaptureFixture[str]
    ) -> None:
        code = main(
            [
                "web-template",
                "inspect",
                "--web-template",
                wt_file,
                "--path",
                "adverse_reaction_list/adverse_reaction/temperature|magnitude",
            ]
        )
        assert code == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["id"] == "temperature"

    def test_inspect_unknown_path_exits_nonzero(
        self, wt_file: str, capsys: pytest.CaptureFixture[str]
    ) -> None:
        code = main(
            [
                "web-template",
                "inspect",
                "--web-template",
                wt_file,
                "--path",
                "adverse_reaction_list/nope",
            ]
        )
        assert code == 1
        assert capsys.readouterr().out == ""


# ─── show-paths ─────────────────────────────────────────────────────


class TestShowPaths:
    """The show-paths subcommand."""

    def test_show_paths_text(self, wt_file: str, capsys: pytest.CaptureFixture[str]) -> None:
        code = main(["show-paths", "--web-template", wt_file])
        assert code == 0
        lines = capsys.readouterr().out.strip().splitlines()
        assert "adverse_reaction_list/adverse_reaction/temperature|magnitude" in lines

    def test_show_paths_json(self, wt_file: str, capsys: pytest.CaptureFixture[str]) -> None:
        code = main(["show-paths", "--web-template", wt_file, "--output", "json"])
        assert code == 0
        paths = json.loads(capsys.readouterr().out)
        assert isinstance(paths, list)
        assert "adverse_reaction_list/category|code" in paths

    def test_better_platform_adds_indexed_variants(
        self, wt_file: str, capsys: pytest.CaptureFixture[str]
    ) -> None:
        code = main(
            ["show-paths", "--web-template", wt_file, "--platform", "better", "--output", "json"]
        )
        assert code == 0
        paths = json.loads(capsys.readouterr().out)
        assert any(":0" in p for p in paths)
