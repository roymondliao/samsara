# Root Cause Tracing — Technique Guide

Techniques for yin-side root cause analysis. Not just finding "what broke" — understanding why the system allowed it to hide.

## The Core Question

> 「為什麼系統讓它藏這麼久？」

Every root cause investigation must answer this. The bug itself is the symptom. The real disease is the system's inability to detect it.

## Technique 1: Rot Path Tracing

Trace the path of corruption from entry point to detection point:

```
Entry point (where bad data/state entered)
    ↓
Layer 1: Did it validate? Why not?
    ↓
Layer 2: Did it transform? Did transformation hide the problem?
    ↓
Layer 3: Did it store? Is the stored form still identifiable as corrupted?
    ↓
...
    ↓
Detection point (where the failure finally became visible)
```

**Count the layers.** The number of layers between entry and detection is the "rot distance." Higher rot distance = more dangerous system design.

## Technique 2: Accomplice Identification

Find every component that helped the bug stay invisible:

| Accomplice Type | What It Does | Example |
|----------------|-------------|---------|
| Silent catch | Swallows error, returns default | `try/except: return None` |
| Implicit default | Fills missing data with plausible value | `config.get("timeout", 30)` when config is corrupted |
| Fallback | Switches to backup without marking degraded | Cache serves stale data as if fresh |
| Type coercion | Converts invalid to valid silently | `int("") → 0` in some languages |
| Retry without idempotency | Masks intermittent failures | Retry succeeds but side effect already committed |

## Technique 3: Timeline Reconstruction

Build a timeline from last-known-good to detection:

```yaml
timeline:
  - timestamp: "YYYY-MM-DD HH:MM"
    event: "Last confirmed working (evidence: ___)"
  - timestamp: "YYYY-MM-DD HH:MM"
    event: "Commit/deploy that may have introduced bug"
    commit: "<sha>"
    change_summary: "<what changed>"
  - timestamp: "YYYY-MM-DD HH:MM"
    event: "First observed symptom (evidence: ___)"
  - timestamp: "YYYY-MM-DD HH:MM"
    event: "Bug reported/detected"
```

**Key insight:** The gap between "introduced" and "first symptom" reveals how long the system was lying about its health.

## Technique 4: Differential Analysis

Compare the failing state to the last-known-good state:

- What changed in code? (`git diff` between last-known-good and suspected introduction)
- What changed in environment? (config, dependencies, infrastructure)
- What changed in data? (input patterns, volume, edge cases)

If nothing changed in code but behavior changed → the bug was always there, triggered by new data/load patterns. This is the most dangerous category — it means the system was never actually correct, just lucky.

## Anti-Pattern: Premature Fix

> 找到了一個看起來像 root cause 的東西就立刻修掉，然後宣告完成。

This is the debugging equivalent of "optimistic completion." The fix might address the symptom while leaving the actual root cause intact. Always verify your hypothesis with a death test BEFORE implementing the fix.
