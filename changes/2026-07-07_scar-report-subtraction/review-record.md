# Review Record: scar-report-subtraction

Verbatim excerpts of reviewer verdicts (per dispatch-template Review Record Durability). Absent entry for a reviewed task = never recorded (DC-5 finding), not "nothing to record".

## Task 1 — Compat 讀取契約遷入 iteration Step 1

### Round 1 — yin (samsara:code-reviewer): PASS_WITH_CONCERNS, 2 Critical

> **`tests/test_skills/test_scar_schema_noise_rules.py:266-269`** (`test_death__iteration_step1_documents_all_three_scar_format_generations`): `assert "what" in step1 and "bites_when" in step1` — the `"what" in step1` half is tautological/silent-green in isolation. `"what"` is an ordinary 4-letter English word with no adjacency or quoting constraint […] I confirmed by mutation: deleting the actual Gen-3 identifying line […] and inserting one unrelated sentence containing the word "what" elsewhere in the same section keeps `"what" in step1` == `True` […] If a future edit renames the `what` slot (e.g. to `cause`/`trigger`) while keeping `bites_when` intact, this test stays green even though the docstring explicitly claims to guard "the Gen 3 `what`/`bites_when` slot scar item shape."

> **`changes/2026-07-07_scar-report-subtraction/scar-reports/task-1-scar.yaml:34-42`** (`resolved_items:` list): this new scar report uses the `resolved_items` list form, which `skills/implement/templates/scar-schema.yaml:110` (Rule 11, pre-existing, untouched by this task) explicitly retires […] This is a real self-inconsistency: the artifact documenting the backward-compat migration itself uses the format the schema says is retired for new writes.

Architectural placement (round 1): D3 matches; schema untouched (zero diff lines) matches; D6 matches; D4 transitional tokens preserved matches. Seam check: "the new text is genuinely read-side […] The one soft spot is the Gen-3 pre-announcement of a not-yet-existent schema shape […] a seam-timing risk, not a seam-placement violation, and is already self-flagged."

### Round 1 — quality (samsara:code-quality-reviewer): PASS_WITH_CONCERNS, 0 Critical, 2 Important

> **skills/iteration/SKILL.md:85** — O (Marked Bet) — the field-shape-inference fragility ("if a 4th generation is shape-ambiguous with Gen 2/3, inference breaks silently") is recorded only in `task-1-scar.yaml:86-92`, not inline where a future Step-1 editor adding a Gen 4 would see it.

> **tests/test_skills/test_scar_schema_noise_rules.py:70-79** (structural evidence, not final verdict) — Coupling — `_iteration_step1_section`'s exact-heading-string match couples 3+ tests (one rebound, two new) to the literal doc heading text rather than the Step-1 concept; a cosmetic heading reword reddens all of them at once.

DRY judgment on the disclosed test redundancy: "largely justified — both assertions read the SAME live extraction of the SAME file at test-run time, so there is no independent 'second truth' that can silently drift out of sync […] Downgraded to Suggestion."

### Round 2 (re-review after fixes) — yin: PASS

> **Prior Critical 1 […] — RESOLVED.** `tests/test_skills/test_scar_schema_noise_rules.py:96` now uses `re.search(r"what\s*/\s*bites_when", step1)` […] I ran an independent mutation check (not just trusted the claim): Mutated `skills/iteration/SKILL.md:88` to `- **Gen 3 — whatever nonsense slots:** unrelated decoy prose that happens to contain the word what and separately bites_when somewhere far away.` → test went **RED** with `assert None` on the regex search […] Restored the file → **18 passed**.

> **Prior Critical 2 […] — RESOLVED.** `known_shortcuts[0]` (lines 4–16) now carries the description in place with `status: resolved` (line 11) and a one-line `resolution` […] No `resolved_items` key exists anywhere in the file (confirmed via `yaml.safe_load` key inspection).

### Round 2 (re-review) — quality: PASS_WITH_CONCERNS, 0 Critical

> Prior Important #1 (O — Marked Bet) is **resolved**: `skills/iteration/SKILL.md:85` marks the shape-inference bet inline, at the site, without bloating the section.

> Prior Important #2 (Coupling — `_iteration_step1_section` literal-heading dependency) **remains**, by design (out of scope this round). My position: acceptable to carry forward given it is pre-existing shared infrastructure that fails loudly rather than silently; it should not gate this task's PASS but should not be forgotten either.

> Yin's Critical 1 fix […] introduces no new structural concern — it couples only to the field-name adjacency it is meant to guard, not to surrounding markdown formatting.

**Task-1 aggregate outcome:** both reviewers pass (yin PASS / quality PASS_WITH_CONCERNS with zero Critical); index.yaml updated (done, scar_count 4, unresolved_assumptions 0). Carried-forward non-gating debt: `_iteration_step1_section` literal-heading coupling (pre-existing shared test infra).

## Task 2 — scar-schema.yaml 重寫為一頁寫入契約

### Round 1 — yin: PASS_WITH_CONCERNS, 1 Critical + 3 Important

> **`tests/test_skills/test_scar_schema_noise_rules.py:783-786`** […] the `where:` slot-declaration assertion is silent-green/tautological. Confirmed by mutation test: I deleted all three actual `where: "..."` slot lines […] and the test **still passed**, because the substring `"where:"` is also matched inside `# go-elsewhere:` […] the assertion currently provides zero protection for the `where` slot field specifically.

> **Important**: the anti-dup token set covers Rules 7, 8, and 14 but omits Rule 11's own backward-compat clause […] **Important**: `structural_decisions[0].decision` (218 chars), `.refused` (245 chars), `.risk_if_wrong` (295 chars) all exceed the schema's declared "field ≤200 chars" budget […] The schema does not explicitly exempt `structural_decisions` string fields from the general field-char budget […] **Important**: asserts `"≤200"`, `"≤6"`, `"≤90"` as bare Unicode-glyph substrings only […] brittle/over-fit pole.

17-rule spot-check: "Rule 6 […] correctly deleted as a write-side field. Verified this is *intentional retirement*, not information loss […] Rule 14 […] correctly deleted from schema and confirmed present, addressed to the aggregator, in `skills/iteration/SKILL.md` Step 1 […] nothing here was writer-facing, so nothing is lost for writers." Placement: all decisions **matches**；anti-dup test 突變驗證真能轉紅（reintroduced "missing deferred flag = false" → red → restore 乾淨）。

### Round 1 — quality: PASS_WITH_CONCERNS, 0 Critical, 1 Important

> **Coupling** — the two new death tests bind to incidental textual form (exact deleted phrase strings; a single Unicode glyph) rather than the semantic write-contract shape, creating disclosed blind spots […] → referred to yin.

S 原則裁定：schema 重寫後「a genuine single-responsibility narrowing」；DRY：legacy-invalid 與 systemic-ref 均「delegate […] with 'not restated here' rather than copying text」。

### Round 2 (re-review after fixes) — yin: PASS_WITH_CONCERNS, 0 Critical

> **Critical fix (slot-token anchoring), own mutation check on `where:`** […] `re.search(r"^\s*-?\s*where:", ..., re.MULTILINE)` correctly returned no match (red), while a naive bare-substring check still returned `True` […] **RESOLVED.** [All 3 prior Importants] **RESOLVED.**

> New Important: [budget test] guards only three of the schema's five stated budget figures […] It omits `≤120` […] and `≤10` […] A future silent edit narrowing `≤120`→`≤12` or widening `≤10`→`≤100` would have no test catching it.

Budget-scope 裁定（給 task-3 的契約）：「`≤200` chars applies to `what`, `bites_when`, `accepted_because`, `resolution` […] plus `assumption`/`note` […]; `≤120` chars applies only to `where`; `decision`/`refused`/`risk_if_wrong`/`serves_seam`/`forced_by` on `structural_decisions` carry no char cap and are governed only by the `≤10`-lines-per-entry budget.」

### Round 2 (re-review) — quality: PASS_WITH_CONCERNS, 0 Critical

> The budget-scope clarification is honest scoping, not added complexity. The two-tier split […] is drawn along a real pre-existing boundary […] and the boundary is marked in the same paragraph that draws it.

> Suggestion（誠實性）: the claim that [paraphrase-blindness] is *also* written into a scar report's "fail-silently section" does not check out against the live files […] should be added as an explicit `known_shortcuts` item.

### Round 3 — main agent applied both reviewers' verbatim prescriptions (mechanical)

因 implementer session limit，主 agent inline 執行雙方開列處方：budget_patterns 補 `≤120`/`≤10`（5/5 全守）；task-2-scar.yaml 補 anti-dup 逐字比對盲點的 known_shortcuts 條目（使 quality 指出的不實聲稱成真）；schema 補 deferred/resolved 互斥註記（yin Suggestion）。驗證：`uv run pytest tests/` → **933 passed**；scar report 39 行（預算內）、YAML 可解析。

**Task-2 aggregate outcome:** 雙審 0 Critical 通過；index.yaml updated（done, scar_count 6, unresolved_assumptions 0）。

## Task 3 — validate_format.py 長度預算／legacy-form／槽位必填檢查

### Round 1 — yin: PASS_WITH_CONCERNS, 0 Critical, 2 Important

> **tests/test_skills/test_format_validators.py:626-650 vs validate_format.py:339-343** `_check_required_slots` checks all three of `what`/`bites_when`/`where`, but only `bites_when` […] and `where` […] have death tests. There is no death test for a `what`-missing item — an asymmetric coverage gap on one of the three checked axes.

> **validate_format.py:186-199 (`_narrative_line_count`)** The "duplicate top-level `narrative:` key keeps the last occurrence" claim […] is behaviorally correct — I verified it manually against `yaml.safe_load`'s actual last-key-wins semantics — but no test exercises this path.

驗證紀錄：「Drift test […] genuinely parses schema text via regex and compares against the module constants — confirmed non-tautological by manual mutation」；「Line-count technique (yaml.compose node marks) verified empirically against a real 7-line item fixture: computed span = 7」；「`SCAR_OK` fixture investigated: it never used the `description` form to begin with […] not a check hole」；「No judgment-side logic leaked into the validator」。Validator 對 feature dir 實跑：exactly 10 findings, all task-1 Gen-2（已知過渡狀態）。

### Round 1 — quality: PASS_WITH_CONCERNS, 0 Critical, 2 Important

> **task-3-scar.yaml:62** — O: forced_by citation `"affects task-3: ..."` does not resolve to any index.yaml `affects` entry […]; it mimics the feature's own verified-quote convention (`task-1-scar.yaml:71`) without the underlying resolvability. A future reader tracing this bet's justification back to its declared source finds nothing.

> **validate_format.py:85,268,287 vs scar-schema.yaml:29-56** — Coupling: the set of field *names* subject to the char-cap is coupled to the schema's field list but only documented in a comment, not drift-tested (unlike the numeric budgets).

Pattern 原則裁定：三個檢查直呼、無 speculative check-registry framework（from code shape）；DRY Suggestions：char-cap snippet ×4、iteration skeleton ×3。

### Round 2 — main agent verified implementer's fixes (reviewers' verbatim prescriptions)

四項 Important 全修：(1) forced_by 改誠實引用 `git: tasks/task-3.md:9`；(2) 補 `what`-absent death test；(3) duplicate-narrative-key last-key-wins 測試釘住；(4) char-cap 欄位名集中為 `CHAR_CAPPED_FIELD_NAMES` 常數（檢查函式實際使用，非手抄副本）＋欄位名防漂移測試。DRY 兩個 helper 採納（`_char_cap_finding`、`_iter_raw_items`，具體無框架）；拆 `_check_length_budget` 婉拒（granularity-floor：單一 death-reason 下的軸檢查，無獨立消費者）。check-registry 拒絕補為第二個 structural_decisions entry（forced_by: tasks/task-3.md:37）。

主 agent 驗證：`uv run pytest tests/` → **951 passed**；validator 對 feature dir → 恰好 10 findings 全為 task-1 Gen-2（task-3 scar 自身零 findings）。

**Task-3 aggregate outcome:** 雙審 0 Critical 通過；順帶修復既存 `_registry_ids()` bug（registry `entries:` key 被誤判 dangling — 本 feature 首次真實使用 systemic_ref 才踩出）。index.yaml updated（done, scar_count 9, unresolved_assumptions 0）。Follow-up owned by main agent/task-6: task-1 scar 的 Gen-2→Gen-3 一次性機械遷移（validator 目前 10 findings 皆源於此）。

## Task 4 — 數字規則引用全量 sweep → 具名錨點

### Round 1 — yin: PASS_WITH_CONCERNS, 0 Critical, 2 Important

> **skills/implement/scar-report.md:19,26** — this file was modified with exactly this task's citation-rename pattern […] Yet this file's diff is completely absent from the 941-line task4.diff artifact […] and it is missing from the implementer's claim "21 genuine citations across 6 files".
>
> **Main agent arbitration note（歸屬更正）:** scar-report.md 的兩處引用改寫是 task-2 所為（task-2 report-back 明載 "Synced scar-report.md: Rule 13 → write-filter, Rule 12 → no-review-diary"），非 task-4 漏報；diff artifact 是工作樹對 HEAD 的整體 diff，無法按 task 歸屬。task-4 的 21 處/6 檔清單經 quality reviewer 獨立計數證實精確（tracked 15＋gitignored 6）。yin 的 23/7 計入了 task-2 的編輯。residual 教訓（review 供件應標明 diff 的 task 歸屬邊界）記於此。

> **validate_format.py** […] the claimed residual counts for the deliberately-excluded directories ("dist/ 18 hits + changes/ 31 hits") do not match an independent scoped grep […] this repo has an explicit prior "measured-numbers discipline" fix (bf02cb0) that these self-reported figures don't meet.

### Round 1 — quality: PASS_WITH_CONCERNS, 0 Critical, 0 Important, 3 Suggestions

> Token-count of pre-sweep `Rule N` citations in the 4 tracked files = 15; scar report's claimed +6 in `.samsara/modules/skill-implement.yaml` → 21, matching the task's "21 across 6 files" claim exactly. […] Ran `_DANGLING_RULE_CITATION` regex against `Mother Rule 1/2/3` and citation samples directly in Python — lookbehind correctly excludes Mother Rule mentions while catching `Rule 8`, `rules 7 and 8`, `rules: 7,8,9`.

> Suggestions: module docstring 仍稱 "Task 1"（stale scope label）；`_PLAIN_STRING_REINTRODUCTION_DECOY` never exercises the renamed `_LEGACY_INVALID_ACTUAL_CLAIM` branch（verified by execution）；10-anchor list duplicated verbatim。Referrals → yin：`rule_8` 測試函式名已退役術語；per-file anchor-expectation table 的 change-amplifier 疑慮。

### Round 2 — main agent verified implementer's fixes (reviewers' prescriptions)

全數修復：dist 殘留數字改為 pattern-qualified 實測（30 處/11 檔，_DANGLING_RULE_CITATION pattern）；自查出第二個未量測數字（"20+"→實測 22）；`rule_8` 測試更名 `legacy_invalid`＋歷史註記；module docstring scope 更新為三 task 全覽；`_NAMED_ANCHORS` 常數去重；scar-report.md 納入 positive unit test 覆蓋；optional decoy 採納（`_LEGACY_INVALID_ANCHOR_WITHOUT_CLAIM_DECOY` — 隔離測試改名後的 claim regex 分支）。

主 agent 驗證：`uv run pytest tests/` → **954 passed**；validator → 恰好 10 findings 全 task-1（task-4 scar 零 findings）；pre-commit 全過；無 foreign files 觸碰。

**Task-4 aggregate outcome:** 雙審 0 Critical 通過。21 處數字引用（6 檔，含 gitignored .samsara/modules/）全數改具名錨點；「Mother Rule」無關編號系統以 lookbehind 外科排除。index.yaml updated（done, scar_count 6, unresolved_assumptions 0）。

## Task 5 — Golden re-expression＋三代混合聚合測試

### Round 1 — yin: PASS_WITH_CONCERNS, 2 Critical

> **golden-re-expression.md:66-73** — The "Mechanical line-coverage check" claims (verified by script) that only 13 source lines are uncovered and all are blank/already-covered headers. I re-ran the coverage check independently: **16 lines are actually uncovered**, and two of them — line 210 […] and line 212 […] — are **substantive content, not blank/header lines**. […] A "verified by script" claim that does not hold up is worse than no verification claim.

> **golden-re-expression.md:22,24,29,36,38** — Four+ rows claim destination `review-record.md` or `commit message` […] but **no `review-record.md` file exists** in that feature directory at all（該 feature 早於此慣例）[…] the underlying *scar facts* for these rows are separately preserved directly in the golden fixture […] this is a provenance/citation-honesty defect in the table, not evidence that a genuine scar itself was dropped.

其餘驗證全過：source 原檔零改動、golden 75 行、mutation 親測（刪 Gen-3 item → 紅 → restore 綠）、naive-decoy gap 手算吻合非 strawman、golden validator test 用真 importlib＋真 fixture、re_review_signal/owner 折疊已揭露可接受。

### Round 1 — quality: PASS_WITH_CONCERNS, 0 Critical, 1 Important

> **test_scar_aggregation_generations.py:153-161** Coupling — `assert correct_total - naive_total == 2` is coupled to the *exact item count* of gen3 fixture […] Verified empirically: adding one additional legitimate Gen-3 deferred item makes […] gap becomes 3 — the pinned assertion goes red even though the DC-B property […] is still true.

`structural_decisions: []` 裁定 honest；golden 自身拒絕捏造歷史 forced_by 的推理 sound（"inventing a forced_by citation for it now would be exactly the post-hoc rationalization the rule exists to prevent"）。Referral：對照表自稱 23 列實為 22（measured-number off by one）。

### Round 2 — main agent applied fixes inline (human directive: no further review rounds)

**Process note（durable）:** 使用者於本輪裁示「不需要 review，因為自己的 workflow 會被限制修改的方式」— task-5 修正與 task-6 起改由主 agent inline 執行並自行驗證，不再派 reviewer。此為 human-in-command 對 auto workflow 的明示覆寫，記錄於此。

修正內容（reviewer 處方逐項）：對照表加 Destination semantics legend（規範性 vs 描述性）＋judgment call #4；row 36 範圍 196-208→196-212（納入 +27/-19 兩行實質內容）；覆蓋宣稱以重跑腳本數字取代（12 未覆蓋行全空行，行號列明可重現）；23→22 列數修正；golden accepted_because 恢復逐字任務引文；gap==2 精確釘死改為 fixture 動態推導（expected_gap = gen3 非 resolved 條目數）；_detect_generation 補 systemic_ref 形狀在模型外的揭露；task-5 scar 新增「審計宣稱不實」resolved 條目（誤分類風險的已證實例）。

主 agent 驗證：`uv run pytest tests/` → **959 passed**；validator → clean（5 reports 全過含預算）。

**Task-5 aggregate outcome:** kill-condition #3 未觸發（232→75 行無真疤損失，唯一刪除為零讀者價值辯護文）；審計軌跡誠實性缺陷由 yin 抓出並修復。index.yaml updated（done, scar_count 5, unresolved_assumptions 1 — 逐列語意分類屬 judgment 的已揭露假設）。

## Task 6 — dist regenerate＋全套件整合驗證（inline by main agent, per human directive）

驗證輸出（falsifiable trace）：
- `uv run samsara-cli convert --platform codex` / `--platform gemini-cli` → 兩平台 Conversion complete
- `diff skills/implement/templates/scar-schema.yaml dist/{codex,.gemini 路徑}` → 兩平台 byte-IDENTICAL
- dist 全樹數字規則引用（Mother Rule 除外）→ 0
- `uv run pytest tests/` → **959 passed**
- `validate_format.py changes/2026-07-07_scar-report-subtraction/ --repo-root .` → **clean — 6 scar report(s)**（9 類檢查含 length-budget/legacy-form/slot-required）
- `samsara-cli validate --platform codex` → 12 live-surface findings＝issue-002 既知基線 11＋1（skills/pre-thinking/SKILL.md，另一 session 變更）；本 feature 零新增
- dist/ 為 gitignored（`git check-ignore dist/` 證實）→ regenerate 不產生版控 diff，為本地正確性步驟

**Task-6 aggregate outcome:** done（scar_count 4, unresolved_assumptions 0）。Feature status → done。
