# Task 4: Add self-application clause + workaround 3 cases to docs/develop.md

## Context

Read: `../overview.md` 與 `../2-plan.md`

本 task 對應 must-have **M5** + **M3**：

- **M5 (Self-Application clause)**: 在 `docs/develop.md` 明文宣告 L97「unknown 不能塞進 success/failure」原則**也適用於 framework 自身 schema**——防止未來 framework 再次違反同樣原則
- **M3 (Workaround section)**: 在 `docs/develop.md` 加入 workaround 精確定義 + 3 個具體 cases

定義精確化：
> **Workaround = the act of postponing boundary_fail into silent_failure**（把 user 該負責的、應該在 boundary 顯示的失敗，推遲至 system 啟動後變成 silent_failure）

3 個 cases（依 G4 決議）：
1. **Silent default fallback**：API key 未設定但 code 用空字串繼續 call API 然後 401
2. **try/except 吞例外**：用 `except: pass` 把 connection error 全部吃掉
3. **Cache-stale 沉默使用**：Cache TTL 過期但仍使用 stale data，未標記 degraded

## Files

- Modify: `docs/develop.md` — 新增兩個 section：
  - "Self-Application Clause"（接在現有 L97 附近的合適位置）
  - "Workaround in Samsara's Vocabulary"（含 3 cases）
- Test: 死路測試在 task-7 整合

## Death Test Requirements

- Test: `grep -i "self.application" docs/develop.md` 必須回傳 ≥1 match
- Test: `grep "L97" docs/develop.md` 必須回傳 ≥1 match（self-reference 必須存在）
- Test: `grep -i "workaround" docs/develop.md` 必須回傳 ≥1 match
- Test: 3 個 case 名稱在 docs/develop.md 中可被 grep 到：
  - `grep -i "silent default" docs/develop.md` → ≥1
  - `grep -i "except.*pass\|try/except" docs/develop.md` → ≥1
  - `grep -i "cache.stale\|stale cache" docs/develop.md` → ≥1
- Test: `grep "boundary_fail" docs/develop.md` 必須回傳 ≥1 match（workaround 定義中引用新詞彙）

## Implementation Steps

- [ ] Step 1: 寫死路 fixture——在 staging fixture file 故意省略 "self-application" 字眼，驗證 grep 規則會 fail
- [ ] Step 2: Read 既有 `docs/develop.md`（特別是 L97 附近段落）找合適插入點
- [ ] Step 3: 寫 "Self-Application Clause" section：
  - 引用既有 L97「unknown 不能塞進 success/failure 視同缺陷」
  - 明寫此原則對「framework 自身 schema」也適用
  - 給出反面範例：把多種死法塞進同一個 schema type = 等同把 unknown 偽裝成 known
- [ ] Step 4: 寫 "Workaround in Samsara's Vocabulary" section：
  - Workaround 精確定義（boundary_fail → silent_failure 的時序推遲）
  - Case 1: Silent default fallback（含 yang vs yin 對比）
  - Case 2: try/except 吞例外
  - Case 3: Cache-stale 沉默使用
  - 每個 case 寫法包含：trigger condition / 看起來做什麼（謊言）/ 實際發生什麼 / 如何重新分類為 boundary_fail
- [ ] Step 5: 跑上述 7 條 grep 死路測試——確認全綠
- [ ] Step 6: 自我驗證：把寫好的兩個 section 拿給陽面思維讀者讀（mental simulation），確認他們能立刻分辨 silent_failure vs boundary_fail
- [ ] Step 7: **Semantic alignment review** — Before writing scar report, verify:
  - 對齊 `../1.6-recalibration.md` first-principle 結論（schema 層責任明確化，非新 manifesto / 非 backward-compat）
  - 不違反 `docs/philosophy.md` / `thinking.md` / `docs/develop.md` 既有 manifesto
  - 新 enum 語意精確：`silent_failure` 嚴格指「system 啟動後死亡」、`boundary_fail` 嚴格指「system 啟動前死亡」
  - Prose 沒有退化為 yang-side：詞彙換新但思維框架仍假設「死路只有一種」即為失敗
  - Review 結論寫進 scar report `narrative` 欄位；發現本 task 修不到的語意偏差 → 標記 `assumptions_made` 並提請 cross-task iteration
- [ ] Step 8: 寫 scar report → `../scar-reports/task-4-scar.yaml`

## Expected Scar Report Items

- Potential shortcut: Self-Application clause 寫得太抽象（只重複「也適用於 framework」一句）——必須有具體反面範例
- Potential shortcut: Workaround 3 cases 寫成同一個模板填空——必須每個 case 都有不同的 yang 思維與 yin 重新分類
- Assumption to verify: "self-application" 這個英文詞是否在中文哲學文檔（philosophy.md / thinking.md）中有對應詞？預設「沒有，新引入」——若 review 發現 develop.md 此詞彙與其他 docs 用詞風格不協調，回 Planning
- Assumption to verify: 既有 develop.md 是否有「插入新 section 會破壞結構」的風險？預設「沒有」（develop.md 是多 section markdown 文件）——若 review 顯示插入處破壞既有閱讀流，需重新尋找位置

## Acceptance Criteria

從 `../acceptance.yaml` 涵蓋的 scenarios：

- Covers: "Silent failure - self-application clause forgotten in docs/develop.md"（本 task 是此 death case 的直接修復）
- Covers: "Happy path - 全部 7 task 完成 + cross-doc grep 全綠"（本 task 是 happy path 中 develop.md 條件的滿足者）
