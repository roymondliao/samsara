# Overview: schema-axiom-alignment

## Goal

重構 Samsara framework schema 的 failure 分類詞彙——從單一 `type: death_path` 拆解為精確 enum (`silent_failure` | `boundary_fail`)，使 framework 自身遵守既有 manifesto (`docs/develop.md L97`) 對 user 的 system 提出的精確命名要求。

## Architecture

三層改動互相無循環依賴：(1) **Schema definition layer** — `skills/planning/` 成為新 enum 的 single source of truth；(2) **Schema propagation layer** — 把新 enum 同步進 implement / validate-and-ship / codebase-map / debugging / iteration 5 個 skill；(3) **Manifesto & legacy layer** — `docs/develop.md` 補 self-application 條款 + workaround 3 cases，既有 `changes/*` 標記 `legacy_imprecise`，README 中英同步。

所有改動以 `.md` 與 `.yaml` prose-level 為主，不觸碰 `samsara_cli` 程式碼。

## Tech Stack

- Markdown / YAML 編輯
- Shell (`grep`, `find`) for cross-doc death tests
- Git for tracking atomic refresh

## Key Decisions

- **Per-event enum**: `type: silent_failure | boundary_fail | degradation | happy_path` — 對齊 `develop.md L97` 的 enum 精確性
- **Scar schema 結構**: 新增 `boundary_fail_conditions` 與既有 `silent_failure_conditions` **並列**（不合併為單一 typed list）— 名稱承擔清楚責任 + grep 友善
- **Clean break, no backward-compat alias**: 完全刪除 `type: death_path` — 對齊 `thinking.md L40 + L68`
- **Legacy marker 形式**: 每個既有 `changes/*` 目錄加 `_LEGACY_IMPRECISE.md` marker file — 非侵入式、`ls` 即可見
- **Death test 自我驗證**: task-7 grep 必須先用 fixture 驗證自己能抓到舊詞彙 — 否則 grep 自己即為 silent failure
- **README 中英 atomic ship**: 不允許短期語言不一致

## Death Cases Summary

Top 3 最危險的 silent failure paths（完整列表見 `acceptance.yaml`）：

1. **Partial migration cross-doc inconsistency** — task-1 改了 planning enum 但 task-2/3 漏跟進 → framework 自身產生新舊 schema 漂移
2. **Self-application clause silently absent** — task-4 改了 develop.md 但漏寫核心字串 → 未來 framework 又會違反同樣原則，rot 重生
3. **Legacy markers unevenly applied** — task-6 漏標某 1-2 個既有目錄 → 新 implementer 誤用舊目錄為 template

## File Map

詳細列表見 `2-plan.md` Affected Files Inventory。摘要：

- `skills/planning/` — 5 files (task-1)
- `skills/implement/` — 3 files (task-2)
- `skills/{validate-and-ship,codebase-map,debugging,iteration}/` — 7 files (task-3)
- `docs/develop.md` — self-application + workaround section (task-4)
- `README.md` + `README.zh-TW.md` — atomic refresh (task-5)
- `changes/2026-{04-17,04-19,04-21,04-23,04-24,05-09,05-10}_*/_LEGACY_IMPRECISE.md` — 11 new marker files (task-6)
- `tests/cross_doc_grep.sh` — verification script (task-7)
