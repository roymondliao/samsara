"""
Death tests for ManifestConverter — targeting silent failure paths.

Each test names the specific silent failure it guards against.
Death tests run BEFORE unit tests. They must fail red before implementation,
then pass green after.

Silent failures guarded here:
  DMD-1: Source missing required fields (name, version) produces incomplete
         target — no validation error raised, consumer sees partial JSON.
  DMD-2: Source extra unknown fields are silently dropped — future-proof
         fields from authors vanish without error or warning.
  DMD-3: extra_fields from platform config are silently omitted — converted
         manifest works differently than expected on target platform.
  DMD-4: Source has both required and extra fields — converter must carry
         both; testing interaction between the two behaviors.
"""

import json
import pytest
from pathlib import Path


def _make_manifest_path(tmp_path: Path, content: dict) -> Path:
    """Write a plugin.json to tmp_path and return its path."""
    p = tmp_path / "plugin.json"
    p.write_text(json.dumps(content))
    return p


# ---------------------------------------------------------------------------
# DMD-1: Missing required fields must raise, NOT produce partial manifest
#
# Silent failure: source plugin.json missing 'name' or 'version' is silently
# written to target with empty or None values. Consumer of converted manifest
# receives structurally valid JSON that is semantically broken — Codex installs
# a plugin with no name or no version. First discovery: Codex marketplace or
# install fails at runtime, not at conversion time.
# ---------------------------------------------------------------------------


class TestDMD1MissingRequiredFields:
    def test_missing_name_raises_at_validation_not_silently(self, tmp_path):
        """
        Source without 'name' must raise an explicit error.
        Must NOT produce a manifest with name='' or name=None.
        Damage if silent: Codex installs a nameless plugin, references fail.
        """
        from samsara_cli.converter.manifest import ManifestConverter

        source = _make_manifest_path(
            tmp_path,
            {
                "description": "test plugin",
                "version": "1.0.0",
            },
        )
        converter = ManifestConverter()
        with pytest.raises((ValueError, KeyError, TypeError), match=r"(?i)name"):
            converter.convert(source, extra_fields={})

    def test_missing_version_raises_at_validation_not_silently(self, tmp_path):
        """
        Source without 'version' must raise an explicit error.
        Must NOT produce a manifest with version='' or version=None.
        Damage if silent: platform installs incompatible plugin, no version check.
        """
        from samsara_cli.converter.manifest import ManifestConverter

        source = _make_manifest_path(
            tmp_path,
            {
                "name": "samsara",
                "description": "test plugin",
            },
        )
        converter = ManifestConverter()
        with pytest.raises((ValueError, KeyError, TypeError), match=r"(?i)version"):
            converter.convert(source, extra_fields={})

    def test_missing_both_required_fields_raises(self, tmp_path):
        """
        Source with neither name nor version must raise.
        Empty or near-empty JSON must not pass through.
        """
        from samsara_cli.converter.manifest import ManifestConverter

        source = _make_manifest_path(tmp_path, {"description": "orphan"})
        converter = ManifestConverter()
        with pytest.raises((ValueError, KeyError, TypeError)):
            converter.convert(source, extra_fields={})

    def test_valid_source_does_not_raise(self, tmp_path):
        """
        Companion: a complete source must not raise — the error is selective.
        Guards against over-eager validation that rejects all input.
        """
        from samsara_cli.converter.manifest import ManifestConverter

        source = _make_manifest_path(
            tmp_path,
            {
                "name": "samsara",
                "version": "0.8.0",
                "description": "desc",
            },
        )
        converter = ManifestConverter()
        # Must NOT raise
        result = converter.convert(source, extra_fields={})
        assert isinstance(result, dict)

    def test_null_name_raises_not_propagates_silently(self, tmp_path):
        """
        Source with name=null (JSON null -> Python None) must raise.
        Silent failure: name=None passes key-exists check but produces
        a broken manifest with "name": null. Fix: check for None explicitly.
        """
        from samsara_cli.converter.manifest import ManifestConverter

        source = _make_manifest_path(
            tmp_path,
            {
                "name": None,  # JSON null
                "version": "0.8.0",
            },
        )
        converter = ManifestConverter()
        with pytest.raises(ValueError):
            converter.convert(source, extra_fields={})

    def test_null_version_raises_not_propagates_silently(self, tmp_path):
        """
        Source with version=null (JSON null -> Python None) must raise.
        """
        from samsara_cli.converter.manifest import ManifestConverter

        source = _make_manifest_path(
            tmp_path,
            {
                "name": "samsara",
                "version": None,  # JSON null
            },
        )
        converter = ManifestConverter()
        with pytest.raises(ValueError):
            converter.convert(source, extra_fields={})


# ---------------------------------------------------------------------------
# DMD-2: Extra unknown fields from source must be preserved, not dropped
#
# Silent failure: source plugin.json has 'author', 'homepage', or other fields
# not anticipated by the converter. Converter maps only known fields and drops
# the rest. Converted manifest is missing fields silently. First discovery:
# whoever depends on those fields in the target environment finds them absent,
# with no error — just missing data.
# ---------------------------------------------------------------------------


class TestDMD2UnknownFieldsPreserved:
    def test_author_field_preserved_in_output(self, tmp_path):
        """
        'author' field is not a required field but must not be dropped.
        Source: {"name": ..., "version": ..., "author": {...}}
        Target: must include author field verbatim.
        """
        from samsara_cli.converter.manifest import ManifestConverter

        source = _make_manifest_path(
            tmp_path,
            {
                "name": "samsara",
                "version": "0.8.0",
                "description": "desc",
                "author": {"name": "Roymond Liao"},
            },
        )
        converter = ManifestConverter()
        result = converter.convert(source, extra_fields={})
        assert "author" in result, (
            "SILENT FAILURE: 'author' field was dropped during conversion. "
            "Extra fields from source must be preserved."
        )
        assert result["author"] == {"name": "Roymond Liao"}, (
            f"'author' field value was mutated during conversion. Got: {result['author']!r}"
        )

    def test_unknown_future_field_preserved(self, tmp_path):
        """
        A field not known at conversion time must pass through unchanged.
        This guards against a future where plugin.json gains new fields that
        this converter does not explicitly handle.
        """
        from samsara_cli.converter.manifest import ManifestConverter

        source = _make_manifest_path(
            tmp_path,
            {
                "name": "samsara",
                "version": "0.8.0",
                "description": "desc",
                "future_field_xyz": "some_value_2030",
            },
        )
        converter = ManifestConverter()
        result = converter.convert(source, extra_fields={})
        assert "future_field_xyz" in result, (
            "SILENT FAILURE: unknown field 'future_field_xyz' was dropped. "
            "Converter must preserve all source fields, not only known ones."
        )
        assert result["future_field_xyz"] == "some_value_2030"

    def test_multiple_unknown_fields_all_preserved(self, tmp_path):
        """
        All unknown fields must be preserved, not just the first one.
        """
        from samsara_cli.converter.manifest import ManifestConverter

        source = _make_manifest_path(
            tmp_path,
            {
                "name": "samsara",
                "version": "0.8.0",
                "description": "desc",
                "author": {"name": "Roymond Liao"},
                "homepage": "https://github.com/roymond/samsara",
                "license": "MIT",
            },
        )
        converter = ManifestConverter()
        result = converter.convert(source, extra_fields={})
        assert result.get("author") == {"name": "Roymond Liao"}
        assert result.get("homepage") == "https://github.com/roymond/samsara"
        assert result.get("license") == "MIT"


# ---------------------------------------------------------------------------
# DMD-3: extra_fields from platform config must appear in output
#
# Silent failure: converter ignores extra_fields parameter, produces output
# without platform-required fields (e.g., 'skills'). The converted manifest
# is missing the Codex-required skills path. First discovery: Codex install
# fails or loads no skills — silently broken plugin.
# ---------------------------------------------------------------------------


class TestDMD3ExtraFieldsIncluded:
    def test_skills_extra_field_appears_in_output(self, tmp_path):
        """
        extra_fields={"skills": "./skills/"} must appear in converted output.
        Missing 'skills' key: Codex doesn't know where to find skill files.
        """
        from samsara_cli.converter.manifest import ManifestConverter

        source = _make_manifest_path(
            tmp_path,
            {
                "name": "samsara",
                "version": "0.8.0",
                "description": "desc",
            },
        )
        converter = ManifestConverter()
        result = converter.convert(source, extra_fields={"skills": "./skills/"})
        assert "skills" in result, (
            "SILENT FAILURE: 'skills' extra_field was not included in output. "
            "Codex manifest will be missing required field."
        )
        assert result["skills"] == "./skills/", (
            f"'skills' field has wrong value: {result['skills']!r}"
        )

    def test_multiple_extra_fields_all_included(self, tmp_path):
        """
        All extra_fields must appear — not just the first.
        """
        from samsara_cli.converter.manifest import ManifestConverter

        source = _make_manifest_path(
            tmp_path,
            {
                "name": "samsara",
                "version": "0.8.0",
            },
        )
        converter = ManifestConverter()
        result = converter.convert(
            source,
            extra_fields={
                "skills": "./skills/",
                "marketplace_id": "samsara-codex",
            },
        )
        assert result.get("skills") == "./skills/"
        assert result.get("marketplace_id") == "samsara-codex"

    def test_extra_fields_override_source_fields_on_conflict(self, tmp_path):
        """
        When extra_fields conflicts with a source field, extra_fields wins.
        This is the config-driven override semantic: platform config can
        normalize fields. Documents the expected merge order.
        """
        from samsara_cli.converter.manifest import ManifestConverter

        source = _make_manifest_path(
            tmp_path,
            {
                "name": "samsara",
                "version": "0.8.0",
                "skills": "./old-skills/",
            },
        )
        converter = ManifestConverter()
        result = converter.convert(source, extra_fields={"skills": "./new-skills/"})
        assert result["skills"] == "./new-skills/", (
            "extra_fields must take precedence over source fields of same name. "
            f"Got: {result['skills']!r}"
        )


# ---------------------------------------------------------------------------
# DMD-4: Interaction test — all fields present simultaneously
#
# Guards against implementation that handles each case in isolation but
# fails when all cases occur together.
# ---------------------------------------------------------------------------


class TestDMD4FullManifestInteraction:
    def test_required_unknown_and_extra_fields_coexist(self, tmp_path):
        """
        Full real-world scenario:
        - Required fields present and correct
        - Unknown source fields preserved
        - extra_fields merged in
        All three behaviors must work simultaneously.
        """
        from samsara_cli.converter.manifest import ManifestConverter

        source = _make_manifest_path(
            tmp_path,
            {
                "name": "samsara",
                "version": "0.8.0",
                "description": "samsara plugin",
                "author": {"name": "Roymond Liao"},
            },
        )
        converter = ManifestConverter()
        result = converter.convert(source, extra_fields={"skills": "./skills/"})

        # Required fields
        assert result["name"] == "samsara"
        assert result["version"] == "0.8.0"
        # Unknown source field preserved
        assert result["author"] == {"name": "Roymond Liao"}
        # Extra field from platform config included
        assert result["skills"] == "./skills/"
