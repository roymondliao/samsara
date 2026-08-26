> **已拆分並被取代 — 內容分層遷入 [`v2/`](./v2/)。** 本檔可安全刪除。
>
> | 原內容 | 新位置 |
> |---|---|
> | 一、原始理念（六個失效模式、可組合性、domain 創造性） | [`v2/01-philosophy.md`](./v2/01-philosophy.md) |
> | §9 太極雙面的**原則** | [`v2/01-philosophy.md`](./v2/01-philosophy.md) |
> | §1–§8、§9 的節點**規則**、§10 遞迴 | [`v2/02-method.md`](./v2/02-method.md) |
> | 三、開放問題 | [`v2/90-open-questions.md`](./v2/90-open-questions.md) |
>
> **刻意未遷移**：§9 末段「V1 已發明 dual-face」的依據、§10 的「刪掉什麼」五條清單。
> 兩者是從 V1 差分得來的，依空白畫布規範作廢。結論本身已在 `v2/` 由正向推導重建。

# Samsara v2.0.0 — 原始理念與終點—起點回推法（草稿）

> 狀態：討論草稿，暫存於 `docs/`，尚未定案。
>
> **本檔部分內容違反 [`v2-canvas-rule.md`](./v2-canvas-rule.md)（空白畫布規範），待重推：**
> §9 末段以「V1 已發明 dual-face」為依據、§10 的「刪掉什麼」五條清單、以及「三、開放問題」
> 的兩題。這些是從 V1 差分得來的，不是從 End 與 Origin 正向推導出來的。內容暫時保留供重推
> 時參考，**不得直接當作 V2 的設計依據**。與 `v2-canvas-rule.md` 衝突時，該規範優先。

---

## 一、v2.0.0 原始理念

### 產業現況觀察

Anthropic、OpenAI、Google、DeepSeek 等各家都在做 internal harness engineering（Claude Code、Codex、Antigravity、deepseek-harness）；社群另有 Pi、OpenCode 等 open source harness，以及 mattpocock/skills、cloudflare/security-audit-skill、K-Dense-AI/scientific-agent-skills、EveryInc/compound-engineering-plugin 等大量 external skill 集合。同時有一派聲音認為 LLM 越強，harness engineering 會變得不必要，甚至有專案（如 penguin-harness）主張讓 LLM 直接從 dataset 自建 harness。

### LLM 自建 harness（無規範）的六個失效模式

1. **Overfitting**——只適配同 domain 的相似資料，對 OOD 資料失效。
2. **資料生成本身就是最難的第一步**——沒有好的 synthetic data pipeline 就做不起來。
3. **為簡單問題設計過多技能**。
4. **沒有統一格式規範文檔怎麼寫**（語氣、細節、內容）。
5. **Harness 之間高度相似，出現 DRY 違反**。
6. **Skills 只能單一應用，無法組合**。

### 下一代 external harness engineering 的兩個焦點

**可組合性（Composability）**：Skills 依屬性分類（釐清問題、規劃、實作、QA review、產報告、研究……），可以像 component 一樣依任務需求組成 workflow。目前主流的「LLM 依 description 決定要不要調用」模式，本質是「遇到問題再找 workaround」，而不是「先想清楚這個 task 該怎麼處理」。範例組合：

- 研究任務：規劃研究目標 → 進行研究 → 產生 report
- Bug fix：查看 error message → 復現 → 調查原因 → 修正 → 測試
- Feature：探討實作價值 → 寫文件 → plan → task breakdown → implement → testing → review

DeepSeek harness 的 plugin 模式是可參考的組裝概念，但目前只在 internal harness 層級。

**Domain 創造性（Domain Creativity）**：沒有一套 skills 能適應所有 domain，需要 AI agent 具備 RSI（Recursive Self-Improvement）能力。Hermes-agent（Nous Research）已有類似能力（依 session 內容判斷是否該建立/優化 skill），但目前問題是冗餘、浪費資源、無效創造與更新——RSI 能力還不完整。Lilian Weng 對 harness RSI 的分析是這塊的重要參照。

### v2.0.0 方向

從 workflow 框架跳出，採 DeepSeek harness 式的系統設計概念。核心精神不變——不驗證 happy path，強調 death path、減法思維、e2e/real data testing、少即是多、陰陽兩面平衡（太極生兩儀，兩方平衡才穩定，太過則崩壞）。

---

## 二、終點—起點回推法（End–Origin Backward Derivation）

用來取代/補強「grill-me 式」從起點開始發散提問的問題釐清方式。核心觀察：project、product、feature、research 都有原點（Origin）與終點（End），缺的是過程；從原點正推容易發散失焦，從終點回推才能收斂到「該不該做、怎麼做」。

### 1. 起手式：終點與起點都是釘死的前提

- **終點宣告（End）**：不問「你想要什麼」，問「如果這件事已經完成，世界有什麼不同、誰會注意到、誰在它不存在時受損」——與既有 death test 的「誰先發現靜默失敗」是同一個問句形狀，一個問存在、一個問失敗，可合併成同一套「終點優先」透鏡。
- **起點（Origin）**：一份**凍結、有證據佐證**的現狀快照，在建樹之前就釘死，比照既有 `validate-and-ship` 的「frozen base/candidate commit，任何變更使結果失效並重跑」紀律，只是提早套用在定範圍階段。
- 兩者一旦釘死，回推過程本身**不能修改**。中途若發現節點連不回 Origin 卻把它重新標成起點，等於在證明過程中插入新公理（begging the question）——代表問題最初的假設就錯了，不是回推法允許的合法出口。

### 2. 樹的結構（借用 tree-sitter 的 grammar 概念）

- 節點型別沿用既有的資訊狀態分類：`fact / decision / assumption / proposal / unknown`，外加結構角色 `End / Precondition / Origin-leaf`。
- 文法規則：每個 Precondition 節點只能解到另一個 Precondition、一個 Origin-leaf，或一個 Unknown 葉節點。

### 3. 建樹規則

- 從 End 往回走，每一步只問「這是不是抵達上一節點的必要條件」——二元判斷，不開放式列舉，天然收斂。
- **增量重解析**（tree-sitter 最有價值的借用）：中途出現新證據時，只重算被影響的子樹，不必整條鏈重來。
- **錯誤恢復**：解不出來的節點插入顯式 Unknown 葉節點，不中斷整棵樹的建構——呼應「unknown 永遠不等於 pass」。
- **Query 層**：樹建好後，其他 skill 或 gatekeeper 可用結構化查詢讀取（例如「所有還是 unknown 的葉節點」），不必重讀散文敘述。

### 4. 剪枝（借用 ML tree-based model 的 post-pruning）

- 先長滿樹再剪（post-pruning），而非逐步貪婪剪（pre-pruning）——避免局部最優：某節點單獨看必要，長完全樹後可能有更便宜的路徑繞過它。
- 這是**借用推理схема**，不是真的統計擬合（沒有大量已完成專案的資料集可以擬合 cost-complexity 的 α 參數）：
  - cost = 落實成本 ＋ 風險 ＋ 子樹底下未解 unknown 數量
  - value = 對縮短 Origin→End 距離的貢獻
  - 存活條件類似最小生成樹——拿掉這個子樹會不會讓 Origin 連不到 End，連得到就砍
- 代價比貪婪法高，需要用 `size/risk` 分級當閘門：小型低風險工作維持逐步貪婪剪；大型/模糊/高風險工作才長滿再剪。
- 長滿階段的分岔是**文法邊界內**的分岔（只能長合法節點型別，以連到 Origin-leaf 或 Unknown 收尾），跟 grilling 的無邊界發散不同，收斂性沒被破壞。

### 5. 健全性規則（起點必須連得回去）

- 一個葉節點只有在**確實可驗證**是凍結 Origin 快照裡的既有成員時，才算合法終點——用查證確認，不能斷言。
- 連不上時只有兩種誠實結果：
  - (a) 真缺口 → 變成 scope/task
  - (b) 需求跟 Origin 矛盾或需要無界新能力 → 這就是「該不該做」誠實回答「不該」的時刻，不能被平滑掉
- **剪枝（軟判斷）跟起點驗證（硬判斷）必須分開機制**：不能讓剪枝把「連不上起點」包裝成「這段被剪掉了」，那等於把違規藏進剪枝步驟裡。
- 若事後發現凍結的 Origin 快照本身觀察錯誤（不是回推鏈憑空生出新起點，是對同一起點的原始觀察有誤）——需要顯式、可見的**重新釘點事件**，讓整棵樹失效並記錄重建，比照 ship gate 的 base commit 變動處理，且必須跟「憑空另立起點」明確區分。

### 6. 何時需要一個小陽動作先啟動

- 終點本身講不出來時（fog of war，連問題形狀都看不清），不能硬逼出終點，否則整條回推鏈建立在假前提上。
- 解法：先用一個最小正推動作提出「候選終點」（不必保證正確，只需具體到可被回推鏈檢驗），再用回推去驗證/剪裁/修正它——純陰或純陽都會崩壞，回推需要一個小陽的動作才能發動。

### 7. 高度分層：先看全貌，再看範圍，再看細節

- 樹要補上一個**高度（altitude）**維度，建構順序必須是 BFS（breadth-first，先看完同一層再往下），不能 DFS（一頭栽進某條分支的細節）：
  - Level 0 = End
  - Level 1 = 全貌／blueprint（End 的宏觀必要前提，粗粒度）
  - Level 2 = 範圍／scope（每個宏觀前提展開的次級前提）
  - Level 3+ = 細節
- 規則：當前層沒有完整看過、確認粗粒度上能走到 Origin 之前，不准展開下一層的細節。多數思維「太快掉入細項」正是用 DFS 走樹的結果。
- 這跟 `docs/development_workflow.md` 既有的 PRD → Domain/Behavior Spec → HLD → LLD 分層，以及「圖表選擇規則」的 Context → Container/component → Sequence 順序是同一種由上而下的高度紀律（即 C4 model 的分層邏輯），只是這裡要把它套用到回推樹的**建構順序**上。
- 好處：剪枝可以在 blueprint 層就先剪掉整條分支，不必等展開到細節才發現這條路不通——比純粹的「先長滿再剪」更早停損。

### 8. 同層候選選擇：奧坎剃刀（Occam's razor），但要驗證過

- 同一個前提節點常有多條候選路徑能滿足它（足球比喻：千萬種戰術都是為了進球）。選擇規則是：**已驗證過、trade-off 比較過的候選裡，選最簡單的那個**——簡單不是預設立場，是驗證之後的勝出者；複雜路徑不會被直接淘汰，只有在簡單路徑驗證不通時才輪到它。
- 「簡單」是**相對於 Origin 這個具體系統**，不是抽象的最佳實踐——這也是為什麼 Origin 必須是具體、有證據的凍結快照（見第 1、5 節）：只有具體的 Origin，才能讓「對這個系統而言最簡單」變成一個有意義、非憑感覺的判斷標準。
- 機制上類似 beam search：每層只留驗證通過的最簡候選繼續往下展開，該候選在下一層驗證失敗才回溯、換次簡單的候選——同樣是借推理схема，不是真的跑搜尋演算法。

### 9. 太極讀法：每個節點雙面，不是兩棵樹

「陽面終點」與「陰面終點」分立回推是**兩儀**（兩極並列），不是太極。太極是黑白相互滲透，各自含著對方的種子。機制上的差別：

- 兩儀讀法會長出兩棵樹，成本加倍，且兩棵樹會漂移。
- 太極讀法只有**一棵樹，每個節點本身雙面**：
  - **白面**：沒有你，抵達 End 的哪一步做不到？（必要性）
  - **黑面**：你靜默失效時，誰先發現？擴散到哪？（死法）
  - 兩面缺一，節點不合法，不得展開下一層。

如此「硬度」是結構性的，不是一道可跳過的閘門——不可能宣告一個只有白面的節點。

**這不是外來概念，V1 已經發明了，只是埋在最底層。** `agents/implementer.md:247` 要求每個 structural decision 是 dual-face entry（yang `forced_by` + yin `refused`/`risk_if_wrong`），`skills/implement/templates/scar-schema.yaml:57` 同樣規定兩面俱全，validator 檢查 dual-face completeness。V1 在最深、最晚、最小的位置做到了黑白相生，卻沒把它提升到推導層。V2 是把 V1 自己最好的發明拉到頂層。

**兩條具體規則：**

- **白中有黑**：End 宣告本身必須帶自己的失效條件。「做完長什麼樣」的同一句話裡要有「這個 End 在什麼條件下是錯的」。`develop.md` 的北極星 corruption signature 已有這個形狀，但只用在指標。
- **黑中有白**：死法分析必須帶存活面。每個 death path 要說出「壞掉之後什麼仍然成立、從哪裡接回去」。純記錄傷口而不指認殘存能力的 scar，是黑而無白。

**物極必反，要偵測兩種太過：**

| 太過 | 症狀 | 偵測手段 |
|---|---|---|
| 陽之太過 | 只測 happy path、祈禱式覆蓋率 | V1 已有：death test、scar、unknown 不算過 |
| 陰之太過 | 儀式化 gate、process weight、跑完流程讓人安心 | 缺席：公理套到 workflow step 層 + 成本帳本 |

`example.md` 開篇寫「如果你讀完感到安心，你走錯方向了」，而 V1 蓋的強制路由與六階段跑完正是讓人安心。陰推到極致生出陽的假穩定。

**S 曲線**：界線是曲線，代表比例隨位置流動，不是「先陽面階段、再陰面階段」。後者就是 pipeline 思維，正是 V1 的形狀。每個位置兩面都在，只是主從不同。沒有任何位置是單面的——這條直接否定了線性管線的存在理由。

### 10. 終點是尺度相對的 — 遞迴結構

北極星就是 project 層的 End。終點沒有絕對層級：project、feature、research、optimize、task 各有自己的終點，差別只在從哪一個高度看。

因此樹是**自相似的**——層級 N 的一個節點，往下看就是層級 N+1 的 End：

```
層級 N                        往下一層看同一個東西
──────────────────────────────────────────────
Project 的 End    ← 即北極星
  └ 節點：Feature A  ══►  Feature A 的 End
       └ 節點：Task 1  ══►  Task 1 的 End
            └ 節點：缺口小到一步可驗證  →  停止遞迴
```

**Origin 同樣是尺度相對的，而且是推導出來的，不是重新凍結的：**

- Project Origin = 凍結、有證據的現狀快照
- Feature Origin = Project Origin ＋ 已完成並驗證的兄弟 feature
- Task Origin = Feature Origin ＋ 已完成並驗證的兄弟 task

子層 Origin 由父層 Origin 加上已驗證的完成推導而來，從不憑空另立——這保住了第 5 節「不得在推導過程插入新公理」的硬規則。

**遞迴終止條件**：Origin 與 End 的缺口小到一步可驗證時停止下降。task 大小因此從結構推導出來，不必另外規定。

**這一節是「過於複雜」的解**，因為它讓下列各自獨立的機制收斂成同一個結構：

- `north-star.yaml` → 就是 project 層的 End，不是獨立 artifact
- `changes/` 與 `bugfix/` 兩套平行 artifact 系統 → 同一結構的不同入口高度
- research / fast-track / debugging 各自的入口 → 同一結構，差別只在從哪一層進入
- `development_workflow.md` 的「Task 大小」規則 → 由遞迴終止條件推導
- `development_workflow.md` 的 Artifact Router（8 問對 8 種 artifact）→ 深度由缺口決定，不由工作分類決定

### 高度軸與候選軸的分工（釐清與第 4 節的關係）

第 4 節的「先長滿再剪」與這裡的高度/候選規則不衝突，是兩個不同的軸：

- **高度軸（跨 level）**：永遠 BFS，不分 size/risk——看全貌本身很便宜（粗粒度），跳過這步才是真正浪費。
- **同層候選軸（同一 level 內）**：`size/risk` 決定的是同一層內要驗證比較幾個候選——小型低風險工作挑最簡單、驗證通過就走；大型高風險工作多驗幾個候選、trade-off 比較後才選。size/risk 從不影響要不要跳過全貌層，全貌層對誰都不能跳。

---

## 三、尚待決定的開放問題

- 這套終點回推法要**取代**現有入口儀式成為所有工作類型共用入口，還是**疊加**成為新的先行步驟？注意 V1 有**兩套**入口儀式並存，需一併決定：`example.md` 的 STEP 0 三問（最想聽到的實作先不走／什麼條件不該實作／靜默失敗誰先發現）與 `develop.md` 的 Interrogate 四問（問題形狀誰給的／何時不該解／誰受損／完成長什麼樣）。
- Origin 的凍結快照要直接複用既有 codebase-map/ship-manifest 證據機制，還是需要一個獨立的新 artifact？
