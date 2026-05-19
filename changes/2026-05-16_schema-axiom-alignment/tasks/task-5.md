# Task 5: Atomic vocabulary refresh in README.md + README.zh-TW.md

## Context

Read: `../overview.md` 與 `../2-plan.md`

依 G6 決議：README.md 與 README.zh-TW.md 必須 **atomic ship**（同一 commit）——不允許短期語言不一致。

主要改動：Philosophy section 與任何提及 silent failure / death path 的段落更新為新 enum 詞彙。新增 light touch 描述 boundary_fail 與 silent_failure 的區分（不需要長篇 manifesto，因為 1.6-recalibration 已確認本次不寫新 manifesto）。

## Files

- Modify: `README.md`
- Modify: `README.zh-TW.md`
- Test: 死路測試在 task-7 整合

## Death Test Requirements

- Test: `grep -c "silent_failure\|silent failure" README.md` 與 `grep -c "silent_failure\|靜默失敗" README.zh-TW.md` 數量大致對應（差距 ≤ 2，容許輕微語言慣用差異）
- Test: `grep -c "boundary_fail\|boundary failure" README.md` 與 `grep -c "boundary_fail\|邊界失敗" README.zh-TW.md` 數量大致對應
- Test: `grep -i "death.path" README.md` 必須回傳 0 matches（除非引用歷史 context 並明確標註）
- Test: `grep -i "death.path\|死路" README.zh-TW.md` — 0 matches 或所有 matches 都在引用 context

## Implementation Steps

- [ ] Step 1: 寫死路 fixture——故意在 staging README 留一個未翻譯的 "death path" 字眼，驗證 grep 能抓到
- [ ] Step 2: Read 既有 `README.md` 與 `README.zh-TW.md`，找出所有提及 silent failure / death path 的段落
- [ ] Step 3: Map 出兩個檔案的對應段落（同一 section 在兩語言版本中的位置）
- [ ] Step 4: 改 `README.md` Philosophy section + 其他相關段落：
  - 替換 "death path" / "silent failure" 為新詞彙
  - 加 1-2 句說明 boundary_fail 與 silent_failure 的時序軸區分（不超過一個段落）
- [ ] Step 5: 改 `README.zh-TW.md` 對應段落——確保翻譯詞彙與英文版對齊（boundary_fail 對 boundary 失敗或保留原文、silent_failure 對靜默失敗等）
- [ ] Step 6: 跑上述 4 條 grep 死路測試——確認全綠
- [ ] Step 7: **Semantic alignment review** — Before writing scar report, verify:
  - 對齊 `../1.6-recalibration.md` first-principle 結論（schema 層責任明確化，非新 manifesto / 非 backward-compat）
  - 不違反 `docs/philosophy.md` / `thinking.md` / `docs/develop.md` 既有 manifesto
  - 新 enum 語意精確：`silent_failure` 嚴格指「system 啟動後死亡」、`boundary_fail` 嚴格指「system 啟動前死亡」
  - Prose 沒有退化為 yang-side：詞彙換新但思維框架仍假設「死路只有一種」即為失敗
  - Review 結論寫進 scar report `narrative` 欄位；發現本 task 修不到的語意偏差 → 標記 `assumptions_made` 並提請 cross-task iteration
- [ ] Step 8: 寫 scar report → `../scar-reports/task-5-scar.yaml`，包含 cross-language diff 大小（兩個檔案分別 +N -N 行數）

## Expected Scar Report Items

- Potential shortcut: 只改 Philosophy section 顯眼處，忽略例如 README 末尾 / FAQ / glossary-like 段落中的舊用語
- Potential shortcut: 中文版翻譯時用詞不統一（同一個 silent_failure 在不同段落翻成「靜默失敗」與「沉默失敗」）
- Assumption to verify: README 中是否有與本次升級無關但碰巧含 "death" 字眼的句子（例如「kill switch」段落）？預設「需 manual review，不機械替換」——若 grep 將不相關 match 列入死路，需精細化 grep 規則
- Assumption to verify: README.zh-TW.md 與 README.md 是否 1:1 對應翻譯？預設「結構對應但用語可能有翻譯差異」——若發現某 section 只存在於其中一版，本 task 不負責補翻譯，但在 scar report 標記為 cross-language 不對等候選

## Acceptance Criteria

從 `../acceptance.yaml` 涵蓋的 scenarios：

- Covers: "Silent failure - README 中英版本悄悄漂移"（本 task 是此 death case 的直接修復）
- Covers: "Happy path - 全部 7 task 完成 + cross-doc grep 全綠"（README 中英對應驗證為 happy path 的一部分）
