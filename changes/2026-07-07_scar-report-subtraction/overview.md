# Overview: scar-report-subtraction

## Goal

讓 scar report 的簡潔可讀由結構＋validator 機械保證：新寫入用定長槽位、超預算 = handoff finding、schema 瘦身為一頁寫入契約。

## Core Identity (L1 — cited from pre-thinking, not re-derived)

Scar report 是寫給未來讀者的最小損害地圖：一條疤 = 哪裡有疤、什麼條件下咬人、去哪裡看。Schema 是寫入契約，validator 是契約唯一有牙齒的執行者；不被機器消費也不改變未來讀者行動的字，不屬於這份文件。

## Architecture

寫入端（scar-schema.yaml → dispatch 注入 → implementer）與讀取端（iteration Step 1 aggregator）分家：schema 只載當前寫入格式＋預算＋去別處對照表；三代格式相容規則的 canonical home 遷至讀取端。validate_format.py 新增 length-budget 與 legacy-form 檢查類，沿用既有 finding 語彙與 exit 0/1/2 三態。

## Tech Stack

Python 3（validate_format.py, PyYAML）、pytest（doc-contract ＋ 行為測試）、samsara_cli（dist regenerate）。

## Key Decisions

- D1 定長槽位（what/bites_when/where/accepted_because）取代 description blob；`assumptions_made` 保三欄；`structural_decisions` 完全不動：structural_decisions 是定長欄位成功先例，且被測試與 quality reviewer 消費中
- D2 預算住 validate_format.py，超標 = FINDING 非 warning：validator 是唯一有牙齒的 gate；warning = 回到已失敗的 prose 規則路線
- 預算數值（校準自 25 份歷史 report 條目分佈）：欄位 ≤200 chars（where ≤120）、item ≤6 行、structural entry ≤10 行、narrative ≤10 行、report ≤90 行；中位 ≤60 是 North Star 結果指標非 validator 上限
- D3 compat 讀取規則 canonical home = skills/iteration/SKILL.md Step 1：寫者只見當前格式、讀者見全歷史（write-read-boundary）；沿 Rule 9 canonical-home 先例
- D4 廢規則編號 → 具名錨點（write-filter、granularity-floor…）：編號被 5 檔 ~14 行跨檔承重且無機制驗證，本次刪規則必然重編號 → 具名化
- D6 世代識別用欄位形狀推斷（plain string／description／what+bites_when），不加 schema_version；舊 report 不遷移
- legacy-form 檢查封死逃逸：新 report 用 description blob = finding（validator 只在新 feature handoff 執行，可嚴格）
- Placement：schema 留 skills/implement/templates/（單一寫入源不動）；golden fixture 進 tests/fixtures/scar_reports/（Primary evaluator 必須能消費）

### Real Seams (L1 — single source of seam declarations)

- seam: scar-write-contract
  what: scar-schema.yaml 作為唯一寫入契約，全文注入每次 implementer/iteration-fix dispatch
  evidence: already-happened（git af437a5 "unify into single source of truth"；skills/implement/dispatch-template.md:38,84）
  planned: task-2, task-4, task-6
- seam: write-read-boundary
  what: 寫入端（schema→implementer，只見當前格式）與讀取端（iteration Step 1 aggregator，讀全歷史三代）的邊界
  evidence: already-happened（Rule 9 canonical-home 先例，git eb4ae07）＋ domain-essential（寫者與讀者生命週期本質不同）
  planned: task-1, task-5
- seam: format-vs-judgment
  what: validate_format.py 只檢機械可判定形狀；語意品質（白話/具體）歸 reviewer，永不進 validator
  evidence: already-happened（skills/implement/scripts/validate_format.py:2-8 docstring）
  planned: task-3

## Death Cases Summary

1. DC-A 預算逃逸：寫作者改用 legacy `description` blob 繞過槽位預算 → legacy-form finding 封死
2. DC-B 聚合丟失：aggregator 誤判第三代欄位形狀，新格式 items 靜默掉出 signal_lost → 三代混合 fixture 計數測試
3. DC-C 單一源漂移：compat 規則在 schema 與 iteration 兩處並存各自演化 → anti-duplication death test（schema 再現 compat token 即紅）

## File Map

- `skills/implement/templates/scar-schema.yaml` — 重寫為一頁寫入契約（槽位＋具名錨點＋預算表＋去別處表＋短例）
- `skills/implement/scar-report.md` — 同步指引（write filter 引用改具名錨點）
- `skills/implement/scripts/validate_format.py` — 新增 length-budget／legacy-form／槽位必填檢查
- `skills/implement/SKILL.md` — :184 等規則編號引用改具名錨點
- `skills/implement/dispatch-template.md` — 規則編號引用（如有）改具名錨點；schema 注入指示不變
- `agents/implementer.md` — :144,184,208,255-256 規則編號引用改具名錨點
- `skills/iteration/SKILL.md` — Step 1 新增「Scar 格式世代」compat canonical home；:77,80 編號引用改具名
- `tests/test_skills/test_scar_schema_noise_rules.py` — compat 斷言重綁至 iteration；新增 anti-dup／dangling-citation death tests
- `tests/test_skills/test_format_validators.py` — length-budget／legacy-form／槽位解析行為測試
- `tests/fixtures/scar_reports/golden_task4_slot_form.yaml` — golden re-expression fixture（create）
- `tests/fixtures/scar_reports/` 三代混合聚合 fixtures（create）
- `changes/2026-07-07_scar-report-subtraction/golden-re-expression.md` — 誠實無損對照清單（create）
- `dist/codex/…`, `dist/gemini-cli/…` — samsara_cli regenerate（機械同步）
