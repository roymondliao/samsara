# Problem Autopsy: samsara-code-quality-reviewer

## original_statement

原始 user statements（保留原語氣，不 paraphrase）：

> 「Samsara 是負責看 system level 的問題，所以在實作上，coding quality 是否好這件事不職責，所以才要添加 coding quality 的處理。」

> 「什麼叫做好，就是 1. 可讀性 2. 可維護 3. 易拓展 4. 容易 debug 5. Reuse 6. 結構明確 7. 能優雅的處理 code 的邏輯就不添加多餘的東西 8. 沒有 redundant 的 code。」

> 「這個規範要讓在 implement step? 作為一個 code quality review agent? 還是 code-reviewer 具有這個規範？」

研究初期 user 的原始 framing（更前面幾輪）：

> 「使用 Samsara 在不同的 project 後，會發現，這 coding 的 quality 確實不好，因為 1. 都是用 function 來實作 2. 多餘的 redundant code 3. 缺乏 module 的結構設計 4. 沒辦法 reuse 相同功能 5. 架構不易擴展、缺啥彈性 6. 實作上應該有更好的方式可以來實作。這些都像是一個 junior engineer 會出現的問題。因此，這次的討論就是要將一個 staff/principle level 的 engineer 給帶入到 Samsara 的底層實作中。」

## reframed_statement

建立 `samsara:code-quality-reviewer` agent，配合 `samsara/references/code-quality.md`（包含 8 條 criteria + 實驗產出的 good/bad examples），作為既有 `samsara:code-reviewer` 的 sibling，在 `samsara:implement` 和 `samsara:iteration` 的 review 觸發點並行 dispatch。兩個 reviewer 都 pass 才允許 commit。既有 yin reviewer 保持原貌不動，以維持其 yin 焦點純度。

## translation_delta

```yaml
translation_delta:
  - original: "添加 coding quality 的處理"
    reframed: "新建 samsara:code-quality-reviewer agent + reference 檔"
    delta: |
      User 說「添加處理」未指定層級。我先走了兩個岔路（(1) 放 implement step、
      (2) 新 agent、(3) 擴充既有 code-reviewer），用 /level-analysis 三層評估，
      三層皆傾向 (2)。此 delta 代表：user 的意圖是「補一層」，工程選擇是
      「agent 層」，證據來自 samsara 既有 pattern（specialist composition）
      和 LLM attention dilution 的已知特性。

  - original: "Samsara 不職責 coding quality"
    reframed: "既有 samsara:code-reviewer 的 Three Mother Rules + review order
              是 system-level yin 視角，其 constraints（Do NOT focus on what
              code LOOKS LIKE）明確排除 conventional code-quality concerns"
    delta: |
      User 的 framing 是 responsibility 分工。我加了具體證據層（讀既有
      code-reviewer.md 確認不是 stub、constraints 和 quality review 直接衝突），
      這讓 responsibility 分工從抽象 framing 變成可驗證的技術判斷。

  - original: "這些都像是一個 junior engineer 會出現的問題...要將一個 staff/principle
              level 的 engineer 給帶入到 Samsara 的底層實作中"
    reframed: "建立一個審查 agent，審查標準是用 staff/principle-level 的
              code-quality criteria"
    delta: |
      User 原本期望是「注入 senior engineering mindset 到 implementer」。
      經實驗（2×2 factorial, N=3 per cell）證實：單靠 prompt/guide 注入無法
      reliably 改變 output quality（variance 大，en-must cell 出現 compliance
      theater）。Delta：從「上游 shape implementer」改為「下游 gate via
      reviewer」。這個改變 user 未明確同意，但通過級別分析 + 實驗數據支持。

  - original: "原始 feature name: yin-coding-spirit"
    reframed: "feature name: samsara-code-quality-reviewer"
    delta: |
      研究過程中 scope 從「寫哲學 guide」→「寫技術 reference + 建 agent」。
      原 folder 名稱保留以記錄研究路徑，但交付物命名已脫離「spirit」language。
      Delta 代表：user 最初傾向哲學文件，最終選擇具體工程 artifact。
```

## kill_conditions

```yaml
kill_conditions:
  - condition: "Samsara agent 架構從 specialist composition 轉向 generalist agents"
    rationale: |
      新 agent 的存在理由是「每個 concern 一個 agent」的 pattern。
      若 samsara 決定走相反路（例如併成一個 mega-reviewer），此 agent 應
      被合併或廢除。

  - condition: "first_pass_rate 持續 > 85% 超過 3 個月"
    rationale: |
      Reviewer 太寬鬆，等於 rubber stamp。繼續 dispatch 會浪費 token 且
      給開發者虛假信心。應該要嚴化 criteria 或直接廢除。

  - condition: "first_pass_rate 持續 < 20% 超過 3 個月"
    rationale: |
      Reviewer 太嚴格，幾乎每個 task 都被打回。implementer 改不動，或
      criteria 根本不適用於 samsara 的任務類型。應該重審 criteria 範圍。

  - condition: "出現 corruption signature：pass 的 code 被 human reviewer 標為
                junior-level 超過 20%"
    rationale: |
      Implementer 學會繞 reviewer。此時 reviewer 變成 compliance theater 的
      自身，沒有保護價值。需要重新設計 criteria 或換 review approach（例如
      從 criteria-based 改為 example-based judgment）。

  - condition: "Python ecosystem 出現可強制執行此 8 條的 linter（類似 pylint
                + ruff 的組合加強版）"
    rationale: |
      若工具能做到 deterministic enforcement，agent reviewer 反而不必要——
      agent 適合判斷，linter 適合規則化檢查。兩者競爭時，linter 勝。

  - condition: "此 project 大部分新 code 透過 samsara 之外的路徑產生"
    rationale: |
      Reviewer 只在 samsara flow 生效。若 95% 的 code 經由其他路徑進來，
      此 reviewer 的影響半徑太小，不值得維護。
```

## damage_recipients

```yaml
damage_recipients:
  - who: "samsara:implement / samsara:iteration runtime"
    cost: |
      每個 task 的 review 階段多一次 subagent dispatch，token 成本約加倍
      （兩個 ~100 行 prompt 的 reviewer 並行）。wall-clock 時間幾乎不變
      （parallel dispatch），但 token spend 上升。

  - who: "短期：implementer re-work cycles"
    cost: |
      新的 reviewer 會抓出原本通過 yin review 但違反 code-quality 的 code。
      implementer 要額外跑 fix 循環。預估前兩週 first-pass rate 會是 30% 上下，
      之後 implementer 學會適應，rate 上升到目標區間（40-65%）。

  - who: "samsara 維護者（今後每一位）"
    cost: |
      多兩個 artifact（agent definition + reference 檔）要 keep current。
      當 8 條 criteria 演化、或 examples 需要更新時，多一個維護點。
      同時 implement + iteration skills 的 SKILL.md 變動須同步。

  - who: "新接手 samsara 的讀者"
    cost: |
      必須理解「兩個 reviewer 的分層」這個架構決策。
      學習曲線從「有一個 reviewer」變成「有兩個 reviewer、各自何時用」。
      mitigation：在 samsara README 明確 document 分層。

  - who: "未來 code-quality criteria 演化的提議者"
    cost: |
      每增加一條 criteria 都要評估是否真的不在既有 8 條之內、是否應該合併、
      是否要寫新的 good/bad example。維護紀律比「隨意加」更累。
      但這是預期成本，不是 regression。
```

## observable_done_state

**未解決狀態**（目前）：
samsara:implement 產出的 code 只經 samsara:code-reviewer（yin 視角）審視；像 `hooks/scripts/observe-learnings.py` 這類 `main()` 111 行、多處 silent except、stringly-typed contract 的 code 可以通過 review，junior-level 結構缺陷**在現有 pipeline 中看不見**。

**已解決狀態**：
samsara:implement 和 samsara:iteration 每次 review 時並行 dispatch 兩個 reviewer（yin + quality），兩者都 pass 才 commit；對 `hooks/scripts/observe-learnings.py` 重跑 review 時，新的 `samsara:code-quality-reviewer` 至少回報 3 個 Critical issues（例如：`main()` 函數職責過多、silent except 未標記、`state_paths` 回傳 dict 未使用 dataclass），這些 issue 用既有 yin reviewer 看不出來。

**可觀測差異**：
在 `hooks/scripts/` 下選一份現有 script 做 before/after 驗收——執行 `samsara:code-quality-reviewer` 對原檔，產出 issue 列表；依 issue 修正後重跑，issue 數歸零。若這個 round-trip 在建立後一週內可以無痛跑通，視為 done。
