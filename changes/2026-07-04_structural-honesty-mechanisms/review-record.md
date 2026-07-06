# Review Record: structural-honesty-mechanisms（durable 化的 reviewer verdict 摘錄）

依 `skills/implement/dispatch-template.md` Review Record Durability 慣例（本 feature iteration fix-1 自己引入——本檔即該慣例的首次 dogfood）。摘錄非總結——以下為 verdict 原文。task-1~6 的 review 歷程先於此慣例存在，其 verdict 原文已隨 session 逝去（誠實記錄：那些 round 只餘 index.yaml review 欄的壓縮行）；本檔自 iteration fix-1 起。

## Iteration fix-1: dispatch-record durability convention

### Dispatcher-side injection record

`structure_spec: absent`（本 feature 先於它自己建立的機制——planning 時 structure-spec 機制尚不存在，pre-existing feature exemption；無片段注入，無 50% 計算）。

### code-quality-reviewer — verdict 摘錄（round 1）

> ### Mode Declaration
> **Principles Mode.** Feature `changes/2026-07-04_structural-honesty-mechanisms/` predates the structure-spec mechanism it built; no `structure-spec.yaml` instance exists for the feature (`structure_spec: absent`, pre-existing feature exemption). This dispatch injects no spec fragments and no `structure_refs` entries are present in the diff. No Spec Mode Additions apply.
>
> ### drift_items
> `[]` — Principles Mode; no `structure-spec.yaml` entries exist for this feature to check drift against.
>
> ### Summary
> - Critical concerns: 0
> - Important concerns: 5
> - Suggestions: 1
> - Principles with UNKNOWN (non-applicable): 3 (L, Pattern, and Mode-level: no Spec Mode Additions apply)
> - Overall verdict: **PASS_WITH_CONCERNS**

（5 個 Important 全數修正於同 fix 的 round-2 修正批次：consumer-side 3-source order、yin Feature 欄位 ghost promise、檔內 DRY、test helper span、O-bet honest marker——主 agent 依 task-5 先例（0 Critical）直接驗證結案，驗證方式：逐項 diff 檢視 + 測試實跑 60/60。）

### code-reviewer（yin）— verdict 摘錄（round 1）

> ### Verification Performed
> - Mutation testing (edit → run targeted test → revert, diff-confirmed restoration) on all 4 new tests, each confirmed to go RED on the specific claim it guards
> - Cross-checked the cited precedent `changes/2026-07-05_issue-002-validate-live-surface/review-record.md:8,10` — the "30 lines vs 25" transcription annotation is present verbatim as claimed.
>
> ### Summary
> - Deletable code found: no
> - Placement vs plan Key Decisions: **matches** — KD-1 (review-record.md landing in `changes/<feature>/` is consistent with feature-dir artifacts being the durable layer), KD-2 (all changes in `skills/` + companion test file, no `samsara_cli` paths), KD-4 (the fix documents drift_items' *persistence location* only, does not take over iteration's aggregation or validate-and-ship's reconciliation responsibilities — explicitly disclaims wiring a consumer)
> - Dishonest names found: no
> - Silent rot paths found: yes (disclosed) — prose-only convention with no runtime/test enforcement of actual compliance; see Important Issues
> - Overall: **PASS_WITH_CONCERNS**

（yin 3 個 Important：fix-1-scar Rule 10 violation（修正於 round-2 批次）、self-iteration all-deferred pattern surfaced（rationale 已在 scar，無動作）、prose-only silent rot（systemic，ISSUE-003 承載）。）

## Iteration fix-2: measured-numbers discipline

### Dispatcher-side injection record

`structure_spec: absent`（同 fix-1——本 feature 無 spec 實例，無注入）。

### code-reviewer（yin）— verdict 摘錄（round 1）

> ### Important Issues
> - **`agents/implementer.md:184-185`** — The `## Report Format` addition ("Every quantitative field below follows Mandatory Behavior #5 — measured with a named command, or labeled as an unmeasured estimate.") is a compressed **restatement**, not a bare pointer. [...] The scar report's assumption (`fix-2-scar.yaml:24-26`) marks this "verified: true" with the claim it "does not duplicate content," which is an overstated self-verification — ironic in a fix whose entire subject is not overstating verified claims.
>
> ### Summary
> - Critical: 0 / Important: 1 / Suggestions: 1
> - Placement vs plan Key Decisions: matches（KD-2、KD-5 +5 lines 實測相符、constraint-ownership split respected）
> - Overall: **PASS_WITH_CONCERNS**

### code-quality-reviewer — verdict 摘錄（round 1）

> **Mode:** principles mode (structure_spec: absent — pre-existing feature exemption confirmed)
>
> ### Important Issues
> - **`tests/test_skills/test_structure_spec_contract.py:1943`** Coupling — `assert "\n6." in section` pins the measured-numbers rule to its ordinal position (6th) in the `## Rules` list, not only to its substantive content [...] insertion of a new rule that shifts rule 6's ordinal [...] reddens this test for a reason unrelated to the observable contract.
>
> ### drift_items
> []
>
> ### Summary
> - Critical concerns: 0 / Important concerns: 1 / Suggestions: 0
> - Overall verdict: **PASS_WITH_CONCERNS**

（兩個 Important 均由主 agent 於 review round 直接修正並實測驗證（task-5 先例，0 Critical）：Report Format 行改純 pointer、測試移除 "\n6." 序數斷言改內容錨定、fix-2-scar 第三 assumption 如實改記 verified: false + resolved。全套 936 綠（`uv run pytest tests/`）。註記：quality 對 Report Format 行判 DRY Pass 與 yin 的 restatement 判定相左——主 agent 讀原文裁決 yin 正確（該行含 MB#5 執法機制的迷你重述），已修。）
