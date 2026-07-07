# Evaluation Result — 三段式檢核（Primary Evaluator）

執行日期：2026-07-04（task-8 最終對帳）
執行者：main agent（inline；量測與聚合性質，基線歷史由 main agent 持有）
總判定：**三段全數 PASS**

---

## 第一段：測試全綠且 death tests 無刪除弱化 — PASS

**命令**：`source .venv/bin/activate && uv run pytest`
**輸出**：`856 passed`（基線 732 → 856；淨增 124 個測試）

**Death-test 完整性**（`git diff HEAD --stat -- tests/`）：
- 修改的既有測試僅 `tests/test_auto_mode/` 四檔（619 insertions / 108 deletions）——全部是 task-4 Auto Gate 去重的**斷言目標同步**（canonical 完整性斷言移至 references/auto-mode.md、per-skill 改斷言指針結構）。task-4 的 yin review 逐項對照 `git show HEAD:` 舊版驗證「每個舊斷言概念在新結構有家」，無弱化；`gatekeeper_answer`/`prompt_type` 等舊斷言由未動的 test_gatekeeper_contract*.py 續守。
- 新增 5 個測試檔（tests/test_skills/）：scar 規則、re-review signal、security fold、iteration 判準、fast-track——每檔含 death tests＋permanent wrong-direction decoys。
- 無任何 death test 被刪除。

**附註（非 evaluator 條款，誠實記錄）**：`samsara-cli validate --platform codex` 本分支 36 issues vs **main 基線 42 issues**（HEAD worktree 對照實測）——validate 失敗為既有狀態，本次淨改善 6 個（security 舊模式清除連帶），未引入新失敗。dist/codex regenerate 完成，舊 `samsara-security-privacy-review` 目錄確認消失。

---

## 第二段：指令面積淨量為負（先減少為主）— PASS

**命令**（前後同一命令；基線由 HEAD git worktree 實測，非引用估計值）：
```
find skills -name "*.md" -not -path "*/templates/*" | xargs wc -l   # skills 非模板
wc -l agents/*.md references/*.md                                    # agents + references
```

| 範圍 | 基線（HEAD） | 現況 | 差 |
|---|---|---|---|
| skills（非模板 md） | 2,808 | 2,599 | **−209** |
| agents + references | 3,548 | 3,589 | +41 |
| **核心指令面（上兩者合計）** | **6,356** | **6,188** | **−168** |
| templates（資訊性） | 493 | 555 | +62 |
| `.samsara/systemic-scars.yaml`（新） | 0 | 51 | +51 |
| **單一 session 可載入總計** | 6,849 | 6,794 | **−55** |

**判定**：核心指令面淨減 168 行、全含口徑淨減 55 行——淨量為負，PASS。
**搬家假減法檢查**：references 增量 41 行 ≪ skills 減量 209 行，非等量搬移；templates +62 與 registry +51 是**新增守護規則**（scar schema Rules 9–14、fast-track reviewed 聲明、系統性傷疤登記），性質是新契約而非內容搬家。
**對參考值的誠實說明**：pre-thinking 記錄的參考值 ~300 行未達成（實際核心 −168）。主因：(a) Auto Gate 去重實際省 ~46 行（原估 125）——階段特異語義（Step 0 overrides、雙重 trace、iteration 決策點）經 review 判定必須 inline 保留；(b) 減法項目同時帶入了新守護（decoy 死測契約、systemic registry、reviewed 聲明），這些是正增量但每行都有測試或消費者。「每個存在都有人負責」優先於行數，符合 invalidation condition 的精神。

---

## 第三段：逐項可觀測完成條件 — PASS（8/8）

| # | 條件 | 證據 |
|---|---|---|
| 1 | 6 skill 的 Auto Mode Gate 段受行數預算鎖定 | tests/test_auto_mode/test_skill_auto_mode_protocol.py `_BUDGETS`（12/12/16/18/19/49，actual+1；原 ≤8 形式目標的修正理由記於 task-4 scar） |
| 2 | `.samsara/systemic-scars.yaml` 存在且 schema 支援 systemic_ref | 檔案存在（51 行、2 entries）；scar-schema.yaml Rule 9；test_scar_schema_noise_rules.py（含 .gitignore 死測） |
| 3 | verified:true 單行＋status:resolved 就地標記落地 | scar-schema.yaml Rules 10/11/14；本 feature 7 份 scar 全用新格式（dogfood） |
| 4 | expiry 移除、rule 2 改訊號驅動 | iteration SKILL Step 2＋Yin constraints；ship-manifest.md rule 2；兩模板；test_accept_rereview_signal.py；歷史檔未動（yin review git status 驗證） |
| 5 | 0-design-direction.md 六項修訂各有決定文字 | task-7＋main agent 全文核對（六決定、跨節一致、grep 復核、§9 修訂記錄） |
| 6 | iteration 進入判準資料驅動 | implement SKILL Transition 三態分支（unknown 不准 skip＋durable 紀錄）；test_iteration_entry_criteria.py |
| 7 | fast-track 只記違規＋reviewed 聲明 | fast-track SKILL Step 4＋template；test_fast_track_quality_review.py（DC7 封死） |
| 8 | security-privacy-review 折入＋路由同步 | validate-and-ship Step 0（7 語義逐條核對無損）；bootstrap 路由圖；README×2；test_security_gate_fold.py；dist 舊目錄消失 |

---

## Feedback loop 使用記錄

無——三段皆 PASS，未觸發回退。
