# Death-First BDD Specification

Write acceptance criteria that test death paths before happy paths.

## Ordering Rule

1. **Silent failure scenarios first** — the system appears to succeed but doesn't
2. **Degradation scenarios** — fallback activates but isn't marked as degraded
3. **Unknown outcome scenarios** — timeout, partial write, outcome indeterminate
4. **Happy path with evidence chain** — success must include verifiable proof

## Format: acceptance.yaml

```yaml
feature: <feature-name>

scenarios:
  # --- Death paths first ---
  - name: "Silent failure - <description>"
    type: death_path
    given: "<precondition>"
    when: "<action>"
    then:
      - "<expected observable outcome>"
      - "state must be exactly one of: success, failure, unknown"
      - "unknown must trigger <recovery action>, never silent pass-through"

  - name: "Degradation - <description>"
    type: degradation
    given: "<precondition>"
    when: "<action>"
    then:
      - "system must mark degraded_mode: true"
      - "response must include degradation_reason"
      - "fallback must not silently impersonate normal operation"

  # --- Happy paths with evidence ---
  - name: "Success - <description>"
    type: happy_path
    given: "<precondition>"
    when: "<action>"
    then:
      - "<expected outcome>"
      - "success event must include: <evidence fields>"
      - "any future audit must reconstruct this decision from logs alone"
```

## Example: User Authentication

```yaml
feature: user-authentication

scenarios:
  - name: "Silent failure - session appears valid but token expired"
    type: death_path
    given: "user with session created 23h 59m ago"
    when: "system checks session validity at the boundary"
    then:
      - "session state must be exactly one of: valid, expired, unknown"
      - "unknown must trigger re-authentication, never silent pass-through"
      - "auth check must log the decision path with timestamp"

  - name: "Unknown outcome - auth service timeout"
    type: death_path
    given: "registered user attempting login"
    when: "auth service does not respond within 3 seconds"
    then:
      - "login result must be recorded as outcome_unknown"
      - "user must see explicit unable to verify message"
      - "system must never fall back to cached auth state silently"

  - name: "Success - login with evidence chain"
    type: happy_path
    given: "registered user with correct credentials"
    when: "user submits login form"
    then:
      - "user sees Dashboard"
      - "session valid for 24 hours"
      - "success event includes: auth_method, token_issued_at, verification_source"
```

## Anti-Pattern: Prayer Coverage

If your acceptance criteria only contain happy_path scenarios, it is not a test plan — it is a prayer. Mark it:

```yaml
coverage_type: prayer  # REJECTED — add death_path scenarios
```
