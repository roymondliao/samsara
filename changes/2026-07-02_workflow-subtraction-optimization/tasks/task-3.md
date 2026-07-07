# Task 3: security-privacy-review 折入 validate-and-ship 成 Step 0 STOP gate

## Context

Read: overview.md

現況：`skills/security-privacy-review/`（SKILL.md 293 行）是獨立 skill，位置永遠固定在 validate-and-ship 前一格。User 決定折入：成為 validate-and-ship 的 Step 0 STOP gate，不可跳過性不變，少一次 skill 轉場、一個獨立 gate、一份 Auto Mode Gate 複本。

**必須保留的語義（折入時逐條核對，一條都不能掉）**：
1. diff 計算（`git diff <base>...HEAD`）＋ 空 diff／無法判定 base branch 的 edge-case gate
2. 平台無內建 review 能力 → 可見降級 gate，不是靜默跳過
3. 三態結果：pass / fail / unknown；**unknown ≠ pass**（timeout、partial、工具錯誤都是 unknown）
4. fail → issues 按嚴重度列出 → 修復選擇 gate → inline fix loop（fix → commit → **全量 diff** re-review，非僅 fix delta）；round 計數，≥3 輪起每輪 safety gate
5. human 接受的風險 carry forward 到 ship manifest
6. auto mode：capability 缺失／unknown／partial／failing → 高不確定 `reject`，不得 transition；accepted risk 在 auto mode 無效
7. Red Flags：不得指名特定平台工具（platform-agnostic）

## Files

- Modify: `skills/validate-and-ship/SKILL.md` —
  - 新增 `## Step 0: Security & Privacy Gate（STOP）` 於 Failure Budget Review 之前；壓縮收錄上列 7 條語義（原 293 行中大量per-decision execution-mode 路由樣板可合併敘述，但語義逐條保留）；process 圖加入 step0 節點。
  - Prerequisites 補「feature branch 有 committed changes」。
  - Transition/前言中原「security review passed 才進入」的表述改為內建 Step 0。
- Delete: `skills/security-privacy-review/`（整目錄）
- Modify: `skills/samsara-bootstrap/SKILL.md` — 路由圖：刪 `security_review` 節點，`implement`／`iteration` 直接連 `validate`（label 註明 validate 內含 security gate）；Chain Skills 清單刪該行、validate-and-ship 描述補「含 security & privacy Step 0」。
- Modify: `skills/implement/SKILL.md` — Transition 與 process 圖中 `invoke samsara:security-privacy-review` 改為 `invoke samsara:validate-and-ship`；選項文字同步。
- Modify: `skills/iteration/SKILL.md` — 同上（Transition、process 圖、Auto Mode Gate 內 proceed 目標）。
- Modify: `README.md`、`README.zh-TW.md` — 工作流圖、skills 表、Artifacts 表移除獨立 security 列、validate-and-ship 描述更新。
- Modify: `references/auto-mode.md` — `stage` 允許值清單移除 `security-privacy-review`（或標記 folded into validation）；Security And Privacy Unknowns 段保留、措辭指向 validation 階段的 Step 0。
- Modify: `tests/test_auto_mode/test_protocol_helpers.py` — LATER_STAGE_SKILLS／REQUIRED_WORKFLOW_STAGES 移除 security-privacy-review 條目。
- Test: `tests/test_skills/test_security_gate_fold.py`（新）
- 驗證（不一定改）：`.claude-plugin/` 是否有 skill 清單需同步；`grep -r "security-privacy-review" --include="*.md" --include="*.py"` 全域清點殘留引用（docs/ 歷史文件除外）。

## Death Test Requirements

- Test: validate-and-ship SKILL.md 中 security gate 若不在 failure budget review 之前（結構位置比較，index_of 斷言）轉紅（DC5：折入後被移到後面或刪除）
- Test: 「unknown ≠ pass」條款消失時轉紅
- Test: 「全量 diff re-review（非僅 fix delta）」條款消失時轉紅
- Test: auto mode「capability 缺失／unknown／failing → 高不確定 reject」條款消失時轉紅
- Test: bootstrap SKILL.md 仍含 `samsara:security-privacy-review` 字樣時轉紅（防路由圖殘留懸空節點）
- Test: implement／iteration SKILL.md 仍指示 invoke `samsara:security-privacy-review` 時轉紅

## Unit Test Contract

- Contract source: 文件化 artifact shape——validate-and-ship SKILL.md 的 Step 0 條款（7 條語義的 concept tokens，遵循 references/test-contract.md：順序用結構位置比較，非 label-presence）、bootstrap 路由圖節點集合、implement/iteration 的 Transition 目標 skill 名
- A unit test must assert this named contract source, not implementation details.

## Implementation Steps

- [ ] Step 1: Write death tests
- [ ] Step 2: Run death tests — verify they fail
- [ ] Step 3: Write unit tests asserting the named Unit Test Contract source
- [ ] Step 4: Run unit tests — verify they fail
- [ ] Step 5: Implement minimal doc changes to pass all tests（先寫入 validate-and-ship，最後才刪 skills/security-privacy-review/——刪除順序在後，中途中斷不會出現兩邊皆無的狀態）
- [ ] Step 6: Run all tests — verify they pass
- [ ] Step 7: Write scar report
- [ ] Step 8: Report back (do not commit)

## Expected Scar Report Items

- Potential shortcut: 293 行壓縮進 Step 0 時，某些 per-decision 的 execution-mode 路由細節被合併敘述——列出被合併的決策點清單，供 review 核對語義無損
- Assumption to verify: 除 grep 清點的檔案外，無其他活文件（hooks、CLI、converter 配置）引用 security-privacy-review 目錄路徑
- Assumption to verify: dist/codex 的舊 security skill 目錄由最終 regenerate 移除（本 task 不動 dist/）
- Potential shortcut: 折入後 validate-and-ship SKILL.md 變長（單檔 300+ 行）——單檔膨脹 vs 總量減少的取捨，記錄實際行數變化

## Acceptance Criteria

- Covers: "Silent failure - security gate 折入後可跳過或 unknown 當 pass"
