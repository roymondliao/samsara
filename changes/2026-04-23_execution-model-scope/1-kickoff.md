# Kickoff: Execution Model Scope (Phase 6)

## Problem Statement

Samsara 的 `code-quality-reviewer` 和 `code-reviewer` 在收到非 imperative code（Terraform, Dockerfile, K8s YAML, CI/CD configs 等）時，會用不適用的 principles 產出 misleading 的 verdict。問題不是「不能審 IaC」，而是「假裝能審 IaC」— reviewer 不會告訴你它不該審這個，它會給你一個看起來合理但實際無意義的結果。

## Evidence

- `code-quality-reviewer` 的 9 yin principles 全部基於 imperative code 結構（function, class, module, interface）設計
- `code-quality.md` reference file 僅以 Python fixtures 驗證過 3 次（見 `2026-04-19_yin-coding-spirit` ship-manifest）
- `code-reviewer` 的 "Silent Rot Paths" 檢查 try/catch, fallbacks, timeouts — 全是 imperative patterns
- IaC 的 silent failure 模式（state drift, provider lock, apply blast radius）與 imperative code 完全不同
- AI-assisted development 讓開發者跨 domain 的頻率增加，「我只寫 Python」越來越少見

## Risk of Inaction

一個 `.tf` 檔進入 review pipeline，9 個 principles 都用 imperative code 的 judgment questions 審查，產出看似合理的 PASS。開發者看到 PASS，以為程式碼品質被驗證了。實際上 reviewer 根本不理解 state drift 和 resource lifecycle — PASS 是 rubber stamp。這比沒有 review 更危險，因為它創造了「品質已被把關」的錯覺。

## Scope

### Must-Have (with death conditions)

- **Execution model router (two-pass detection)** — Death condition: 如果連續 50 次 review 中 Pass 2 (content inspection) 從未被觸發，移除 Pass 2，退化為 pure extension-based
- **Reference file applicability declaration (`excluded_principles`)** — Death condition: 如果所有 domain reference files 都是 9/9 applicable，移除此機制
- **現有 `code-quality.md` 加入 applicability header** — Death condition: 無（schema migration）
- **`iac-quality.md` 第一份 domain reference** — Death condition: 撰寫後 6 個月內沒被真實 Terraform review 使用過，降級為 draft
- **`code-reviewer` execution-model awareness** — Death condition: 如果 `code-reviewer` 未來被統一 dispatch，此獨立 awareness 隨之移除

### Nice-to-Have

- `container-quality.md`（Dockerfile）— 等 IaC reference 驗證可行後
- `pipeline-quality.md`（CI/CD, Airflow）— 等 IaC reference 驗證可行後
- Router mapping 外部 config file — 過早抽象

### Explicitly Out of Scope

- Linter 整合（tflint, hadolint 等）— 業界標準開發習慣，LLM 已知
- `orchestration-quality.md`（K8s/Helm）— 等 IaC 驗證後
- ML config review — signal 不足
- 多 agent 架構（每個 domain 獨立 reviewer）— 已排除

## North Star

```yaml
metric:
  name: "Review Honesty Rate"
  definition: "review output 的 domain classification 正確率 — reviewer 是否用了正確的 reference file（或正確地回傳 UNKNOWN）"
  current: "0% for non-imperative code"
  target: "100% domain classification accuracy for files with known execution model"
  invalidation_condition: "如果所有實際 review 請求都只包含 imperative code，指標 vacuously true"
  corruption_signature: "router 把所有 ambiguous files 都判為 UNKNOWN — accuracy 100% 但實際在逃避判斷"

sub_metrics:
  - name: "Domain Reference Coverage"
    definition: "已有 reference file 的 execution model 數量 / 實際遇到的 execution model 數量"
    current: "1/7"
    target: "2/7（加入 IaC）"
    proxy_confidence: medium
    decoupling_detection: "coverage 上升但 reference file 品質未經真實 review 驗證"

  - name: "Excluded Principle Accuracy"
    definition: "被 excluded 的 principles 是否真的不適用於該 domain"
    current: "N/A"
    target: "每個 exclusion 有 rationale 且經至少一個真實 case 驗證"
    proxy_confidence: low
    decoupling_detection: "exclusion 數量越多 review 越快 — 可能為效率而非正確性排除"
```

## Stakeholders

- **Decision maker:** yuyu_liao（框架作者）
- **Impacted teams:** 使用 samsara review 的開發者（尤其是跨 domain 開發者）
- **Damage recipients:** reference file 維護者（持續進化責任）、框架可信度（第一份 domain reference 品質決定擴展信心）
