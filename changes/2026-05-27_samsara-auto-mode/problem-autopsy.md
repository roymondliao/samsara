# Problem Autopsy: samsara-auto-mode

## original_statement

> 目前 Samsara 的設計流程都會有 human gate 的把關，但目前在 AI 的進步下，其實不一定完全需要 human 來做 gate，而只需要目標明確，
> 具有可驗證跟回饋的方式，那麼 Agent 就能夠採用 auto mode 的方式，在 human 不介入下去執行。就是像是 `/goal` 的功能，不過目前 coding agent 的 `/goal` 功能太過簡單膚淺，只是產生類似 PoC level 的 code。
> Samsara 的 auto mode 是更高層級的，目標是要能夠完成到 pre-production level 的等級。
>
> 因此，我想提出 Samsara 的 auto mode 方式，可以透過 project config or session ask 的方式，來選擇是要 human-in-the-loop or auto
> mode 的選擇。
> 這個 auto mode 會有幾個重點：
> 1. 不是完全取代目前的 workflow，而是多一個 auto 的選項，可以不用 human-in-the-loop
> 2. 原本需要 human 來回答的部分，採用 subagent 來代替 review，並且做出決定
> 3. 如果當中 subagent 遇到 "不知道怎麼回答或是有困或的問提，都回到最初的設計理念來思考，用 first-principle 來作答。"
> 4. 這個替代 human 來回答的 subagent 是 auto mode 的核心，也是理解整的 project 的部分，所以是 principle level 的思維，然後可以從 high level 該注意每個部分的細節。
>
> 這是我對 Samsara 進化有 auto mode 的概念。

## reframed_statement

Samsara needs a configurable execution policy: `human-in-the-loop` or `auto`. In `auto` mode, the system must still run the existing Samsara workflow, but every human gate is handled by a principle-level gatekeeper subagent that understands the project, reasons from first principles when uncertain, records its decisions, and falls back to human when it cannot responsibly decide. The purpose is to enable autonomous pre-production-level execution, not shallow PoC generation.

## translation_delta

```yaml
translation_delta:
  - original: "human gate 的把關"
    reframed: "explicit gate decisions inside the same Samsara workflow"
    delta: "The issue is not the existence of gates; it is who or what answers them. Auto mode must preserve gate semantics."

  - original: "不一定完全需要 human 來做 gate"
    reframed: "human gates can be replaced only when goals, verification, feedback, and fallback are strong enough"
    delta: "The reframing adds decision conditions; not every gate is automatically safe to delegate."

  - original: "像是 `/goal` 的功能"
    reframed: "not a `/goal` wrapper; a higher-level workflow execution policy"
    delta: "`/goal` is used as a contrast case. Samsara auto mode must retain design discipline and auditability instead of optimizing for simple continuation."

  - original: "pre-production level"
    reframed: "gate alignment, workflow preservation, verification evidence, and post-run auditability"
    delta: "Pre-production quality needs observable criteria; otherwise it collapses into subjective satisfaction with generated code."

  - original: "project config or session ask"
    reframed: "execution mode must be selected before gates begin"
    delta: "The exact UI/config mechanism is left for planning, but the policy must be visible and explicit before execution."

  - original: "subagent 來代替 review，並且做出決定"
    reframed: "principle-level gatekeeper subagent can answer workflow questions, confirm transitions, request revision, reject unsafe continuation, or accept explicitly recorded gaps"
    delta: "The substitute is not merely a reviewer; it owns gate decisions and must be able to stop or redirect work without asking the user after auto mode begins."

  - original: "回到最初的設計理念來思考，用 first-principle 來作答"
    reframed: "uncertainty protocol: reason from project principles first, then decide or fall back"
    delta: "First-principles reasoning becomes an explicit uncertainty-handling mechanism, not just a style preference."
```

## kill_conditions

```yaml
kill_conditions:
  - condition: "If auto mode removes human gates without replacing them with explicit, auditable, evidence-backed agentic gate decisions."
    rationale: "That would turn Samsara from governed workflow into unchecked continuation, increasing late-stage user debugging cost."

  - condition: "If auto mode continues execution when requirements, risk, or verification criteria are unclear and the gatekeeper cannot resolve the uncertainty from project principles."
    rationale: "The system would confidently produce work that may not match the user's real intent; responsible fallback is mandatory."

  - condition: "If auto mode skips or weakens the existing Samsara workflow stages."
    rationale: "User clarified that auto mode does not replace research, pre-thinking, planning, implementation, iteration, or validation; it only replaces human gate answers."

  - condition: "If the substitute subagent is only a local checklist reviewer and does not understand project-level principles."
    rationale: "The core of auto mode is a design-authority-like subagent, not another narrow review pass."
```

## damage_recipients

```yaml
damage_recipients:
  - who: "User / project owner"
    cost: "If auto output does not align with the user's expected requirement, the user must do another debugging and correction pass."

  - who: "Maintainer / reviewer"
    cost: "If auto mode produces unclear decision traces, maintainers must reconstruct reasoning and audit decisions after the fact."

  - who: "Gatekeeper subagent design"
    cost: "The auto-mode core becomes a critical bottleneck; weak project understanding or shallow principle reasoning corrupts the whole run."
```

## observable_done_state

Samsara can select `human-in-the-loop` or `auto` through session-level ask before `research`, with persistent config support left out of the first cut. In `auto`, every original human question or confirmation is still present but is handled by a principle-level subagent that can answer, proceed, revise, reject, or accept an explicitly recorded gap. A completed auto run leaves an append-only auditable decision trace showing why each gate passed, which first principles were used, what uncertainty remained, and what verification supported the decision.
