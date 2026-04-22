# Problem Autopsy: Samsara Phase 4 — Auto Iteration

## original_statement

MEMORY.md Phase 4 定義：

> 一個自動化的系統自我審問機制 — 從「系統哪裡在假裝健康」出發，附帶陽面的指標改善。

> 自動化迴圈（半自動，Phase 4 v1）：陰面診斷（系統哪裡假裝健康）→ 排序（最危險的腐爛點）→ 提出修改方案 → [Human Gate] → 實作 → 雙面驗證（陽面指標 + 陰面代價）→ 保留/丟棄 → 更新 codebase-map + iteration-log → 下一輪

使用者補充（2026-04-17 discussion）：

> iteration 的對象就是當 scar-report 已經把證據都攤在眼前了，難道不持續修正嗎？將潛在的可能問題修改好？或是修改到一個可以接受的狀況？陰面的精神會把這些問題假裝沒看見就放過嗎？我想不會，陽面的做法才會。

## reframed_statement

Phase 4 是 scar report 的 resolution engine。Samsara 的 implement → validate-and-ship 流程已經產出結構化的傷口清單（scar reports），但 ship 後這些清單就是死文件。Phase 4 把這些已知傷口轉化為 iteration action items，透過「triage → 排序 → 修復 → 驗證」迴圈持續處理，直到陰面代價超過繼續修的收益。

核心不是「新的診斷能力」— scar report 已經是診斷結果。Phase 4 是「診斷結果 → 持續行動」的機制化。

## translation_delta

```yaml
translation_delta:
  - original: "自動化的系統自我審問機制"
    reframed: "scar report 的 resolution engine"
    delta: "原始描述暗示需要新的診斷能力（自我審問）。實際上診斷已經由 scar report 完成，Phase 4 的核心是 resolution 不是 diagnosis。診斷能力的改善是 scar-schema 品質的問題，不是 Phase 4 的問題。"

  - original: "從系統哪裡在假裝健康出發"
    reframed: "從 scar report 中已記錄的 silent failure conditions 和 unverified assumptions 出發"
    delta: "原始描述是抽象的哲學陳述。具體的起點是已存在的結構化數據 — scar-schema.yaml 定義的 known_shortcuts、silent_failure_conditions、assumptions_made。不需要另外「發現」假裝健康的地方，scar report 已經指出了。"

  - original: "附帶陽面的指標改善"
    reframed: "陽面改善是 side effect，不是 input"
    delta: "原始措辭可能暗示 iteration 也要追蹤陽面指標（如 design.md 的 north-star.yaml）。實際上 Phase 4 的 input 純粹是陰面的 scar data，陽面指標改善是修復 rot 後的自然結果，不是 Phase 4 要直接優化的對象。"

  - original: "自動化迴圈（半自動，Phase 4 v1）"
    reframed: "半自動迴圈，human gate 在 triage 和 fix/accept 決策點"
    delta: "原始描述把 human gate 放在「提出修改方案」之後。但 triage（這個 scar item 要 fix 還是 accept）本身也是需要 human judgment 的決策點。v1 的 human gate 可能比原始設計更多，不是更少。"
```

## kill_conditions

```yaml
kill_conditions:
  - condition: "Scar report 品質持續不可靠 — 連續 3 個 feature 的 scar items 都是 generic/cargo-cult，導致 iteration actions 沒有價值"
    rationale: "Garbage in → garbage out。Phase 4 的品質上限由 scar report 品質決定。如果 scar report 不可靠，Phase 4 只是在 iterate on noise。應該先修 scar report 品質（Phase 1 的問題），而非在壞的 input 上建 iteration。"

  - condition: "所有 scar items 都是不可修的 accepted risk（如 AI 能力限制、外部依賴限制），沒有 actionable items"
    rationale: "Phase 4 的價值在於把 actionable scars 轉化為修復。如果 scar items 本質上都不可修（不是 code rot 而是環境限制），iteration 迴圈無事可做。應該改善 scar report 的分類能力，區分 code rot 和 environmental limitation。"
```

## damage_recipients

```yaml
damage_recipients:
  - who: "使用者（samsara user）"
    cost: "Ship 後需要 review iteration proposals、通過 human gates。原本「已完成」的 feature 變成持續需要關注的 item。開發節奏從「完成 → 下一個」變成「完成 → iterate → 可能還要 iterate → 才能真正放下」。"

  - who: "Token / 計算預算"
    cost: "每輪 iteration 需要 AI 讀取 scar reports、codebase context、做 triage 和修復方案設計。如果終止條件設計不好，成本失控。"

  - who: "開發速度（velocity）"
    cost: "Phase 4 把一部分資源從「建新東西」重新分配到「修舊傷口」。短期的 feature velocity 會下降。這是正確的 trade-off（避免 rot 累積），但 damage 是真實的。"
```

## observable_done_state

有 Phase 4 時：validate-and-ship 完成後，scar report 中的每一個 item 都被 triage（fix / accept / defer），能修的進入 iteration 修復，不能修的標記為 accepted risk 並附上 expiry date。Ship manifest 的 `silent_failure_surface` 在 iteration 後持續下降。

沒有 Phase 4 時：scar report 寫完歸檔，`done_with_concerns` 的 concerns 永遠停留在 concerns，ship manifest 的 `accepted_risks[].expires` 到期但沒有人注意到。

可觀測差異：ship manifest 中每一項 `accepted_risks` 都有處理紀錄和 re-evaluation 時間點，而不是開放式的「we know about it but did nothing」。
