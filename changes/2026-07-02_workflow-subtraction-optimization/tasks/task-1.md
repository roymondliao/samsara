# Task 1: Scar 產出瘦身 — schema 噪音規則 + systemic registry + implementer 報告格式

## Context

Read: overview.md

現況問題（實測）：73 份 scar 共 8,239 行（平均 ~113 行）。噪音四來源：(1) 系統性事實（如「doc-presence ≠ runtime obedience」）跨 feature 全文重述；(2) `verified: true` 的 assumptions 附長 note，但下游 signal_lost 只計 `verified: false`；(3) `resolved_items` 把原 item 描述完整重抄；(4) `narrative` 淪為 review 輪次流水帳。此外 `agents/implementer.md` 的 Report Format 要求 scar YAML、self-iteration summary、self-review findings 三處重疊——只改 schema 不改報告格式，膨脹會換地方再生。

## Files

- Create: `.samsara/systemic-scars.yaml` — 登記檔，schema：`id`（kebab-case）、`description`、`first_recorded`（ISO date）、`applies_when`（何種 task 會命中）。預填兩條：`doc-vs-runtime-obedience`（doc-presence 測試無法證明 agent runtime 服從）、`doc-instruction-no-code-enforcement`（doc 指令無 code 層強制，服從依賴 agent 遵循）。檔頭註明：寫入時機為 Level 2 iteration 或 validate-and-ship 認定某 item 屬跨 feature 結構性事實時。
- Modify: `skills/implement/templates/scar-schema.yaml` — 新增規則（沿用既有 Rules 區塊編號續寫）：
  - `systemic_ref: <id>` item 形式：只寫 ref ＋一行本 task 的具體落點，禁止重抄 registry 描述；懸空 ref（id 不在 registry）＝ parse failure。
  - `verified: true` 的 assumption 壓縮為單行：`assumption` ＋ `note` 只放證據指標（file:line／測試名），禁長篇敘述。
  - 取消 `resolved_items` 重抄：改為在原 item 上加 `status: resolved` ＋ 一行 `resolution`。讀取端向後相容：舊 scar 的 `resolved_items` 仍有效。
  - `narrative` 追加禁令：禁止 review 輪次流水帳（「Round N 修了什麼」屬 review 流程史，不是 code 的傷）；只寫結構化欄位裝不下的傷疤脈絡。
  - 新增寫入過濾問句：每個 item 寫入前問「這條被未來讀者讀到時，會改變他的行動嗎？」不會 → 不寫。
- Modify: `skills/implement/scar-report.md` — 同步格式指南；Anti-Pattern 區加「review 流水帳 narrative」。
- Modify: `skills/implement/dispatch-template.md` — schema 注入段若複述舊規則，同步。
- Modify: `agents/implementer.md` — Report Format 段去重複：scar YAML 是唯一傷疤載體；Self-iteration summary 只報數字（resolved/deferred/remaining counts）；Self-review findings 只列「未寫入 scar 的新發現」；加入上述寫入過濾問句。不得刪除 STEP 0、death test 順序、scar report 必要性等既有約束。
- Modify: `skills/iteration/SKILL.md` — Step 1 聚合段：`systemic_ref` item 對 registry 解析；懸空 ref 列入既有 parse-failure 處理（明列檔名＋id，不靜默略過）；registry 檔缺失時全部 systemic_ref 標 unknown 並過 gate。`status: resolved` 與舊 `resolved_items` 皆視為已解。
- Test: `tests/test_skills/test_scar_schema_noise_rules.py`（新）

## Death Test Requirements

- Test: scar-schema.yaml 缺「懸空 systemic_ref ＝ parse failure」條款時轉紅（防規則被靜默刪除）
- Test: iteration SKILL.md 聚合段缺「registry 缺失 → unknown 不准靜默略過」條款時轉紅
- Test: scar-schema.yaml 的 backward-compat 條款（plain string、缺 flag、舊 resolved_items）被刪除時轉紅（DC3：舊 scar 聚合靜默歸零）
- Test: implementer.md 被過度刪除時轉紅——STEP 0 四問、death-test-first 順序、scar report 必要性三者任一消失即紅（防減法誤殺守護）

## Unit Test Contract

- Contract source: 文件化 artifact shape——`scar-schema.yaml` 的 Rules 區塊、`.samsara/systemic-scars.yaml` 的欄位結構（id/description/first_recorded/applies_when）、`agents/implementer.md` 的 Report Format 段落與 `skills/iteration/SKILL.md` 聚合段的條款文字（concept-token 斷言，遵循 references/test-contract.md 的 self-exemplar 規則：斷言概念不斷言整句，honest rewrite 後仍綠）
- A unit test must assert this named contract source, not implementation details.

## Implementation Steps

- [ ] Step 1: Write death tests
- [ ] Step 2: Run death tests — verify they fail
- [ ] Step 3: Write unit tests asserting the named Unit Test Contract source
- [ ] Step 4: Run unit tests — verify they fail
- [ ] Step 5: Implement minimal doc/schema changes to pass all tests
- [ ] Step 6: Run all tests — verify they pass
- [ ] Step 7: Write scar report（用本 task 剛落地的新規則寫——本 task 的 scar 是新格式的第一個 dogfood）
- [ ] Step 8: Report back (do not commit)

## Expected Scar Report Items

- Potential shortcut: 新規則只能約束文件層，implementer 是否照辦屬 runtime 服從（正好以 `systemic_ref: doc-vs-runtime-obedience` 引用——驗證引用機制）
- Assumption to verify: 既有 doc-contract 測試沒有斷言舊 `resolved_items` 措辭（若有，需同步而非刪除）
- Assumption to verify: dispatch-template.md 的 schema 注入方式（全文貼 vs 指路徑）——全文貼則新版 schema 自動生效

## Acceptance Criteria

- Covers: "Silent failure - 舊格式 scar 聚合靜默歸零"
- Covers: "Silent failure - systemic_ref 懸空"
