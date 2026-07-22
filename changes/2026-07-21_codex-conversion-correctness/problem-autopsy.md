# Problem Autopsy: codex-conversion-correctness

## original_statement

> 請協助修正 Bootstrap hook、Codebase Map freshness hook、Auto Gatekeeper companion script、agent 權限／effort／description，以及 B 級防止假成功的問題。Codex skill 呼叫以 `SKILL.md.name` 為準；目錄可維持 `samsara-research`，呼叫是 `$research`。Gemini live support 可移除，但 CLI 的 multi-platform 定位保留給未來 Antigravity CLI 或 Pi。

## reframed_statement

Make the Codex adapter preserve the source workflow's runtime authority graph,
and make conversion/update fail when that graph cannot be resolved. Remove the
retired Gemini adapter without narrowing the CLI's future platform role.

## translation_delta

```yaml
translation_delta:
  - original: "folder 是 samsara-research，但是在 codex 內呼叫是 $research"
    reframed: "directory naming and skill identity are separate target contracts"
    delta: "prevents rewriting source names merely to match packaging paths"
  - original: "B 選項的部分建議很好"
    reframed: "add mechanical teeth for runtime refs, companion dependencies, and install ownership"
    delta: "turns a broad acceptance into individually testable contracts"
```

## kill_conditions

```yaml
kill_conditions:
  - condition: "A proposed check judges prose quality instead of a machine-observable Codex contract."
    rationale: "content micro-assertions recreate the brittle tests already rejected for workflow prose"
  - condition: "Owned-file cleanup cannot distinguish Samsara files from user files."
    rationale: "unsafe deletion is worse than retaining a stale generated file"
```

## damage_recipients

```yaml
damage_recipients:
  - who: "Codex users"
    cost: "successful install followed by broken workflow transitions or missing bootstrap context"
  - who: "repository maintainers"
    cost: "green tests conceal target-platform drift and stale installed artifacts"
  - who: "target project owners"
    cost: "installer may otherwise delete foreign files or require an unrelated Python environment"
```

## observable_done_state

A live conversion exposes the expected `SKILL.md.name` identities to Codex and
every generated `$skill`, agent, hook, and companion reference resolves. Update
removes only previously recorded Samsara-owned paths. Gemini is absent from the
live adapter surface while generic future-platform wording remains.

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
