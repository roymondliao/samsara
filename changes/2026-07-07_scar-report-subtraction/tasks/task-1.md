# Task 1: Compat 讀取契約遷入 iteration Step 1（canonical home）＋ noise-rules 測試重綁

## Context

Read: overview.md（Core Identity、Real Seams: write-read-boundary、Key Decisions D3/D6）

Scar report 即將分三代格式：plain string（最舊）、`description` dict（第二代）、`what`/`bites_when` 槽位（第三代，task-2 引入）。寫入端只見當前格式，讀取端（iteration Step 1 aggregator）讀全歷史 —— 因此 backward-compat 讀取規則的 canonical home 必須在讀取端。本 task 先建新家並把測試重綁過去；**schema 本身一字不動**（刪除由 task-2 做），確保本 task 全程測試綠。先例：schema Rule 9 已宣告 systemic_ref resolution procedure 的 canonical home 在 iteration SKILL.md Step 1（schema 明言 "not restated here"）。

現況：`skills/iteration/SKILL.md:77,80-83` 已重述部分 compat 規則；schema Rules 7/8/11(相容半段)/14 是遷移 source。

## Files

- Modify: `skills/iteration/SKILL.md`（Step 1，:65-103 區域內新增小節）
- Modify: `tests/test_skills/test_scar_schema_noise_rules.py`（:186-210、:248-288 重綁讀取目標）

## Death Test Requirements

- Test: 三代世代識別文字缺任一代（plain string／description dict／槽位形）的識別語句 → doc-contract 測試轉紅（防止未來刪節時靜默丟掉一代的讀取承諾）
- Test: 「三代條目一律計入 signal_lost」承諾語句消失 → 轉紅（DC-B 的文字面防線）
- Test: 既有 :213-245（registry missing → unknown 不靜默丟）與 :604-621（三條 resolution 路徑）在遷移後仍綠 —— 新小節不得破壞既有 Step 1 釘住內容

## Unit Test Contract

- Contract source: `skills/iteration/SKILL.md` Step 1 的成文聚合契約（documented artifact shape）— 概念 token 斷言，沿 `test_scar_schema_noise_rules.py` 自述的「tolerant of rewording, intolerant of concept deletion」風格（:29-32）
- A unit test must assert this named contract source, not implementation details.

## Implementation Steps

- [ ] Step 1: 寫 death tests（上述三條，綁 `skills/iteration/SKILL.md`）
- [ ] Step 2: 跑 death tests — 確認紅（新小節尚不存在）
- [ ] Step 3: 在 iteration SKILL.md Step 1 新增「Scar 格式世代（read-side canonical）」小節：三代識別（欄位形狀推斷，無 schema_version）、三代一律計入 signal_lost、deferred/resolved/systemic_ref 語意跨代一致；把 schema Rules 7/8/11相容半段/14 的讀取語句改寫併入（保留被測試釘住的**全部 6 個 token**，缺一即紅："missing deferred flag = false"、"missing resolved_items = no self-iteration"、"plain string format backward compatibility"、"do not reject or silently skip plain string format items"、"rules 7 and 8 continue to apply unchanged"、"additive"。注意末兩個 token 含規則編號指涉，是**過渡狀態**：本 task 先逐字保留（測試斷言不變），task-4 廢編號時再同步改寫 iteration 端文字與測試斷言為無編號語句 — 本 task 不得自行改寫該 token）
- [ ] Step 4: 重綁 `test_scar_schema_noise_rules.py` :248-288 與 :186-210 中讀 SCAR_SCHEMA 的 compat 斷言 → 改讀 iteration SKILL.md（保持 token 斷言不變；純綁定目標搬移）。注意 :186-210 的 systemic_ref/dangling/parse-failure token 在 schema 寫入側仍會以 systemic_ref 條目形式存在 —— 只搬「讀取解析」語句的綁定，寫入側指引歸 task-2
- [ ] Step 5: 實作至全綠
- [ ] Step 6: `uv run pytest tests/test_skills/ tests/test_agents/` 綠；全套件抽查
- [ ] Step 7: 寫 scar report（本 task 尚用現行 schema 格式 — 新格式 task-2 才生效）
- [ ] Step 8: Report back（不 commit）

## Expected Scar Report Items

- Potential shortcut: 遷入文字與 :77,80-83 既有重述的合併可能留下措辭重複 — 記錄殘留重複點
- Assumption to verify: "rules 7 and 8 continue to apply unchanged" 這句含規則編號的 token 重綁後如何改寫（編號制 task-4 才廢）— 若測試 token 與編號耦合，記錄與 task-4 的交接面
- Assumption to verify: 重綁後 test_scar_schema_noise_rules.py 沒有任何斷言仍讀 SCAR_SCHEMA 的 compat 內容（grep 驗證）

## Acceptance Criteria

- Covers: "Silent failure - third-generation items dropped from aggregation"（文字契約面）
- Covers: "Silent failure - compat rules regrow inside scar-schema.yaml"（前置：新家先立，task-2 的 anti-dup 才有單一源可護）
