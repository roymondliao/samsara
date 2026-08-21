# Plan: scar-report-subtraction

Execution mode: auto

## Pre-thinking Commitments Consumed

- **Decision:** Proceed（decision-003）
- **Accepted gaps:** none
- **System design constraints（pre-thinking Step 4，本 plan 引用不重推導）:**
  - D1 定長槽位取代 description blob（新寫入）；`assumptions_made` 保三欄；`structural_decisions` 不動
  - D2 預算住 validate_format.py，超標 = finding；數值由本 plan 校準（見下）
  - D3 schema = 純寫入契約；compat 讀取規則 canonical home 移至 iteration SKILL.md Step 1
  - D4 廢規則編號 → 具名錨點；跨檔引用同批 sweep（gatekeeper 實測 ~14 行 / 5 檔）
  - D5 narrative 保留，≤10 行
  - D6 世代識別用欄位形狀推斷，不加 schema_version；舊 report 不遷移
- **L1（core identity + real seams）:** 已逐字複製至 overview.md（Core Identity、Real Seams）
- **Primary evaluator:** `uv run pytest tests/` 全綠（含新 length-budget 行為測試、重綁 compat death tests、新槽位解析測試）— decision-002
- **Pass signal:** 全套件 0 failed；新測試能對 over-budget／舊格式 fixture 轉紅
- **Fail signal:** 任何 failed/error；新檢查誤傷既有 clean fixtures
- **Feedback loop:** 先分類 finding 是「檢查錯」還是「文件/fixture 未同步」；重綁類失敗改測試綁定側，行為類失敗改 validator

## Technical Specification

### 1. 新寫入契約（scar-schema.yaml 重寫為一頁）

新 item 形（`known_shortcuts`、`silent_failure_conditions`）：

```yaml
known_shortcuts:
  - what: "疤是什麼，一行白話"                 # 必填, ≤200 chars
    bites_when: "什麼條件下咬人，一行"          # 必填, ≤200 chars
    where: "file:line 或段落指針"              # 必填, ≤120 chars
    accepted_because: "為何接受，一行"          # 可選, ≤200 chars
    deferred_to_feature_iteration: false       # 可選，同現制
    status: resolved                           # 可選，同現制（in-place resolution）
    resolution: "一行"                         # status: resolved 時必填, ≤200 chars
  - systemic_ref: <id>                         # 同現制，note 一行
    note: "本 task 落點一行"
```

`assumptions_made` 保持 assumption/verified/note（note = pointer，≤200 chars）。`structural_decisions` 欄位完全不動（測試釘住、reviewer 消費中）。

保留在 schema 的寫入側規則，以**具名錨點**行內化（不再有 Rules 1–17 編號清單）：
- `# write-filter:` 未來讀者不會因此改變行動就不寫（原 Rule 13）
- `# no-empty-scar:` 全空清單 = 沒想夠（原 Rule 1）
- `# granularity-floor:` structural bet 才留 entry；`structural_decisions: []` = 檢查過無 bet（原 Rule 15，錨點文字保留 Lens A 釘住的 token："granularity floor"、"structural bet"、literal `structural_decisions: []`）
- `# dual-face:` / `# forced-by-evidence:` 原 Rule 16/17（保留 token："existed at decision time"、"post-hoc"）
- `# verified-pointer:` verified: true 的 note 只能是指針（原 Rule 10）
- `# no-review-diary:` narrative 不裝 review 輪次史（原 Rule 12）
- **去別處對照表**（新增，一張小表）：review 裁決史 → review-record.md；驗證過程/測試計數 → transition record 或測試名指針；before/after 統計 → commit message；跨 feature 重複事實 → systemic_ref
- **預算表**（新增，與 validator 數值同源；validator 是執行者，表是宣告）

**移出 schema 的內容**：Rules 7/8/9(resolution 半段)/11(相容半段)/14（讀取相容規則）→ iteration SKILL.md Step 1；Verbatim Example 縮為新格式 8–12 行短例。

### 2. 預算數值（residual #1 校準）

校準依據：近 5 個 feature 25 份 report 實測 — 條目數中位數 10、有效最大 14–16（排除 resolved_items 舊制重複計數，新制 in-place 吸收）。算術：中位 10 條 × 4 行 + 標頭 ≈ 50–60 行（North Star 中位 ≤60 自然可達）；重尾 14 條 × 平均 4 行 + 標頭 10 + narrative 10 ≈ 76，仍在 90 內；**絕對最壞**（14 條全頂 6 行上限 + 標頭 10 + narrative 10）= 104 > 90 —— 這是刻意的：90 上限就是要對病態尾端施加壓縮力，該情境的出路是去別處對照表分流、systemic_ref 去重、或 task 本身該再拆分。若 golden re-expression（task-5）實證 90 裝不下誠實內容，走 kill condition #3 重校準路徑上修並記錄。

| 預算 | 值 | finding 條件 |
|---|---|---|
| 槽位純量欄位 | ≤200 chars（where ≤120） | 任一欄超標 |
| 單 item（shortcuts/silent/assumptions） | ≤6 實體行 | 超標 |
| 單 structural_decisions entry | ≤10 實體行 | 超標 |
| narrative | ≤10 實體行 | 超標 |
| 整份 report | ≤90 實體行 | 超標 |

North Star 的「中位數 ≤60」是結果指標（validate-and-ship 觀測），不是 validator 上限。kill condition #3 的重校準路徑保留：golden re-expression（task-5）若證明誠實內容裝不下，數值上修並記錄。

### 3. validate_format.py 擴充

新 finding 類（沿用現有 `FINDING <class>: <msg>` 語彙與 exit code 慣例 0/1/2）：
- `length-budget:` 上表五類超標，訊息含實測值與上限
- `legacy-form:` 新 report 的 shortcuts/silent 條目使用 `description` 自由文本或 plain string —— **封死預算逃逸路徑**（validator 只在新 feature handoff 執行（A6），故可嚴格）；`systemic_ref` 條目除外
- 新槽位解析：`what`/`bites_when`/`where` 必填缺一 = finding（同 dual-face 檢查風格）

I/O 三態（沿用現制）：exit 0 = success（clean）、exit 1 = failure（findings）、exit 2 = unknown（cannot validate — 缺 PyYAML／目錄不存在）。unknown 永不當 pass（implement SKILL.md 既有措辭已涵蓋）。

### 4. Compat 讀取契約（iteration SKILL.md Step 1 canonical home）

Step 1 新增「Scar 格式世代」小節：三代識別（plain string → 最舊；`description` dict → 第二代；`what`/`bites_when` → 第三代）；三代條目一律計入 signal_lost；deferred/resolved/systemic_ref 語意跨代一致。原 schema Rules 7/8/11/14 的讀取語句遷入此處（保留 Lens A 釘住 token："missing deferred flag = false"、"plain string format backward compatibility" 等——重綁後 token 住這裡）。

### 5. 引用 sweep（D4）

5 檔 ~14 行（agents/implementer.md:144,184,208,255-256；skills/iteration/SKILL.md:77,80；skills/implement/SKILL.md:184；skills/implement/scar-report.md:19,26；skills/implement/scripts/validate_format.py:29,170 等）— 全部 `grep -rn 'Rule [0-9]'` 全量掃描後改為具名錨點引用。新增 death test：live surfaces（skills/、agents/）不得再出現對 scar-schema 的數字規則引用。

### 6. Golden re-expression（decision-002 附帶義務）

`changes/2026-07-02_workflow-subtraction-optimization/scar-reports/task-4-scar.yaml`（232 行）以第三代格式重寫為測試 fixture `tests/fixtures/scar_reports/golden_task4_slot_form.yaml`＋誠實無損對照 `changes/2026-07-07_scar-report-subtraction/golden-re-expression.md`（每條舊內容 → 新槽位或去別處目的地）。fixture 必須過 validator clean（含預算）且行數 ≤90 —— 這是 kill condition #3 的實證。

### Death Cases（非 edge cases）

| # | 觸發 | 表象（謊言） | 實情 | 偵測 |
|---|---|---|---|---|
| DC-A | 寫作者用 `description` blob 或 plain string 逃逸預算 | report「有寫、validator 綠」 | 預算被繞過，冗長回歸 | `legacy-form` finding（death test：blob fixture 必紅） |
| DC-B | aggregator 誤判第三代欄位形狀 | 聚合「完成」 | 新格式 items 被靜默丟出 signal_lost | 三代混合 fixture 聚合測試：計數必須等於實際 items |
| DC-C | compat 規則在 schema 與 iteration 兩處並存（漂移開端） | 重綁測試綠（token 兩處都在） | 單一源破裂，兩處各自演化 | anti-duplication death test：schema 不得再含 compat token（沿 eb4ae07 anti-dup test 先例） |
| DC-D | sweep 漏掉第 6 處數字規則引用 | 文件「看起來一致」 | 引用指向已不存在的編號 → 讀者跟丟 | death test：grep live surfaces 無 `scar-schema` 數字規則引用 |
| DC-E | 預算計數實作對 folded scalar（`>`）行數計錯 | over-budget report 過 validator | 預算名存實亡 | death test：folded 長欄位 fixture 必紅（char cap 兜底行數計法差異） |

## File Map Consistency Check

Placement/ownership Key Decisions 對照：
- 「schema 留在 skills/implement/templates/ 作單一寫入源」→ File Map 改寫該檔於原位 — **matches**
- 「compat canonical home = skills/iteration/SKILL.md Step 1」→ File Map 修改該檔 — **matches**
- 「預算執行者 = skills/implement/scripts/validate_format.py」→ File Map 修改該檔 — **matches**
- 「golden fixture 供測試消費」→ 置於 tests/fixtures/scar_reports/（由 Primary evaluator 推導：測試必須能讀）— **matches**
- D2/D5/D6（數值、narrative、世代推斷）不約束路徑 — **out of scope**

無 contradicts → 通過，進入分解。

## Task Summary（分解見 tasks/）

| task | 內容 | seam | depends_on |
|---|---|---|---|
| 1 | compat 讀取契約遷入 iteration Step 1＋noise-rules 測試重綁（iteration 側先行，schema 未動全程綠） | write-read-boundary | — |
| 2 | scar-schema.yaml 重寫為一頁寫入契約＋scar-report.md 同步＋anti-dup death test | scar-write-contract | 1 |
| 3 | validate_format.py 預算/legacy-form/槽位檢查＋行為測試 | format-vs-judgment | 2 |
| 4 | 數字規則引用全量 sweep → 具名錨點＋dangling-citation death test | scar-write-contract | 1, 2 |
| 5 | golden re-expression fixture＋誠實對照＋三代混合聚合測試 | write-read-boundary | 2, 3 |
| 6 | dist/ regenerate（codex/gemini byte-copy 更新）＋全套件整合驗證 | scar-write-contract | 1–5 |

## 本 plan 的假設（顯式）

- 本實作假設：validate_format.py 是新 report 唯一 handoff gate（A3/A6）。若不成立（fast-track 產 scar 不經 gate），預算對該路徑無牙 —— 已記錄為已知邊界（pre-thinking residual #4），不在本 feature 解。
- 本實作在以下條件下會靜默失敗：具名錨點被改名而跨檔引用未同步（頻率低於編號制但非零，DC-D 的 death test 只擋數字引用，不擋錨點改名）—— 記入 task-4 expected scars。
