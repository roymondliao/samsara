# Problem Autopsy: codex-global-companion-runtime

## original_statement

> 是否有完全修正的解決方案，而不要只是臨時的 workround 處理

> 好，那就以這方案來修改。

## reframed_statement

Codex global installation must own a durable companion runtime and prove that
every installed command remains executable outside the Samsara source virtualenv.
Missing runtime, incompatible syntax, or missing dependencies must stop install
or validation visibly; agents must not invent a fallback interpreter.

## translation_delta

```yaml
translation_delta:
  - original: "不要只是臨時的 workaround"
    reframed: "global installation owns and validates a durable companion runtime"
    delta: "turns an immediate environment repair into an installer lifecycle contract"
  - original: "以這方案來修改"
    reframed: "implement runner provenance, absolute command resolution, syntax floor, smoke tests, and no-fallback guidance"
    delta: "makes each accepted design point mechanically testable"
```

## kill_conditions

```yaml
kill_conditions:
  - condition: "Codex provides a native, dependency-aware companion executable packaging contract."
    rationale: "Samsara should remove its private runner layer when the target platform owns the same lifecycle."
  - condition: "The repair requires agents to execute companion scripts with an inferred system interpreter."
    rationale: "That recreates the observed dependency and Python-version drift."
```

## damage_recipients

```yaml
damage_recipients:
  - who: "Samsara CLI maintainers"
    cost: "Must maintain runner provenance, manifest migration, and runtime smoke tests."
  - who: "Global-install users"
    cost: "Must install or expose one durable Samsara CLI runtime before installing the Codex adapter."
```

## observable_done_state

A global Codex install launched from a different project and a clean PATH runs
every companion through one absolute, manifest-recorded Samsara CLI command.
Ephemeral runners, missing dependencies, incompatible companion syntax, and
fallback interpreter attempts fail visibly before a workflow transition.

## decision_refs

```yaml
decision_refs:
  research.problem-source: null
  research.do-not-solve: null
  research.damage-recipient: null
  research.done-state: null
```

## accepted_gaps

none
