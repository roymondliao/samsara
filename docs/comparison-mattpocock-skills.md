> **V1 稽核 — 基準是 Samsara v1.0.1，不是 V2。**
> 分類依據見 [`README.md`](./README.md)。V2 重建後，本文 §8 的 P0/P1 修正項失效
> （README 安裝路徑、validator 依賴、`implement/SKILL.md` 重寫都指向會被刪除的檔案）。
> **背後原則活過 V2**：成本帳本、user/model invocation 二分、正向陳述取代 `Never:`、
> leading words 勝過生造代號、「It's working if」。§8 P2 的能力缺口清單
> （prototype、wayfinder、triage、domain-modeling、tracker）是 V2 可組合性要涵蓋的
> skill 種類。所有量化數據（字數、test 數、validator 行數）皆為 v1.0.1 當下的快照。

# Samsara vs. mattpocock/skills — 深度比較

比較對象：[mattpocock/skills](https://github.com/mattpocock/skills)（`skills/engineering/` + `skills/productivity/`，v1.2.0，22 個 skills）
基準：本 repo Samsara v1.0.1（12 個 skills、7 個 agents、6 個 references）

---

## 0. 量化基準

| 指標 | mattpocock | Samsara |
|---|---|---|
| Skills（比較範圍內） | 22 | 12 |
| `SKILL.md` 總字數 | 16,211 | 11,084 |
| 平均每 skill `SKILL.md` | 737 字 | 924 字 |
| 含 support/reference 總字數 | 29,366 | ~42,700（skills 24,492 + references 18,214） |
| 最大單一 skill | wayfinder 2,023 字 | implement 2,625 字（+ dispatch-template 2,180） |
| 最小單一 skill | grill-me 20 字 | debugging 431 字 |
| 確定性 validator | 0 行 | 3,652 行 Python（6 支） |
| 自身測試 | 無 | 108 檔 / 1,039 個 test |
| CI | changesets release only | pytest + pre-commit + version-sync（每 PR） |
| 執行期依賴 | 無（純 Markdown + 2 支 bash） | Python 3.14 + uv + 10 個套件 |
| Session 常駐注入 | 無 | bootstrap 1,089 字（SessionStart hook） |

**第一個結論**：Samsara 用一半的 skill 數量承載約 1.45 倍的指令語料，單 skill 重量約 3.5 倍。這不是缺點本身，但決定了後面五個維度的所有 trade-off。

---

## 1. 設計精神

### mattpocock — 工具箱，人類保有控制權

README 開宗明義反對流程型框架：「GSD、BMAD、Spec-Kit 想幫忙，但過程中拿走了你的控制權，並讓流程本身的 bug 難以修復。」設計目標是 **small, easy to adapt, composable, work with any model**。

四個失效模式驅動全部設計：

1. Agent 沒做我要的 → `grilling`（一次一問的訪談）
2. Agent 太囉唆 → ubiquitous language（`CONTEXT.md` + ADR）
3. 程式不能跑 → feedback loop（`tdd`、`diagnosing-bugs`）
4. 做出一坨大泥球 → deep modules（`codebase-design`、`improve-codebase-architecture`）

理論根基是點名的：Pragmatic Programmer、Evans DDD、Ousterhout、Feathers（seam）、Kent Beck、Fowler（12 個 smell）。核心公理寫在 `writing-great-skills`：**predictability（每次跑同一個 process）是根本德性**，並由此推導出 context load / cognitive load 的雙成本模型與 user-invoked / model-invoked 二分。

`ask-matt` 是 router 而非 gate——它回答「你該用哪個」，不決定你必須用哪個。決策權明確保留給人：*「If a fact can be found by exploring the environment, look it up. The decisions, though, are mine.」*

### Samsara — 軌道系統，紀律不可繞過

核心公理 **存在即責任，無責任即無存在**，把驗證問題從陽面（「它能動嗎」）翻轉到陰面（「它靜默壞掉時誰知道」）。三個支柱：death test 先於 unit test、scar report 先於完成、STEP 0 先於任何實作。

架構上與 mattpocock 相反：

- **強制路由**：`samsara-bootstrap` 由 SessionStart hook 每次注入，Skill Matching 規則「Stop at the first match」，state-changing 工作預設進 research 全流程。
- **線性管線**：`research → pre-thinking → planning → implement → iteration → validate-and-ship`，每個 stage 有 Transition 契約。
- **產物即事實**：`changes/<feature>/` 下的 kickoff / autopsy / plan / acceptance / index / scar / review-record / ship-manifest 是權威狀態，不是對話的副產品。
- **單一寫者紀律**：每個 artifact 明確宣告唯一 writer 與 consumers，其他角色只回傳 evidence。
- **結構性約束**：`agents/implementer.md` 讓 subagent「本身就是」samsara implementer，而非被 prompt 告知要遵守 samsara。
- **Auto mode**：把人類 gate 換成 `auto-gatekeeper`，決策 append-only 記錄於 `auto-decisions.md`。

### 評

兩者是同一問題的兩種答案，且互為對方的風險。

- mattpocock 的風險是它自己承認的 **cognitive load**：user-invoked skill 多到記不住時，人就是那個 index。沒有人啟動，紀律就不存在。
- Samsara 的風險是 **process weight**：三行改動也要證明 fast-track 四個入場條件才能走捷徑，而證明本身就是一場對話。強制路由在 agent 判斷錯誤時沒有便宜的逃生口。

值得注意的是，Samsara 有一件 mattpocock 完全沒有的東西：**一個貫穿全部的透鏡（silent failure）**，而不只是一條流程。mattpocock 的四個失效模式是四個獨立問題；Samsara 的陰面視角是同一個問題在每一層的投影。這是 Samsara 在設計精神上的真正優勢——不是「更嚴謹」，而是**更一致**。

反過來，mattpocock 有 Samsara 沒有的一件事：**明確的成本模型**。每一條指令都被問「這值多少 context load / cognitive load」。Samsara 沒有這個帳本，於是 bootstrap 1,089 字常駐、12 個 skill 的 description 全部常駐、implement 2,625 字，都沒有對應的成本反思。

---

## 2. 內容流暢度

### mattpocock：敘事流暢，人讀得下去

- README 是一條敘事線：問題 → 引言 → 修法 → 指向 skill。
- Skill 之間的依賴用 **prose invocation** 表達（`Run a /grilling session`），而非 `../other-skill/FILE.md` 的跨資料夾連結。`grill-me` 整個 skill 只有一行：「Run a `/grilling` session.」——極致的組合。
- `ask-matt` 用 main flow / on-ramps / standalone 的地理隱喻，把 22 個 skill 排成一張可讀的地圖。
- 每個 skill 另有一份人類向的 docs 頁（`docs/<bucket>/<skill>.md`），固定四段：**What it does / When to reach for it / It's working if / Where it fits**。

`It's working if` 這節特別值得抄——它給出「這個 skill 有在生效」的**可觀察訊號**，例如 `tdd` 的：「它寫一個測試、讓它過，然後才寫下一個——而不是一批測試接一批程式。」Samsara 完全沒有這個層次的東西。

**弱點**：流程只存在於敘事與人腦中。中途掉出來，只有 `handoff` 能救。

### Samsara：機器流暢，人讀得吃力

每個 `SKILL.md` 結構高度一致：`Prerequisites → Instruction Ownership → Process (dot graph) → Step Index → Output → Transition → Auto Mode Gate`。對 agent 來說這是優點——可預期的取用位置。對人來說：

1. **抽象階梯過深**。`pre-thinking/SKILL.md` 只有 498 字，實際程序在 `flow.md`（4,682 字）。SKILL.md 幾乎變成「索引的索引」，讀完不知道 pre-thinking 到底做什麼。progressive disclosure 的結構是對的，但頂層留下的資訊太少。

2. **語言契約自我違反**。Bootstrap 明訂「Executable instructions use English…Do not mix languages inside one instruction sentence」，但 `implement/SKILL.md` 的 dot graph 節點是中文（`讀取 index.yaml`、`主 agent: Code Review`、`寫 scar-report`），本文也有 `index.yaml 是唯一真實狀態（source of truth）；TaskCreate/TaskUpdate 是盡力而為的 UI 投影`。research 的 Step 1 是 user-facing prompt，屬合法例外；implement 的不是。

3. **`implement` 以否定為骨架**。Red Flags 一節有 20 條以上的 `Never:`。mattpocock 的 `writing-great-skills` 把這個明確列為失效模式：*「Negation — steering by prohibition backfires: don't think of an elephant names the elephant. Prompt the positive.」* 這是一條可以直接套用的改進。

4. **自創術語密度高**。`PT-EVAL`、`PL-D*`、`L1/L2 global thinking channel`、`systemic_ref`、`iteration_entry`、`signal_lost`、`accept_gap`、`global_channel: absent`——這些不在模型的 pretraining 裡，每一個都要靠上下文重建。對照 mattpocock 刻意挑選 **leading words**（tracer bullet、fog of war、seam、red、tight loop、smart zone），這些詞是已存在的概念，一個 token 就召喚一整區行為。

   公平地說，Samsara 的**好** leading words 也很強：`death test`、`scar report`、`rot path`、`death clause`、`blast radius`、`陰面/陽面`。問題不在沒有，而在好詞與生造代號混在一起。

### 評

流暢度上 mattpocock 明顯勝出，但兩者衡量的是不同的流暢：mattpocock 讓**人**讀順，Samsara 讓 **agent** 取用順。Samsara 的真正缺口是它沒有 mattpocock 的第二層——一份給人看的 onboarding 敘事。README 是規格書，不是入門。

一個 Samsara 做得比 mattpocock 好的地方：**derived view 的標註機制**。Samsara 每處重複視圖都標 `derived overview` 並宣告 canonical source（「If this summary conflicts with `flow.md`, `flow.md` wins」）。mattpocock 只說「single source of truth」，沒有機制，於是 README、bucket README、docs 頁、`ask-matt` 四處描述同一個 skill，靠 CLAUDE.md 的約定與人工同步。

---

## 3. 文字說明：具體、簡潔、明瞭

### 具體度

**mattpocock 明顯較具體。** 它給字面的東西：

- `code-review` 直接寫出兩個 sub-agent 的完整 prompt brief，含 400 字上限。
- Fowler 12 smell 每條是 *是什麼 → 怎麼修*：「Feature Envy — 一個 method 存取別的物件的資料比自己的多 → 把 method 搬到它羨慕的資料上。」
- `codebase-design` 附 ASCII 的 deep/shallow 圖與 TypeScript 正反例。
- `diagnosing-bugs` 列出 10 種建 feedback loop 的具體手段（failing test / curl / CLI + fixture diff / Playwright / replay trace / throwaway harness / fuzz / bisect harness / differential / HITL script），並排序。

**Samsara 較抽象。** 大量「record X in the owning artifact」「resolve refs」「apply the returned conclusion to the section it owns」。具體形狀被下推到 `templates/*.yaml`。這是合理的架構切分，但代價是 SKILL.md 本身讀起來像法條。

`diagnosing-bugs` vs `debugging` 是最鮮明的對照：前者告訴你**怎麼做出**一個能紅的迴圈；後者告訴你**必須產出**哪兩個 YAML 與路由到哪裡。Samsara 的授權紀律更嚴（診斷不等於修復授權），但方法學的具體度低得多。

### 簡潔度

Samsara 的 `writing-skills` 自訂目標：「Frequently loaded skills should be shortest; other skills should aim for fewer than 500 words」。實測：

| Skill | 字數 | vs 自訂 500 字 |
|---|---|---|
| implement | 2,625 | 5.3× |
| validate-and-ship | 1,495 | 3.0× |
| research | 1,230 | 2.5× |
| samsara-bootstrap | 1,089 | 常駐注入，卻是第二長 |
| codebase-map | 1,066 | 2.1× |

`samsara-bootstrap` 尤其值得檢視：它是唯一每個 session 都付費的檔案，卻包含完整的 User-facing Communication Contract（6 條）、Prohibited/Required Behavior（9 條）、Skill Matching（6 條）、以及一張 derived routing graph。那張 graph 自己標明「visualizes topology only; do not infer conditions」——即是說它**不承載任何新資訊**，純粹是重複，卻常駐佔位。

mattpocock 的做法是反過來的：常駐成本只有 model-invoked skill 的 description 一行；11 個 user-invoked skill（含 `wayfinder` 2,023 字、`teach` 1,490 字）的 context load 是 **零**，只有被人打出名字時才載入。

### 明瞭度

- **Frontmatter**：Samsara 12 個 skill 一律 `Use when ...`，一致性好。但 **Samsara 沒有 user-invoked / model-invoked 的區分**，等於 12 個 description 全部常駐。`level-analysis`、`writing-skills`、`codebase-map` 幾乎只會由人（或另一個 skill）叫，付常駐費並不划算。
- **重複**：Auto Mode Gate 區塊在 5 個 skill 各重寫一次（各約 100 字），雖有 `references/auto-mode.md` 為 canonical 且標為 derived，仍是可收斂的重複。
- **歧義**：`implement` 的 Arbitration path 寫得非常好——它明確處理「reviewer block 是判斷不是 gate」這個微妙區分，並定義第三方仲裁。這種等級的精確度在 mattpocock 找不到對應。

### 評

Samsara 在**契約精確度**上勝出（誰寫、誰讀、什麼算完成、unknown 怎麼辦），mattpocock 在**可讀性與具體度**上勝出。Samsara 的簡潔度是明確不合格——不是相對別人，是相對它自己寫下的標準。

---

## 4. 對等 / 相似工具比較

| 能力 | mattpocock | Samsara | 比較 |
|---|---|---|---|
| **需求訪談** | `grilling`（可重用原語）/ `grill-me`（無 repo）/ `grill-with-docs`（有 repo，落 CONTEXT.md + ADR） | `research` Step 1 四問 + `pre-thinking` 六步 | mp：一次一問、每題給推薦答案、無強制產物。samsara：固定四問（問題形狀誰給的／何時不該解／誰受損／完成長什麼樣）+ 強制產出 autopsy/kickoff。**mp 更輕更可重用，samsara 更可稽核**。samsara 的四問實質上是 mp 沒有的「殺死問題本身」步驟 |
| **規格** | `to-spec`（一份 PRD 發到 issue tracker，含 user stories / implementation decisions / testing decisions / out of scope） | `planning` → `2-plan.md` + `acceptance.yaml` | mp 產一份人讀的文件；samsara 產可執行的 acceptance 契約（death_path / degradation / unknown_outcome 場景）。**samsara 的驗收可執行，mp 的不行** |
| **拆票** | `to-tickets`：tracer bullet 垂直切片 + blocking edges；wide refactor 用 expand–contract 序列；發到 GitHub/GitLab/local `.scratch/` | `planning` → `index.yaml` DAG + `tasks/task-N.md` | 概念高度重疊（都強調垂直切片、依賴圖）。**差別：mp 有真 issue tracker 整合（native blocking links），samsara 只有本地檔案**。samsara 沒有任何 tracker 抽象層 ← **缺口** |
| **實作編排** | `implement`（70 字：跑 tdd、typecheck、full suite、code-review、commit） | `implement`（2,625 字：wave 平行、disjoint write scope 證明、dual review、arbitration、validator、per-fix commit 契約） | 兩端極值。mp 幾乎不指定，靠被叫用的 skill 自帶紀律；samsara 把編排本身當成受驗證的產品。**samsara 遠更嚴謹，也遠更重** |
| **測試紀律** | `tdd`：red-green、seam 需事前確認、三大反模式（implementation-coupled / tautological / horizontal slicing） | death test → **Test Contract Gate** → unit test；`references/test-contract.md` | 洞見幾乎重疊。mp 抓 tautological（斷言用程式碼同樣方式算出期望值）；samsara 抓**雙極**：over-fit（refactor 就紅）**與** silent-green（永遠不會紅）。**samsara 更完整**——只防 over-fit 會把病灶推到另一極。samsara 另有 death test 先行，mp 無 |
| **Code review** | `code-review`：雙軸 Standards（repo 標準 + Fowler 12 smell baseline）/ Spec（是否忠實實作原 issue），平行 sub-agent，禁止跨軸重排 | `code-reviewer`（陰面：先問可否刪除、命名誠實、silent rot）+ `code-quality-reviewer`（S/O/L/I/D + 內聚/耦合/DRY/Pattern），同訊息平行派發 | **結構幾乎相同**（雙軸 + 平行 subagent + 不合併）。samsara 多：`UNKNOWN` 阻斷、缺席 reviewer 判 FAIL、Critical 爭議走仲裁。mp 多：**Spec 軸**——明確對照原始 issue/PRD 檢查漏做與 scope creep。samsara 的 spec 對照散在 acceptance/plan refs，沒有專責 reviewer ← **值得補** |
| **除錯** | `diagnosing-bugs`：6 phase、10 種建迴圈手段、tight loop 完成條件（必須貼出已跑過的指令與輸出）、minimise、3–5 個可證偽假說、`[DEBUG-xxxx]` 標記清理、post-mortem 轉交架構改善 | `debugging`：`bug-report.yaml` + `root-cause.yaml`、失效分級 1–4、rot path 追蹤、**只診斷不修**、依授權與範圍路由到 fast-track 或 research | **互補性最強的一對**。mp 的迴圈建構方法論具體度遠高；samsara 的職責分離與授權紀律（bug report 授權調查，不授權改碼）更嚴。samsara 可直接吸收 mp 的 10 種手段清單與「必須貼出已執行指令」的完成條件 |
| **架構改善** | `codebase-design`（deep module 詞彙：module/interface/depth/seam/adapter/leverage/locality + deletion test）+ `improve-codebase-architecture`（掃 hot spot → 產互動 HTML 報告 → 選一個進 grilling） | 無對等 skill。相關內容散在 `code-quality-reviewer` + `references/code-quality.md` + `pre-thinking` 的 seam 判定 | **samsara 缺口**：沒有一個可主動觸發的「codebase 健檢」入口。samsara 的架構品質只在 review 時被動觸發，無法主動掃描 |
| **專案知識** | `domain-modeling`：`CONTEXT.md` 詞彙表 + `docs/adr/`，主動挑戰模糊詞、跨檢程式碼、就地更新 | `codebase-map`：`.samsara/codebase-map.yaml`，綁定 commit、detached worktree 隔離、SessionStart hook 偵測 drift、1,073 行 validator | **目標不同，兩邊各缺一半**。mp 建「共同語言」，samsara 建「結構圖」。samsara 的 map 自動化程度高得多；但 samsara **完全沒有 ubiquitous language 的維度** ← 這正好會治它自己的術語負擔 |
| **交付驗證** | 無。`code-review` 通過後 commit 即結束 | `validate-and-ship`：security & privacy STOP gate（全 diff、unknown 不算過、auto mode 不得接受風險）、frozen base/candidate commit、acceptance 逐場景執行、`ship-manifest.yaml` + failure budget | **samsara 獨有，且是它最強的一塊**。mp 沒有任何 pre-ship gate、沒有安全審查、沒有交付紀錄 |
| **快速路徑** | 無明確設計（直接 `/tdd` 或 `/implement`） | `fast-track`：入場需證明四件事（無未決設計／損害半徑有界／無結構影響／確定性驗證），先記 death clause 觀察 pre-change 失敗 | **samsara 獨有**。把「小改」也納入證據約束，而非豁免 |
| **超單 session 規劃** | `wayfinder`：`wayfinder:map` issue + decision tickets + **fog of war**（能精確陳述問題才開票，否則留在 Not yet specified）+ out of scope 分離 + 一 session 只解一票 | 無對等 | **samsara 缺口**。samsara 管線假設 research 時特徵是可知的；對「連問題都還看不清」的大型工作沒有機制 |
| **跨 session 交接** | `handoff`：壓縮對話成文件、含 suggested skills、寫到 OS temp、去識別化 | 無明確動作（靠 `changes/<feature>/` 隱性達成） | samsara 的 artifact 事實上就是 handoff，但缺少「主動壓縮當前對話」這個動作 |
| **原型** | `prototype`：兩分支——LOGIC（可跑的終端小程式驗 state machine）/ UI（同一路由多個激進變體）；throwaway from day one，結束後 commit 到丟棄分支當 primary source | 無 | **samsara 缺口**。pre-thinking 的設計決策只能靠推理，無法靠「跑起來看」解決 |
| **外部研究** | `research`：background agent、primary source（官方文件/原始碼/spec）、產出有引用的 md | 無（Samsara 的 `research` 是**需求訪談**，語意完全不同） | **命名衝突**值得注意。samsara 沒有「delegate 資料蒐集」的機制 |
| **Triage** | `triage`：5 個 state role 的狀態機、redundancy/prior-rejection 檢查、驗證 claim、agent brief、`.out-of-scope/` 知識庫、AI 產出必掛免責聲明 | 無 | **samsara 缺口**。samsara 假設工作從 user 直接來，沒有處理外部 issue/PR 入口 |
| **Meta（寫 skill）** | `writing-great-skills`：predictability 為根本德性、context/cognitive load 雙成本、information hierarchy 三階、progressive disclosure、leading words、6 個失效模式（premature completion / duplication / sediment / sprawl / no-op / negation） | `writing-skills`：是否該存在 → 分類（workflow/technique/pattern/reference/advisory）→ 契約 → **form-to-failure 對照** → **proportional verification** → commit 紀律 → 陰面自檢 | **兩者都很好且互補**。mp 談「怎麼寫得可預測」（成本與資訊階梯）；samsara 談「怎麼證明它有效」（依變更類型選驗證方法）。samsara 缺 mp 的成本模型與 negation 原則；mp 缺 samsara 的驗證比例原則 |
| **Router** | `ask-matt`：user-invoked，回答「你該用哪個」，畫出 main flow / on-ramps / standalone | `samsara-bootstrap` Skill Matching：hook 注入，**強制**路由，Stop at first match | **哲學差異的縮影**：mp 建議，samsara 決定 |
| **顧問分析** | 無 | `level-analysis`：Senior/Staff/Principal 三層視角、evidence/assumption/unknown 三分、明確不做決定 | samsara 獨有 |
| **稽核紀錄** | 無（除 issue 與 commit） | scar report / review-record / auto-decisions / ship-manifest，全部 append-only 或單一寫者 | **samsara 獨有**，這是兩者最大的結構差異 |
| **多平台** | 每個 skill 附 `agents/openai.yaml`；`npx skills@latest add`（第三方 skills.sh 生態） | `samsara-cli convert/install/update/validate`（自建 converter，目前支援 codex） | mp 靠外部生態、覆蓋面廣；samsara 自建、可控性高但只有一個目標平台 |

### 對等關係總覽

**兩邊都有、洞見重疊**：訪談、拆票、TDD 反模式、雙軸平行 review、寫 skill 的方法論。
**Samsara 獨有**：陰面透鏡、death test、scar report、validate-and-ship 安全閘、fast-track 入場證明、auto mode + gatekeeper、level-analysis、確定性 validator、自身測試套件。
**mattpocock 獨有**：ubiquitous language、deep module 詞彙與架構健檢、prototype、wayfinder（fog of war）、triage、handoff、外部 research、issue tracker 整合、user/model invocation 二分、context load 成本模型。

---

## 5. 安裝難易度

### mattpocock：兩條路，都是分鐘級

**路線 A（訂閱）**
```
/plugin install mattpocock-skills
```
已在 Claude Code 官方 marketplace，**不需要先 add marketplace**，自動更新，read-only bundle。

**路線 B（可改）**
```
npx skills@latest add mattpocock/skills
```
互動式挑 skill 與目標 agent，寫成你擁有的一般檔案，`npx skills update` 手動更新。

**設定**：`/setup-matt-pocock-skills`，每 repo 跑一次，三個問題（issue tracker / triage labels / doc 位置），寫出 `docs/agents/*.md`。README 明確警告：兩條路不要同時裝，否則每個 skill 會出現兩次。

**執行期依賴**：無。純 Markdown + 一支 bash template + 一支 git guardrail script。選 GitHub/GitLab tracker 時才需要 `gh`/`glab`。

### Samsara：文件所寫的方法在平台上不成立

**問題 1 — README 的安裝指令與 Claude Code 實際 API 不符。**

README（中英文版皆同）給的是：

```jsonc
// .claude/settings.json
{ "plugins": { "samsara": true } }
```
```bash
claude plugins add /path/to/samsara
```

依 Claude Code 官方文件：
- `settings.json` 沒有 `plugins` 這個 key。正確的是 `extraKnownMarketplaces`（註冊 marketplace）+ `enabledPlugins`（啟用）。
- shell 指令是單數 `claude plugin ...`（`claude plugin marketplace add` / `claude plugin install`），沒有 `claude plugins add`。

本 repo 已有 `.claude-plugin/marketplace.json`（`samsara-marketplace`），所以**正確流程應該是**：

```
/plugin marketplace add roymondliao/samsara
/plugin install samsara@samsara-marketplace
/reload-plugins
```

或本地開發：`claude --plugin-dir /path/to/samsara`。

這是整份比較中**投報率最高的單一修正**——目前照 README 做的使用者裝不起來。

**問題 2 — 未進官方或社群 marketplace。** 使用者必須自己 add marketplace，多一步且需要信任決策。mattpocock 在官方 marketplace，這一步為零。

**問題 3 — plugin 不是自給自足的。** 多個 skill 在流程中要求執行：

```bash
uv run python <installed-implement-skill-directory>/scripts/validate_format.py changes/<feature>/
```

這帶來三個實務問題：
- **Python 3.14**（`requires-python = ">=3.14"`）+ uv + 10 個套件（pydantic、typer、rich、hydra-core、jinja2、pyyaml…）。3.14 很新，多數開發機沒有。
- `uv run` 在**目標專案**執行時會用目標專案的 venv——那裡不會有 Samsara 的依賴，除非目標本身是 uv 專案並額外安裝。
- `<installed-implement-skill-directory>` 是未解析的佔位符，agent 得自己推出 plugin cache 路徑。plugin 的 hook 已經在用 `${CLAUDE_PLUGIN_ROOT}`，skill 內卻沒用，是可修的不一致。

由於 `implement` 明訂「Commit without running implement's format validator ... 是 Red Flag」，validator 跑不起來會直接卡住主流程。

**問題 4 — 多平台安裝步驟較多**（但功能也較強）：
```bash
uv tool install --force /path/to/samsara
samsara-cli convert --platform codex
samsara-cli install codex --scope project
samsara-cli validate --platform codex
```
這條路的設計其實比 mattpocock 嚴謹——它明確拒絕用 source checkout 的 `.venv` 做 global 安裝，因為 checkout 一搬就壞。這種 failure-mode 意識正是 Samsara 的強項，只是沒有用在主安裝路徑上。

### 評

| | mattpocock | Samsara |
|---|---|---|
| 最短路徑步數 | 1（官方 marketplace） | 3（add marketplace → install → reload） |
| 文件正確性 | 正確（`claude plugins install` 是單複數小瑕疵，但 `/plugin install` 正確） | **錯誤**，照做裝不起來 |
| 執行期依賴 | 無 | Python 3.14 + uv + 10 套件 |
| Plugin 自給自足 | 是 | **否**（validator 需外部 toolchain） |
| 每 repo 設定 | 1 個 skill、3 問 | 無（也代表無 tracker 整合） |

**mattpocock 大幅勝出。** 這是 Samsara 目前最不成比例的弱點——一個對「靜默失敗」如此敏感的框架，卻在自己的安裝路徑上留了一個靜默失敗（使用者照 README 做、沒有錯誤訊息、只是什麼都沒發生）。

---

## 6. 驗證的完整性

分兩層看：**對使用者工作的驗證** 與 **對框架自身的驗證**。

### 6.1 對使用者工作的驗證

**mattpocock** — 全部由 LLM 判斷，無機器檢查：

- `tdd`：red before green、one slice、seam 需事前確認。
- `code-review`：雙軸平行 sub-agent，各 400 字上限，禁止跨軸重排。
- `diagnosing-bugs`：**完成條件寫得極好**——Phase 1 只有在你能指名「一條**已經至少跑過一次**的指令（貼出調用與輸出）」且該指令 red-capable / deterministic / fast / agent-runnable 時才算完成。並明說：「若你在這條指令存在前就開始讀程式建理論，**停下來**——直接跳到假說正是這個 skill 要防的失效。」
- `implement`：typecheck 常跑、單檔測試常跑、全套件跑一次、`code-review` 收尾。

沒有 schema、沒有 validator、沒有持久化證據。session 結束後除了 commit 與 issue，什麼都不留。

**Samsara** — 多層，且有確定性層：

| 層 | 機制 |
|---|---|
| 事前 | STEP 0 四問；fast-track 入場四證明 |
| 測試 | death test 先於 unit test（順序不可交換）；**Test Contract Gate 在寫 unit test 之前**跑（寫完再檢查擋不住已落地的 tautological test）；over-fit 與 silent-green 雙極 |
| Review | 雙 reviewer 必須**都**回傳；缺一判 FAIL 而非 PASS；`UNKNOWN` 阻斷而非部分通過；Critical 爭議走第三方仲裁（人 or gatekeeper），reviewer 不能自動贏、implementer 不能自我豁免 |
| 格式 | 6 支 validator 共 3,652 行：scar report（dual-face 完整性、forced_by/seam 解析、systemic_ref 懸空）、plan、ship manifest、bugfix、fast-track、codebase-map |
| 驗收 | `acceptance.yaml` 逐場景執行，順序固定：death_path → degradation → unknown_outcome |
| 交付 | Step 0 security & privacy STOP gate 跑**全 diff** 而非 fix delta；frozen base/candidate commit，任何程式或測試變更使全部結果失效並重跑；ship manifest 含 failure budget |
| 貫穿 | **`unknown` 永遠不等於 pass** — 這條紀律在 debugging、review、security gate、level-analysis、codebase-map 一致出現 |

「unknown 不算過」是 Samsara 最強的單一驗證觀念，mattpocock 沒有任何對應物。它把「沒查到」與「查了沒問題」分開——這正是靜默失敗的溫床。

**但要誠實標註兩件事**：

1. Samsara 自己說得很清楚：validator **只檢查格式**（「The validator checks format only; risk and review adequacy remain judgment」）。判斷層仍然是 LLM。所以在「有沒有做對的事」這個維度上，兩個框架的差距比 test 數量看起來的小。
2. Samsara 沒有驗證**路由本身**是否符合使用者意圖。強制路由把三行改動送進六階段的成本，只能靠 fast-track 的入場證明擋——而證明本身不便宜。

### 6.2 對框架自身的驗證

| | mattpocock | Samsara |
|---|---|---|
| 測試 | **無** | 108 檔 / 1,039 個 test |
| 覆蓋範圍 | — | agents、auto_mode、cli、config、contract_bound_tests、converter、hooks、installer、release、skills、validators、workflows + golden fixtures（三代 scar report 格式） |
| CI | 只有 changesets release | 每 PR：pytest + pre-commit + `release check-version` |
| 一致性強制 | CLAUDE.md 約定（README + plugin.json + docs 頁 + ask-matt 四處同步），**靠 agent 讀約定，無 CI 檢查** | version 三處同步由 CI 檢查 |
| Plugin manifest 驗證 | CLAUDE.md 提到 `claude plugin validate . --strict`，**未接進 CI** | 未見（可補） |
| 自我批判紀錄 | 無 | `issue.md`（框架缺陷 + error chain + root cause）、`roadmap.md`（RM-001~005） |

mattpocock 的四處同步規則完全靠人與 agent 自律，drift 不會被偵測。Samsara 在這一層是完全不同的等級——它把自己的哲學套在自己身上（傷口記錄而非隱藏）。

### 評

**驗證完整性 Samsara 決定性勝出，兩層皆是。** 但 mattpocock 有一個便宜且值得抄的技巧：**用「貼出已執行的指令與輸出」當完成條件**。這不需要任何工具，就把 LLM 的自我宣稱換成證據。Samsara 只在 implement 的 validator 輸出用了這招（「a missing validator output at handoff is a visible missing, never a silent skip」），可以擴散到更多 gate。

---

## 7. 綜合評分

| 維度 | mattpocock | Samsara | 勝方 |
|---|---|---|---|
| 1. 設計精神 | 一致的成本模型、明確反流程框架、人保有控制 | 一致的陰面透鏡、可稽核、紀律不可繞過 | **平手**（不同答案，各自自洽；Samsara 透鏡更一致，mattpocock 成本模型更清醒） |
| 2. 內容流暢度 | 敘事流暢、prose invocation、docs 頁四段式 | 結構一致利於 agent 取用、derived view 標註嚴謹 | **mattpocock** |
| 3. 文字具體/簡潔/明瞭 | 具體度高、leading words 純度高、context 成本低 | 契約精確度高、術語密度高、明顯超出自訂長度標準 | **mattpocock**（Samsara 在契約精確度上勝出） |
| 4. 工具覆蓋 | 22 skill、覆蓋 triage/prototype/wayfinder/domain 等 samsara 空白 | 12 skill、覆蓋 ship gate/scar/auto mode 等 mattpocock 空白 | **平手**（互補大於重疊） |
| 5. 安裝難易度 | 1 步、零依賴、文件正確 | 3 步、重依賴、**文件錯誤** | **mattpocock（差距大）** |
| 6. 驗證完整性 | 全 LLM 判斷、無自身測試 | 多層 + 確定性 validator + 1,039 test + CI | **Samsara（差距大）** |

---

## 8. Samsara 可執行的改進（依投報率排序）

### P0 — 立刻

1. **修正 README 安裝章節**（中英文版）為 `/plugin marketplace add roymondliao/samsara` → `/plugin install samsara@samsara-marketplace` → `/reload-plugins`，並補 `claude --plugin-dir` 的本地開發路徑。目前寫法照做無效且無錯誤訊息。
2. **解除 validator 對宿主專案 Python 環境的依賴**：改用 `${CLAUDE_PLUGIN_ROOT}/skills/<name>/scripts/...`（hook 已在用），並讓 validator 為零依賴純標準庫 script，或隨 plugin 附帶自己的 runtime。`requires-python >= 3.14` 對大多數使用者是硬牆。
3. **把 `claude plugin validate . --strict` 接進 CI**。

### P1 — 結構

4. **引入 user-invoked / model-invoked 二分**（`disable-model-invocation: true`）。`level-analysis`、`writing-skills`、`codebase-map`、`validate-and-ship` 幾乎只由人或上游 skill 觸發，目前為它們的 description 付每回合常駐費。
5. **重寫 `implement/SKILL.md`**：2,625 字對照自訂 500 字上限；20+ 條 `Never:` 依 mattpocock 的 negation 原則改寫為正向陳述；依「split by sequence」把 initial execution 與 Iteration Fix Re-entry 拆成兩條路徑。
6. **修正 `implement/SKILL.md` 的語言契約違反**（dot graph 節點與本文中文），或修訂 Bootstrap 契約承認例外。
7. **精簡 `samsara-bootstrap`**：它是唯一每 session 付費的檔案卻是第二長；那張自承「不承載新資訊」的 derived routing graph 是最明顯的候選。

### P2 — 能力缺口（依價值排序）

8. **ubiquitous language / `CONTEXT.md`**（對應 `domain-modeling`）：Samsara 有結構圖（codebase-map）但沒有共同詞彙。這正好會治 Samsara 自己的術語負擔——`PT-EVAL`、`L1/L2`、`systemic_ref` 之類生造代號，在有詞彙表的專案裡本來就該被收斂。
9. **架構健檢入口**（對應 `improve-codebase-architecture` + `codebase-design`）：目前架構品質只在 review 時被動觸發，沒有主動掃描 hot spot 並提出 deepening 候選的機制。
10. **`prototype`**：pre-thinking 的設計決策目前只能靠推理解決；「跑起來看」是最便宜的高保真度手段。
11. **issue tracker 抽象層**：planning 的 tasks 只存在本地檔案。mattpocock 的 `setup` + tracker 模板（GitHub/GitLab/local）是可直接借鑑的三層設計。
12. **`wayfinder` 式 fog of war**：Samsara 管線假設 research 時特徵可知。對「連問題形狀都看不清」的大型工作，需要「能精確陳述才開票、否則留在 Not yet specified」這種機制。
13. **`handoff`**：`changes/<feature>/` 是隱性交接，但缺少主動壓縮當前對話的動作。
14. **Code review 的 Spec 軸**：mattpocock 明確用一個 sub-agent 對照原始 issue 檢查漏做與 scope creep。Samsara 的 acceptance 驗收在最後，review 階段沒有專責的 spec 對照。

### P3 — 文件體驗

15. **每個 skill 一頁人類向文件**，抄 mattpocock 的四段式，特別是 **「It's working if」**（可觀察的生效訊號）。Samsara README 是規格書，缺入門敘事。
16. **把「貼出已執行的指令與輸出」推廣為通用完成條件**。零成本、把自我宣稱換成證據，目前只用在 implement validator。

---

## 9. 一句話總結

**mattpocock 是一套刻意保持輕、可拆、人主導的工程紀律工具箱，安裝與閱讀體驗優異，但不驗證自己也不留下證據。Samsara 是一套哲學一致、可稽核、有確定性驗證與自身測試的軌道系統，驗證深度領先一個量級，但在簡潔度、安裝正確性與能力廣度上有明確且可修的缺口。**

兩者的重疊遠小於互補：Samsara 該補的是 mattpocock 的**成本紀律與人因設計**（invocation 二分、長度紀律、正向陳述、入門文件、prototype/domain/tracker 等空白），而非它的流程哲學——後者 Samsara 已經走得更遠。
