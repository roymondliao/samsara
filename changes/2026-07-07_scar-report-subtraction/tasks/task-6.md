# Task 6: dist/ regenerate（codex/gemini）＋全套件整合驗證

## Context

Read: overview.md（seam: scar-write-contract、File Map 末兩項）

samsara_cli 轉換時對 YAML companion files 逐字複製（`samsara_cli/converter/skill.py:371,405-410`），repo 內 `dist/codex/` 與 `dist/gemini-cli/` 帶著 scar-schema.yaml 及相關 skill/agent 檔的轉換副本。task-1–5 改動了 source（schema、iteration SKILL、implement SKILL、implementer agent、scar-report.md、validate_format.py）→ dist 副本已 stale，必須 regenerate 至 byte-identical（YAML）／轉換一致（md）。

## Files

- Modify: `dist/codex/`（regenerate 輸出）
- Modify: `dist/gemini-cli/`（regenerate 輸出）
- Test: 既有 integration／snapshot 測試（不新增，驗證不退化）

## Death Test Requirements

- Test:（既有測試承擔）integration/smoke/snapshot 套件在 regenerate 後全綠 — 本 task 不寫新 death test，死路防線是「regenerate 缺漏 = diff 可見」：
- 驗證: `diff skills/implement/templates/scar-schema.yaml dist/codex/.agents/skills/samsara-implement/templates/scar-schema.yaml` 與 gemini 對應路徑 → 零差異（byte-identical）
- 驗證: `git status dist/` 顯示的變更檔案集合與 task-1–5 觸及的 source 檔案集合對應 — 出現「不相關 dist 檔被改」或「已改 source 無對應 dist 變更」都要查明後記入 scar

## Unit Test Contract

- Contract source: 既有 integration 套件的 emitted output（pytest 通過）＋ dist YAML byte-identical 這一可 diff 的 artifact shape
- A unit test must assert this named contract source, not implementation details.

## Implementation Steps

- [ ] Step 1: 找出 regenerate 的既定入口（README／samsara_cli CLI help，如 `uv run samsara-cli convert --platform codex` 與 `--platform gemini`；以 repo 實際命令為準，不得手改 dist）
- [ ] Step 2: 執行 regenerate（兩平台）
- [ ] Step 3: byte-identical diff 驗證（上述兩條）＋ `git status dist/` 對應性檢查
- [ ] Step 4: `uv run pytest tests/` 全綠（Primary evaluator 終驗）
- [ ] Step 5: `uv run samsara-cli validate --platform codex`（如 repo 慣例有此步）確認 live-surface 驗證不退化
- [ ] Step 6: 跑 implement 的 `validate_format.py` 對本 feature scar-reports 全數 clean（含新預算）
- [ ] Step 7: 寫 scar report（新槽位格式）
- [ ] Step 8: Report back（不 commit）

## Expected Scar Report Items

- Assumption to verify: regenerate 命令的實際形態（CLI 子命令與旗標）— 以 repo 文件為準，記錄實際使用的命令
- Potential silent failure: dist 內 md 檔的轉換含 rules 引擎改寫（非逐字）— md 副本無法用 byte-diff 驗證，只能靠 integration 測試；記錄此驗證強度差
- Potential shortcut: dist 變更量大時人工抽查範圍有限 — 記錄抽查了哪些檔

## Acceptance Criteria

- Covers: "Success - full suite green (Primary evaluator)"
