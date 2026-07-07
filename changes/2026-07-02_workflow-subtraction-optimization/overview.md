# Overview: workflow-subtraction-optimization

## Goal

對 samsara 框架本身執行減法：scar 產出去噪、pre-thinking 重設計文件定案刪減、workflow 重複結構移除——同時保證所有既有守護行為不消失。

## Architecture

全部改動都在「指令面」（skill/agent/reference markdown ＋ 兩個 YAML 模板 ＋ 一個新的 repo 層級登記檔），無 runtime code。守護機制是 doc-contract 測試（pytest 讀文件斷言條款存在／缺失時轉紅）；本 feature 的 death tests 同樣採此形式。dist/codex/ 為生成物，最後統一 regenerate。

## Tech Stack

Markdown（skills/agents/references）、YAML（schema/模板/登記檔）、pytest（doc-contract 測試，`uv run pytest`）、samsara-cli（dist 轉換）。

## Key Decisions

- **systemic-scar registry 放 `.samsara/systemic-scars.yaml`**：`.samsara/` 是 repo 層級狀態的既有家（codebase-map.yaml）；scar 以 `systemic_ref: <id>` 引用，不重抄描述。懸空 ref = parse failure。
- **security-privacy-review 折入 validate-and-ship 成 Step 0 STOP gate**：獨立 skill 刪除；三態結果、unknown≠pass、fix loop、auto-reject 語義全數保留且被 death test 釘住。
- **Auto Mode Gate canonical 只存在 `references/auto-mode.md`**：6 個 workflow skill 只留 ≤8 行指針（本階段 workflow_prompt 來源＋gate 覆蓋的決策點）；階段特異行為（validate-and-ship 雙重 trace check）留 inline。
- **expiry 刪除、改訊號驅動重審**：accept 必附「誰在什麼訊號出現時重審」；舊資料的 expiry_date 容忍不報錯。
- **iteration 進入資料驅動**：cross-task pattern 或 signal_lost ≥ 5 才建議進入；解析失敗 → unknown → 不准 skip。
- **index.yaml 是唯一 truth**：TaskCreate/TaskUpdate 是盡力而為的 UI 投影。
- **雙 reviewer 保留**（user 決定）：review 結構與 missing-reviewer 協議不動。
- **正式重寫 skills/pre-thinking/ 不在本次**：只修訂 changes/2026-06-13 的設計文件。
- **舊 scar 格式永遠可讀**：所有新聚合規則必須延續 backward-compat（plain string、缺 flag、含 expiry_date）。

## Death Cases Summary

1. **搬家假減法**——skill 行數降但 reference/新檔等量膨脹，淨 loaded-context 未降；檢核第二段以淨值判定。
2. **去重抹掉階段特異語義**——指針化時 validate-and-ship 的雙重 trace check 或 security auto-reject 消失；death tests 釘住 inline 條款。
3. **舊 scar 聚合靜默歸零／systemic_ref 懸空**——格式演進讓歷史傷疤消失或引用懸空；一律列 parse failure，不准靜默略過。

## File Map

- `.samsara/systemic-scars.yaml` — 新建；repo 層級系統性傷疤登記（id、描述、首錄日期、適用條件）
- `skills/implement/templates/scar-schema.yaml` — 噪音過濾規則：verified:true 單行、resolved 就地標記、narrative 禁流水帳、systemic_ref
- `skills/implement/scar-report.md` — 格式指南同步
- `skills/implement/dispatch-template.md` — schema 注入段同步
- `agents/implementer.md` — Report Format 去重複、scar 寫入過濾問句
- `skills/iteration/SKILL.md` — 聚合（systemic_ref／舊格式）、accept 改訊號驅動、進入判準
- `skills/validate-and-ship/SKILL.md` — 新 Step 0 security gate、Auto Gate 指針化
- `skills/validate-and-ship/ship-manifest.md` — rule 2 改寫（訊號驅動重審）
- `skills/validate-and-ship/templates/ship-manifest.yaml` — accepted_risks 欄位同步
- `skills/security-privacy-review/` — **刪除（整目錄）**
- `skills/samsara-bootstrap/SKILL.md` — 路由圖與 chain skills 清單移除已折入的 skill
- `skills/research/SKILL.md`、`skills/pre-thinking/SKILL.md`、`skills/planning/SKILL.md`、`skills/implement/SKILL.md` — Auto Gate 指針化；implement 另含轉場改寫與 UI 清單措辭
- `skills/fast-track/SKILL.md` ＋ `skills/fast-track/templates/fast-track.yaml` — 只記違規＋reviewed 聲明
- `references/auto-mode.md` — 新增 Stage Gate Protocol canonical 段
- `README.md`、`README.zh-TW.md` — 工作流圖與 skills 表同步
- `changes/2026-06-13_pre-thinking-dynamic-redesign/0-design-direction.md` — 六項修訂
- `tests/test_auto_mode/*` — 指針契約＋canonical 完整性＋反重複 death test
- `tests/test_skills/`（新測試檔）— scar schema 規則、security 折入順序、iteration 判準、fast-track 聲明的 doc-contract 測試
- `dist/codex/` — 最後統一 regenerate（生成物）
