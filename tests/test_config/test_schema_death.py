"""
Death tests for config schema — targeting silent failure paths.

These tests verify that failures FAIL LOUDLY, not silently.
Each test names a specific silent failure this guards against.
"""

import pytest
from pydantic import ValidationError

# Death test imports — will fail until schema.py is implemented
# fmt: off
from samsara_cli.config.schema import (  # noqa: E402
    PlatformConfig,
    PlatformIdentity,
    SourceConfig,
    TransformationRule,
)


# --- DC-1: Missing required field must raise ValidationError, not silently default ---
# Silent failure guarded: If platform.name silently defaults to "" or None,
# all Codex output files would have no platform identity. The generated plugin.json
# would have a blank name. Nobody notices until the Codex marketplace rejects it.

class TestMissingRequiredFields:
    def test_platform_identity_missing_name_raises(self):
        """platform.name is required. Missing it must raise ValidationError immediately."""
        with pytest.raises(ValidationError) as exc_info:
            PlatformIdentity()  # name is required, no default
        errors = exc_info.value.errors()
        field_names = [e["loc"][0] for e in errors]
        assert "name" in field_names, (
            f"Expected 'name' in validation errors, got: {field_names}"
        )

    def test_platform_config_missing_platform_identity_raises(self):
        """Full PlatformConfig without platform identity must raise ValidationError."""
        with pytest.raises(ValidationError):
            PlatformConfig(
                source=SourceConfig(
                    plugin_dir=".claude-plugin",
                    skills_dir="skills",
                    agents_dir="agents",
                    hooks_dir="hooks",
                    references_dir="references",
                ),
                # platform identity missing
            )

    def test_transformation_rule_missing_id_raises(self):
        """TransformationRule.id is required. Missing silently would produce rules
        with no identity — impossible to debug which rule fired."""
        with pytest.raises(ValidationError) as exc_info:
            TransformationRule(
                scope="body",
                type="literal",
                match="some text",
                replace="other text",
                priority="medium",
                # id missing
            )
        errors = exc_info.value.errors()
        field_names = [e["loc"][0] for e in errors]
        assert "id" in field_names

    def test_transformation_rule_missing_match_raises(self):
        """TransformationRule.match is required. A rule with no match pattern
        would either crash at apply-time or silently match nothing."""
        with pytest.raises(ValidationError):
            TransformationRule(
                id="test_rule",
                scope="body",
                type="literal",
                replace="other text",
                priority="medium",
                # match missing
            )

    def test_transformation_rule_missing_replace_raises(self):
        """TransformationRule.replace is required. Missing silently would
        delete matched text (replacing with None/empty)."""
        with pytest.raises(ValidationError):
            TransformationRule(
                id="test_rule",
                scope="body",
                type="literal",
                match="some text",
                priority="medium",
                # replace missing
            )


# --- DC-2: Invalid regex pattern must fail at Pydantic validation time ---
# Silent failure guarded: If an invalid regex compiles silently to an empty-match
# pattern, every line in every agent file "matches" and gets incorrectly replaced.
# The failure only surfaces when someone reads the corrupted agent body.

class TestInvalidRegexPattern:
    def test_regex_rule_with_invalid_pattern_raises_at_validation_time(self):
        """An invalid regex in a rule typed 'regex' must raise ValidationError,
        not at conversion time (which is too late — the user sees corrupted output)."""
        with pytest.raises(ValidationError) as exc_info:
            TransformationRule(
                id="bad_rule",
                scope="body",
                type="regex",
                match="[unclosed bracket",  # invalid regex
                replace="something",
                priority="high",
            )
        # Must be a validation error, not a re.error at apply-time
        errors = exc_info.value.errors()
        assert len(errors) > 0, "Expected at least one validation error"
        # Error must reference the match field
        match_errors = [e for e in errors if "match" in str(e["loc"])]
        assert match_errors, f"Expected error on 'match' field, got: {errors}"

    def test_regex_rule_with_valid_pattern_passes(self):
        """Valid regex must not raise — sanity check that validator isn't over-eager."""
        rule = TransformationRule(
            id="valid_rule",
            scope="body",
            type="regex",
            match=r'invoke `samsara:([\w-]+)`',
            replace=r'use the `$samsara-\1` skill',
            priority="high",
        )
        assert rule.match == r'invoke `samsara:([\w-]+)`'

    def test_literal_rule_with_invalid_regex_chars_passes(self):
        """Literal rules must NOT validate regex — 'Read tool' contains no special chars
        but a rule with literal type and bracket in match is still valid (not compiled as regex)."""
        rule = TransformationRule(
            id="literal_rule",
            scope="body",
            type="literal",
            match="Read [tool]",  # contains regex metachar, but type=literal
            replace="file reading",
            priority="medium",
        )
        assert rule.match == "Read [tool]"


# --- DC-3: Extra unexpected keys must be rejected in strict mode ---
# Silent failure guarded: A typo in codex.yaml (e.g., 'formts' instead of 'formats')
# would create an extra ignored key. The real 'formats' section would be absent,
# causing KeyError or silent empty-template rendering downstream.
# By rejecting extra fields, the typo surfaces at load time, not conversion time.

class TestExtraKeyRejection:
    def test_platform_config_rejects_extra_keys(self):
        """PlatformConfig must reject unknown keys (Pydantic extra='forbid')."""
        with pytest.raises(ValidationError) as exc_info:
            PlatformConfig(
                platform=PlatformIdentity(name="codex", version_cmd="codex --version"),
                source=SourceConfig(
                    plugin_dir=".claude-plugin",
                    skills_dir="skills",
                    agents_dir="agents",
                    hooks_dir="hooks",
                    references_dir="references",
                ),
                unexpected_typo_field="this should be rejected",
            )
        errors = exc_info.value.errors()
        extra_errors = [e for e in errors if e["type"] == "extra_forbidden"]
        assert extra_errors, f"Expected extra_forbidden errors, got: {errors}"

    def test_transformation_rule_rejects_extra_keys(self):
        """TransformationRule must reject unknown keys."""
        with pytest.raises(ValidationError) as exc_info:
            TransformationRule(
                id="test",
                scope="body",
                type="literal",
                match="Read tool",
                replace="file reading",
                priority="medium",
                unknown_field="surprise",
            )
        errors = exc_info.value.errors()
        extra_errors = [e for e in errors if e["type"] == "extra_forbidden"]
        assert extra_errors


# --- DC-4: Invalid enum values must be rejected ---
# Silent failure guarded: An invalid scope (e.g., 'frontmater' typo) silently
# allows the rule to run on wrong content sections, causing mismatched replacements.

class TestEnumValidation:
    def test_transformation_rule_rejects_invalid_scope(self):
        """scope must be one of the defined values — invalid scope must raise."""
        with pytest.raises(ValidationError) as exc_info:
            TransformationRule(
                id="test",
                scope="frontmater",  # typo: should be 'frontmatter' or 'body'
                type="literal",
                match="Read tool",
                replace="file reading",
                priority="medium",
            )
        errors = exc_info.value.errors()
        scope_errors = [e for e in errors if "scope" in str(e["loc"])]
        assert scope_errors, f"Expected error on 'scope' field, got: {errors}"

    def test_transformation_rule_rejects_invalid_type(self):
        """type must be 'regex' or 'literal' — invalid type must raise."""
        with pytest.raises(ValidationError) as exc_info:
            TransformationRule(
                id="test",
                scope="body",
                type="wildcard",  # not a valid type
                match="Read tool",
                replace="file reading",
                priority="medium",
            )
        errors = exc_info.value.errors()
        type_errors = [e for e in errors if "type" in str(e["loc"])]
        assert type_errors

    def test_transformation_rule_rejects_invalid_priority(self):
        """priority must be 'high', 'medium', or 'low'."""
        with pytest.raises(ValidationError):
            TransformationRule(
                id="test",
                scope="body",
                type="literal",
                match="Read tool",
                replace="file reading",
                priority="urgent",  # not a valid priority
            )


# --- DC-14: Regex replace with $N backrefs must be rejected ---
# Silent failure guarded: Python re.sub() uses \1 for backrefs, not $1.
# A replace string with $1 produces literal "$1" in output — the captured
# group is silently lost. The output looks like it converted but contains
# garbage. First discoverer: user who sees literal "$1" in their skill text.


class TestRegexReplaceBackrefValidation:
    def test_dollar_backref_in_regex_replace_raises(self):
        """$1 in a regex rule's replace string must raise ValidationError.
        Python re.sub uses \\1, not $1. $1 silently produces literal '$1'."""
        with pytest.raises(ValidationError) as exc_info:
            TransformationRule(
                id="bad_backref",
                scope="body",
                type="regex",
                match=r"invoke `samsara:([\w-]+)`",
                replace=r"use the `$samsara-$1` skill",
                priority="high",
            )
        errors = exc_info.value.errors()
        replace_errors = [e for e in errors if "replace" in str(e["loc"])]
        assert replace_errors, f"Expected error on 'replace' field, got: {errors}"

    def test_dollar_two_backref_also_rejected(self):
        """$2 and higher backrefs must also be caught."""
        with pytest.raises(ValidationError):
            TransformationRule(
                id="bad_backref_2",
                scope="body",
                type="regex",
                match=r"(foo)(bar)",
                replace=r"$2-$1",
                priority="medium",
            )

    def test_backslash_backref_in_regex_replace_passes(self):
        """\\1 is the correct Python re.sub backref syntax — must pass."""
        rule = TransformationRule(
            id="good_backref",
            scope="body",
            type="regex",
            match=r"invoke `samsara:([\w-]+)`",
            replace=r"use the `$samsara-\1` skill",
            priority="high",
        )
        assert r"\1" in rule.replace

    def test_literal_rule_with_dollar_sign_passes(self):
        """Literal rules don't use re.sub — $1 is just a literal string, not a backref."""
        rule = TransformationRule(
            id="literal_dollar",
            scope="body",
            type="literal",
            match="price",
            replace="$100",
            priority="low",
        )
        assert rule.replace == "$100"

    def test_dollar_sign_not_followed_by_digit_passes(self):
        """$samsara (not a backref) must pass — only $N is dangerous."""
        rule = TransformationRule(
            id="dollar_non_backref",
            scope="body",
            type="regex",
            match=r"samsara:([\w-]+)",
            replace=r"$samsara-\1",
            priority="high",
        )
        assert "$samsara" in rule.replace
