# Task 4: Auto Mode Gate 去重 — canonical 入 references/auto-mode.md，6 skills 留指針

## Context

Read: overview.md

現況：6 個 workflow skill（research、pre-thinking、planning、implement、iteration、validate-and-ship；security-privacy-review 已折入 validate-and-ship）各有一段 21–40 行的 `## Auto Mode Gate`，內容 80%+ 相同：dispatch `samsara:auto-gatekeeper` → append-only 寫入 `auto-decisions.md` → 依 proceed/revise/reject/accept_gap 行動。`references/auto-mode.md` 已是 canonical schema，但通用「gate 執行協議」散在各 skill 重複。implementer.md 自己寫著「restatement is itself DRY rot」。

去重契約：
- **canonical（一處）**：references/auto-mode.md 新增 `## Stage Gate Protocol` 段——dispatch 方式（`subagent_type: "samsara:auto-gatekeeper"`）、append-before-continue、entry 必填欄位引用既有 schema、四個 decision 值的通用語義與行動。
- **指針（各 skill ≤8 行）**：每個 skill 的 Auto Mode Gate 只留：(1) 指向 references/auto-mode.md Stage Gate Protocol；(2) 本階段的 `workflow_prompt` 來源（哪個原始 prompt）；(3) 本階段 gate 覆蓋的決策點清單；(4) 本階段特異行為 inline 保留。
- **階段特異行為必須 inline 保留**（不得被去重吸走）：validate-and-ship 的「最終決策前後雙重 decision-trace 檢查」與「security unknown/absent/failing → 高不確定 reject」；iteration 的「gate 覆蓋 triage／blocked-fix／round 續行／safety valve 全部決策點」清單；implement 的「execution strategy 也過 gate」。

## Files

- Modify: `references/auto-mode.md` — 新增 `## Stage Gate Protocol` 段（通用協議收攏一處；不重抄 Required Fields，引用之）
- Modify: `skills/research/SKILL.md`、`skills/pre-thinking/SKILL.md`、`skills/planning/SKILL.md`、`skills/implement/SKILL.md`、`skills/iteration/SKILL.md`、`skills/validate-and-ship/SKILL.md` — Auto Mode Gate 段替換為指針格式（特異行為 inline）
- Modify: `tests/test_auto_mode/test_protocol_helpers.py` — section 讀取邏輯適配指針格式
- Modify: `tests/test_auto_mode/test_skill_auto_mode_protocol.py` — 各 skill 斷言改為：指針段存在、指向 references/auto-mode.md、含本階段 workflow_prompt 來源與決策點清單；canonical 完整性斷言移到對 references/auto-mode.md 的測試（proceed/revise/reject/accept_gap、append-only、subagent_type 全在 canonical）
- Modify: `tests/test_auto_mode/test_skill_auto_mode_protocol_death.py` — 特異行為 inline 斷言（validate-and-ship 雙重 trace、iteration 全決策點、implement execution strategy）；**新增反重複 death test**：任一 skill 的 Gate 段若重新內嵌四個 decision 值的完整定義（重複 canonical）轉紅——這是防止重複悄悄長回來的結構壓力
- Modify: `tests/test_auto_mode/test_auto_mode_docs_death.py` — 若斷言各 skill 全文協議，改指 canonical

## Death Test Requirements

- Test: references/auto-mode.md 的 Stage Gate Protocol 缺四個 decision 值任一的語義時轉紅（canonical 不完整＝所有 skill 同時失去定義）
- Test: validate-and-ship 指針段缺「雙重 decision-trace 檢查」inline 條款時轉紅（DC2）
- Test: iteration 指針段缺「gate 覆蓋全部決策點（triage/blocked-fix/round/safety）」清單時轉紅（DC2）
- Test: 反重複——任一 skill Gate 段重現 canonical 的 decision 定義全文時轉紅（防漂移回九份複本）

## Unit Test Contract

- Contract source: 文件化 artifact shape——references/auto-mode.md 的 Stage Gate Protocol 條款、各 SKILL.md Auto Mode Gate 段的指針結構（指向語＋workflow_prompt 來源＋決策點清單）。concept-token 斷言（heading 改名仍綠、概念消失轉紅），行數上限斷言用行數計數（≤8 行為 stage-2 可觀測條件）
- A unit test must assert this named contract source, not implementation details.

## Implementation Steps

- [ ] Step 1: Write death tests
- [ ] Step 2: Run death tests — verify they fail
- [ ] Step 3: Write unit tests asserting the named Unit Test Contract source
- [ ] Step 4: Run unit tests — verify they fail
- [ ] Step 5: Implement — 先寫 canonical、再逐 skill 指針化、最後改測試斷言目標（改測試是同步斷言目標，不是弱化：每個舊斷言概念在新結構下都要有家）
- [ ] Step 6: Run all tests — verify they pass
- [ ] Step 7: Write scar report
- [ ] Step 8: Report back (do not commit)

## Expected Scar Report Items

- Potential shortcut: 「≤8 行」是形式上限，若某 skill 特異行為多（validate-and-ship）可能達 10–12 行——記錄實際行數與理由，不硬塞
- Assumption to verify: fast-track／debugging／codebase-map 沒有 Auto Mode Gate 段（實測只有 6+1 個 skill 有；若發現遺漏，同規則處理）
- Assumption to verify: auto mode 的既有整合測試（tests/integration/）不依賴各 skill 全文協議字樣
- Potential shortcut: 指針段的資訊密度依賴 agent 真的去讀 references/auto-mode.md——`systemic_ref: doc-vs-runtime-obedience`

## Acceptance Criteria

- Covers: "Silent failure - Gate 去重抹掉階段特異語義"
- Covers: "Silent failure - 搬家假減法"（canonical 增量必須遠小於 skills 減量，計入 stage-2 淨值）
