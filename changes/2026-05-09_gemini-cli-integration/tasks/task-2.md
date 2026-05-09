# Task 2: Add Gemini markdown subagent conversion

## Context

Read: `changes/2026-05-09_gemini-cli-integration/overview.md`

Codex agents are currently rendered as TOML. Gemini agents must be markdown files in `.gemini/agents/*.md` with YAML frontmatter and transformed body instructions.

## Files

- Modify: `samsara_cli/converter/agent.py`
- Modify: `samsara_cli/converter/engine.py`
- Modify: `samsara_cli/config/templates/gemini-cli/agent.md.j2`
- Create: `tests/test_converter/test_agent_gemini.py`
- Modify: `tests/test_converter/test_agent_death.py`
- Modify: `tests/test_converter/test_engine.py`
- Modify: `tests/test_converter/test_engine_death.py`

## Death Test Requirements

- Test: Gemini agent conversion rejects empty body instead of rendering an empty system prompt.
- Test: Gemini agent conversion rejects or fails validation for invalid slug names.
- Test: converted Gemini agent contains YAML frontmatter with `name` and `description`.
- Test: Gemini conversion never writes `.toml` agent files.
- Test: `subagent_type:` source syntax is transformed out of Gemini agent bodies.

## Implementation Steps

- [ ] Step 1: Write Gemini agent death tests.
- [ ] Step 2: Run death tests with `source .venv/bin/activate` and `uv run pytest <test files>`; verify they fail.
- [ ] Step 3: Write happy-path tests for markdown frontmatter output.
- [ ] Step 4: Run happy-path tests; verify they fail.
- [ ] Step 5: Add a markdown agent conversion path selected by `formats.agent.type == "markdown"`.
- [ ] Step 6: Update engine agent output extension to `.md` for Gemini and `.toml` for Codex.
- [ ] Step 7: Run Codex agent tests plus Gemini agent tests; verify both pass.
- [ ] Step 8: Write scar report.
- [ ] Step 9: Commit.

## Expected Scar Report Items

- Potential shortcut: using the source agent filename as Gemini frontmatter name without applying `samsara-` naming.
- Potential shortcut: preserving source frontmatter accidentally and producing two frontmatter blocks.
- Assumption to verify: Gemini descriptions should be concise enough for automatic subagent selection.

## Acceptance Criteria

- Covers: "Silent failure - Gemini agent output uses wrong format"
- Covers: "Silent failure - unconverted source syntax leaks into Gemini output"
