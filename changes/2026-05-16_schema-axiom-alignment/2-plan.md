# Plan: schema-axiom-alignment

## Goal

重構 Samsara framework schema 的 failure 分類詞彙——把單一 `type: death_path` 拆解為精確 enum (`silent_failure` | `boundary_fail`)，使 framework 自身遵守既有 manifesto（`docs/develop.md L97`）對 user 的 system 提出的「狀態必須精確命名」要求。

## Scope Anchor

本檔案的所有 must-have / out-of-scope 以 `1.6-recalibration.md` Section 6 為準（已 user 簽收於 2026-05-18）。`1-kickoff.md` 的 M1/M4 已被 supersede。

## I/O Specification

### Inputs

| Input | Source | unknown_output 處理 |
|-------|--------|--------------------|
| 既有 skill 檔案內容（15 個 `.md` + `.yaml`） | `skills/*/` | 不允許「假設意圖」——遇到模糊 prose 必須在 task scar report 標記 |
| 既有 `docs/develop.md` | 不變動原有結構 | 新增 self-application section 接在 L97 後 |
| 既有 v0.9.1 `changes/*` 目錄 | 11 個既有 feature 資料夾 | 不修改既有檔案內容，只加 `_LEGACY_IMPRECISE.md` marker |

### Outputs

| Output | Definition | unknown_output |
|--------|-----------|---------------|
| 新 enum 在 schema 中可用 | `type: silent_failure | boundary_fail | degradation | happy_path` 四值 | 任何 implementer 寫入第五個值 → boundary_fail event（在 schema validation 時點明確拒絕）|
| Framework prose 一致性 | Grep 結果：`skills/` 下無 `type: death_path` 字串殘留 | unknown 不能存在——grep 結果是 0 或 ≥1 的二值 |
| Legacy 標記覆蓋率 | 既有 `changes/*` 每個目錄含 `_LEGACY_IMPRECISE.md` | unknown 不能存在——`find changes -mindepth 1 -maxdepth 1 -type d | xargs -I{} test -f {}/_LEGACY_IMPRECISE.md` 必須對所有目錄為 true |

## Death Cases（不只是 edge cases）

### Death Case 1: Partial migration cross-doc inconsistency

| 觸發條件 | task-1 (planning enum) 完成但 task-2 (implement scar) 漏改 |
|---|---|
| **System 看起來做了什麼**（謊言）| Implementer 開啟 planning template，看到新 enum；寫 scar 時 scar-schema 仍是舊欄位名，照舊填寫 |
| **實際發生什麼**（真相）| Acceptance.yaml 用 silent_failure / boundary_fail，但 scar report 仍 silent_failure_conditions 單欄收容兩種死法 → 同一 feature 內 schema 漂移 |
| **如何偵測** | task-7 死路測試：grep 整個 `skills/` 路徑，要求 `silent_failure_conditions` 與 `boundary_fail_conditions` 兩個欄位**同時存在於 implement schema**；任何只有單一欄位的情況視為 partial migration |

### Death Case 2: Self-application clause silently absent

| 觸發條件 | task-4 寫了某些段落但漏掉 self-application key phrase |
|---|---|
| **System 看起來做了什麼** | docs/develop.md 看起來被更新了（diff 顯示有改動）|
| **實際發生什麼** | 改動只在 workaround section，self-application 條款未實際寫入 → 未來 framework 又會違反同樣原則 |
| **如何偵測** | task-7 死路測試：grep `docs/develop.md` for 精確字串 `"Self-Application"` 與 `"L97 also applies"`（或對應中文）。Boolean check，不允許「找到類似的」這種模糊驗證 |

### Death Case 3: Legacy markers unevenly applied

| 觸發條件 | task-6 跑批次但漏掉某些舊 `changes/*` 目錄 |
|---|---|
| **System 看起來做了什麼** | `ls changes/` 顯示大部分目錄都有 `_LEGACY_IMPRECISE.md` |
| **實際發生什麼** | 某 1-2 個目錄漏標——新 implementer 開了那個目錄當 reference template → 誤用舊 schema |
| **如何偵測** | task-7 死路測試：列舉所有 `changes/2026-*/` 目錄，每個都必須包含 `_LEGACY_IMPRECISE.md`。Count mismatch 即 fail。本 feature（`schema-axiom-alignment`）除外 |

### Death Case 4: README 中英版本悄悄漂移

| 觸發條件 | task-5 改了 README.md 但忘了同步 README.zh-TW.md |
|---|---|
| **System 看起來做了什麼** | `git diff` 看起來 README 都改了（因為 task-5 task 名稱顯示「中英同步」）|
| **實際發生什麼** | 兩個 README 詞彙不一致——英文 reader 看 boundary_fail，中文 reader 還看 death_path |
| **如何偵測** | task-7 死路測試：grep 兩個 README 對應段落，新詞彙必須同時出現於兩個檔案，數量大致對應 |

### Death Case 5: Grep 死路測試自身偽 pass

| 觸發條件 | task-7 grep 規則只查 `type: death_path` 字串，未涵蓋 prose（如「all death paths」、「the death case」這類描述）|
|---|---|
| **System 看起來做了什麼** | Grep 全綠，task-7 通過 |
| **實際發生什麼** | Prose 殘留如「Write death tests for all death paths」這類句子 → vocabulary 仍漂移、framework 看似活著實際說謊 |
| **如何偵測** | 在 task-7 內**先寫 anti-test**：故意在 staging file 中放一句「death path」prose，驗證 grep 規則能抓到。若 anti-test 漏掉，grep 規則本身就是 silent failure 候選 |

## Architecture

三層改動，互相無循環依賴：

### Layer 1: Schema definition (task-1)

- **單點定義 enum**: `skills/planning/templates/acceptance.yaml` 與 `skills/planning/death-first-spec.md` 成為新 enum 的 single source of truth
- **enum 值**: `silent_failure` | `boundary_fail` | `degradation` | `happy_path`
- **per-event 結構**: 每個 scenario 一個 type，不允許混合
- 新增 `coverage_type: legacy_imprecise` enum 值

### Layer 2: Schema propagation (task-2, task-3)

- task-2 把新 enum 同步進 `skills/implement/`（scar 結構新增 `boundary_fail_conditions` parallel to `silent_failure_conditions`）
- task-3 把詞彙同步進 `skills/validate-and-ship/`、`skills/codebase-map/`、`skills/debugging/`、`skills/iteration/`

### Layer 3: Manifesto & legacy (task-4, task-5, task-6)

- task-4: `docs/develop.md` 補上 self-application 條款 + workaround section（3 個 cases）
- task-5: README.md + README.zh-TW.md 詞彙同步（atomic）
- task-6: 既有 `changes/2026-*/` 目錄批次加 `_LEGACY_IMPRECISE.md` marker file

### Final verification: task-7

死路測試 script — 對所有 layer 跑 cross-doc grep。失敗時必須給出精確檔名 + 行號。

## Key Design Decisions

| 決策 | 選擇 | Rationale |
|------|------|-----------|
| **Scar schema 結構** | 新增 `boundary_fail_conditions` 與既有 `silent_failure_conditions` 並列 | 名稱承擔清楚責任 + grep 友善。對齊 thinking.md「狀態必須精確命名」 |
| **Legacy 標記形式** | 在每個既有 `changes/*` 加 `_LEGACY_IMPRECISE.md` marker file | 非侵入式（不改既有 plan/scar）、`ls` 即可見、自我解釋。對齊 develop.md「不允許 silent rewrite history」|
| **Workaround section 形式** | 寫進 `docs/develop.md` 而非新檔 | 對齊 G2 決議：不分散 single source of truth |
| **No backward-compat alias** | 完全刪除 `type: death_path` | 對齊 G1 + A2/A5 + recalibration |
| **Anti-test 寫法** | task-7 必須先用 fixture 文字驗證 grep 規則本身能抓到舊詞彙 | 對齊 thinking.md「沒聲音不是健康，是失聰」——grep 自己也需要被驗 |

## Affected Files Inventory

完整列舉（task-7 grep 驗證範圍）：

```
skills/planning/templates/acceptance.yaml      (task-1)
skills/planning/death-first-spec.md            (task-1)
skills/planning/templates/overview.md          (task-1)
skills/planning/SKILL.md                       (task-1)
skills/planning/task-format.md                 (task-1)
skills/implement/templates/scar-schema.yaml    (task-2)
skills/implement/scar-report.md                (task-2)
skills/implement/SKILL.md                      (task-2)
skills/validate-and-ship/ship-manifest.md      (task-3)
skills/validate-and-ship/templates/ship-manifest.yaml (task-3)
skills/validate-and-ship/SKILL.md              (task-3)
skills/codebase-map/SKILL.md                   (task-3)
skills/codebase-map/templates/codebase-map.yaml (task-3)
skills/debugging/templates/fix-summary.yaml    (task-3)
skills/iteration/SKILL.md                      (task-3)
docs/develop.md                                (task-4)
README.md                                      (task-5)
README.zh-TW.md                                (task-5)
changes/2026-04-17_*/_LEGACY_IMPRECISE.md      (task-6, new file)
changes/2026-04-19_*/_LEGACY_IMPRECISE.md      (task-6, new file)
... (共 11 個既有目錄)
tests/cross_doc_grep.sh                        (task-7, new file)
```

## Schema Delta Examples

### Before (current acceptance.yaml template)

```yaml
scenarios:
  - name: "<Silent failure description>"
    type: death_path
    ...
```

### After (task-1 output)

```yaml
scenarios:
  # --- Silent failure paths (system 啟動後死亡：看起來活著實際在說謊) ---
  - name: "<Silent failure description>"
    type: silent_failure
    given: "<precondition>"
    when: "<action>"
    then:
      - "<observable outcome>"

  # --- Boundary fail paths (system 啟動前死亡：user 立即知道) ---
  - name: "<Boundary fail description>"
    type: boundary_fail
    given: "<precondition>"
    when: "<action at boundary>"
    then:
      - "<explicit rejection observable>"
      - "<error message indicates which user input is invalid>"
```

### Before (current scar-schema.yaml)

```yaml
silent_failure_conditions:
  - description: "..."
```

### After (task-2 output)

```yaml
silent_failure_conditions:
  # System 啟動後死亡——看起來活著實際在說謊
  - description: "..."

boundary_fail_conditions:
  # System 啟動前死亡——user 該負責的明確死亡
  - description: "..."
```

## Task Summary

| ID | Title | Depends on | 主要產出 |
|----|-------|-----------|---------|
| task-1 | Define new enum in planning templates | — | acceptance.yaml + death-first-spec.md + 4 個 planning prose |
| task-2 | Update implement skill scar structure | task-1 | scar-schema.yaml 新欄位 + scar-report.md + SKILL.md |
| task-3 | Sync vocabulary in remaining skills | task-1 | validate-and-ship + codebase-map + debugging + iteration |
| task-4 | docs/develop.md self-application + 3 workaround cases (M5+M3) | task-1 | develop.md 新增 section |
| task-5 | README atomic vocabulary refresh (M2 outward facing) | task-1 | README.md + README.zh-TW.md |
| task-6 | Apply legacy_imprecise markers (M6) | task-1 | 11 個 `_LEGACY_IMPRECISE.md` marker files |
| task-7 | Cross-doc grep death test | all above | tests/cross_doc_grep.sh + 執行驗證紀錄 |

## Per-Task Semantic Review Discipline

Every task in this Plan MUST include a **Semantic Alignment Review** step before writing its scar report.

**This is NOT a grep test.** Grep 死路測試 catches literal strings——它能告訴你 `death_path` 字串不見了，但**不能告訴你替換後的 prose 是否真的傳達了新 enum 的精確語意**。本次升級的本質是「概念精確化」，因此驗證必須包含概念層的環節，不能只有字串層的。

每個 task implementer 在跑完 grep 死路測試後、寫 scar report 前，必須對修改後的內容做以下檢查：

1. **對齊 `1.6-recalibration.md` first-principle 結論** — schema 層責任明確化（Samsara 自我應用），非新 manifesto / 非 backward-compat
2. **不違反既有 manifesto** — `docs/philosophy.md` / `thinking.md` / `docs/develop.md` 中的公理與概念不能被新詞彙稀釋或扭曲
3. **新 enum 語意精確使用**:
   - `silent_failure` 嚴格指「system 啟動後死亡（看起來活著實際在說謊）」
   - `boundary_fail` 嚴格指「system 啟動前死亡（user 立即知道、user 該負責）」
   - 不允許「silent_failure 包含部分 boundary_fail 含義」這類概念漂移
4. **Yin-side discipline 保留** — 詞彙換新但思維框架可能仍是 yang-side（「讓 system 看起來成功」）。Review 必須抓出這類退化，例如：
   - Prose 仍假設「死路只有一種」、只是換了名字
   - 範例仍以「失敗就是 crash」為框架，未體現 silent vs boundary 的本質差異
   - 詞彙正確但缺少對應的 yin-side 行為要求（如「必須留下傷口」、「不准偽裝正常」）
5. **Review 結論記錄** — 寫入該 task 的 scar report `narrative` 欄位；若發現語意偏差但無法在本 task scope 內修，標記為 `assumptions_made` 並提請 cross-task iteration

### Failure mode this discipline prevents

**機械替換死路**——把所有 `death_path` 替換成 `silent_failure | boundary_fail` 但 prose 框架仍假設「死路只有一種」，造成詞彙是新的、思維是舊的「假升級」。這正是 `thinking.md` 警告的「狀態模糊 = 責任模糊 = 腐敗開始」的另一形態：表面精確但實質不變。

### 與 task-7 grep 死路測試的關係

| 環節 | 驗什麼 | 工具 |
|------|--------|------|
| Grep 死路測試（task-7）| 字串層精確性——舊詞彙是否完全清除、新欄位是否存在 | 機械化 shell script |
| Semantic alignment review（每個 task）| 概念層精確性——新詞彙是否被正確理解與使用 | Human/yin-side judgement |

兩者互補不可替代——只有 grep = 失聰；只有 review = 規模不可控、容易漏網。

---

## Undocumented Assumptions Carried from Recalibration

從 `1.6-recalibration.md` 與簽收前的 gap 中保留為 undocumented：

- **U2 carryover**: Skill-by-skill vocabulary 更新範圍以 task-2/3 file inventory 為界。若 implementer 在 task 執行中發現未列出的 skill 殘留舊詞彙 → 必須在 scar report 標記為 `unresolved_assumptions`，不可 silent 補修
- **G3 carryover**: 本次升級確認以 `.md` / `.yaml` prose 改動為主。若任一 task 執行中發現需要改動 samsara_cli 程式碼或 format processor，task 必須立即停下、回 Planning 重新評估，不可 silent 擴張範圍
- **M6 marker file 內容**: marker 內容暫定為「This feature directory was produced under the v0.9.1 schema (type: death_path). It is preserved as historical record and must not be used as a template for new features.」由 task-6 最終定稿，但這個內容本身即為 undocumented assumption——若日後發現此 marker 措辭被誤解，視為 task-6 設計失敗

## Open Questions（Step 2 完成後仍未決）

| Q | 推延處理時點 |
|---|------------|
| Death test script 用 bash 還是 python？ | 留給 task-7 內決定（取決於既有 `tests/` 慣例）|
| `_LEGACY_IMPRECISE.md` 是否需要 frontmatter 含 schema_version 欄位？ | 留給 task-6 決定，但傾向「不需要」（marker 是 binary 標記）|
| Task-3 涵蓋的 4 個 skill 是否要拆成多個 task？ | 暫定單一 task。若 task-3 執行時發現過於龐雜 → 在 scar report 標記為「task 大小設計失敗」，下次 iteration 拆分 |
