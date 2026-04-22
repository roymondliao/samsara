# Kickoff: Security & Privacy Review Gate

## Problem Statement

Samsara 的 validate-and-ship 流程缺少 security & privacy 檢查。Committed changes 可能包含 credential leaks、injection vulnerabilities、privacy violations 等問題，直接 push 到 repo 後才被發現（或永遠不被發現）。需要在 push 前加入一個 security gate，用平台內建的 security review 能力攔截問題。

## Evidence

- 當前流程：implement → (iteration) → validate-and-ship → push。沒有任何 security-specific 檢查步驟。
- validate-and-ship 的 code review (Step 5) 問的是「能不能刪、命名有沒有說謊、三年後會不會被詛咒」— 這是 code quality，不是 security。
- Security issues 的特性是 blocking — 不能像 failure budget 一樣 accept and ship。

## Risk of Inaction

Credential leaks、API keys、PII exposure 等直接進入 repo。一旦 push 到 remote，即使後續刪除，git history 仍然保留。Secret rotation 的成本遠高於 push 前攔截。

## Scope

### Must-Have (with death conditions)

- **獨立 chain skill `samsara:security-privacy-review`** — Death condition: 如果連續 20 次 review 都是 no issues，且專案類型不涉及 secrets/PII，考慮是否 scope 太窄
- **Platform-agnostic 描述** — 不綁定特定 coding agent 的 security tool。Death condition: 如果 Phase 7 multi-platform 計畫取消（所有平台都不支援），可退化為 Claude Code 專用
- **Human gate on issues** — 發現問題時呈現 issue list + 修復建議，human 確認。Death condition: 如果 human 連續 10 次都不看內容直接 approve，gate 已失效
- **Fix loop** — 修復後可重跑 security review 直到通過。Death condition: 如果 fix loop 超過 3 次，問題可能不在 security 而是 architecture

### Nice-to-Have

- Security review 結果記錄在 ship manifest 中（history preservation）
- Review scope 可配置（例如排除特定 file patterns）

### Explicitly Out of Scope

- 不自建 security review 工具或 agent — 用平台內建能力
- 不覆蓋 CI/CD security scanning — 那是 pipeline 層的防線，不是 dev workflow 層
- 不處理 Phase 6 提到的非 imperative code（IaC、Dockerfile 等）的 security review

## North Star

```yaml
metric:
  name: "pre-push security issue interception rate"
  definition: "security/privacy issues caught by the gate before reaching remote repo"
  current: 0 (no gate exists)
  target: ">0 (any interception proves value)"
  invalidation_condition: "if all security issues are caught by CI/CD before human review, this gate is redundant"
  corruption_signature: "gate only catches low-severity issues (formatting, naming) while missing high-severity (credential leak, injection) — numbers look good but protection is hollow"

sub_metrics:
  - name: "false positive rate"
    current: unknown
    target: "<50% (security domain inherently noisy)"
    proxy_confidence: low
    decoupling_detection: "if human always approves without reading, proxy is decoupled from actual security posture"
```

## Stakeholders

- **Decision maker:** Human (repo owner)
- **Impacted teams:** All developers using samsara workflow
- **Damage recipients:** Developer velocity (extra gate before push); human attention (reviewing false positives)
