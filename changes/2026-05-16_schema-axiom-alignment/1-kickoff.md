# Kickoff: samsara-manifesto-v1

## Problem Statement

Samsara framework 目前的 failure 分類 schema（`type: death_path`、`silent_failure_conditions`）把「是否需要驗證」與「system 是否能接受」兩個維度混為一談，導致 implementer 在面對「user 該負責的 loud failure」（如 config 設定錯誤）時無法準確分類，跨多個 project 出現系統性誤用。更深一階的問題是：framework 尚未明文宣告 **「Samsara 面向 system，不面向 developer」**，使得 user 持續以 developer-facing 思維（TDD 加強版）解讀 framework。本次升級為 manifesto v1：(1) 宣告 framework 身份；(2) 把 failure 分類軸重構為時間軸（boundary-fail vs runtime-fail）；(3) 明文化 workaround 的精確定義；(4) 提供向後相容遷移路徑。

## Evidence

- User 跨多個 project 測試後回報「Samsara 機制不容許 death path 沒被 cover，但有些 death path 是必然要發生」——anecdotal 但跨 project 的系統性觀察
- Schema 自我矛盾：`type: death_path` 名稱比實際內容（只測 silent failure）寬，invitation to mis-read
- `scar-schema.yaml` 缺少「合法 loud failure」的承認欄位——implementer 沒有合法位置可放此類 case，被迫誤塞入 silent_failure_conditions
- Skill prose 的核心詞彙（"silent failure"）正確，但 schema 用了寬泛的 "death_path" 命名，造成 prose 與 schema 脫鉤
- AI 時代的 TDD 已退化為「pass test 的遊戲」，Samsara 若不明文宣告 system-facing，會被誤認為「更嚴格的 TDD framework」，失去差異化價值
- **尚未蒐集**：既有 v0.9.1 user 的 plan/scar 真實樣本——這是 kill condition C1 提醒需要在 Planning 階段補齊的 evidence

## Risk of Inaction

- **短期**：每個踩到 loud-failure 的 implementer 都會誤分類，scar report 含有不應修復的「待修項」，浪費 iteration 成本
- **中期**：Samsara 自己持續違反 Samsara 公理——schema 在缺乏 loud-failure category 時偷偷讓 implementer 塞 silent 欄位，這是 framework 的自我打臉
- **長期**：framework 失去身份錨點，後續任何 skill 升級都缺乏哲學依據；在 AI 時代被當作「另一個更嚴格的 TDD framework」採用，失去差異化
- **不行動的最高代價**：Samsara 的 anti-thesis（AI-era test-gaming）從未被明寫，使 framework 無法清楚說明「自己不是什麼」

## Scope

### Must-Have (with death conditions)

- **M1: Manifesto 明文宣告 "Samsara is system-facing, not developer-facing"** — 寫入 samsara-bootstrap、README、新增 glossary
  - Death condition: 6 個月內 ≥3 個 skill 或 PR 明確引用這條 manifesto，否則降為 nice-to-have（代表 manifesto 未被內化）

- **M2: Failure 分類軸從 loud/silent 重構為 boundary-fail vs runtime-fail** — schema + glossary + acceptance/scar templates 同步更新
  - Death condition: 新軸在 3 個獨立 case study 後仍無法穩定分類（implementer 仍頻繁問 maintainer），承認 axis 選錯、回退到 loud/silent

- **M3: Anti-pattern 明文化「workaround = 把 boundary-fail 推遲為 runtime-fail」** — 規則 + 至少 2 個具體 case（missing config、failed precondition with silent default）
  - Death condition: 規則寫完後 implementer 仍頻繁踩同樣的 workaround 模式，視為定義過於抽象，必須補具體 case 教學

- **M4: Migration path** — `type: death_path` 保留為 deprecated alias ≥6 個月，附 migration 指引
  - Death condition: 6 個月後仍有 ≥10% 新檔案使用 deprecated alias，視為強制升級失敗，必須二擇一：強制移除或永久保留 alias

### Nice-to-Have

- ADR `docs/adr/000X-system-facing-failure-axis.md` 記錄這次決策過程
- 業界詞彙借用（SRE / chaos engineering 對齊）—— 延後到 Principal-level 時機
- 自動 migration script（手動改一份範例就能解決，當前不需要自動化）

### Explicitly Out of Scope

- 重寫所有既有 skill 的內部邏輯（只改詞彙與 schema，不動 skill 流程）
- 工具化 system fragility budget 計算（屬於 v2 範疇）
- 與 SRE 文化的詳細對齊文件（Principal-level，本次不做）
- 既有 v0.9.1 plan/scar 的自動遷移（手動 + alias 已足夠）
- 修改 CLI/agent/hook 機制（用戶已確認不受影響）

## North Star

```yaml
metric:
  name: "Failure classification independence and accuracy"
  definition: "Implementer 能否獨立、準確地分類 failure 為 boundary-fail vs runtime-fail，且分類結果可被 reviewer 一眼驗證"
  current: low  # 跨多 project 出現分類混亂
  target: high  # implementer 自我分類正確，無須詢問 maintainer
  invalidation_condition: "如果分類正確的 implementer 寫出的 scar report 仍未能讓 system 在 boundary 死亡，代表分類軸只解了詞彙、沒解結構問題——需重新審視軸的定義"
  corruption_signature: "boundary-fail 比例 > 30% in any single feature's scar reports — 同時偵測兩種病：(a) implementer 把責任推給 user 以逃避修復；(b) system boundary 設計太脆弱，太多銳角讓 user 容易踩到"

sub_metrics:
  - name: "Independent reviewer 驗證分類正確率"
    current: unknown
    target: ">= 90% accuracy across 3 case studies"
    proxy_confidence: high
    decoupling_detection: "此為 main metric，無 proxy 風險"
  - name: "Scar report 中 ambiguous_classification 標記比例"
    current: not tracked
    target: "< 10%"
    proxy_confidence: medium
    decoupling_detection: "若 proxy 為 0 但抽樣 review 顯示誤分類，proxy 失效——必須加 hard verification 機制"
  - name: "Implementer 詢問 maintainer 「這算哪一類」的頻率"
    current: high (cross-project anecdotal)
    target: "near zero within 3 months of manifesto release"
    proxy_confidence: low
    decoupling_detection: "沉默不代表懂——可能正在偷偷誤分類；需配合 reviewer 抽查作為交叉驗證"
```

## Stakeholders

- **Decision maker:** yuyu_liao (Samsara framework maintainer)
- **Impacted teams:** 全體 Samsara user（含 internal team + open-source adopter）
- **Damage recipients:**
  - 既有 v0.9.1 user with already-generated plan/scar files — **唯一真實受損群體**，由 M4 migration path 救援
  - （主動排除受損地位）想用 Samsara 當「更嚴格 TDD」的 user — Samsara 不站在他這邊，這是 framework 邊界宣告而非 damage
