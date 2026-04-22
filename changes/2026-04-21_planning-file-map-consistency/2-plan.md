# Plan: Research ↔ Planning Bidirectional Completeness Gate

## Design Philosophy

This fix follows the AI-native framework principle:

```
Framework responsibility = guarantee the floor (強制輸出假設清單)
LLM capability          = determine the ceiling (假設清單的品質)
```

The framework does NOT prescribe what information Research must contain. It prescribes that Planning must surface its information assumptions as a visible artifact before proceeding — so the human gate has something concrete to review and correct.

Rigid sub-fields (e.g., "Architectural Constraints") violate this principle: they lock the ceiling to what the spec author could anticipate, not what LLM capability can derive. Pre-thinking scales with LLM capability.

---

## What Is Being Modified

**One file only:** `samsara/skills/planning/SKILL.md`

Add a pre-thinking step (Step 1.5) between "read Research" and "write Tech Spec." This step forces Planning to:

1. Derive what information it needs to write this plan (feature-specific, not from a checklist)
2. Output a visible "Information Assumptions" artifact — what it assumes it has, what it sees as gaps
3. Stop at a human gate with this artifact visible
4. Human decides: confirm assumptions and proceed, or send back to Research with specific questions

Research template is NOT modified. Research produces what it produces. Planning's pre-thinking is what catches gaps — and the catch quality scales with LLM capability.

---

## I/O with Unknown Output

**Pre-thinking step (Step 1.5):**

| Planning's self-assessment | Output | State |
|---|---|---|
| All needed information present in Research | Assumption list + "ready to proceed" | `success` |
| One or more gaps identified | Assumption list + gap questions | `failure` — stop, return to human |
| Cannot determine if information is sufficient | Assumption list + explicit uncertainty | `unknown` — surface to human, do not assume |

The `unknown` state matters: Planning must NOT silently treat "I'm not sure if I need more" as "I have enough." Uncertainty must be surfaced.

**Information Assumptions artifact format:**

```markdown
## Planning Pre-thinking: Information Assumptions

To write this plan, I am assuming:
- [assumption 1]: <what I believe Research established>
- [assumption 2]: <what I believe Research established>

Gaps I cannot resolve from Research:
- [gap 1]: <specific question — what decision would I need to make that Research hasn't constrained?>

Uncertainties:
- [uncertainty 1]: <I cannot tell if Research intended X or Y — which is it?>

Ready to proceed? Human confirmation required.
```

---

## Death Cases

**Death Case 1: Pre-thinking produces a silent pass**

- Trigger: Planning outputs "no gaps identified" but actually missed a dimension it didn't think to check (unknown unknown).
- The lie: Pre-thinking passed. Assumption list looks complete.
- The truth: A gap exists that Planning didn't know to look for.
- Detection: This is the hardest case — it's the LLM ceiling problem. Mitigation is the human gate: the assumption list gives human the chance to spot what Planning didn't ask. As LLM capability grows, silent passes decrease.

**Death Case 2: Pre-thinking produces gaps but human gate skips review**

- Trigger: Gap list is present, human says "proceed" without reading it.
- The lie: Human gate passed.
- The truth: Gaps were not actually resolved; Planning proceeds with unverified assumptions.
- Detection: After implementation, cross-check: does the plan contain any decision that was listed as a gap? If yes, gate was bypassed.

**Death Case 3: Pre-thinking step omitted under pressure**

- Trigger: Planning agent feels the Research is "obviously complete" and skips Step 1.5 to save time.
- The lie: Plan looks well-grounded.
- The truth: No assumption list was produced; human gate reviewed no artifacts.
- Detection: Planning output must include the assumption list artifact. If it's absent, Step 1.5 was skipped. This is a hard stop — no assumption list = Step 1.5 not done.

---

## What Counts as a Gap

Planning should ask itself, for each section it is about to write:

> "Am I about to make a decision that Research has not constrained? If yes, that's a gap."

Examples:
- Writing File Map → "Do I know WHERE things should live? Has Research constrained location?" → if not, that's a gap
- Writing Tech Spec interface → "Do I know WHO owns the interface?" → if not, that's a gap
- Writing acceptance criteria → "Do I know what 'success' looks like to the stakeholder?" → if not, that's a gap

This is feature-specific and cannot be enumerated upfront. That's the point.

---

## Task Decomposition

**One task.** Research template is not modified.

### Task 1: Update Planning skill — add Step 1.5 Pre-thinking

Modify `samsara/skills/planning/SKILL.md`:
- Insert Step 1.5 between Prerequisites and Step 2 (Technical Specification)
- Step 1.5 content: pre-thinking instructions, assumption list format, gap question format, uncertainty handling, hard stop instruction
- Hard stop: "If gaps or uncertainties exist, do NOT proceed to Step 2. Output assumption list to human gate first."
- The assumption list is a mandatory artifact — its absence means Step 1.5 was skipped
