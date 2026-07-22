# Evaluation Result: user-facing-communication-contract

## Evidence Boundary

- Observed baseline: Bootstrap had no canonical user-facing presentation contract and required some completion facts through fixed filler-shaped prompts.
- Mechanically verified change: semantic tests now guard the contract owner, response shapes, evidence floor, identifier readability, anti-filler rules, and live Codex conversion.
- Qualitative evaluation: the examples below are contract projections, not claims that every host model has already produced identical prose.
- Unmeasured: response quality across model families and reasoning settings.

## Scenario 1 — Command-only request

**Request:** Reinstall the current Samsara build globally for Codex.

**Before failure shape:** The response can begin with environment explanation,
installation history, and alternative commands before showing the command the
user asked for.

**After projection:**

```text
執行：
uv tool install --force . && samsara-cli install codex --scope global --force

這會以目前 working tree 重新安裝 CLI，並更新 Codex global artifacts。
```

**Difference:** The command is first. One consequence remains because it changes
what the user is authorizing; no workflow recap or forced next step is added.

## Scenario 2 — Completed change with verification detail

**Request:** Confirm the complete Codex companion runtime repair.

**Before failure shape:** The response can lead with implementation chronology,
repeat each planning decision, and scatter modified files and tests across a
long narrative. A terse alternative can overcorrect by saying only that the
tests pass.

**After projection:**

```text
已完成 Codex global companion runtime 修正，commit c058444。全域安裝現在使用 manifest 記錄的絕對 samsara-cli 路徑，不再依賴 source .venv。

主要改動
- Installer：驗證 durable runner、寫入 runtime manifest、拒絕 interpreter fallback。
- Converter：將 companion command 解析成已驗證的 absolute runner。
- Tests：覆蓋 foreign cwd、clean PATH、manifest migration 與 missing-runtime failure。

驗證
- 全套 pytest 通過。
- pre-commit 通過。

未解風險
- 無已知未解項目。
```

**Difference:** A result-only reader can stop after the first paragraph. A
detail-oriented reader still gets responsibility-grouped changes, verification,
and an explicit unresolved-risk result without reading planning artifacts.

## Scenario 3 — Detailed review with many findings

**Request:** Review a workflow layer and list every meaningful issue.

**Before failure shape:** Findings can appear in discovery order, mix design
violations with wording polish, and refer to unexplained IDs such as `AC-2` or
`PT-D3` as if the codes were conclusions.

**After projection:**

```text
結論：有 2 個會改變執行行為的契約問題，另有 3 個文字精度問題；設計方向本身可保留。

契約問題
- 驗證發現交接欄位不一致（驗收情境 AC-2）：Validate 產出的 finding 缺少 Iteration 要求的 severity 與 path，weak model 可能在兩層間被互相拒絕。
- Auto decision 引用未固定 snapshot：目前 ref 可能在 manifest 清空後失效。

文字問題
- ...

需要修改的檔案
- skills/validate-and-ship/SKILL.md — finding producer contract
- skills/iteration/flow.md — consumer reference
```

**Difference:** Severity and responsibility provide the scan path. The semantic
label explains each machine ID at first use, so the user need not open the
acceptance artifact merely to decode it. Detail is retained rather than capped.

## Scenario 4 — Blocked or unknown result

**Request:** Validate an installed Codebase Map artifact.

**Before failure shape:** The response can narrate attempted workarounds or imply
that a missing validator was bypassed successfully.

**After projection:**

```text
尚未完成驗證：安裝內容沒有可執行的 Codebase Map validator。

- 證據：預期的 installed companion path 不存在。
- 原因：目前未知；不能用 system Python 推測替代 runtime。
- 恢復方式：重新安裝包含 companion runtime 的 Samsara build，再重跑原 validator command。
```

**Difference:** Status, evidence, unknown cause, and recovery are visible. The
response does not hide the blocker or invent a successful fallback.

## Scenario 5 — Destructive action

**Request:** Discard the current uncommitted changes.

**Before failure shape:** A generic short-response rule can put a destructive
command first or treat confirmation as removable preamble.

**After projection:**

```text
這會永久丟棄 3 個 tracked files 的未 commit 修改；untracked files 不受影響。請確認是否執行。
```

**Difference:** Brevity stops at the safety boundary. The response states the
observable damage and waits for confirmation instead of exposing an executable
destructive command.

## Contract Evaluation

| Signal | Result | Evidence |
|---|---|---|
| Opening stands alone | pass at contract level | Four request shapes are explicit in Bootstrap and guarded by test |
| Applicable detail survives | pass at contract level | Changed files, verification, unresolved risk, blockers, and uncertainty are named |
| Machine IDs remain readable | pass at contract level | Human-facing semantic label must precede a machine ID |
| Arbitrary brevity is rejected | pass | Fixed word caps, hard list caps, and unsupported estimates are explicitly prohibited |
| Safety survives compression | pass | Blocker, uncertainty, decision-changing evidence, and destructive confirmation are non-removable |
| Codex receives the contract | pass | Live `ConversionEngine("codex")` output assertion |
| Cross-model behavior | unknown | Requires future dogfood across model and reasoning settings |

## Verdict

PT-EVAL (evaluation-contract) passes for instruction shape, semantic guards, and
Codex conversion. Cross-model response quality remains an explicit unmeasured
surface; it is not represented as implementation failure because the shipped
contract and its observable semantics are present.
