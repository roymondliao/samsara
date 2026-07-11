# Problem Autopsy — Format Guide

The problem autopsy is the yin-side output of the research phase. It forces the problem to face its own death before any solution is proposed.

## Ownership

`problem-autopsy.md` is the sole owner of source wording, reframe, translation
delta, kill conditions, damage recipients, and observable done state.
`1-kickoff.md` must not duplicate this content; it points here and owns the
decision-ready handoff instead.

## Structure

The autopsy has six sections. Address every section with supported content or
this exact marker:

`Input incomplete; missing: <specific information or evidence>.`

Name the missing input precisely. The recorded gap is the finding. Do not infer
a value or use `TBD` or `N/A`.

### 1. original_statement
The exact wording of the problem as given by the user or stakeholder. Do not paraphrase. Copy verbatim.

### 2. reframed_statement
Your understanding of the problem. Write it in your own words.

### 3. translation_delta
Line-by-line comparison of original vs reframed. Each difference is a potential translation loss. Example:

```yaml
translation_delta:
  - original: "users can't log in"
    reframed: "authentication flow fails for returning users after session expiry"
    delta: "Original implies all users; actual scope is returning users with expired sessions"
```

### 4. kill_conditions
At least two conditions under which this problem should be abandoned, even if technically solvable:

```yaml
kill_conditions:
  - condition: "If fewer than 5% of users encounter this issue"
    rationale: "Cost of fix exceeds impact"
  - condition: "If the upstream auth service is being replaced within 3 months"
    rationale: "Fix would be thrown away"
```

### 5. damage_recipients
Who bears the cost when this problem is solved? Every solution transfers cost somewhere:

```yaml
damage_recipients:
  - who: "Backend team"
    cost: "Must maintain new auth middleware indefinitely"
```

### 6. observable_done_state
In three sentences or fewer: what is the observable difference between "solved" and "not solved"? If you cannot describe this, the problem is not yet understood.

## Example

See `templates/problem-autopsy.md` for a complete filled template.
