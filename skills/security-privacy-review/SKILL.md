---
name: security-privacy-review
description: Use after implement/iteration completes and before validate-and-ship — reviews committed changes for security and privacy issues using the platform's built-in review capability
---

# Security & Privacy Review — Gate Before Ship

Review committed changes for security and privacy issues before entering validation. Uses the platform's built-in security review capability — no custom tooling.

> 陽面問「功能做完了嗎」，陰面問「功能做完的同時，有沒有把鑰匙也一起交出去」。

## Prerequisites

- All implementation tasks completed and committed (from implement or iteration)
- A feature branch with commits ahead of the base branch (typically `main`)

## Process

```dot
digraph security_privacy_review {
    node [shape=box];

    start [label="Entry\n計算 diff\n(committed changes vs base branch)" shape=doublecircle];
    empty_check [label="Diff 為空？" shape=diamond];
    empty_gate [label="Human gate\ndiff 為空，是否預期？" shape=diamond];
    review [label="Step 1: Security & Privacy Review\n使用平台內建能力\n檢查 diff 內容"];
    capability_check [label="平台有 review 能力？" shape=diamond];
    no_capability [label="Human gate\n平台無內建 security review\n(A) 手動確認後繼續\n(B) 停止"];
    result [label="Review 結果？" shape=diamond];
    pass [label="Pass\n報告 review 摘要"];
    unknown [label="Human gate\nreview 無法完成\n(A) 重試\n(B) 手動確認後繼續\n(C) 停止"];
    fail [label="Step 2: Present Issues\n嚴重度 + 位置 + 修復建議"];
    human_gate [label="Human gate\n確認修復項目" shape=diamond];
    fix [label="Step 3: Inline Fix\n修復 → commit\n(round_count++)"];
    re_review [label="Re-review\n(全量 diff，非僅 fix delta)"];
    safety [label="Fix loop ≥ 3 rounds？" shape=diamond];
    safety_gate [label="Human gate\n已達 3 輪（每輪都問）\n(A) 繼續修復\n(B) 接受剩餘風險"];
    accept_risk [label="記錄 accepted risks\n(carry forward to validate-and-ship)"];
    transition [label="invoke samsara:validate-and-ship" shape=doublecircle];
    abort [label="中止" shape=doublecircle];

    start -> empty_check;
    empty_check -> empty_gate [label="yes"];
    empty_check -> review [label="no"];
    empty_gate -> transition [label="預期，繼續"];
    empty_gate -> abort [label="非預期，停止"];
    review -> capability_check;
    capability_check -> result [label="yes"];
    capability_check -> no_capability [label="no"];
    no_capability -> accept_risk [label="手動確認\n(記錄 no-capability skip)"];
    no_capability -> abort [label="停止"];
    result -> pass [label="pass"];
    result -> unknown [label="unknown"];
    result -> fail [label="fail"];
    pass -> transition;
    unknown -> review [label="重試"];
    unknown -> accept_risk [label="手動確認\n(記錄 unknown skip)"];
    unknown -> abort [label="停止"];
    fail -> human_gate;
    human_gate -> fix [label="確認修復項目"];
    human_gate -> accept_risk [label="接受風險"];
    fix -> re_review;
    re_review -> safety;
    safety -> result [label="< 3 rounds"];
    safety -> safety_gate [label="≥ 3 rounds\n(每輪重新詢問)"];
    safety_gate -> fix [label="繼續"];
    safety_gate -> accept_risk [label="接受剩餘風險"];
    accept_risk -> transition;
}
```

## Entry: Compute Diff

Compute the diff of committed changes against the base branch:

```bash
git diff <base-branch>...HEAD
```

Before proceeding, check for two edge cases:

**Empty diff:**
> 「Diff 為空 — implement/iteration 後沒有新的 committed changes。這是預期的嗎？
>
> (A) 預期，跳過 security review 繼續
> (B) 非預期，停止檢查」

**Cannot determine base branch:**
> 「無法判斷 base branch。請指定 diff 的比較基準（例如 `main`、`develop`）。」

## Step 1: Security & Privacy Review

Use the current platform's built-in security and privacy review capability to analyze the diff.

**Platform-agnostic instruction:** This skill does NOT specify which tool to invoke. The executing agent determines the mechanism based on the current platform's available capabilities. Examples:
- Claude Code: may use built-in `security-review` skill or equivalent
- Other platforms: use whatever security review capability is available

**If the platform has no built-in security review capability:**
> 「當前平台無內建 security & privacy review 能力。
>
> (A) 你自行檢查後確認繼續
> (B) 停止」

This is a visible degradation, not a silent skip. If human chooses (A), this is recorded as an accepted risk and carried forward to validate-and-ship (see `accept_risk` node in the process graph).

**Review scope:** The review should cover the FULL diff — all files changed in the feature branch relative to the base branch. The agent should report which files were included in the review.

## Step 2: Result Handling

Review results must be exactly one of three states:

### Pass

No security or privacy issues detected. Report:
- Summary of what was reviewed (file count, file types)
- Transition to validate-and-ship

### Fail

Issues detected. Present to human:
- Each issue with: severity (critical / high / medium / low), file and location, description, suggested fix
- Group by severity, critical first

Then human gate:
> 「Security & privacy review 發現以下問題：
>
> [issue list]
>
> (A) 修復以上問題
> (B) 選擇要修復的項目（輸入編號）
> (C) 接受風險，繼續（必須說明理由）」

### Unknown

Review could not complete (timeout, partial results, tool error). This is NOT a pass.
> 「Security review 無法完成。原因：___
>
> (A) 重試
> (B) 你自行確認後繼續
> (C) 停止」

If human chooses (B), this is recorded as an accepted risk and carried forward to validate-and-ship.

## Step 3: Fix Loop

When human confirms issues to fix:

1. Agent performs inline fix (no subagent dispatch)
2. Commit the fix
3. Increment round counter (one round = one `fix → commit → re-review` cycle)
4. Re-run security review on the **full diff** (not just the fix delta) — fixes can introduce new issues
5. Return to Step 2 result handling

**Round counting:** A round is one complete `fix → commit → re-review` cycle. The counter starts at 0 on entry and increments after each commit. Partial fixes (started but not committed) do not count.

**Safety valve:** From round 3 onward, the safety gate triggers every round (not just once):
> 「已執行 3 輪修復。剩餘問題：
>
> [remaining issues]
>
> (A) 繼續修復（超出常規輪數）
> (B) 接受剩餘風險，繼續」

**Accepted risks carry forward:** If human accepts remaining risks, these must be mentioned when presenting the transition to validate-and-ship, so the ship manifest can record them.

## Yin-Side Constraints

- **No silent pass-through:** empty diff, unknown results, absent platform capability — all must be made visible to human, never silently treated as pass
- **Full diff re-review:** fix loop must re-review the entire diff, not just the fix delta. Fixes can introduce new vulnerabilities
- **Unknown ≠ pass:** partial, timed-out, or errored review results are `unknown`, never `pass`
- **Accepted risks are explicit:** any risk acceptance by human must carry forward to validate-and-ship

## Red Flags

**Never:**
- Silently skip the review step (even if diff is small or "looks safe")
- Treat unknown/partial review results as pass
- Re-review only the fix delta instead of the full diff
- Accept risks on human's behalf — only human can accept security risks
- Name a specific platform tool in this skill (maintain platform-agnostic)

**Watch for:**
- Review that always passes — may indicate narrow review scope
- Same issue reappearing across fix rounds — may indicate architectural problem, not point fix
- Human accepting all risks without reading — gate losing effectiveness

## Transition

Review passed (or human accepted remaining risks). Then:

> 「Security & privacy review 完成。[N files reviewed, M issues found in final review, K fixed across R rounds, J accepted as risk]。進入 Validation。」

Invoke `samsara:validate-and-ship` skill.
