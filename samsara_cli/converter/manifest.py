"""
ManifestConverter — Convert source plugin.json to target platform format.

Design decisions:
- Source plugin.json is read as a raw dict. All fields are preserved (pass-through).
  This is future-proof: unknown fields added by plugin authors survive conversion.
- extra_fields from platform config are merged in after source fields.
  extra_fields take precedence on key conflict — platform config overrides source.
- Required field validation (name, version) happens before merge.
  Missing required field raises ValueError with a named field, not a downstream
  KeyError from a consumer who receives None.

Merge order: {**source_dict, **extra_fields}
- Source fields are base.
- extra_fields override on conflict.
- Result contains all keys from both.

This design assumes:
- Source JSON is a flat or nested dict (JSON object at root level). A JSON array
  at root would pass JSON parsing but fail required-field validation — acceptable.
- extra_fields is a plain dict[str, Any] — no nested merging, no path notation.
  If a platform needs nested extra_fields, this is a known shortcut to revisit.
- 'name' and 'version' are the only required fields. If future required fields are
  added (e.g., 'api_version'), validation must be updated here.

Silent failure conditions documented:
- If source JSON has name=null or version=null (JSON null maps to Python None),
  the None value passes required-field validation and propagates silently.
  Considered acceptable: null is an author error, not a converter error.
"""

import json
from pathlib import Path
from typing import Any


# Required fields that must be present and non-None in the source manifest.
_REQUIRED_FIELDS: tuple[str, ...] = ("name", "version")


class ManifestConverter:
    """Convert a source plugin.json manifest to target platform format.

    The converter reads source JSON, validates required fields, merges platform
    extra_fields, and returns the combined dict. No template rendering is used —
    the target format is a plain JSON object preserving all source fields.

    This design was chosen over Jinja2 template rendering because the manifest
    template (manifest.json.j2) expects agents/hooks/skills_dir variables that
    are not available at manifest conversion time. The template is suited for
    full plugin manifest generation by an orchestrator, not for source→target
    field mapping. See scar report for details on this architectural decision.
    """

    def convert(
        self, source_manifest: Path, extra_fields: dict[str, Any]
    ) -> dict[str, Any]:
        """Convert source plugin.json to target platform manifest dict.

        Reads source JSON, validates required fields, merges extra_fields.
        All source fields are preserved (unknown fields pass through).
        extra_fields take precedence on key conflict.

        Args:
            source_manifest: Path to source plugin.json file.
            extra_fields: Platform-specific fields to add/override.
                         From PlatformConfig.formats.manifest['extra_fields'].

        Returns:
            Dict representing the converted manifest. All source fields present,
            extra_fields merged in with higher precedence.

        Raises:
            FileNotFoundError: If source_manifest does not exist.
            json.JSONDecodeError: If source_manifest contains malformed JSON.
            ValueError: If a required field (name, version) is missing from source.
                        Error message names the specific missing field.

        Does NOT raise:
            - For unknown source fields (they pass through)
            - For extra_fields that conflict with source (extra_fields wins)
            - For empty extra_fields (source fields only in result)
        """
        if not source_manifest.exists():
            raise FileNotFoundError(
                f"Source manifest not found: {source_manifest}. "
                "The source plugin.json must exist before conversion."
            )

        raw_text = source_manifest.read_text(encoding="utf-8")
        try:
            source_dict: dict[str, Any] = json.loads(raw_text)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Invalid JSON in source manifest {source_manifest}: {e.msg}",
                e.doc,
                e.pos,
            ) from e

        # Validate required fields — check before producing any output.
        # Also checks for None (JSON null): name=null or version=null is structurally
        # present but semantically absent — raises the same error as missing field.
        for field in _REQUIRED_FIELDS:
            if field not in source_dict or source_dict[field] is None:
                if field not in source_dict:
                    reason = "field is absent"
                else:
                    reason = "field is null (JSON null → Python None)"
                raise ValueError(
                    f"Source manifest required field '{field}' {reason}: {source_manifest}. "
                    f"Required fields: {list(_REQUIRED_FIELDS)}. "
                    "Conversion aborted — partial manifest would be worse than no manifest."
                )

        # Merge: source is base, extra_fields override on conflict
        result: dict[str, Any] = {**source_dict, **extra_fields}
        return result
