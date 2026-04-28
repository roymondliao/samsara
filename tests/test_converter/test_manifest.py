"""
Unit tests for ManifestConverter.

Tests normal-path behavior after death tests establish the error boundaries.
"""

import json
import pytest
from pathlib import Path


def _write_manifest(tmp_path: Path, content: dict) -> Path:
    p = tmp_path / "plugin.json"
    p.write_text(json.dumps(content))
    return p


class TestManifestConverterBasicConversion:
    def test_required_fields_pass_through_to_output(self, tmp_path):
        """name and version from source appear in output."""
        from samsara_cli.converter.manifest import ManifestConverter

        source = _write_manifest(
            tmp_path,
            {
                "name": "samsara",
                "version": "0.8.0",
                "description": "samsara plugin",
            },
        )
        converter = ManifestConverter()
        result = converter.convert(source, extra_fields={})
        assert result["name"] == "samsara"
        assert result["version"] == "0.8.0"

    def test_description_preserved(self, tmp_path):
        """description field from source appears in output."""
        from samsara_cli.converter.manifest import ManifestConverter

        source = _write_manifest(
            tmp_path,
            {
                "name": "samsara",
                "version": "0.8.0",
                "description": "向死而驗",
            },
        )
        converter = ManifestConverter()
        result = converter.convert(source, extra_fields={})
        assert result["description"] == "向死而驗"

    def test_extra_fields_merged_into_output(self, tmp_path):
        """extra_fields from platform config are merged into the output dict."""
        from samsara_cli.converter.manifest import ManifestConverter

        source = _write_manifest(
            tmp_path,
            {
                "name": "samsara",
                "version": "0.8.0",
            },
        )
        converter = ManifestConverter()
        result = converter.convert(source, extra_fields={"skills": "./skills/"})
        assert result["skills"] == "./skills/"

    def test_output_is_dict(self, tmp_path):
        """convert() returns a dict, not a JSON string or Path."""
        from samsara_cli.converter.manifest import ManifestConverter

        source = _write_manifest(
            tmp_path,
            {
                "name": "samsara",
                "version": "0.8.0",
            },
        )
        converter = ManifestConverter()
        result = converter.convert(source, extra_fields={})
        assert isinstance(result, dict)

    def test_source_fields_not_mutated(self, tmp_path):
        """convert() must not mutate the source file on disk."""
        from samsara_cli.converter.manifest import ManifestConverter

        original_content = {
            "name": "samsara",
            "version": "0.8.0",
            "description": "desc",
        }
        source = _write_manifest(tmp_path, original_content)
        converter = ManifestConverter()
        converter.convert(source, extra_fields={"skills": "./skills/"})

        # Source file must be unchanged
        on_disk = json.loads(source.read_text())
        assert on_disk == original_content, "convert() mutated the source file on disk."


class TestManifestConverterFieldMergeOrder:
    def test_source_fields_form_base_of_output(self, tmp_path):
        """
        Source fields are the base; extra_fields are layered on top.
        Fields only in source must appear in output.
        """
        from samsara_cli.converter.manifest import ManifestConverter

        source = _write_manifest(
            tmp_path,
            {
                "name": "samsara",
                "version": "0.8.0",
                "author": {"name": "Roymond Liao"},
            },
        )
        converter = ManifestConverter()
        result = converter.convert(source, extra_fields={"skills": "./skills/"})
        assert "author" in result
        assert "skills" in result

    def test_extra_fields_win_on_key_conflict(self, tmp_path):
        """When source and extra_fields share a key, extra_fields value wins."""
        from samsara_cli.converter.manifest import ManifestConverter

        source = _write_manifest(
            tmp_path,
            {
                "name": "samsara",
                "version": "0.8.0",
                "skills": "./old/",
            },
        )
        converter = ManifestConverter()
        result = converter.convert(source, extra_fields={"skills": "./new/"})
        assert result["skills"] == "./new/"

    def test_empty_extra_fields_returns_all_source_fields(self, tmp_path):
        """extra_fields={} means source fields only, nothing added."""
        from samsara_cli.converter.manifest import ManifestConverter

        source = _write_manifest(
            tmp_path,
            {
                "name": "samsara",
                "version": "0.8.0",
                "description": "desc",
            },
        )
        converter = ManifestConverter()
        result = converter.convert(source, extra_fields={})
        assert set(result.keys()) == {"name", "version", "description"}


class TestManifestConverterRealWorldPluginJson:
    def test_actual_plugin_json_converts_correctly(self, tmp_path):
        """
        Test with the actual source plugin.json content from the repo.
        This verifies the full conversion pipeline works end-to-end.
        """
        from samsara_cli.converter.manifest import ManifestConverter

        actual_source = {
            "name": "samsara",
            "description": "向死而驗 — Death-first development workflow. Existential accountability for every line of code.",
            "version": "0.8.0",
            "author": {"name": "Roymond Liao"},
        }
        source = _write_manifest(tmp_path, actual_source)
        converter = ManifestConverter()
        result = converter.convert(source, extra_fields={"skills": "./skills/"})

        assert result["name"] == "samsara"
        assert result["version"] == "0.8.0"
        assert result["description"] == actual_source["description"]
        assert result["author"] == {"name": "Roymond Liao"}
        assert result["skills"] == "./skills/"

    def test_converted_manifest_is_json_serializable(self, tmp_path):
        """
        The output dict must be serializable back to valid JSON.
        Guards against any non-JSON-serializable values sneaking in.
        """
        from samsara_cli.converter.manifest import ManifestConverter

        source = _write_manifest(
            tmp_path,
            {
                "name": "samsara",
                "version": "0.8.0",
                "author": {"name": "Roymond Liao"},
            },
        )
        converter = ManifestConverter()
        result = converter.convert(source, extra_fields={"skills": "./skills/"})
        # Must not raise
        serialized = json.dumps(result)
        assert isinstance(serialized, str)
        # Must round-trip correctly
        round_tripped = json.loads(serialized)
        assert round_tripped == result


class TestManifestConverterErrorHandling:
    def test_nonexistent_source_path_raises(self, tmp_path):
        """Missing source file must raise FileNotFoundError."""
        from samsara_cli.converter.manifest import ManifestConverter

        converter = ManifestConverter()
        with pytest.raises(FileNotFoundError):
            converter.convert(tmp_path / "does_not_exist.json", extra_fields={})

    def test_invalid_json_in_source_raises(self, tmp_path):
        """Malformed JSON in source file must raise, not silently produce empty result."""
        from samsara_cli.converter.manifest import ManifestConverter

        bad_json = tmp_path / "plugin.json"
        bad_json.write_text("{ not valid json }")
        converter = ManifestConverter()
        with pytest.raises(Exception):  # json.JSONDecodeError or ValueError
            converter.convert(bad_json, extra_fields={})
