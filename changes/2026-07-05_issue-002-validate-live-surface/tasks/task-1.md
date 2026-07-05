# Task 1: TargetValidator live-surface 預設排除（單一常數）+ 死法/契約測試

## Context

Read: overview.md

`samsara-cli validate`（TargetValidator 對 source tree 的掃描）目前掃 repo 全部檔案，歷史/示範文字（changes/ docs/ bugfix/ tests/ 內合法含未轉換樣式）混入 issue 計數 —— main 恆 42、branch 恆 36，gate 不可消費（ISSUE-002）。本 task：掃描預設排除非 live-surface 路徑。

## Files

- Modify: `samsara_cli/validators/target.py` — 新增 live-surface 排除常數（排除 `changes/`、`docs/`、`bugfix/`、`tests/` 頂層前綴）+ 掃描時過濾
- Test: `tests/test_validators/test_target_live_surface.py`（create）

## Death Test Requirements

- Test: 排除生效後，planted 在 `changes/` 假目錄下的洩漏樣式**不再**被計入 issue（噪音確實被排除）
- Test: planted 在 `skills/` 下的洩漏樣式**仍然**被抓到（死法 1：排除清單不得誤傷 live 路徑）
- Test: 直接呼叫 TargetValidator（不經 CLI）與經 CLI 呼叫看到同一排除行為（死法 2 / SD-1：單一常數，無雙份清單）

## Unit Test Contract

- Contract source: **public API/return value** —— `TargetValidator.validate(source_dir, platform)` 的回傳 issue 清單（對 planted 檔案的包含/排除為可觀測行為）。不斷言排除常數的內部表示。

## Structure Refs

- structure_refs: [SS-1, SD-1]

## Implementation Steps

- [ ] Step 1: Write death tests
- [ ] Step 2: Run death tests — verify they fail
- [ ] Step 3: Write unit tests asserting the named Unit Test Contract source
- [ ] Step 4: Run unit tests — verify they fail
- [ ] Step 5: Implement minimal code to pass all tests
- [ ] Step 6: Run all tests — verify they pass
- [ ] Step 7: Write scar report
- [ ] Step 8: Report back (do not commit)

## Expected Scar Report Items

- Assumption to verify: 排除清單四個前綴是否涵蓋全部噪音來源（實測 repo-root validate 前後 issue 數，殘餘者逐一歸類）
- Potential shortcut: 排除以路徑前綴比對 —— symlink/絕對路徑邊界情況如實記錄

## Acceptance Criteria

- Covers: repo-root validate issue 數從 36 降到 live-surface 真實數；`uv run pytest` 全綠；skills/ planted 洩漏仍被抓（不誤傷）
