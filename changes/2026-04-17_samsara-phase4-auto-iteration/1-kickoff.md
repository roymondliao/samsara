# Kickoff: Samsara Phase 4 — Auto Iteration

## Problem Statement

Samsara 的 implement → validate-and-ship 流程產出 scar reports，記錄了 silent failure conditions、unverified assumptions、known shortcuts。但 ship 之後這些 scar items 就是靜態文件 — 沒有機制回來審視、沒有後續 action、沒有人追蹤哪些 concerns 被解決了。知道問題卻不處理，等問題真的爆發才反應，是系統最嚴重的問題。

## Evidence

- **llm-wiki paper-metadata-registry**：6 個 tasks 產出 21 個 scar items，4 個 tasks 是 `done_with_concerns`，累積 8 個 unresolved assumptions。Ship 後沒有任何機制回訪這些 items。
- **Scar report 設計本身承認這個 gap**：`scar-report.md` 定義了 `verified: false` 欄位，但沒有定義誰、何時來 verify。`ship-manifest.md` 的 `accepted_risks` 有 `expires` 欄位，但沒有機制在 expiry 時觸發 review。
- **validate-and-ship 的 failure budget review** 是唯一一次 aggregation，但它發生在 ship 之前，ship 之後就沒有了。

## Risk of Inaction

- Scar reports 退化為儀式性文件 — agent 寫了、人看了、然後歸檔。陰面的精神在 ship 之後斷裂。
- `done_with_concerns` 的 concerns 永遠停留在 concerns，沒有 resolution path。
- Unverified assumptions 持續累積但不被追蹤，直到某個 assumption 在 production 被證偽。
- Ship manifest 的 `accepted_risks[].expires` 到期但沒有人注意到。

## Scope

### Must-Have (with death conditions)

- **Scar report → action 轉化機制** — 將 scar items 轉化為可 triage、可排序、可 assign 到 iteration 的 action items。
  - Death condition：如果連續 3 個 feature 的 scar items 都是 generic/cargo-cult 導致轉化後的 actions 沒有價值，移除此機制。

- **Iteration 迴圈 + 終止條件** — 看見 → 排序 → 修 → 驗證 → 下一輪 or 停止。終止條件是陰面的：不是「修夠了」而是「繼續修的代價超過 rot 本身的風險」。
  - Death condition：如果迴圈在實務上每次都跑一輪就被使用者終止（human gate 100% 選 stop），簡化為一次性 scar review。

- **Signal_lost 累積計量** — 跨 tasks 的 unverified assumptions 和 silent failure conditions 的累積 visibility，作為 iteration 排序和終止的輸入。
  - Death condition：如果連續 5 個 features 中 signal_lost 都是 0，代表計量未捕捉到真實 rot，重新定義或移除。

### Nice-to-Have

- 全自動模式（無 human gate）— v1 半自動已足夠驗證概念
- 跨 project 的 signal aggregation
- Dashboard / 視覺化

### Explicitly Out of Scope

- Samsara framework 自身的 rot iteration（meta-iteration）— 那是 `writing-skills` 的職責
- 陽面的指標優化迴圈（design.md 的「數據驅動優化」）— Phase 4 從陰面出發，陽面改善是附帶效果
- 修改現有的 implement / validate-and-ship flow — Phase 4 是它們之後的新階段

## North Star

```yaml
metric:
  name: "Scar Resolution Rate"
  definition: "ship 後 30 天內，scar report 中的 actionable items（non-accepted-risk）被處理的比例"
  current: 0%
  target: 70%
  invalidation_condition: "如果 scar report 品質不可靠（cargo-cult），resolution rate 高只代表在修假問題"
  corruption_signature: "resolution rate 上升但 production incidents 沒有下降 — 代表修的不是真正的 rot"

sub_metrics:
  - name: "Scar Item Triage Rate"
    definition: "scar items 被分類為 fix / accept / defer 的比例"
    current: 0%
    target: 100%
    proxy_confidence: high
    decoupling_detection: "triage 100% 但 fix 比例持續為 0% — triage 變成 rubber stamp"

  - name: "Signal Lost Accumulation"
    definition: "跨 tasks 的 unverified assumptions 累積數"
    current: null
    target: "monotonically decreasing within a feature iteration cycle"
    proxy_confidence: medium
    decoupling_detection: "signal_lost 下降但新 unverified assumptions 以相同速率產生 — 在還舊債但不斷產新債"
```

## Design Decisions (from Research)

### Commit Strategy

Phase 4 的 deliverable unit 是 **scar fix**（不是 feature），因此 commit 粒度不同於 implement 階段：

| Phase | Commit 策略 | 語義 |
|-------|------------|------|
| Implement | All tasks 完成才 commit | Feature coherence — partial state 不完整 |
| Validate-and-ship | Ship manifest commit/PR | 驗證通過的 feature 交付 |
| Phase 4 iteration | **Per-fix commit** | 每個 scar fix 是獨立的 verified improvement |
| Phase 4 validate-and-ship | Final commit | 更新後的 ship manifest（iteration 結果） |

理由：scar fix 之間互相獨立，per-fix commit 支援單獨 revert、降低跨 session 遺失風險、為未來全自動模式的 auto-revert 提供前提。

### Flow Position

Iteration 插入在 implement 和 validate-and-ship **之間**（方案 A），不是 ship 之後：

```
research → planning → implement → iteration ⟲ → validate-and-ship
```

- validate-and-ship 只跑一次，驗證 post-iteration state
- Ship manifest 反映最終狀態（含 iteration 修復），不存在多版本 manifest
- 陰面一致性：看見傷口、能修就修完再交付，不允許帶傷 ship

**Safety valve（防止 iteration 阻塞交付）：**
- Iteration 有最大輪數或時間上限 — 超過就強制進入 validate-and-ship，剩餘未修的 scar items 變成 accepted risk
- 每輪 human gate 問「繼續還是停止」+ 「這輪修的東西值得延遲 ship 嗎？」
- 使用者在第一輪選 stop = 原本的 implement → validate-and-ship flow（iteration 0 輪），向後兼容

## Stakeholders

- **Decision maker:** Roymond (samsara author + primary user)
- **Impacted teams:** All samsara users across projects
- **Damage recipients:**
  - 使用者時間成本 — ship 後需要 review iteration proposals、通過 human gates
  - Token / 計算成本 — 每輪 iteration 需要 AI 讀取 codebase-map、scar reports、做診斷
  - 開發節奏 — Phase 4 可能打斷「完成 feature → 開始下一個」的自然節奏
