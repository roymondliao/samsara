# Kickoff: issue-002-validate-live-surface（mini-feature，task-6 演練載體）

## Problem Statement

`samsara-cli validate` 掃描 repo 根目錄的全部檔案，把 `changes/`、`docs/`、`bugfix/`、`tests/fixtures/` 裡的歷史/示範文字（合法含有未轉換樣式）與真正的轉換缺陷混在同一個 issue 計數裡 —— main 上恆為 42、本 branch 36，永遠非零，因此沒有任何 gate 能消費它的 exit code（ISSUE-002，issue.md 已登記；CI 從不呼叫 validate 即此因）。修法：validate 預設只掃 live instruction surface（`skills/`、`agents/`、`references/`、`hooks/`、`.claude-plugin/`），讓 issue 數回到可歸零、可被 gate 消費的狀態。

## Evidence

- `issue.md` ISSUE-002（2026-07-04 登記）：42 issues on main、CI 恆綠、候選修法之一即「scope validate to live instruction surface」。
- 本 feature task-5 實測：repo-root 掃描 36 issues，`--source dist/codex` 掃描 0 errors —— 證明噪音全部來自非 live-surface 路徑。

## Risk of Inaction

validate 永遠不可消費 → ISSUE-002 永久開放 → TargetValidator 的實際執法力維持零（本 session codebase map 已列為 rot hotspot）。

## Scope

### Must-Have (with death conditions)

- **live-surface 預設排除**：TargetValidator 對 source-tree 掃描預設排除 `changes/`、`docs/`、`bugfix/`、`tests/`。
  Death condition: 若排除清單導致真實 live-surface 缺陷被漏檢（例：skills/ 下的洩漏樣式被錯誤排除），回退並改用 opt-in flag。

### Explicitly Out of Scope

- CI workflow 增加 validate 步驟（ISSUE-002 的完整關閉，另案）
- `--strict`/`--all` flag 設計（若排除後仍有殘餘 live-surface issues 再議）

（無 `poc_death_date` —— 本 feature 走 spec path 預設。）

## North Star

repo-root `samsara-cli validate --platform codex` 的 issue 數從 36 降到 live-surface 真實數（預期 0 或個位數），且 `uv run pytest` 全綠。
