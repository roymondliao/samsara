# Kickoff: scar-report-subtraction

Execution mode: auto

## Problem Statement

Scar reports in `changes/` have grown too long, vague, and defensive to be read. Recent reports run 146–232 lines with single items up to 60 lines (`changes/2026-07-02_workflow-subtraction-optimization/scar-reports/task-4-scar.yaml:48-83`), stuffed with review history, verification transcripts, and justification prose. The schema already fought this with nine appended prose rules (scar-schema.yaml Rules 9–17) and lost: verbosity got worse as rules accumulated (early 2026-04 reports: 14–24 lines). The reports have become write-only evidence — the exact opposite of a scar's purpose.

## Problem Essence (named handoff to pre-thinking)

一份 scar report 必須讓未來讀者在一分鐘內知道：哪裡有疤、什麼條件下會咬人、去哪裡看。這個可讀性必須由機制保證，不能依賴寫作者的自律或規則文字。

## Boundary Scope (what the seams may be drawn inside)

- **真正要解什麼:** scar report 的簡潔與可讀性從「寫在註解裡的規則」變成「結構與 validator 保證的機械事實」。
- **涉及哪些:** `skills/implement/templates/scar-schema.yaml`、`skills/implement/scar-report.md`、`skills/implement/SKILL.md`（step 9/11/18）、`skills/implement/dispatch-template.md`（schema 注入面）、`skills/implement/scripts/validate_format.py`、`skills/iteration/SKILL.md` Step 1（讀取面向後相容）、`agents/implementer.md`（若引用 scar 格式）、`tests/test_skills/test_scar_schema_noise_rules.py`、`tests/test_skills/test_format_validators.py`。
- **哪些現在不做:**
  - 不遷移/回填舊 scar reports — 歷史文件無讀者，遷移成本純損耗；aggregator 保持雙格式讀取即可。
  - 不重設計 review record / transition record 容器 — 本 feature 只給「這類內容去別處」的指引，不動別人的地盤。
  - 不做語意品質（白話與否、具體與否）的自動判斷 — 那是 judgment，屬於 reviewer；validator 只管機械可判定的長度與形狀。
  - 不動 `.samsara/systemic-scars.yaml` registry 格式 — systemic_ref 機制本身運作正常。
  - 不動 iteration 的 signal_lost 計算公式 — 只要新舊條目都能被計入，公式不變。

## Evidence

- `wc -l` over all 91 scar reports: recent features median ~180 行；`workflow-subtraction` task-4 = 233 行，`contract-bound-unit-tests` 六份全部 205–254 行。
- Task-4 是在 Rules 10–13（write filter、單行 verified、narrative 反模式）已存在之後寫的，仍含 60 行單一條目、review 裁決史（"FINAL DISPOSITION"、"HONESTY CORRECTION"）— 規則被寫進註解，行為未改變。這正是本 repo 已登記的 systemic scar `doc-vs-runtime-obedience` 的又一實例。
- `validate_format.py` 只檢查形狀（dual-face、dangling ref、debt consistency），零長度檢查 → 「寫長」永遠不會被任何機制抓，「漏寫」會被 reviewer 抓 → 冗長是理性策略。
- 下游消費面（`skills/iteration/SKILL.md:74-103`）只讀：`deferred_to_feature_iteration` 條目、`status: resolved` 標記、`systemic_ref`、parse 成敗。長敘事無任何消費者。

## Risk of Inaction

Scar report 徹底淪為儀式：寫的人花 token 產出防禦文，讀的人（人類與 agent）跳過它，真正的疤（會咬人的 silent failure）淹沒在辯護噪音裡。到某一天一個被埋住的疤咬人時，report 明明「有寫」但等於沒寫 — 這比不寫更糟，因為它提供了虛假的已盡責感。

## Scope

### Must-Have (with death conditions)

- **定長槽位 item 結構**（如 `what` / `bites_when` / `where` / `accepted_because`，每欄一行）取代自由文本 `description` blob — Death condition: 若新結構上線後 3 個 feature，槽位仍平均被塞超過預算的長文（結構治不了，寫的人繞過槽位），降級此項、改由 validator 預算獨挑。
- **`validate_format.py` 長度預算**：每欄位/每條目/整份 report 的機械上限，超標 = format finding，handoff 不得通過 — Death condition: 若預算導致真疤被砍（reviewer 在 ≥2 個 feature 抓到 honesty loss 源於壓縮），重新校準閾值；若無法校準到不傷誠實，移除預算、只留槽位。
- **「去別處」對照表**：review 裁決史 → review record；驗證過程 → transition record / 測試名；before/after 統計 → commit message — Death condition: 若連續 3 個 feature 無任何 report 需要引用它，縮成 schema 內一行提示。
- **Schema 本身瘦身**：writer 看到的是一頁模板＋預算；backward-compat 讀取規則（現 Rules 7/8/11/14/15 的相容半段）移到 aggregator 端（iteration Step 1 already canonical for部分） — Death condition: 若搬移後兩端規則漂移（同一相容行為兩處描述不一致被測試抓到），收回單一檔案。

### Nice-to-Have

- Dispatch-template 注入的 schema 片段同步瘦身（減少每次 dispatch 的 token 成本）。
- `rtk`/CLI 端若有 snapshot 測試引用 schema 全文，順手更新。

### Explicitly Out of Scope

- 舊 scar reports 的遷移或重寫。
- Review record、transition record、commit message 格式的重設計。
- 語意品質（白話、具體性）的自動評分。

## North Star

```yaml
metric:
  name: "new_scar_report_budget_compliance"
  definition: "新制上線後，每份新 scar report 通過 validate_format.py 長度預算（整份 ≤60 行、單一條目 ≤6 行、單欄位 ≤200 字元 — 確切閾值由 planning 校準）且零 over-budget finding at handoff"
  current: "無預算檢查；近期 report 中位數 ~180 行，最長 254 行"
  target: "100% 新 report 通過預算；中位數 ≤60 行"
  invalidation_condition: "若 iteration/debugging 反覆需要重新挖掘被壓縮掉的脈絡（同一疤因缺context被重新調查 ≥2 次），證明長敘事其實有讀者，目標本身錯了"
  corruption_signature: "內容位移：narrative 原文整段搬進 commit message / task log 以繞過預算；或 report 變短但條目數異常下降（clean-scar 反模式率上升）而 diff 規模不變 — 由 reviewer 抽查 + iteration signal_lost 趨勢偵測"

sub_metrics:
  - name: "budget_findings_per_feature_at_handoff"
    current: n/a
    target: 0
    proxy_confidence: medium
    decoupling_detection: "validator 全綠但人類在 validate-and-ship 仍讀不懂 report（主觀抽查）→ proxy 與主指標脫鉤，代表預算閾值對了但槽位語意設計錯了"
```

## Stakeholders

- **Decision maker:** roymond（repo owner）
- **Impacted teams:** implementer agent（寫入面）、iteration aggregator（讀取面）、code reviewers（引用面）
- **Damage recipients:** implementer 承受壓縮成本；reviewer 失去 in-scar 的 review 軌跡（必須改用 review record）；schema 維護者承受雙格式並存期
