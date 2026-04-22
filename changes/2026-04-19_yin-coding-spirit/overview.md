# Overview: samsara-code-quality-reviewer

## Goal

建立 `samsara:code-quality-reviewer` agent 與配套 reference，作為既有 `samsara:code-reviewer` (yin) 的 sibling，在 `samsara:implement` / `samsara:iteration` 並行 dispatch，填補 samsara 目前 **code-level quality review** 的缺口。

## Architecture

Sibling parallel reviewer pattern：兩個 reviewer（yin-focused + quality-focused）在既有 review 觸發點並行 dispatch，各自獨立，無共享 state。兩者都 PASS 才允許 commit；其中一個 FAIL 就 block。這延續 samsara 既有的 **specialist composition** 架構（類似 structure-explorer / infra-explorer / yin-explorer 三者的關係）。

## Tech Stack

- Agent definition: YAML frontmatter + Markdown system prompt (~100 lines, 同 samsara 其他 agents)
- Reference doc: Markdown with code examples (參考 `samsara/references/` convention)
- Skill modifications: 既有 `samsara/skills/implement/SKILL.md` 和 `iteration/SKILL.md` 的 dispatch sections
- Model: sonnet (與既有 code-reviewer 同，避免無理由的 model variance)
- Test infrastructure: Manual dispatch validation procedure (non-CI)

## Key Decisions

- **新 agent 而非擴充既有 code-reviewer**: 既有 reviewer 有明確 `Focus on what code DOES, not LOOKS LIKE` 的 constraint，和 quality review 直接衝突。混合會稀釋身份。（/level-analysis 三層一致建議）

- **Parallel dispatch 而非 sequential**: 兩者 scope 不重疊，無順序依賴；parallel 節省 wall-clock 時間；也避免「先跑哪個」的偏見污染後跑者。

- **Reference-driven 而非 rules-driven**: code-quality.md 以 8 條 criteria + good/bad examples 為主，**不寫 MUST/MUST NOT rules**。實驗證明 rules-like 寫法在 English 環境下容易誘發 compliance theater；example-driven 可以讓 agent 做具體對照判斷。

- **Reference-unavailable 必須回 UNKNOWN**: 若讀不到 code-quality.md，agent **不得** fallback 到「記憶中的 criteria」；必須 explicit output reviewer 失效。這避免 drift 和虛假 PASS。

- **Scope boundary 寫在 agent prompt 裡**: agent prompt 必須明確列出 out-of-scope 議題（silent rot, dishonest naming, security, performance）並指向哪個 reviewer 負責。避免 Death Case 3 (Scope Violation)。

- **No anchor in implementer prompt (MVP)**: nice-to-have but 不阻塞；implement skill 的 step 強制性就是 gate，不需要 prompt 層級提示。

## Death Cases Summary (Top 3)

1. **Silent False PASS on junior code** — Agent 被餵給明顯 junior-level code 但沒抓到（例如 observe-learnings.py）。驗證用 `fixtures/junior.py`，必須 FAIL + 3 Critical issues。

2. **Scope Violation (Yin Duplication)** — Agent 開始報 silent rot / dishonest naming，跟既有 code-reviewer 重複。驗證：比對兩個 reviewer output 的 file:line 重複率，>10% = scope 滲透。

3. **Parallel Dispatch Silent Skip** — implement skill bug 導致只 dispatch 一個 reviewer。驗證：main agent 必須驗證**兩份** output 到達；單一份 = FAIL with "missing reviewer"，絕不可假設缺席者 = PASS。

## File Map

| Path | Responsibility |
|---|---|
| `samsara/references/code-quality.md` | 8 條 criteria + good/bad examples + 決策規則 |
| `samsara/agents/code-quality-reviewer.md` | Agent identity, scope boundary, I/O format, 決策流程 |
| `samsara/skills/implement/SKILL.md` | 修改 Line 115 (subagent mode) + Line 142 (inline mode) 區塊，改為 parallel dispatch |
| `samsara/skills/implement/dispatch-template.md` | 加入 code-quality-reviewer dispatch template |
| `samsara/skills/iteration/SKILL.md` | 修改 Line 100 區塊，改為 parallel dispatch |
| `samsara/skills/fast-track/SKILL.md` | Step 4 checklist 對稱化（加 3-4 條 quality 問題），fast-track.yaml schema 加 quality_checklist 欄位 |
| `tests/samsara/code-quality-reviewer/fixtures/junior.py` | 來自 hooks/scripts/observe-learnings.py (known-bad) |
| `tests/samsara/code-quality-reviewer/fixtures/clean.py` | 來自 experiment/outputs/en-must-output.py (known-good) |
| `tests/samsara/code-quality-reviewer/fixtures/over_engineered.py` | 來自 experiment/outputs/en-is-output.py (known-over-OOP) |
| `tests/samsara/code-quality-reviewer/validation-procedure.md` | 手動 dispatch 步驟 + 預期結果對照表 |
