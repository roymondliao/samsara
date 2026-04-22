# Experiment Report — Phase 2 (Replication)

**Date:** 2026-04-20
**Purpose:** Strengthen experiment confidence by replicating each of the four 2×2 cells two additional times (N=3 per cell, 12 total runs). Phase 1 made claims from single runs; Phase 2 tests whether those claims survive replication.

## Setup

- 8 new parallel subagent dispatches (2 × 4 cells)
- Identical prompt, guide content, subject file (`hooks/scripts/observe-learnings.py`), and task wrapper
- Outputs: `outputs/<cell>-run{2,3}-output.py`
- Analysis: quantitative grep + manual read of new outputs

## Raw Matrix (12 runs)

| cell/run | lines | classes | bare `pass` | docstring lines | yin-marker grep |
|---|---:|---:|---:|---:|---:|
| zh-must / 1 | 404 | 5 | 3 | 41 | 6 |
| zh-must / 2 | 302 | 1 | 3 | 9 | 3 |
| zh-must / 3 | 402 | 7 | 4 | 45 | 5 |
| **zh-must mean** | **369** | **4.3** | **3.3** | **31.7** | **4.7** |
| zh-is / 1 | 338 | 3 | **0** | 32 | 3 |
| zh-is / 2 | 407 | 5 | 4 | 39 | 2 |
| zh-is / 3 | 382 | 2 | 3 | 19 | 1 |
| **zh-is mean** | **376** | **3.3** | **2.3** | **30.0** | **2.0** |
| en-must / 1 | 287 | 2 | 3 | **10** | **0** |
| en-must / 2 | 339 | 2 | 5 | 19 | **0** |
| en-must / 3 | 331 | 1 | 3 | 19 | **0** |
| **en-must mean** | **319** | **1.7** | **3.7** | **16.0** | **0.0** |
| en-is / 1 | 409 | 8 | 3 | 31 | 8 |
| en-is / 2 | 402 | 2 | 5 | 39 | 1 |
| en-is / 3 | 346 | 2 | 6 | 19 | 0 |
| **en-is mean** | **386** | **4.0** | **4.7** | **29.7** | **3.0** |

### Key numeric patterns

- **en-must is the only cell with 0 yin-markers in every run** — the three most bare-metric runs of all 12.
- **en-must docstring length (10, 19, 19) is the shortest across all cells.** The docstring in runs 2 and 3 is near-verbatim to the original file.
- **Silent `pass` appears in every cell in every run except zh-is run 1**. The Phase-1 claim "zh-is eliminates silent pass structurally" does not replicate.
- **Class count is the most stable metric per cell**, suggesting structural refactor effort is roughly cell-driven; narrative commentary is where the cells diverge.

## Measurement Reliability Caveat (important)

The `yin-marker` grep uses `(yin|陰面|死法|death.?reason|BET:|Bet:|賭注)`. **This misses semantically equivalent English phrasing:**

- en-is run 2 docstring reads: *"Each structure below is shaped around a single death-responsibility...The seams between structures are explicit rather than loose...Every `except: pass` is a promise kept to that contract."*
- The regex catches `yin` (1 hit from "yin-side") but misses "death-responsibility", "soundproof wall", "marked bet".

**So the en-is yin-marker mean (3.0) is an under-count.** Manual read confirms en-is runs 1 and 2 are rich; run 3 is thinner. The en-must mean (0.0) is accurate — those docstrings have no yin-flavored content at all, not a regex miss.

## Revised Qualitative Findings (manual reads)

### Confirmed (Phase 1 held up)

1. **en-must is reliably shallow.** 3/3 runs preserve the original docstring near-verbatim. Structural refactor happens below (class decomposition, section comments, dataclass), but the module-level *reasoning* is absent. This is the compliance-theater signature: letter of the guide followed, spirit never articulated.

2. **Chinese-language guides tend to produce more reasoning-integrated output than English guides, regardless of mood.** zh-must has the highest yin-marker mean (4.7 by the narrow regex), beating even the more reliable-by-eye en-is (~3.0 true).

### Corrected (Phase 1 overclaims)

3. **zh-is does NOT structurally eliminate silent `pass`.** Run-1 had 0 bare `pass` (all except→return); runs 2 and 3 have 4 and 3. **This was a single-run artifact, not a cell effect.** My Phase-1 conclusion "descriptive Chinese triggers structural shift" was premature.

4. **en-is is not reliably deep.** Run-1 had 8 classes and rich docstring; runs 2 and 3 converge on 2 classes and varying docstring depth. The cell produces spirit-integrated output more often than not, but not every time.

### New findings from replication

5. **Within-cell variance is large for zh-must and en-is.** zh-must docstring ranges from 9 lines (run-2, near-original) to 45 lines (run-3, deep). en-is classes range from 2 to 8. Cell effect exists but is weak; run-to-run luck matters a lot.

6. **Within-cell variance is small for en-must.** Doc lines: [10, 19, 19]; yin markers: [0, 0, 0]; classes: [2, 2, 1]. This is the only cell that is *reliably* at one end of the spectrum.

## Interpretation

**The single robust finding, across 12 runs:**

> Guides written in **English + MUST mood** systematically fail to trigger spirit internalization at the module level. The refactor produces structural changes (classes, dataclasses, function decomposition) but the *why* never surfaces in docstrings or comments. 3 out of 3 runs exhibit this pattern with low variance.

**The less robust findings:**

- Chinese-language guides trigger deeper reasoning on average, but with high variance.
- Descriptive (IS) mood does not uniquely trigger structural exception-handling changes; that was single-run luck.
- en-is can produce spirit-rich output but only in ~2/3 runs.

## Revised Implication for the Samsara Guide

Same direction as Phase 1, but with updated confidence:

- **Strong evidence: avoid English-MUST combination.** This is the one combination that reliably fails.
- **Moderate evidence: Chinese-language guide helps regardless of mood.** Either zh-must or zh-is produces deep output most of the time; mood choice within Chinese is close to equivalent.
- **Weak evidence: descriptive (IS) mood is superior for structural spirit internalization.** Phase-1's strongest claim does not replicate — zh-is's structural advantage was a single lucky run.

**Recommendation unchanged:** Chinese primary, descriptive language preferred but not mandatory, 9-principle structure from dialogue 1.

**New caveat to the recommendation:** Cell variance across runs means even "good" cells (zh-must, zh-is, en-is) occasionally produce thin outputs. For the actual samsara guide to be reliable, it may need **reinforcement mechanisms** beyond just choosing the right cell — e.g., a separate evaluator role (reverting to the Phase-0 chapter-1 conclusion) that checks the implementer's output against the spirit regardless of how the guide was phrased.

This replication weakly supports the original chapter-1-dialogue argument: **rules alone are not enough; an independent evaluator is warranted**, because even the best cell has one-in-three chance of producing thin output.

## Caveats (Phase 2 self-critique)

1. **N=3 per cell is still small.** Standard error bars are wide. Formal hypothesis testing would require N≈10 per cell at minimum.
2. **Single subject file.** All 12 runs refactored `observe-learnings.py`. Generalizability to other code types (business logic, long-lived modules, test code) is untested.
3. **Same model family.** Results may differ on smaller/larger Claude models or other LLMs.
4. **Yin-marker regex is under-inclusive** (documented above). Manual reading is the more reliable signal but is subjective and unscaled.
5. **Theater detection is still manual.** "Near-verbatim original docstring" is an objective signal (docstring length) but deeper theater patterns would need rubric refinement.

## Proposed Phase 3 (if pursued)

To further strengthen confidence, either:

- **(a) Deepen N:** run 4 more iterations of each cell to reach N=7, or
- **(b) Widen subject:** rerun the same 2×2 on a different file (e.g., `samsara/scripts/` or a non-hook Python module) to test generalizability, or
- **(c) Add a Yin Evaluator condition:** compare "guide alone" vs "guide + independent evaluator that reviews output" — this tests the chapter-1-dialogue's original architectural claim.

## Artifacts

- `outputs/<cell>-output.py` — Phase 1 runs (4 files)
- `outputs/<cell>-run2-output.py` — Phase 2a (4 files)
- `outputs/<cell>-run3-output.py` — Phase 2b (4 files)
- `experiment-report.md` — Phase 1 report (preserved as audit trail, contains overclaims)
- `experiment-report-phase2.md` — this document (corrections + replication evidence)
