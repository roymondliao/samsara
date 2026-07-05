# Kickoff: structural-honesty-mechanisms

## Problem Statement

Samsara 對結構品質的處理方式，恰好是它自己批判的模式：品質只存在於 review-time 攔截（`code-quality-reviewer` 的 9 個抽象原則），是事後驗屍而不是事前死亡設計 —— 結構從來沒有被 spec 過。行為層的謊言可以被 death test 抓到，但結構層的謊言（不誠實的邊界、混雜的職責、錯亂的依賴）是讓行為謊言「容易發生且難以偵測」的土壤（`docs/thinking.md` 第四章，2026-07-04 定案）。本次工作把結構品質從 review-time gate 提升為 generation-time 規格：結構決策在 planning 被顯式承諾（附證據的變動理由）、在 implement 被定向注入、在 review 被對照驗證、在 iteration/reconciliation 被度量漂移 —— 讓「這個 feature 的結構長這樣，是哪份文件承諾的？」第一次有答案。受益者是**用 Samsara 開發的專案**；Samsara 自己是第一個 dogfooding 對象。

## Evidence

- **框架內部的斷層**：`docs/design.md` 第一天的筆記就寫著「implement 要有 modules 的設計、UML design pattern」，但這個意圖從未長成 skill。現行 planning 產出 File Map（檔案放哪裡）與 placement consistency check，「結構長什麼樣」沒有任何 artifact 承諾。9 個陰面結構原則只活在 reviewer agent 定義裡 —— 唯一的結構品質存在點在驗屍台上。
- **跨 project 實戰觀察（user 的核心體悟）**：AI coding 時代 codebase 停留在 POC 等級的無窮循環 —— 打掉重做時 tasks 清單歸零，「證據可及的未來」全部蒸發，每一輪的結構決策只服務眼前需求。系統腐爛可以用髒手法延緩，codebase 結構腐爛只會複利。
- **偏好不是判準**：主流 coding agent 的 system prompt 偏好 simple（防 AI 過度設計的疤痕組織），但把 simple 翻轉成 production 只是換一個偏誤方向。缺的是可被證據推翻的判準：結構投資必須引用有落點的變動理由（已發生的變動 > 已計畫的變動 > domain 本質分界；想像不是證據）。
- **context 蒸發機制**：AI 沒有資深工程師的十年之腦 —— 全局結構不成為 durable artifact 就會在沒人看見的地方退化。Samsara 已在行為層證明「durable artifact + 強制執行點」有效（scar report），結構層缺同樣的機制。

## Risk of Inaction

- Samsara 產出的專案繼續依賴 reviewer 的抽象原則攔截：PASS 之後沒人知道結構是被設計出來的還是碰巧長成這樣。結構品質不可歸因、不可累積 —— 每個 feature 的結構知識隨 session 蒸發。
- 使用 Samsara 的專案在多 feature 累積後重演 POC 循環：行為層的 death test 全綠，結構層靜默腐爛到重寫成為唯一選項 —— 框架承諾的「傷口可見」在結構維度上從未成立。
- `code-quality-reviewer` 持續拿 9 個無 feature 脈絡的原則審 code，無法區分「有證據的抽象」與「cargo-cult 抽象」—— 兩者在原則層面長得一模一樣。

## Scope

### Must-Have (with death conditions)

- **M1: Structure spec artifact（planning 生成）** — planning 新增結構規格產出：module 邊界＋職責、pattern 決策＋變動理由證據（證據等級：已發生/已計畫/domain 本質分界，引用必須可解析到 artifact——task id、kickoff scope 條目、git 路徑）、依賴方向規則。File Map 從 structure spec 推導，placement consistency check 升級為對照 spec。
  Death condition: 接下來兩個 dogfooding features 中，若 structure spec 未被任何下游（dispatch/review/reconciliation）實際引用消費，spec 是死重 —— 移除 artifact，結構品質退回 review-time 模式並記錄失敗原因。
- **M2: 定向注入（implement/iteration dispatch）** — 主 agent 策展時附上「該 task 觸及的 spec 片段＋證據」，不是整份 spec（控制 token 稅）。Inline mode C 由主 agent 直接持有。前置條件：結構 context 新鮮度 —— codebase map stale 超過閾值時不准注入腐爛藍圖，依現行 pre-thinking 的 auto-regen 條款處理。
  Death condition: 若注入使 dispatch context 顯著膨脹（單 task 注入超過整份 spec 的 50%，代表「定向」失效）而 review 發現率無改善，回退為 overview.md 內嵌關鍵決策的輕量形式。
- **M3: Reviewer 雙模式消費** — `code-quality-reviewer` 在 spec 存在時對照「feature 自己承諾的結構」＋審查證據可解析性；spec 不存在時（舊 feature、fast-track）保持現行 9 原則模式。兩種模式都必須誠實回報自己用的是哪種。
  Death condition: 若 reviewer 開始為 cargo-cult 證據蓋章（抽查發現引用不可解析卻 PASS），對照模式比原則模式更危險 —— 停用對照模式，證據審查機制重新設計。
- **M4: 進入判準（spec path 的邊界）** — 明確定義哪些工作走 structure spec path：預設為走 research→planning 完整 workflow 的 feature；fast-track 不受影響；「有死期的真 POC」可顯式豁免（死期必須寫入 kickoff——沒寫死期的 POC 就是 production）。
  Death condition: 若後續 feature 出現「production 意圖的工作靜默繞過 spec path」，判準有漏洞 —— 收緊為 planning 的 STOP gate。
- **M5: Structural rot signal（iteration＋reconciliation）** — iteration 新增結構漂移訊號來源（實作結構 vs spec 承諾的偏差項）；validate-and-ship 的 reconciliation check 加上結構維度。
  Death condition: 若連續多個 features 訊號恆為零，要麼結構從不腐爛（不可信），要麼訊號是瞎的 —— 重新設計度量方式，而不是留著一個永遠綠燈的儀式。

### Nice-to-Have

- **N1: Greenfield 結構起點** — research 階段對零 codebase 專案的 PRD / system design 事前討論步驟，產出初版全局藍圖。先在一個 greenfield dogfooding 專案取證再決定形式。
- **N2: Ship 後 map 回寫閉環** — validate-and-ship 完成後觸發 codebase map regenerate，讓下個 feature 的 research 從新鮮藍圖開始（現有 churn autoregen 已覆蓋大半，先驗證缺口是否真實存在）。

### Explicitly Out of Scope

- 正式重寫 `skills/pre-thinking/`（獨立工程，0-design-direction.md 的下一步）
- workflow-subtraction-optimization branch 的未完成項（本 feature 開新 change 目錄、北極星獨立計算，不佔用減法預算）
- 平台 system prompt 的 simple 偏好本身（改不了，機制設計把它當環境約束）
- 多平台 converter 策略（實作時同步 regenerate `dist/`，不改策略）
- roadmap.md RM-001 ~ RM-005（loop engineering）

### Compatibility Ruling（user 裁決，2026-07-04）

確定淘汰的機制**連同其測試一起刪除**，不保留 backward-compatibility —— 不重演 expiry_date 式的「留著沒人讀的欄位」。歷史 artifacts（舊 feature 的 changes/ 目錄）不回填，但聚合邏輯不得因舊格式崩潰。

## North Star

```yaml
metric:
  name: "結構決策證據鏈完整率"
  definition: "在 spec path 上跑完的 feature 中，structure spec 的每個結構投資（邊界/抽象/pattern）同時滿足：(1) 引用可解析的變動理由證據 (2) 被至少一個下游消費點實際引用（dispatch 片段/review verdict/reconciliation 報告）的比例"
  current: 0（機制不存在——現行 workflow 中結構決策無承諾文件，鏈完整率恆為零）
  target: "接下來兩個 dogfooding features 達到 100%，且平均每 feature 的 spec 相關儀式行數不超過 scar report 均值（噪音教訓：沒人讀的 spec 等於沒有 spec）"
  invalidation_condition: "若證據鏈 100% 完整但 dogfooding 專案的結構品質無可觀測差異（reviewer Critical 結構議題數不降、重寫衝動依舊），鏈完整率是儀式指標——目標本身錯了，判準需要重新設計而不是機制需要更嚴"
  corruption_signature: "cargo-cult 證據：每個 pattern 都自動配上煞有介事但不可解析的變動理由（引用的 task 不存在、kickoff 條目是編的、git history 查無此變動）。偵測：證據引用必須機器可解析（task id / 檔案路徑 / scope 條目），validate-and-ship 抽查解析"

sub_metrics:
  - name: "定向注入率（dispatch 含 spec 片段的 task 比例，spec path features）"
    current: 0
    target: "100%（觸及結構決策的 task）；純行為 task 可為零——全量注入反而是定向失效的訊號"
    proxy_confidence: high
    decoupling_detection: "注入率 100% 但 reviewer 從未引用 spec 條目 → 注入變成無人消費的 context 稅，proxy 與主目標脫鉤"
  - name: "structural rot signal 有效性（iteration/reconciliation 報告的結構漂移項）"
    current: "不存在"
    target: "訊號存在且至少一次非零（漂移被抓到）或有證據證明結構確實零漂移"
    proxy_confidence: medium
    decoupling_detection: "訊號恆為零且無零漂移證據 → 瞎的度量，觸發 M5 death condition"
  - name: "框架儀式淨增量（本 feature 引入的 loaded-context 行數）"
    current: 0
    target: "structure spec 模板＋skill 修改的單 session loaded-context 增量 <= 200 行（依減法 branch 的『單一 session 會被載入的總行數』度量法）"
    proxy_confidence: medium
    decoupling_detection: "行數達標但內容搬進 references/ 等量膨脹（假減法的鏡像：假輕量）→ 用減法 branch 的 corruption 偵測法交叉檢查"
```

## Stakeholders

- **Decision maker:** yuyu_liao（solo maintainer）
- **Impacted teams:** 所有使用 samsara plugin 的專案（Claude Code / Codex / Gemini CLI 轉換目標）—— 受益者是這些專案的 codebase 品質
- **Damage recipients:**
  - 小改動使用者 —— M4 進入判準是他們的防線；fast-track 不受影響是硬承諾
  - 每次 implementer/reviewer dispatch —— 定向注入的 token 稅；M2 的 50% 上限是止血點
  - 框架維護面 —— doc-contract 測試、`dist/` 全量 regenerate、skill 行數上升與減法北極星的張力（以獨立 change 目錄＋儀式淨增量 sub-metric 圈住）
  - `code-quality-reviewer` —— 角色從單一模式變雙模式，過渡期對新舊 feature 都必須誠實
