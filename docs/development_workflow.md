> **外部來源 — 本文的「目前 repository」不是 samsara。**
> 分類依據見 [`README.md`](./README.md)。內文舉的 Cloudflare D1、Worker、recurring rule、
> report endpoint P95 等案例都不存在於 samsara（全 repo grep 只命中本檔）。這是為另一個
> 專案寫的通用方法論，搬進來當 V2 的參考材料。閱讀時把「目前 repository」讀成「來源專案」。
>
> **V2 已借用的部分**：資訊狀態分類（`fact / decision / assumption / proposal / unknown`）
> 成為回推樹的節點型別；`work_type / size / risk` profile 成為同層候選數的閘門；
> PRD → Domain/Behavior → HLD → LLD 的分層成為回推樹高度紀律的先例。
> 詳見 [`v2-redesign-backward-derivation.md`](./v2-redesign-backward-derivation.md)。

# Standardized Software Development Workflow

## 文件目的

本文件以目前 repository 的 `docs/`、`changes/`、architecture decisions、phase planning、tasks、LLD 與 verification practices 為實際案例，整理一套可與 AI 共同執行的通用軟體開發工作流。

這套工作流的目的不是修正某一份既有文件，也不是要求所有 project 固定依序產生 PRD、BDD、HLD、Phase、Task 與 LLD，而是建立一套穩定的規則，讓不同形式的工作都能用一致的方法完成需求釐清、設計、規劃、實作與驗證。

工作流必須達成以下品質：

- **標準化**：文件格式、artifact responsibility、狀態與完成條件有明確定義。
- **可重複性**：可套用於初次產品開發、系統重構、新增需求、bug fix、系統優化與研究設計。
- **一致性**：相同類型、規模與風險的工作，即使重新與 AI 討論多次，也能產生高度相似的結構、涵蓋範圍與內容深度。
- **高品質**：內容明確、具體、可驗證且沒有不必要的重複；文字、表格與圖表各自用於最適合的資訊關係。

核心原則如下：

> 不將 PRD → BDD → HLD → Phase → Task → LLD 視為每次都必須完整執行的線性流程。建立固定的工作流核心，再依工作類型、複雜度與風險決定需要哪些 artifacts。

## Repository 實踐帶來的結論

目前 repository 最值得保留的基礎分界是：

```text
docs/       = 長期有效的 current truth
changes/    = 某次改動的目的、設計、執行與驗證
code/tests  = 可執行的 truth
```

這個分界可以同時保存系統目前狀態與個別 change 的歷史脈絡。真正需要標準化的不是文件數量，而是 artifact system：

- 什麼情況需要 PRD？
- 什麼情況需要 BDD 或 Behavior Spec？
- HLD 與 System Design 的邊界是什麼？
- LLD 應屬於 Phase、Feature 還是 Component？
- Task 可以包含多少 Design？
- Phase 是產品階段、部署環境，還是工作分組？
- Bug fix、研究或效能改善是否需要相同文件？

因此，一個可重複的工作流必須先定義 artifact selection rules，而不是只增加更多 templates。

## 固定核心與可變 Profile

### 固定工作流核心

任何工作，不論類型，都經過相同的七個狀態：

```text
Explore
→ Define
→ Design
→ Plan
→ Execute
→ Verify
→ Close
```

這七個狀態是工作流的一致性來源：

1. **Explore**：理解現況、問題、目標、限制與未知事項。
2. **Define**：定義需求、範圍、非目標與可觀察結果。
3. **Design**：決定系統、component、data 與 interaction design。
4. **Plan**：切分可交付 tasks、dependencies 與 verification boundaries。
5. **Execute**：實作、測試並同步必要文件。
6. **Verify**：以可執行 evidence 驗證需求、設計與品質目標。
7. **Close**：將長期有效內容提升至 durable docs，保存 change history。

每個狀態不一定產生獨立文件。小型 bug 可以在單一 `CHANGE.md` 內完成所有必要內容；大型產品或重構則可以拆成 PRD、Domain Spec、HLD、ADR、Behavior Spec、LLD 與多個 tasks。

### 工作 Profile

開始工作時先使用固定欄位分類：

```yaml
work_type: product | refactor | feature | bug | optimization | research
size: small | medium | large
risk: low | medium | high
```

- `work_type` 決定主要問題與必要 evidence。
- `size` 決定內容是否需要拆分成多個 artifacts。
- `risk` 決定設計、驗證、rollout 與 recovery 的深度。

文件深度應由這些條件決定，不由 User 或 AI 臨時憑感覺決定。

## 通用 Artifact Model

通用工作流只定義八種 artifact。PRD、BDD、HLD 與 LLD 是不同的資訊視圖，不是固定 phase。

| Artifact | 回答的問題 | 內容所有權 |
| --- | --- | --- |
| Product Brief / PRD | 為什麼做、為誰做、成功是什麼 | 長期產品需求 |
| Domain Spec | 業務名詞、規則與不變量是什麼 | 長期業務真相 |
| Change Spec | 這一次要改變什麼 | 單次 change |
| Behavior Spec | 使用者或外部系統應觀察到什麼 | Acceptance behavior |
| HLD | 系統邊界與 components 如何協作 | 跨 component 設計 |
| ADR | 為什麼選擇這個方案 | 長期技術決策 |
| LLD | 某個 component 內部如何實作 | 複雜 implementation |
| Task / Verification | 如何交付，以及如何證明完成 | 執行與 evidence |

### Product Brief / PRD

Product Brief 定義產品或大型 initiative 的 `why` 與 `what`：

- problem / opportunity
- users / stakeholders
- desired business and user outcomes
- primary journeys
- scope / non-goals
- success metrics
- quality attributes
- business constraints
- assumptions and open questions

Product Brief 不定義 API、class、file path 或內部 implementation。

### Domain Spec

Domain Spec 保存與單次 implementation 無關的長期業務真相：

- glossary
- entities and concepts
- business rules
- calculations
- invariants
- valid and invalid state transitions
- representative examples and edge cases

Domain rule 改變時，應更新 Domain Spec；單次 change 只引用並描述本次差異。

### Change Spec

Change Spec 是所有非微小工作的核心 artifact，至少包含：

- motivation
- current behavior / desired behavior
- in scope / out of scope
- affected users and journeys
- constraints
- risks
- acceptance summary
- affected durable artifacts

Change Spec 描述 delta，不複製完整產品、domain 或 architecture 定義。

### Behavior Spec

Behavior Spec 定義外部可觀察行為，可以使用 scenarios、examples 或 decision tables。BDD 的價值在於消除行為歧義，不在於將所有需求機械地改寫成 Gherkin。

適合使用 Given / When / Then 的例子：

```gherkin
Given recurring rule 已套用於 2026-08
When 使用者再次套用相同 rule 與月份
Then 不建立第二筆 occurrence
And 回傳既有結果
```

簡單 CRUD、欄位存在性或已由 schema 完整表達的 validation，不需要全部重寫為 BDD。

### High-Level Design

HLD 只處理跨 component 或 system boundary 的問題：

- external actors and systems
- runtime components
- component responsibilities
- trust and security boundaries
- data ownership
- major request / event flows
- deployment topology
- cross-cutting consistency and failure behavior
- applicable non-functional requirements

精確 request schema、DTO、function signature 與 file-level implementation 不屬於 HLD。

### Architecture Decision Record

ADR 用於保存有長期影響、存在合理替代方案且值得保留理由的技術決策：

- context
- decision drivers
- considered alternatives
- decision
- consequences and trade-offs
- status

單純套用既有規則或沒有實際 alternatives 的 implementation detail 不需要 ADR。

### Low-Level Design

LLD 將已定案的系統或 component design 轉換為可直接實作的內部結構：

- module responsibilities
- internal contracts
- state and lifecycle
- algorithms
- transaction and consistency boundaries
- concurrency and idempotency
- error propagation
- test seams
- complex interaction sequences

LLD 應以複雜 component 或 feature 為單位，不應固定要求每個 Phase 都建立一份。

### Task 與 Verification

Task 定義可獨立交付與 review 的 execution slice：

- observable outcome
- scope
- dependencies
- affected components
- requirement / behavior references
- task-specific verification
- deliverables

Verification 保存完成 evidence：

- automated tests
- validation commands
- benchmark results
- migration reconciliation
- manual evidence
- staging / production verification
- remaining known limitations

## Source of Truth 原則

### 一個事實只能有一個 owner

例如：

| Information | Owner |
| --- | --- |
| Business goal | Product Brief / PRD |
| Domain formula | Domain Spec |
| API request schema | Code-owned contract |
| 選擇 Cloudflare D1 的理由 | ADR |
| Worker、frontend 與 D1 的關係 | HLD |
| Recurring apply transaction boundary | Feature / component LLD |
| 本次需要修改哪些 components | Task |
| 是否達成需求 | Tests and verification evidence |

其他文件只能引用 source of truth，不能建立平行定義。

### Durable truth、change history 與 executable truth

```text
Durable docs
  定義目前長期有效的 product、domain、architecture 與 decisions

Change artifacts
  定義某次 change 的 motivation、delta、plan 與 evidence

Executable artifacts
  以 schemas、migrations、code、tests 與 CI 表達可被工具驗證的行為
```

Change 完成後，只將仍會長期有效的內容提升到 durable docs。Task、討論過程與一次性 delivery evidence 保留在 change history，不複製進 System Design。

## Artifact Selection Rules

### Artifact Router

每次工作開始時以固定問題決定需要哪些 artifacts：

| 判斷問題 | 是的話需要 |
| --- | --- |
| 是否涉及新產品、使用者目標或產品範圍？ | Product Brief / PRD |
| 是否新增或修改長期業務規則？ | Domain Spec |
| 是否改變使用者或外部系統可觀察行為？ | Behavior Spec |
| 是否改變 system、service、component 或 trust boundary？ | HLD |
| 是否做出有長期影響且存在替代方案的技術決策？ | ADR |
| 是否涉及複雜 state、algorithm、transaction、concurrency 或 migration？ | LLD |
| 是否需要多個可獨立交付單位？ | Tasks |
| 是否需要 rollout、migration、benchmark 或 production validation？ | Verification / Delivery Plan |

因此：

- 不是每個 change 都需要 PRD。
- 不是每個 feature 都需要 HLD。
- 不是每個 task 都需要 LLD。
- BDD 只用在重要且容易產生歧義的 observable behavior。
- 每個 change 都必須有明確範圍與完成 evidence。

### LLD Trigger

符合下列任一條件時，通常需要 LLD：

- 跨三個以上 internal modules，責任邊界不容易從既有 architecture 推導。
- 涉及 transaction、partial failure、concurrency 或 idempotency。
- 涉及 migration、reconciliation、backfill 或 rerun。
- 涉及 security-sensitive identity、authorization 或 sensitive state。
- algorithm、state machine 或 transformation pipeline 不容易直接理解。
- 多人或多個 AI agents 需要平行實作同一 component。
- 錯誤設計會造成高成本、不可逆資料影響或 production outage。

簡單 CRUD、單一 component 修改或已有明確 pattern 的 implementation，不需要獨立 LLD；在 Change Spec 或 Task 中加入簡短 implementation notes 即可。

## 不同工作類型的 Profile

| Work type | 必要內容 | 常見選配 |
| --- | --- | --- |
| 初次產品開發 | PRD、Domain、Behavior、HLD、Tasks、Verification | ADR、LLD |
| 系統重構 | Change Spec、as-is / to-be HLD、invariants、migration plan、Verification | ADR、component LLD |
| 新增需求 | Change Spec、Behavior、Tasks、Verification | HLD、ADR、LLD |
| Bug fix | Reproduction、expected / actual、root cause、regression test、Verification | LLD、ADR |
| 系統優化 | Baseline、bottleneck、target metric、experiment、Verification | HLD、ADR |
| 研究設計 | Research question、constraints、alternatives、experiment、conclusion | ADR、prototype design |

### 初次產品開發

初次產品開發通常需要完整定義：

- 使用者與問題
- business outcome
- domain model
- primary journeys
- MVP boundary
- quality attributes
- system context
- delivery slices

但即使是新產品，也不應在需求尚未穩定時過早產生完整 LLD。

### 系統重構

重構的重點是保持或明確改變既有行為，因此需要：

- as-is state
- target state
- preserved invariants
- intentionally changed behavior
- migration strategy
- compatibility boundary
- rollback / recovery
- reconciliation evidence

重構不一定需要完整 PRD，但必須明確知道為什麼重構，以及什麼行為不得改變。

### 新增需求

新增需求以 observable behavior 為中心：

- change motivation
- user-visible behavior
- domain impact
- architecture impact
- acceptance scenarios
- vertical delivery tasks

若不改變 architecture boundary，就不需要為了形式建立新的 HLD。

### Bug Fix

小型 bug 可以使用單一 change artifact：

```text
Problem
Reproduction
Expected vs Actual
Impact
Root Cause
Fix Boundary
Regression Scenarios
Validation Evidence
```

Bug fix 不應被迫建立完整 PRD。若 root cause 揭露長期 architecture 問題或需要改變既有 decision，才增加 HLD、LLD 或 ADR。

### 系統優化

Optimization 必須以可重複量測的 baseline 與 target 為核心，不能只寫「改善效能」：

```text
Baseline: P95 850 ms
Target: P95 <= 400 ms
Dataset: 10k transactions
Constraint: memory increase <= 10%
```

至少包含：

- measurement environment
- baseline
- bottleneck evidence
- hypothesis
- proposed change
- target
- guardrail metrics
- result and interpretation

### 研究設計

Research 的完成不一定代表進入 implementation。它的完成條件可以是：

- research question 被回答
- alternatives 被比較
- assumptions 被驗證或否定
- prototype / experiment 已執行
- recommendation 與 confidence 已記錄
- remaining uncertainty 已明確列出

研究結論若形成長期技術決策，再建立或更新 ADR。

## 標準工作流與 Quality Gates

### G0：Intake Ready

進入正式定義前，必須知道：

- work type
- problem / opportunity
- desired outcome
- scope / non-goals
- constraints
- known unknowns
- size / risk

不知道的內容標示為 `unknown`，AI 不得自行補成 fact。

### G1：Definition Ready

需求定義完成時必須符合：

- 每項 requirement 具有唯一 ID。
- 每項 requirement 可觀察或可驗證。
- Business rules 與 implementation 分開。
- Scope 與 non-goals 明確。
- 重要 behavior 有 example、scenario 或 decision table。
- Assumptions、decisions 與 unknowns 有明確區分。
- 沒有未處理的 blocking question。

### G2：Design Ready

設計完成時必須符合：

- System / component boundaries 明確。
- Data ownership 明確。
- Happy path、failure path 與 retry behavior 已定義。
- Security、consistency、performance 等適用 NFR 已處理。
- 重大 trade-off 有 ADR。
- LLD 只處理真正複雜的部分。
- Diagrams 與文字、contracts 一致。

### G3：Plan Ready

規劃完成時必須符合：

- Task 是 vertical slice 或可驗證 deliverable。
- Dependency 只有一個 source of truth。
- 每個 task 對應 requirement / behavior IDs。
- 每個 task 有明確完成 evidence。
- Task scope 適合獨立實作與 review。
- 不以「完成 frontend」或「完成 backend」作為沒有 observable outcome 的孤立 task。

### G4：Implementation Complete

Implementation 完成時必須符合：

- Code、tests 與 executable contracts 同步。
- Task-specific validation 通過。
- 沒有 placeholder 或隱藏的 scope change。
- 新的 architecture decision 已更新 ADR。
- 新的 domain rule 已更新 Domain Spec。
- Implementation 與 approved design 的差異已記錄。

### G5：Verified

Verification 完成時必須符合：

- Requirement → behavior → test → evidence 可追蹤。
- Required regression 通過。
- NFR target 有實際量測。
- Migration、rollback、deployment 依風險完成驗證。
- Manual verification 有具體 evidence，不只記錄「已測試」。
- Remaining limitations 與 deferred work 已明確記錄。

### G6：Closed

Change 關閉時：

- Durable product behavior 提升到 Product / Domain Spec。
- Durable architecture 提升到 System Design。
- Long-term technical decisions 提升到 ADR。
- Current API / data model 由 executable contracts 表達。
- Implementation history 與 delivery evidence 保留在 change。
- 不將整份 Task 或 LLD 複製回長期文件。

## AI 協作的一致性協議

### 95% 一致性的定義

95% 一致性不代表不同 project 產生相同業務內容，而是：

- 章節結構一致。
- 名詞定義一致。
- 推理順序一致。
- Artifact selection 一致。
- 相同情況使用相同深度。
- Completion criteria 一致。
- 同樣輸入會得到相近的文件邊界與涵蓋範圍。

業務事實與 project-specific decisions 是合理的差異來源；文件缺章、概念混用、設計深度隨機則不是。

### 固定生成順序

AI 每次都依下列順序處理：

```text
1. Classify work
2. Extract facts
3. Separate facts / decisions / assumptions / proposals / unknowns
4. Select artifacts
5. Draft requirements
6. Draft behaviors
7. Draft design
8. Split tasks
9. Build traceability
10. Run quality review
```

不得跳過需求與 artifact routing，直接從不完整資訊產生 LLD 或 tasks。

### 資訊狀態分類

每項尚未成為 executable truth 的重要內容應能分類為：

| State | Definition |
| --- | --- |
| `fact` | 已由 User、現有系統或可信 evidence 確認 |
| `decision` | 已明確接受的選擇 |
| `assumption` | 暫時成立、仍需驗證的前提 |
| `proposal` | 尚未接受的建議方案 |
| `unknown` | 目前沒有足夠資訊回答 |

AI 不得將 assumption、proposal 或 unknown 寫成 fact。

### Requirement Contract

Requirement 使用固定語法：

```yaml
id: REQ-xxx
statement: 系統必須……
rationale: 為什麼需要
priority: must | should | could
verification: test | inspection | measurement | demonstration
source: user | domain | regulation | technical-constraint
```

高品質 requirement 必須：

- 只有一個主要 obligation。
- 使用明確 actor 或 system subject。
- 描述 observable outcome 或 invariant。
- 不混入未定案 implementation。
- 可以對應至少一種 verification method。

### Traceability Contract

重要需求應能追蹤到行為、設計、task、test 與 evidence：

```text
REQ-014
→ SCN-007
→ DESIGN-003
→ TASK-021
→ TEST-E2E-012
→ CI / verification evidence
```

不是每個 implementation detail 都需要完整 trace chain，但所有 `must` requirement 與 high-risk behavior 必須具備。

Task status 只表示執行狀態，不能取代 traceability 或 verification evidence。

## 高品質文件規則

### 每個章節只回答一種問題

| Section | Question |
| --- | --- |
| Goal / Motivation | 為什麼要做？ |
| Requirement | 必須發生什麼？ |
| Behavior | 外部可以觀察到什麼？ |
| Design | 如何實現？ |
| Task | 要交付什麼？ |
| Verification | 如何證明完成？ |

不要在 Requirement 中加入 class 或 file design，也不要在 LLD 中重新描述完整 business requirements。

### 明確與可驗證

不佳：

> 系統應妥善處理錯誤。

較佳：

> 當 recurring apply 中任一 rule 不適用於指定月份時，系統必須拒絕整個 request，且不得建立 target record、occurrence 或 audit row。

不佳：

> 改善系統效能。

較佳：

> 在指定的 10k transaction dataset 與相同執行環境下，report endpoint 的 P95 latency 必須由 baseline 850 ms 降至 400 ms 以下，且 peak memory 不得增加超過 10%。

### 避免冗餘

- 引用 source，不複製 source。
- Task 不重述 HLD。
- LLD 不重述 PRD。
- ADR 不重述完整 implementation plan。
- Verification 不重述 requirement，只記錄 requirement ID、方法與結果。
- 可由 code 或工具準確產生的資訊，不人工維護第二份完整版本。

### 使用 Controlled Vocabulary

Status、priority、work type、risk 與 verification method 應使用固定 enum，避免同義詞造成不一致。例如 task lifecycle 不同時使用 `doing`、`in progress`、`implementing` 表達相同狀態。

## 圖表選擇規則

圖表只有在能比文字更清楚表達關係時才使用。

| 要表達的關係 | 建議圖表 |
| --- | --- |
| 系統與外部 actors | Context diagram |
| Runtime components 與責任 | Container / component diagram |
| 跨三個以上 participants 的 operation | Sequence diagram |
| 三個以上有意義的 states | State diagram |
| Data entities 與 relationships | ERD |
| 複雜條件組合 | Decision table |
| Data transformation pipeline | Flowchart |
| Task dependencies | DAG / flowchart |

圖表必須遵守：

- 一張圖只回答一個主要問題。
- 圖中的名稱與文件、contracts、code terminology 一致。
- 圖後補充重要 success、failure、retry 或 state semantics。
- 不建立包含整個 project 所有 details 的巨型圖。
- 如果兩三句文字更清楚，就不建立圖表。

## Task 切分規則

### 優先使用 Vertical Slice

Task 優先交付一個可觀察、可驗證的結果，例如：

```text
使用者可以建立 recurring rule，並在指定月份安全地 apply
```

而不是拆成互相沒有獨立價值的：

```text
完成 database
完成 backend
完成 frontend
```

必要的 infrastructure 或 foundation task 可以獨立存在，但必須有明確 consumer、exit criteria 與不過度延伸的 scope。

### Task 最小內容

- goal / observable outcome
- in scope / out of scope
- `depends_on`
- affected components
- requirement / behavior references
- task-specific tests
- deliverables

不重複保存：

- 反向推導即可得到的 `blocks`
- 全 project 通用 validation commands
- 已在 HLD / LLD 定義的完整設計
- 沒有實質內容、只為符合模板而存在的段落

### Task 大小

一個 task 應：

- 可以獨立實作與 review。
- 有單一主要 outcome。
- 不需要跨越多個不相關 domain concerns。
- 有明確 validation boundary。
- 完成後不留下未定義的必要 layer。

## Verification 與 Definition of Done

Definition of Done 應盡可能由 automation 判定：

- Requirement 對應 tests。
- Required checks 通過。
- Schema / contracts 與 implementation 一致。
- Document links 有效。
- Task status 與 acceptance evidence 一致。
- Staging / production evidence 有保存。

Verification evidence 的強度依序為：

```text
Automated executable test
→ deterministic command output
→ measured benchmark / reconciliation report
→ structured manual evidence
→ unsupported assertion
```

應優先使用較強的 evidence。無法自動化時，manual verification 必須記錄環境、步驟、預期、實際結果與 evidence location。

## 建議的標準目錄模型

```text
docs/
├── product/
│   ├── product-brief.md
│   └── roadmap.md
├── domain/
│   ├── glossary.md
│   └── rules.md
├── architecture/
│   ├── system-overview.md
│   └── adr/
├── standards/
│   ├── workflow.md
│   ├── artifact-routing.md
│   └── definition-of-done.md
└── operations/

changes/
└── <change-id>/
    ├── CHANGE.md
    ├── BEHAVIOR.md       # conditional
    ├── DESIGN.md         # conditional HLD / LLD
    ├── TASKS.md          # 或獨立 TASK files
    └── VERIFICATION.md
```

小型 change 可以只使用一份 `CHANGE.md`，但仍遵守相同的 section contracts。大型 change 才將 Behavior、Design、Tasks 與 Verification 拆成獨立檔案。

## 對目前 Repository 方法論的評價

目前 repository 已經接近一套成熟流程的中後段：

- `docs/` 與 `changes/` 的 durable truth / change delta 分界正確。
- ADR 能保存長期 architecture decisions。
- Phase gates 能表達 delivery progression。
- Vertical slices 比 horizontal layer tasks 更接近可驗證價值。
- Acceptance criteria、validation commands 與 test layering 已建立。
- LLD template 已意識到 requirements、ADR、schema 與 tests 不應互相複製。

需要補上的不是更多 implementation 文件，而是統一控制層：

```text
Work classification
→ Artifact routing
→ Content contracts
→ Quality gates
→ Traceability
```

目前的 `Phase` 概念適合 migration 與 deployment progression，但不適合作為所有工作類型的最高層抽象。通用工作流應以 `Change` 為主要單位，Phase 只是大型 change、release 或 rollout 的可選 grouping。

如此，同一套方法才能自然涵蓋：

- 初次產品開發
- 系統重構
- 新增功能
- Bug fix
- 系統優化
- 研究與技術評估

## 最終原則

最終要標準化的不是「每次都產生同一批文件」，而是：

> 對相同類型、規模與風險的工作，每次都能用相同規則選出相同 artifacts，使用相同結構完成需求、設計、執行與驗證。

高品質工作流的衡量方式不是文件數量，而是：

- 任何重要資訊都能找到唯一 owner。
- User 與 AI 對 facts、decisions、assumptions 和 unknowns 有共同理解。
- Requirements、behaviors、design、tasks 與 evidence 可以追蹤。
- 不同工作類型共用相同 process kernel，但不被迫產生不必要 artifacts。
- 同樣的輸入條件可以穩定產生結構與深度高度一致的結果。
- 文件能支持實作與決策，而不是增加維護成本。
