# Problem Autopsy: Execution Model Scope

## original_statement

「整套 samsara skills 和 agents（含 `samsara:code-reviewer`、`samsara:code-quality-reviewer`、9 yin principles、8 outcome criteria C1-C8）都是以 imperative code（Python / TS / Go / Rust 等）為預設 execution model 設計的。」

## reframed_statement

`code-quality-reviewer` 接收到非 imperative code 時，會用不適用的 principles 產出 misleading 的 PASS/FAIL verdict，但使用者無法從 output 中辨識這是錯誤的審查結果。問題不是「不能審 IaC」，是「假裝能審 IaC」— scope boundary invisible。

## translation_delta

```yaml
translation_delta:
  - original: "以 imperative code 為預設 execution model 設計的"
    reframed: "收到非 imperative code 時產出 misleading verdict"
    delta: "原始描述是 scope limitation（我們只設計了 X）。Reframe 揭示真正的 damage 是 scope boundary invisible — reviewer 不告訴你它不該審這個。Scope 小不是問題，假裝 scope 大才是。"

  - original: "現代軟體工程包含多種 execution model"
    reframed: "AI-assisted development 讓開發者跨 domain 的頻率增加"
    delta: "原始是靜態觀察（世界上有很多 execution model）。Reframe 加入時間維度 — 跨 domain 不是偶發事件，是趨勢。問題的 urgency 隨 AI adoption 上升。"

  - original: "每種的悄悄失敗死法不同"
    reframed: "imperative code 的 principles 套用到 IaC 上會產出 rubber stamp"
    delta: "原始說的是差異存在。Reframe 說的是差異的後果 — 不只是「不同」，是「用錯了會假裝正常」。"
```

## kill_conditions

```yaml
kill_conditions:
  - condition: "如果 samsara 的使用者全部只寫 imperative code，沒有人觸發非 code file 的 review"
    rationale: "問題是理論上的 scope gap，不是實際 damage。Domain reference files 的撰寫成本（yin principle × domain expertise）沒有對應回收。但在 AI-assisted development 時代，此條件越來越不可能觸發。"

  - condition: "如果 domain-specific reference files 的品質無法被驗證 — 寫了 iac-quality.md 但沒有真實 Terraform codebase 可以跑 review"
    rationale: "未驗證的 reference file 比沒有 reference file 更危險 — 給了覆蓋的錯覺。品質不好就迭代，但前提是有迭代的 input（真實 review 結果）。"
```

## damage_recipients

```yaml
damage_recipients:
  - who: "Reference file 維護者（框架作者）"
    cost: "持續進化責任 — domain best practice 演進時 reference file 需跟著更新。但這不是維護成本，是開發者有沒有在進化的問題。"

  - who: "Review 消費者（開發者）"
    cost: "ambiguous file 得到 UNKNOWN 而非（可能不準確的）review。但不知道總比隨便唬爛好 — 寧願真實的 UNKNOWN 也不要虛假的回應。這是 Samsara 的本質。"

  - who: "框架可信度"
    cost: "第一份 domain reference 品質決定擴展信心。但品質不好就迭代 — implement 已有 iteration 機制。"
```

## observable_done_state

`code-quality-reviewer` 收到 `.tf` 檔時，自動載入 `iac-quality.md`，用 IaC-specific judgment questions 和 koans 產出有意義的 principle verdicts。收到無法辨識的檔案類型時，回傳 UNKNOWN 並說明原因。Review output 的可信度從「只對 imperative code 可信」變成「對已有 reference file 的 domain 可信，對其餘 domain 明確標記不可信」。
