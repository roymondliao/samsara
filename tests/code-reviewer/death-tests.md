# Death Tests — code-reviewer (Task 3)

These tests define behavioral contracts that the refactored code-reviewer MUST satisfy.
Each test specifies: input scenario, required agent behavior, and failure condition.

"Death tests" here means: scenarios where silent failure would be undetected.
Each test targets a specific pattern that could be silently lost during extraction.

---

## DC-1: Silent Rot Detection — Swallowed Exception (Python)

**Death case:** After refactoring, the agent no longer detects errors caught but not re-raised or logged.
If this regresses, every Python PR with swallowed exceptions gets a PASS. Damage spreads silently.

**Input file type:** `.py` (Python) → Pass 1 domain = `code` → reads `references/code-review.md`

**Input scenario:**
```python
def fetch_user(user_id):
    try:
        response = db.get(user_id)
        return response
    except Exception:
        return None  # swallowed — caller gets None, no log, no re-raise
```

**Required agent behavior:**
- Identifies this as a Silent Rot Path
- Classifies it as **Critical**
- The finding references the specific pattern: "errors caught but not re-raised or logged"
- Does NOT produce PASS or PASS_WITH_CONCERNS without flagging this

**Failure condition:** Agent produces PASS or PASS_WITH_CONCERNS without a Critical finding on this pattern.

**Verdict:** FAIL if swallowed exception is not detected as Critical.

---

## DC-2: Dishonest Naming Detection — Misleading Boolean (Python)

**Death case:** After refactoring, the agent no longer detects names that misrepresent behavior.
If this regresses, naming lies compound across codebases silently.

**Input file type:** `.py` (Python) → Pass 1 domain = `code` → reads `references/code-review.md`

**Input scenario:**
```python
def is_success(response):
    # Returns True when response is not None,
    # but also True when response contains an error field
    if response is None:
        return False
    return True  # includes error responses — name lies
```

**Required agent behavior:**
- Identifies `is_success` as a dishonest name (returns True for error responses)
- Classifies it as **Critical**
- The finding references the naming honesty principle
- Does NOT produce PASS without flagging this

**Failure condition:** Agent produces PASS without a Critical finding on dishonest naming.

**Verdict:** FAIL if `is_success` dishonesty is not detected as Critical.

---

## DC-3: Router — IaC File with Missing Reference

**Death case:** Router selects domain `iac` for a `.tf` file, but `iac-review.md` doesn't exist.
Agent silently falls back to `code-review.md` and produces a review using wrong domain patterns.

**Input file type:** `.tf` (Terraform) → Pass 1 domain = `iac` → looks for `references/iac-review.md`

**State:** `references/iac-review.md` does NOT exist (current state of repo).

**Required agent behavior:**
- Does NOT fallback to `references/code-review.md`
- Does NOT produce any PASS/FAIL/PASS_WITH_CONCERNS verdict
- Returns UNKNOWN with reason: "no reference file for execution model: iac"
- Action required message instructs to create the missing reference

**Failure condition:** Agent produces any verdict (PASS/FAIL/PASS_WITH_CONCERNS) for a `.tf` file,
or produces UNKNOWN with a reason that does not identify the missing reference file.

**Verdict:** FAIL if agent does not return UNKNOWN with correct reason when iac-review.md is missing.

---

## DC-4: Router — Unknown File Type

**Death case:** Agent receives a file with no recognizable extension (e.g., `Makefile`, `.toml`, `.sql`)
and silently applies `code-review.md` patterns anyway, producing a review it shouldn't.

**Input file type:** `.sql` (SQL file) → Pass 1: no match → Pass 2: content inspection → no match → domain = UNKNOWN

**State:** No reference file for UNKNOWN domain.

**Required agent behavior:**
- Completes both Pass 1 and Pass 2 detection
- Finds no matching domain after content inspection
- Returns UNKNOWN with reason: "unable to determine execution model for this file"
- Does NOT produce a review verdict

**Failure condition:** Agent produces any verdict for a `.sql` file,
or skips Pass 2 content inspection before declaring UNKNOWN.

**Verdict:** FAIL if agent does not return UNKNOWN with correct reason for unrecognized file types.

---

## DC-5: Regression — All Three Mother Rules Present

**Death case:** Extraction removes or weakens the Three Mother Rules from the agent definition.
If this regresses, the cross-domain judgment standard is lost from reviews of any domain.

**Verification method (static — read the refactored agent file):**
The refactored `agents/code-reviewer.md` MUST contain all three Mother Rules verbatim:
1. "Any structure must be able to articulate its death."
2. "Any boundary must label its assumptions."
3. "Any abstraction must make errors easier to see, not harder."

**Failure condition:** Any of the three Mother Rules is missing from `agents/code-reviewer.md` after refactoring.

**Verdict:** FAIL if any Mother Rule is absent from the agent definition.

---

## DC-6: Regression — Scar Report Integrity (Step 4) Stays in Agent

**Death case:** Extraction accidentally moves Step 4 (Scar Report Integrity) into `code-review.md`,
making it domain-specific. Then IaC reviews skip scar report checking entirely.

**Verification method (static — read both files after refactoring):**
- `agents/code-reviewer.md` MUST contain Step 4 (Scar Report Integrity) with all three sub-checks:
  - Schema compliance
  - Self-iteration honesty
  - Resolved items validity
- `references/code-review.md` MUST NOT contain Step 4.

**Failure condition:** Step 4 is absent from `agents/code-reviewer.md` OR present in `references/code-review.md`.

**Verdict:** FAIL if Step 4 is not exclusively in the agent definition.

---

## DC-7: Regression — Review Order Framework Stays in Agent

**Death case:** Extraction moves the Review Order framework into `code-review.md`,
making the 1-2-3-4-5 ordering domain-specific instead of universal.

**Verification method (static — read both files after refactoring):**
- `agents/code-reviewer.md` MUST contain the Review Order section with steps 1-5 enumerated
- The step descriptions in the agent may reference the reference file for behavioral details,
  but the ordering and step names must be present in the agent definition

**Failure condition:** Review Order is absent from `agents/code-reviewer.md` after refactoring.

**Verdict:** FAIL if the 5-step Review Order is not in the agent definition.

---

## How to Run These Tests

**DC-1, DC-2:** Mental walkthrough — trace the instruction flow from the refactored agent through
the reference file for a Python input. Verify the specific patterns appear in `references/code-review.md`
and that the agent's Step 3 and Step 2 instructions correctly reference the file.

**DC-3, DC-4:** Mental walkthrough — trace the router logic in the refactored agent for the given
input. Verify the UNKNOWN failure modes are present and specific.

**DC-5, DC-6, DC-7:** Static file verification — read `agents/code-reviewer.md` and
`references/code-review.md` after refactoring and check presence/absence of required content.

---

## Pre-refactoring Test Run (Step 3)

**DC-1:** PASS against current agent (swallowed exception pattern is in Step 3 inline)
**DC-2:** PASS against current agent (is_success pattern is in Step 2 inline)
**DC-3:** FAIL against current agent (no router exists — agent would attempt review of .tf file)
**DC-4:** FAIL against current agent (no router exists — agent would attempt review of .sql file)
**DC-5:** PASS against current agent (Three Mother Rules present)
**DC-6:** PASS against current agent (Step 4 present, code-review.md doesn't exist yet)
**DC-7:** PASS against current agent (Review Order present)

Post-refactoring target: ALL tests PASS.
