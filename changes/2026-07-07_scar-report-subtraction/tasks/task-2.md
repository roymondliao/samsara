# Task 2: scar-schema.yaml 重寫為一頁寫入契約＋scar-report.md 同步＋anti-dup death test

## Context

Read: overview.md（Core Identity、seam: scar-write-contract、Key Decisions D1/D2 數值/D4/D5）

scar-schema.yaml 現為 205 行、17 條編號規則＋立法史，全文被逐字注入每次 implementer dispatch（dispatch-template.md:38,84）。重寫為**一頁純寫入契約**。compat 讀取規則的新家已由 task-1 建於 `skills/iteration/SKILL.md` Step 1（本 task 可安全刪除 schema 內對應文字）；綁 schema 的 compat 測試已重綁完畢。

新 item 形（known_shortcuts／silent_failure_conditions）：
```yaml
- what: "疤是什麼，一行白話"            # 必填 ≤200 chars
  bites_when: "什麼條件下咬人，一行"     # 必填 ≤200 chars
  where: "file:line 或段落指針"         # 必填 ≤120 chars
  accepted_because: "一行"              # 可選 ≤200 chars
  deferred_to_feature_iteration: false  # 可選（語意同現制）
  status: resolved                      # 可選（in-place resolution，同現制）
  resolution: "一行 ≤200 chars"         # status: resolved 時必填
- systemic_ref: <id>                    # 同現制
  note: "本 task 落點一行"
```
`assumptions_made` 保三欄（assumption/verified/note=pointer ≤200）。`structural_decisions` **一字不動**（欄位名、dual-face、granularity floor、forced_by 規範全保留）。

## Files

- Modify: `skills/implement/templates/scar-schema.yaml`（全檔重寫）
- Modify: `skills/implement/scar-report.md`（引用同步）
- Test: `tests/test_skills/test_scar_schema_noise_rules.py`（新增 anti-dup death test）

## Death Test Requirements

- Test: anti-duplication — schema 若再含 compat 規則 token（"plain string format backward compatibility"、"missing deferred flag = false" 等，逐字比對，沿 eb4ae07 anti-dup test 先例）→ 紅。compat 單一源 = iteration Step 1
- Test: schema 必含新槽位欄位宣告 token（`what:`、`bites_when:`、`where:`、`accepted_because:`）與預算表數值（`≤90`／`≤6`／`≤200`）— 防未來刪節
- Test: schema 保留 write-side 承重 token（Lens A 釘住項）："write filter"＋"future reader"＋"change their action"；"granularity floor"＋"structural bet"＋literal `structural_decisions: []`；"existed at decision time"＋"post-hoc"；"single line"＋"file:line"／"test name"；`status:\s*resolved` regex＋"resolution"；"review-round"／"round-by-round"（no-review-diary）— 既有測試（重寫後仍讀 schema 的部分）必須保綠

## Unit Test Contract

- Contract source: `skills/implement/templates/scar-schema.yaml` 的 documented artifact shape（寫入契約成文內容）— 概念 token 斷言；以及 `tests/test_skills/test_global_thinking_channel.py:204-233` 既有釘點（structural_decisions 五欄位名）保綠
- A unit test must assert this named contract source, not implementation details.

## Implementation Steps

- [ ] Step 1: 寫 death tests（anti-dup、槽位宣告、預算表存在）
- [ ] Step 2: 跑 death tests — 確認紅
- [ ] Step 3: 重寫 schema 為一頁結構：(a) 新 item 形模板（上方 Context 所示）＋assumptions/structural_decisions 現制；(b) 具名錨點行內規則：`# write-filter:`（原R1+R13）、`# verified-pointer:`（原R10）、`# no-review-diary:`（原R12）、`# granularity-floor:`（原R15）、`# dual-face:`（原R16）、`# forced-by-evidence:`（原R17）、`# systemic-ref:`（寫入側用法，resolution 指向 iteration Step 1）；(c) 預算表（欄位≤200/where≤120、item≤6行、structural entry≤10行、narrative≤10行、report≤90行 — 與 task-3 validator 同值）；(d) 去別處對照表（review 裁決史→review-record.md；驗證過程→transition record/測試名；before/after 統計→commit message；跨 feature 事實→systemic_ref）；(e) 新格式短例 8–12 行。刪除：Rules 編號清單、compat 規則文字、232 行舊 Verbatim Example
- [ ] Step 4: 同步 scar-report.md（Rule 13/12 引用改具名錨點 write-filter／no-review-diary；其餘指引不變）
- [ ] Step 5: 實作至全綠（含 test_global_thinking_channel.py、重綁後的 noise-rules 全部）
- [ ] Step 6: `uv run pytest tests/` 全綠
- [ ] Step 7: 寫 scar report — **本 task 起用新槽位格式**（自我示範；validator 預算檢查 task-3 才上線，先以人工遵守預算）
- [ ] Step 8: Report back（不 commit）

## Expected Scar Report Items

- Potential shortcut: 去別處對照表的目的地（review-record.md 等）只是指引，無機器驗證內容真的去了那裡 — doc-vs-runtime-obedience 系譜，可考慮 systemic_ref
- Assumption to verify: dispatch-template.md 的注入指示（paste full content）在 schema 縮短後語意不變、無需改動
- Assumption to verify: 刪掉的 17 條規則中沒有任何一條的「寫入側語意」被遺漏（逐條對照：保留/遷移/刪除三分類清單放進 scar 或 narrative ≤10 行內）

## Acceptance Criteria

- Covers: "Silent failure - compat rules regrow inside scar-schema.yaml"
- Covers: "Success - clean slot-form report validates clean"（格式宣告面）
