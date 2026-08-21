# Task 4: 數字規則引用全量 sweep → 具名錨點＋dangling-citation death test

## Context

Read: overview.md（seam: scar-write-contract、Key Decision D4）

scar-schema.yaml 的 Rule 1–17 編號被跨檔承重引用（已知 5 檔 ~14 行），且無任何機制驗證編號引用有效性。task-2 已廢編號制、改具名錨點（write-filter、verified-pointer、no-review-diary、granularity-floor、dual-face、forced-by-evidence、systemic-ref）。本 task 把所有殘留的數字引用改為具名錨點引用，並立 death test 防回歸。

已知引用點（起點，**不是全集** — 必須全量掃描）：
- `agents/implementer.md:144,184,208,255-256`（Rule 11/13/15-17）
- `skills/implement/SKILL.md:184`（Rule 11/14）
- `skills/iteration/SKILL.md:77,80`（Rule 9/11/14；task-1 遷移後行號已位移，以 grep 為準）
- `skills/implement/scar-report.md:19,26`（Rule 13/12 — task-2 可能已改，驗證之）
- `skills/implement/scripts/validate_format.py:29,170,190`（docstring／finding 訊息內 "schema Rule 15"/"Rule 17" 字樣）

## Files

- Modify: `agents/implementer.md`
- Modify: `skills/implement/SKILL.md`
- Modify: `skills/iteration/SKILL.md`
- Modify: `skills/implement/scar-report.md`（如 task-2 有殘留）
- Modify: `skills/implement/scripts/validate_format.py`（訊息字樣；行為不動）
- Test: `tests/test_skills/test_scar_schema_noise_rules.py`（新增 dangling-citation death test）

## Death Test Requirements

- Test: live surfaces（`skills/`、`agents/`）任何檔案含對 scar schema 的數字規則引用模式（**大小寫不敏感**：`(?i)(schema )?rules? [0-9]`，涵蓋 `Rule 13`、`rules 7 and 8` 等變體）→ 紅，訊息列出檔案與行（DC-D）。排除 `changes/`、`docs/`、`bugfix/`、`dist/`（歷史與生成物）
- Test: sweep 後全量 grep 零殘留（death test 本身就是持續防線）

## Unit Test Contract

- Contract source: live-surface 檔案的 documented artifact shape — 「不含數字規則引用」這一可 grep 的成文事實（同 repo 既有 doc-contract 測試風格）
- A unit test must assert this named contract source, not implementation details.

## Implementation Steps

- [ ] Step 1: 寫 dangling-citation death test
- [ ] Step 2: 跑 — 確認紅（引用仍在）
- [ ] Step 3: `grep -rniE '(schema )?rules? [0-9]' skills/ agents/ --include='*.md' --include='*.py'` 全量清點（**-i 大小寫不敏感** — 必須抓到 task-1 遷入 iteration 的小寫 "rules 7 and 8" 片語；結果數若 > 已知 14 行，逐一納入）。本 step 的清點結果包含該片語時，同步改寫 iteration 端文字與 test_scar_schema_noise_rules.py 的對應 token 斷言為無編號語句（與 task-1 Step 3 的過渡註記交接）
- [ ] Step 4: 逐處改寫為具名錨點引用（如 "scar-schema.yaml Rule 13" → "scar-schema.yaml write-filter"；validate_format.py 的 "schema Rule 15" 訊息 → "schema granularity-floor"）。**只改引用字樣，不改任何行為與周邊語意**
- [ ] Step 5: 同步受影響測試斷言（test_format_validators.py 若有斷言含 "Rule 15" 訊息字樣、noise-rules 的 "rules 7 and 8 continue to apply unchanged" token — 與 task-1 重綁後的措辭協調：該 token 若已在 iteration 端改寫為無編號語句，確認斷言一致）
- [ ] Step 6: `uv run pytest tests/` 全綠
- [ ] Step 7: 寫 scar report（新槽位格式，過 validator）
- [ ] Step 8: Report back（不 commit）

## Expected Scar Report Items

- Potential silent failure: 具名錨點改名而引用未同步 — 本 death test 只擋數字引用，不擋錨點改名（頻率較低但非零；此為 D4 的已接受殘餘風險，寫入 scar）
- Assumption to verify: grep pattern 覆蓋 "Rule"/"Rules"/"rule" 大小寫與全形變體 — 記錄實際 pattern
- Potential shortcut: dist/ 排除意味 dist 內殘留舊引用直到 task-6 regenerate — 記錄此窗口

## Acceptance Criteria

- Covers: "Silent failure - dangling numbered-rule citation survives sweep"
