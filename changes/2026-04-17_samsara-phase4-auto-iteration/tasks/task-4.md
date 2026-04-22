# Task 4: Create iteration skill SKILL.md for feature-level iteration (Level 2)

## Context

Read: overview.md

新建 `samsara/skills/iteration/SKILL.md` — feature-level iteration skill。

這個 skill 只處理 **Level 1 self-iteration 後剩餘的 cross-task / feature-level scar items**。它的 input 是：
- 所有 tasks 的 remaining scar items（`deferred_to_feature_iteration: true` + 未 resolved 的 items）
- `index.yaml` 的 task scar 統計

核心迴圈：aggregate → triage（human gate）→ fix（per-fix commit）→ round check → human gate → next round or exit

設計慣例（參考現有 skills）：
- Flow 用 Graphviz digraph
- Frontmatter: name, description
- Yin-side constraints section
- Red flags section
- Support files reference
- Transition section

Key differences from implement:
- Fix 是 **per-fix commit**（不是 all-tasks commit）
- Triage 需要 human gate（不是 agent 自己決定）
- Safety valve：max 3 rounds, signal_lost 停滯偵測, net rot increase 偵測
- 向後兼容 skip gate（使用者可以不 iterate）

## Files

- Create: `samsara/skills/iteration/SKILL.md`

## Death Test Requirements

- Test: SKILL.md 必須定義 cargo-cult triage 偵測（accept > 80% + zero fixes → warning）
- Test: SKILL.md 必須定義 net rot increase 偵測（fixes_scar_count >= fixes_applied）
- Test: SKILL.md 必須定義 signal_lost 停滯偵測（2 輪不降 → forced stop 提示）
- Test: SKILL.md 必須定義 non-conforming scar report 處理（explicit parse failure）
- Test: SKILL.md 必須定義 entry gate skip 選項

## Implementation Steps

- [ ] Step 1: 設計 SKILL.md 結構（frontmatter, process digraph, sections）
- [ ] Step 2: 寫 entry gate（aggregate remaining scars + skip option）
- [ ] Step 3: 寫 aggregate + signal_lost 計量邏輯
- [ ] Step 4: 寫 triage flow（human gate, fix/accept/defer, cross-task focus）
- [ ] Step 5: 寫 fix flow（復用 implementer dispatch, per-fix commit）
- [ ] Step 6: 寫 safety valve 邏輯
- [ ] Step 7: 寫 round check + human gate
- [ ] Step 8: 寫 iteration-log output 邏輯
- [ ] Step 9: 寫 yin-side constraints + red flags
- [ ] Step 10: 寫 transition（exit → validate-and-ship）
- [ ] Step 11: Write scar report

## Expected Scar Report Items

- Potential shortcut: safety valve max rounds 硬編碼為 3
- Potential shortcut: signal_lost 只計 count 不考慮 severity
- Assumption to verify: implementer dispatch-template pattern 是否適用於 scar fix（fix context 不同於 initial impl）
- Assumption to verify: per-fix commit 在 cowork/inline mode 下能否正確執行

## Acceptance Criteria

- Covers: "Success - Level 2 iteration reduces feature-level signal_lost"
- Covers: "Success - user skips Level 2 (backward compatible)"
- Covers: "Success - Level 2 triage classifies all items with rationale"
- Covers: "Silent failure - cargo-cult triage marks all items as accept at Level 2"
- Covers: "Silent failure - fix introduces equal or more rot than it resolves"
- Covers: "Degradation - safety valve forces Level 2 termination"
- Covers: "Degradation - Level 2 iteration interrupted mid-round"
