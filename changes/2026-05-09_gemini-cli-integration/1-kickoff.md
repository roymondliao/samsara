# Kickoff: Gemini CLI Integration

## Problem Statement

Samsara already has a `samsara-cli`-based conversion and installation path for Codex. Gemini CLI should be added through the same multi-platform mechanism, not by manually maintaining a forked `.gemini/` copy. The integration must convert canonical samsara skills, agents, hooks, and references into Gemini CLI native project/user locations while preserving the core workflow chain and bootstrap behavior.

## Evidence

- Gemini CLI discovers workspace skills from `.gemini/skills/` and user skills from `~/.gemini/skills/`; a `SKILL.md` file with YAML frontmatter is the required skill artifact. Source: https://geminicli.com/docs/cli/creating-skills/
- Gemini CLI custom subagents are markdown files under `.gemini/agents/*.md` or `~/.gemini/agents/*.md`, with YAML frontmatter and markdown body as the agent system prompt. Source: https://geminicli.com/docs/core/subagents/
- Gemini CLI hooks are configured inside `settings.json`, not a standalone `hooks.json`; `SessionStart` can inject `hookSpecificOutput.additionalContext`. Source: https://geminicli.com/docs/hooks/reference/
- Gemini CLI settings live at project `.gemini/settings.json` and user `~/.gemini/settings.json`; project settings override user settings. Source: https://geminicli.com/docs/cli/settings/
- The existing Codex integration already has the relevant extension seams: platform YAML config, Jinja templates, converter modules, installer, CLI detection, and project/global install scopes.

## Risk of Inaction

If Gemini CLI support is not added, Samsara remains tied to Claude Code and Codex while Gemini CLI users cannot use the workflow through the supported installer path. The current multi-platform architecture would also remain only partially proven: Codex is a TOML-agent target, while Gemini is a markdown-agent/settings-json target. Not exercising that second shape leaves platform abstraction risks hidden until later.

## Scope

### Must-Have (with death conditions)

- **Gemini platform config** — Add `gemini-cli` as a first-class `samsara-cli` target with native path, naming, template, hook, and install metadata. Death condition: if Gemini CLI removes or breaks local `.gemini/skills`, `.gemini/agents`, or `settings.json` discovery before release, stop the integration.
- **Skill conversion to `.gemini/skills/`** — Convert all canonical samsara skills into Gemini-discoverable skill directories while preserving companion files and updating platform-specific invocation/tool language. Death condition: if Gemini skill activation cannot reliably trigger chained workflow skills even with explicit descriptions, downgrade to manual docs rather than claiming workflow support.
- **Subagent conversion to `.gemini/agents/*.md`** — Produce Gemini markdown agents with valid frontmatter (`name`, `description`, optional tool/model fields) and transformed body instructions. Death condition: if Gemini subagents cannot be dispatched or forced in a way compatible with samsara implement/review flows, mark agents unsupported and fail validation.
- **Hook conversion into `.gemini/settings.json`** — Generate and idempotently merge `SessionStart` hook configuration plus executable scripts using Gemini JSON stdin/stdout protocol. Death condition: if bootstrap context cannot be injected through `SessionStart` without stdout pollution or settings overwrite risk, do not install hooks.
- **Project/global install parity** — `samsara-cli install gemini-cli --scope project|global` installs to project `.gemini/` or user `~/.gemini/` locations without overwriting existing user settings. Death condition: if safe merge semantics cannot be implemented, only support `convert` and require manual install.
- **Smoke validation** — Validate structural discovery with Gemini CLI where available: skills listable, agents discoverable, settings JSON valid, and core chain entrypoint triggerable. Death condition: if verification cannot distinguish "files exist" from "workflow actually loads", label support experimental and block release claims.

### Nice-to-Have

- Generate a dry-run install diff for `.gemini/settings.json` merges.
- Convert Gemini tool names more precisely by consulting Gemini CLI's current tools reference.
- Add extension packaging later if Gemini extensions become the preferred distribution channel.

### Explicitly Out of Scope

- Rewriting canonical samsara skills/agents for Gemini only.
- Publishing to a Gemini extension marketplace or external registry.
- Windsurf support.
- Changing the existing Codex integration behavior except where shared abstractions need a minimal, backward-compatible extension.
- Supporting remote Gemini subagents through Agent2Agent.
- Supporting `.agents/skills` alias output; Gemini integration will use `.gemini/skills` as the default target.

## North Star

```yaml
metric:
  name: "Gemini workflow chain completeness"
  definition: "Percentage of canonical samsara workflow steps that can be converted, installed, discovered, and used in Gemini CLI through samsara-cli without manual file edits"
  current: 0%
  target: 100%
  invalidation_condition: "If Gemini CLI can discover files but cannot reliably execute the chained samsara workflow, file-level completeness is the wrong goal"
  corruption_signature: "Converted .gemini files exist and validation passes, but SessionStart bootstrap is absent or research cannot transition to planning in a real Gemini session"

sub_metrics:
  - name: "gemini-cli convert success rate"
    current: 0%
    target: 100%
    proxy_confidence: high
    decoupling_detection: "Conversion succeeds but target validator finds non-Gemini paths or unconverted Codex/Claude syntax"
  - name: "settings merge safety"
    current: 0%
    target: 100%
    proxy_confidence: high
    decoupling_detection: "Install succeeds while deleting, duplicating, or reordering unrelated user settings"
  - name: "Gemini discovery success"
    current: 0%
    target: 100%
    proxy_confidence: medium
    decoupling_detection: "Skills or agents appear in Gemini CLI listings but are not selected when matching prompts are used"
  - name: "end-to-end chain smoke pass"
    current: 0%
    target: 100%
    proxy_confidence: medium
    decoupling_detection: "Entrypoint skill activates but workflow chain stops before planning, implementation, review, or ship validation"
```

## Stakeholders

- **Decision maker:** Roymond Liao
- **Impacted teams:** Samsara maintainers and Gemini CLI users who want the same workflow available through `samsara-cli`
- **Damage recipients:** Maintainers who inherit one more conversion/validation surface; Gemini CLI users if installed files look valid but workflow behavior diverges; `samsara-cli` architecture if Gemini-specific settings merge logic leaks into otherwise generic converters
