# Problem Autopsy: Gemini CLI Integration

## original_statement

「現在要來進行整合 gemini-cli 的部分，要將 samsara 整合到 gemini-cli，會採用跟 codex 的整合方式一樣，要透過 `samsara-cli` 來進行整合。」

「以下是關於 Gemini CLI subagent/skills/hooks 的文件」

「請先閱讀文件內容(很重要)了解 gemini cli 的機制。」

「對，採用跟 Codex 一樣的 samsara-cli 方式」

## reframed_statement

Add Gemini CLI as a `samsara-cli` target using the existing multi-platform conversion/install architecture. The target output should be Gemini-native: `.gemini/skills/`, `.gemini/agents/`, and `.gemini/settings.json` hooks for project scope, with equivalent `~/.gemini/` locations for global scope. The goal is not merely file generation; the converted installation must preserve Samsara's bootstrap and core skill chain behavior in a real Gemini CLI session.

## translation_delta

```yaml
translation_delta:
  - original: "整合 gemini-cli"
    reframed: "Add a first-class gemini-cli platform target to samsara-cli"
    delta: "Integration could mean manual files, docs, or native extension packaging. The confirmed shape is samsara-cli convert/install/update."

  - original: "跟 codex 的整合方式一樣"
    reframed: "Use the same CLI lifecycle and platform registry, but with Gemini-native artifact formats"
    delta: "Same approach does not mean same files. Codex uses TOML agents and hooks.json/config.toml behavior; Gemini uses markdown agents and settings.json hooks."

  - original: "透過 samsara-cli 來進行整合"
    reframed: "The canonical samsara source remains unchanged; platform-specific adaptation happens in converter/config/templates/installer"
    delta: "This rejects a Gemini-specific fork of skills and agents as the primary implementation path."

  - original: "請先閱讀文件內容(很重要)"
    reframed: "Gemini CLI mechanism discovery is a hard prerequisite before planning"
    delta: "Planning must be based on Gemini's actual discovery and hook protocols, especially settings.json merge and hook JSON stdout rules."
```

## kill_conditions

```yaml
kill_conditions:
  - condition: "Gemini CLI skills, subagents, or hooks cannot support the core Samsara chain: research -> planning -> implement -> iteration -> security-privacy-review -> validate-and-ship"
    rationale: "A platform target that only installs files but cannot run the workflow creates false confidence and should not ship as supported."

  - condition: "Implementation requires maintaining a long-lived Gemini-only fork of canonical samsara skills or agents"
    rationale: "The requested architecture is samsara-cli conversion. A fork shifts maintenance cost into duplicated content and invalidates the multi-platform strategy."

  - condition: "Safe idempotent merge of .gemini/settings.json / ~/.gemini/settings.json cannot be implemented"
    rationale: "Hooks are configured in settings.json. Overwriting user settings or duplicating hook entries is worse than requiring manual installation."

  - condition: "Gemini CLI discovery/activation cannot be validated beyond file existence"
    rationale: "The main failure mode is silent non-activation: skills and hooks look installed but the session never receives the intended workflow context."
```

## damage_recipients

```yaml
damage_recipients:
  - who: "Maintainer"
    cost: "Every samsara skill, agent, hook, and reference change gains another conversion and smoke-test surface."

  - who: "Gemini CLI users"
    cost: "They may see successful installation while encountering broken skill activation, missing bootstrap context, or subagent dispatch mismatches at runtime."

  - who: "samsara-cli architecture"
    cost: "Gemini introduces markdown-agent output and settings.json hook merging, which can complicate abstractions originally proven mainly through Codex."

  - who: "Codex users"
    cost: "Shared converter or installer refactors made for Gemini could regress the existing Codex path if compatibility tests are insufficient."
```

## observable_done_state

Running `samsara-cli convert --platform gemini-cli` produces Gemini-native `.gemini/skills/`, `.gemini/agents/`, and `.gemini/settings.json` output from canonical samsara source. Running `samsara-cli install gemini-cli --scope project|global` installs those files idempotently without overwriting unrelated Gemini settings. In a fresh Gemini CLI session, Samsara bootstrap context loads, skills and subagents are discoverable, and the core workflow chain can progress past the research entrypoint.
