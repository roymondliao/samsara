# Task 6: Apply legacy_imprecise markers to existing changes/

## Context

Read: `../overview.md` 與 `../2-plan.md`

依 must-have **M6**：既有 v0.9.1 `changes/*` 目錄全部標記為 `legacy_imprecise`——這些檔案在不精確 schema 下產出，**不可作為新 feature 的 template**。

實作方式：在每個既有 `changes/2026-*` 目錄頂層新增 `_LEGACY_IMPRECISE.md` marker file（非侵入式，不修改既有 plan/scar 內容）。

既有目錄清單（11 個，本 feature `schema-axiom-alignment` 除外）：

```
changes/2026-04-17_samsara-phase4-auto-iteration/
changes/2026-04-19_yin-coding-spirit/
changes/2026-04-21_planning-file-map-consistency/
changes/2026-04-21_security-privacy-review/
changes/2026-04-23_execution-model-scope/
changes/2026-04-23_explorer-gitignore-respect/
changes/2026-04-24_multi-platform-support/
changes/2026-05-09_auto-version-release/
changes/2026-05-09_gemini-cli-integration/
changes/2026-05-09_version-0.9.0/
changes/2026-05-10_local-cli-test-ci-gating/
```

## Files

- Create (11 new files):
  - `changes/2026-04-17_samsara-phase4-auto-iteration/_LEGACY_IMPRECISE.md`
  - `changes/2026-04-19_yin-coding-spirit/_LEGACY_IMPRECISE.md`
  - `changes/2026-04-21_planning-file-map-consistency/_LEGACY_IMPRECISE.md`
  - `changes/2026-04-21_security-privacy-review/_LEGACY_IMPRECISE.md`
  - `changes/2026-04-23_execution-model-scope/_LEGACY_IMPRECISE.md`
  - `changes/2026-04-23_explorer-gitignore-respect/_LEGACY_IMPRECISE.md`
  - `changes/2026-04-24_multi-platform-support/_LEGACY_IMPRECISE.md`
  - `changes/2026-05-09_auto-version-release/_LEGACY_IMPRECISE.md`
  - `changes/2026-05-09_gemini-cli-integration/_LEGACY_IMPRECISE.md`
  - `changes/2026-05-09_version-0.9.0/_LEGACY_IMPRECISE.md`
  - `changes/2026-05-10_local-cli-test-ci-gating/_LEGACY_IMPRECISE.md`
- Do NOT modify: 既有的 `1-kickoff.md` / `2-plan.md` / `acceptance.yaml` / scar reports 內容
- Test: 死路測試在 task-7 整合

## Death Test Requirements

- Test: `find changes/ -mindepth 1 -maxdepth 1 -type d -not -name "2026-05-16_schema-axiom-alignment"` 列出的每個目錄必須包含 `_LEGACY_IMPRECISE.md`
- Test: 每個 marker file 必須包含核心字串「schema version: v0.9.1 (type: death_path)」與「must not be used as a template」
- Test: `_LEGACY_IMPRECISE.md` 內容長度 ≥ 200 bytes（防止空殼 placeholder）
- Test: 本 feature 目錄 (`changes/2026-05-16_schema-axiom-alignment/`) **不可**含 `_LEGACY_IMPRECISE.md`

## Implementation Steps

- [ ] Step 1: 寫死路 fixture——把 marker file 內容寫成只有「This is legacy.」一句，驗證「長度 ≥ 200 bytes」與「core string 存在」兩個 grep 都會 fail
- [ ] Step 2: 定稿 marker file 內容範本（建議結構）：
  ```markdown
  # ⚠️ LEGACY — Imprecise Schema

  This feature directory was produced under the v0.9.1 schema, which used the
  imprecise single `type: death_path` classification.

  As of 2026-05-18, the schema has been refined into per-event enum:
    - `silent_failure` — system 啟動後死亡（看起來活著實際在說謊）
    - `boundary_fail` — system 啟動前死亡（user 立即知道、user 該負責）

  See:
    - `changes/2026-05-16_schema-axiom-alignment/` — the upgrade itself
    - `docs/develop.md` Self-Application Clause section

  **This directory is preserved as historical record and must NOT be used as a
  template for new features.** The acceptance/scar files inside use deprecated
  `type: death_path` vocabulary that does not reflect current framework standards.

  coverage_type: legacy_imprecise
  schema_version: v0.9.1
  superseded_at: 2026-05-18
  ```
- [ ] Step 3: 對 11 個目錄逐一建立此 marker file（內容一致，可機械化）
- [ ] Step 4: 跑死路測試 enumerate 既有目錄——每個必須有 marker、本 feature 不能有
- [ ] Step 5: 跑 marker 內容驗證——core string 全部 ≥1 match
- [ ] Step 6: **Semantic alignment review** — Before writing scar report, verify:
  - 對齊 `../1.6-recalibration.md` first-principle 結論（schema 層責任明確化，非新 manifesto / 非 backward-compat）
  - 不違反 `docs/philosophy.md` / `thinking.md` / `docs/develop.md` 既有 manifesto
  - 新 enum 語意精確：`silent_failure` 嚴格指「system 啟動後死亡」、`boundary_fail` 嚴格指「system 啟動前死亡」
  - Prose 沒有退化為 yang-side：詞彙換新但思維框架仍假設「死路只有一種」即為失敗
  - Review 結論寫進 scar report `narrative` 欄位；發現本 task 修不到的語意偏差 → 標記 `assumptions_made` 並提請 cross-task iteration
- [ ] Step 7: 寫 scar report → `../scar-reports/task-6-scar.yaml`

## Expected Scar Report Items

- Potential shortcut: 11 個 marker file 內容完全一致——但日後若有 user 想客製某些目錄的 marker（例如標註該 feature 的特殊狀態），預設一致內容會被改成不同 content，造成標記不對等。本 task 預設「所有 marker 一致」，scar 標記此為「未來可能 split 的設計風險」
- Potential shortcut: 漏掉某個目錄（11 個 → 10 個）——必須 cross-check `ls changes/` 數量
- Assumption to verify: marker file 命名 `_LEGACY_IMPRECISE.md`（底線開頭）——這在 Unix 慣例中表示「隱式檔案 / config-like」。若日後 framework 對「以底線開頭」的檔案有 sort 規則或 grep ignore，可能造成 marker 被忽略。本 task 預設「底線開頭可接受」，scar 標記為 verify-required
- Assumption to verify: 本 feature 目錄 `2026-05-16_schema-axiom-alignment/` 是否需要 marker？預設「不需要」——本 feature 是建立新 schema 的起點，不是 legacy。若 review 後決定本 feature 也需 marker（例如標註為「first feature on new schema」），是另一個 task 範疇

## Acceptance Criteria

從 `../acceptance.yaml` 涵蓋的 scenarios：

- Covers: "Silent failure - legacy v0.9.1 changes/ unevenly marked"（本 task 是此 death case 的直接修復）
- Covers: "Boundary fail - 既有 v0.9.1 changes/ 被當作 template fork"（本 task 在 ls 時點建立 boundary）
- Covers: "Degradation - task-6 marker 內容過於 generic"（本 task 必須避免——marker 內容需具體寫明「為什麼是 legacy」「不可作 template」）
