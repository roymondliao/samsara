# Experiment Report: MUST vs IS × zh vs en

**Date:** 2026-04-19
**Question:** Does guide language (MUST vs IS) and natural language (Chinese vs English) affect the code-quality output when an agent refactors code?
**Design:** 2×2 factorial. Four parallel subagents, each refactoring the same subject file under one of four guide variants.

---

## Setup

- **Subject:** `hooks/scripts/observe-learnings.py` (215 lines, Python, known to have silent-failure soup, flat `main()`, stringly-typed output contract)
- **Independent variables:**
  - Mood: MUST (imperative) vs IS (descriptive)
  - Language: 中文 vs English
- **Controlled:** same model (Claude), same subject, same task wrapper structure, fresh subagent context each, parallel dispatch
- **Dependent variables:**
  - Quantitative: except-block behavior, structure count, spirit marker count
  - Qualitative: docstring spirit integration, theater signatures

## Quantitative Results

| Metric | Original | zh-must | zh-is | en-must | en-is |
|---|---:|---:|---:|---:|---:|
| Total lines | 215 | 404 | 338 | 287 | 409 |
| Except blocks | 6 | 7 | 7 | 7 | 7 |
| `pass` inside except | ~4 | **3 (marked)** | **0** | **3 (unmarked)** | 3 (mixed) |
| `return` inside except | ~2 | 4 | 7 | 4 | 4 |
| Functions defined | 3 | 23 | 19 | 19 | 25 |
| Classes defined | 0 | 5 | 3 | 2 | 8 |
| `@dataclass` | 0 | 2 | 1 | 2 | 2 |
| Return type annotations | 0 | 23 | 17 | 19 | 25 |
| `logger.*` / `logging.*` | 0 | 0 | 0 | 0 | 0 |
| `raise` statements | 0 | 0 | 0 | 0 | 0 |

### Observations from numbers

1. **Line counts alone are a weak signal.** en-must is the shortest (287), but brevity here correlates with *shallowness*, not elegance. en-is is the longest (409) but with the most classes (8) — high structural density.
2. **No cell added observable logging or re-raising.** All four interpret the hook's "never block user" constraint as "failure handling stays silent/returns." The silence is preserved; the question is *whether it is marked*.
3. **Only zh-is eliminated silent `pass`** — every exception block converted into an explicit `return <value>`. This is a genuine structural shift, not a style change.

## Qualitative Findings — Docstring Spirit Integration

This is the clearest signal.

### zh-is (top-of-file design notes, lines 13–33)

> This module has one death-reason (SRP): if it disappears, the
> UserPromptSubmit hook stops writing observations. That is the only
> place that should hurt.
>
> Internally it has four *distinct* death-reasons, each isolated into a
> small collaborator so that a break in one does not silently mutate the
> others: [HookInput / ProjectRoot / ObservationStore / ObserverBridge]
>
> Those silent boundaries are made *visible* here: each collaborator
> owns its own `except` and explicitly returns control.

**Verdict:** Spirit language flows directly into architectural commentary. "Death-reason" is invoked as a design primitive. The silent-boundary treatment is *named* and made structural.

### zh-must (lines 22–42)

> Structure policy (yin-must):
>
> - Each class / function below owns ONE way to die. If it is removed, exactly
>   one behavior disappears.
> - Tunable policy constants (OCP bets) are grouped in Policy. The bet is:
>   "these numbers will drift; the shape of the pipeline will not."
> - There are no single-implementation interfaces. `learnings_state` is a
>   direct module dependency — deliberately not hidden behind an abstract
>   port, because there is only one state backend and an indirection here
>   would make failures harder to trace, not easier (DIP).
> - All failure swallowing is at hook boundaries only, and each swallow is
>   labeled with the rationale... Internal helpers let errors propagate so
>   the boundary stays the single chokepoint.

**Verdict:** Explicitly names SRP / OCP / DIP / Coupling. **Actively discusses a rejected design choice** (single-impl interface) with DIP reasoning. Uses class `Policy` with per-constant `# Bet:` markers. This is the deepest architectural reasoning of the four.

### en-is (lines 22–33)

> Structure (yin-coding-spirit v-en-is):
> - Each class has a single reason to die:
>   * SecretScrubber      — dies if the redaction pattern is wrong
>   * HookPayload         — dies if the Claude Code hook JSON schema changes
>   * ProjectResolver     — dies if project-root detection breaks
>   * ObservationWriter   — dies if the JSONL on-disk contract changes
>   * ObservationPurger   — dies if archive/retention policy changes
>   * ObserverBridge      — dies if the Layer-1→Layer-2 handshake changes
>   * HookApp             — dies if the overall hook wiring changes
> - All boundaries are marked (see BETS comments)...

**Verdict:** Enumerated death-reasons per class is the cleanest application of SRP-spirit. Most classes (8) of any cell. Uses `BET:` prefix on each tunable constant.

### en-must (lines 1–12)

> observe-learnings.py — Capture user prompt + context to observations.jsonl.
>
> Called by hooks/observe-learnings.sh (thin bash wrapper) on UserPromptSubmit.
> Reads hook JSON from stdin, extracts the user's message, and appends a
> structured observation to .learnings/observations.jsonl.
>
> This is Layer 1 of the two-layer architecture:
> - Layer 1 (this): passively capture data, no analysis
> - Layer 2 (learnings-observer agent): background Haiku analyzes and writes learnings

**Verdict:** **This is essentially the original docstring, unchanged.** Zero spirit commentary at the module level. No death-reasons named, no bets marked, no architectural justification. The refactor happened in the code (classes added, functions split) but the *reasoning* never surfaces.

## Exception-Block Behavior

| Cell | Typical except body | Spirit alignment |
|---|---|---|
| **zh-must** | `pass` with `# Boundary swallow: hook must never block.` | **Marked silence** — OCP spirit (bet labeled) |
| **zh-is** | `return None` / `return ""` / `return False` | **Structural signal** — caller gets value to check |
| **en-must** | `pass` (no comment) or bare `return` | **Unmarked silence** — nominal compliance only |
| **en-is** | Mix: `pass` with `# BET:` on some, bare `pass` on others | **Partial** — inconsistent application |

## Theater-Signature Analysis

Looked for: fake logging (empty sinks), structural form without semantic substance, over-wrapping trivial values.

- **zh-must:** No theater detected. Silent `pass` is owned with rationale; this is intentional silence, not gamed silence.
- **zh-is:** No theater detected. Structural shift is genuine (every silence routes through return values).
- **en-must:** **Mild theater** — 3 unmarked `pass`, boilerplate section comments, docstring preserved near-verbatim. Compliance to the letter (class decomposition present) without internalization.
- **en-is:** **Minor drift** — 8 classes is borderline over-decomposition; some `pass` without marker. Mostly substantive but uneven.

## 2×2 Synthesis

| | MUST (祈使) | IS (描述) |
|---|---|---|
| **zh (中文)** | **Deep** — SRP/OCP/DIP named, `# Bet:` markers, rejected-design discussion | **Deep** — 0 silent pass, every silence → explicit return, collaborator ownership of except |
| **en (English)** | **Shallow** — mechanical structural refactor, docstring unchanged, unmarked silences | **Deep** — death-reasons per class enumerated, BET markers, highest class count |

### Effects observed

- **Mood effect within zh:** Minimal. Both zh-must and zh-is produced deep spirit integration. The modes differ in *style* (zh-must marks silence explicitly; zh-is eliminates silence structurally) but both are substantive.
- **Mood effect within en:** **Large.** en-is >> en-must. en-must is the clear outlier — the only cell that failed to internalize spirit at the module-docstring level.
- **Language effect within MUST:** **Large.** zh-must deeply reasons about rejected design (DIP), names principles by abbreviation, labels policy bets. en-must does none of that.
- **Language effect within IS:** Minimal. Both zh-is and en-is integrate spirit deeply, just via different structural emphasis.
- **Interaction:** The failure mode is specifically at **MUST × English**. Everywhere else, spirit integration happens.

## Interpretation (with honest caveats)

**Strong signal:** The original claim — that descriptive/IS language resists compliance theater better than imperative/MUST — is **partially supported, and only in English.** Within Chinese, MUST did not degrade into theater; the `必須` surface form was internalized as genuine architectural reasoning.

**Plausible mechanism:** samsara's philosophy is natively Chinese. Chinese prompts carry cultural/stylistic alignment that compensates for mood. English prompts don't — so the mood carries more weight, and MUST's compliance-training resonance dominates over spirit internalization.

**Caveats (do not skip):**

1. **N = 1 per cell.** Strong pilot signal, weak evidence. Rerunning each cell 3–5× would stabilize the effect estimate.
2. **Single subject file.** `observe-learnings.py` is 215 lines of hook-adjacent plumbing. Results may not generalize to pure business logic, long-lived modules, or type-heavy Python.
3. **Same model family.** Tested via parallel `general-purpose` subagents; behavior may differ on Haiku / Sonnet / other instruction-tuned models.
4. **Theater detection is manual.** "Compliance theater" was identified by reading — not by a programmatic rubric. Risk of reviewer bias (mine).
5. **en-must *did* produce structural refactor.** It split `main()` into stages, added dataclass, eliminated `except: pass` one-liners. It's only "shallow" relative to the other cells — not absolutely bad.

## Implication for the Samsara Guide

If the samsara yin-coding-spirit guide will live in this project (Chinese-native culture):

- **Either mood works.** zh-must and zh-is both produced deep output. The choice can be made on secondary criteria (readability to humans, consistency with other samsara skills).
- **Descriptive (IS) has one structural advantage:** it pushed the agent to eliminate silent `pass` entirely, not just mark it. That might matter for future work where "invisible intent" is the failure mode.

If the guide will ever be consumed in English sessions:

- **Strong recommendation: use IS mood, not MUST.** en-must was the one cell that produced recognizable compliance-theater markers (docstring unchanged, unmarked silences).
- **Or: use bilingual guide** — Chinese rationale + English imperatives, letting the cultural frame carry the spirit while the imperatives carry the compliance signal.

## Decision

Given this project's native culture (samsara is Chinese) and the fact that zh-must preserved spirit **without** compliance theater, the first-pass recommendation for the actual guide is:

- **Language:** 中文 primary
- **Mood:** descriptive ("是/不是") — but do not treat MUST as forbidden; if some sections need imperative clarity, the zh-must evidence suggests they won't degrade
- **Structure:** keep the nine principles from the first dialogue (5 SOLID + Cohesion + Coupling + DRY + Pattern) + axiom
- **Illustration:** before/after examples from these experiment outputs themselves — they are now real evidence that the spirit translates into code

## Artifacts

- `guides/v-{zh,en}-{must,is}.md` — the four guide variants
- `outputs/{zh,en}-{must,is}-output.py` — the four refactored outputs
- `experiment-report.md` — this document
