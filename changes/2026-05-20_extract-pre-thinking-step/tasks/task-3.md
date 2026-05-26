# Task 3: Update skills/planning/SKILL.md

## Context

Read: `overview.md`

`skills/planning/SKILL.md` currently contains Step 1.5 (Pre-thinking — Information Assumptions), which is being moved to the new `samsara:pre-thinking` skill. This task:

1. Removes Step 1.5 entirely
2. Adds `pre-thinking.md` to prerequisites with a guard (planning blocks if pre-thinking incomplete)
3. Updates the dot graph to remove the prethink/human_pt nodes and add a prerequisite guard

**Note:** The planning SKILL.md at `skills/planning/SKILL.md` is the file in the samsara repo — not the marketplace cache. All edits go to `skills/planning/SKILL.md` in the working directory.

## Files

- Modify: `skills/planning/SKILL.md`

## Death Test Requirements

- Test: planning invoked without `pre-thinking.md` → agent stops with explicit message, does NOT proceed to Tech Spec
- Test: planning invoked with `pre-thinking.md` present but missing `## Step C — Commitment` → agent stops, re-invokes `samsara:pre-thinking`
- Test: planning invoked with complete `pre-thinking.md` (commitment = Proceed) → agent proceeds to Step 2 normally

## Implementation Steps

- [ ] Step 1: Confirm `death-tests.md` exists from Task 1
- [ ] Step 2: Read `skills/planning/SKILL.md` fully before editing
- [ ] Step 3: **Remove Step 1.5 section** — delete from `## Step 1.5: Pre-thinking — Information Assumptions` through the closing paragraph ending "This gate is where human high-dimensional judgment is inserted..."
- [ ] Step 4: **Update Prerequisites section** — add `pre-thinking.md` entry with guard text
- [ ] Step 5: **Update dot graph** — remove `prethink` and `human_pt` nodes; add prerequisite guard node
- [ ] Step 6: Verify the skill still flows correctly: start reads prerequisites → guard checks pre-thinking.md → proceeds to spec
- [ ] Step 7: Verify no references to "Step 1.5" remain in the file
- [ ] Step 8: Write scar report

---

### Prerequisites Section Change

**Current:**
```markdown
## Prerequisites

Read from the feature's `changes/` directory:
- `1-kickoff.md` — scope, north star, stakeholders
- `problem-autopsy.md` — translation delta, kill conditions
```

**Replace with:**
```markdown
## Prerequisites

Read from the feature's `changes/` directory:
- `1-kickoff.md` — scope, north star, stakeholders
- `problem-autopsy.md` — translation delta, kill conditions
- `pre-thinking.md` — user-LLM assumption alignment and commitment

**Guard:** If `pre-thinking.md` is absent, or present but missing `## Step C — Commitment` section, **STOP**. Do not proceed to Step 2. Re-invoke `samsara:pre-thinking`.
```

---

### Dot Graph Change

**Current graph has:** `start -> prethink -> spec` (with prethink → human_pt branch)

**Replace the graph with** a version that:
- Starts at `start [label="讀取 1-kickoff.md\n+ problem-autopsy.md\n+ pre-thinking.md" shape=doublecircle]`
- Has `guard [label="pre-thinking.md\n完整？" shape=diamond]`
- Edge `start -> guard`
- Edge `guard -> spec [label="yes\n(commitment present)"]`
- Edge `guard -> blocked [label="no"]`
- Node `blocked [label="STOP:\nre-invoke\nsamsara:pre-thinking" shape=doublecircle]`
- Continue existing chain from `spec` onward (spec → acceptance → plan → decompose → output → gate → next)

---

### Step 1.5 Section Removal

Remove the entire section from `## Step 1.5: Pre-thinking — Information Assumptions` through the end of that section's content (approximately line 50 through line 101 in current file). This includes:
- The "How to pre-think" subsection
- The output template (the ```markdown block)
- The output states subsection
- The human gate subsection
- The closing "This gate is where..." paragraph

After removal, `## Step 2: Technical Specification` becomes the first step section.

## Expected Scar Report Items

- Potential shortcut: leaving any references to "pre-thinking" behavior in the planning skill body (the skill should be silent about pre-thinking internals — it just reads the pre-thinking.md artifact)
- Potential shortcut: not updating the dot graph (leaving prethink/human_pt nodes creates confusion about where pre-thinking now lives)
- Assumption to verify: no other planning skill support files reference Step 1.5 by name

## Acceptance Criteria

- Covers: "Degradation - planning starts without pre-thinking.md"
