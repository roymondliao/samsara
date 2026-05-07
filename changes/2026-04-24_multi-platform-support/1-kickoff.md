# Kickoff: Multi-Platform Support (Phase 7)

## Problem Statement

Samsara 目前只能在 Claude Code 上運行。隨著 AI coding agent 生態系多元化（Codex、Gemini CLI、Windsurf），使用者如果切換平台就完全失去 samsara 的 workflow 支援。需要一套 config-driven 的轉換框架，讓 samsara 的 skills、agents、hooks 能被轉換並安裝到其他平台，首先支援 Codex。

## Evidence

- Codex CLI（v0.124.0）已安裝在本機，且已配置 samsara project 為 trusted
- Codex 的 skill format（SKILL.md + YAML frontmatter）與 Claude Code 完全相同
- Codex 的 plugin manifest（`.codex-plugin/plugin.json`）結構高度相似
- Codex hooks 支援相同的事件類型（SessionStart, PreToolUse, PostToolUse, UserPromptSubmit, Stop）
- Agent 定義格式不同（Claude Code: markdown → Codex: TOML），但欄位可映射
- Skill chaining 機制不同（Claude Code: `Skill` tool → Codex: `$skill-name` implicit matching），需要語法適配

## Risk of Inaction

不做的話，samsara 綁死在 Claude Code 上。如果使用者的主力工具是 Codex，samsara 對他完全沒有價值。隨著其他平台的 skill 生態系成熟，samsara 可能因為平台鎖定而失去採用動力。

## Scope

### Must-Have (with death conditions)

- **Platform config registry** — 定義每個平台的差異（manifest 路徑、agent 格式、hook 輸出、skill syntax、tool mapping）作為 single source of truth。Death condition: 6 個月內只支援 ≤ 1 個非 Claude Code 平台，config 抽象成本 > hardcode。
- **Converter 核心（Python）** — 讀取 samsara source + platform config，產生目標格式。處理 5 個轉換面向 + skill chaining。Death condition: Codex skill format 在 3 個月內 breaking change > 2 次。
- **Python CLI（install / update / convert）** — `samsara-cli install codex`、`samsara-cli update`、`samsara-cli convert --platform codex`。Death condition: 月安裝次數 < 5。
- **Codex platform config** — 第一個 platform config entry，驗證框架可行性。Death condition: Codex 棄用 skill 系統。

### Nice-to-Have

- `agents/openai.yaml` 自動生成（Codex UI metadata）
- Marketplace 發布機制
- 自動偵測所有已安裝的 AI coding tools
- Convert diff 預覽（dry-run mode）

### Explicitly Out of Scope

- Gemini CLI 支援（Phase 7.1）
- Windsurf 支援（Phase 7.2）
- Web UI / dashboard
- CI/CD 自動化（auto-convert on samsara release）

## North Star

```yaml
metric:
  name: "Codex workflow chain completeness"
  definition: "在 Codex 上從 research → validate-and-ship 的 6 個 chain skills + 3 個 entry skills + 2 個 utility skills 全部可觸發且行為正確的比例"
  current: 0%
  target: 100%
  invalidation_condition: "如果 '完整度' 只看檔案是否存在而非 end-to-end 可運行，指標就是錯的"
  corruption_signature: "convert 後 SKILL.md 全部存在且語法正確（100%），但 Codex agent 實際 skip skills 或 chain 斷裂。偵測：smoke test 觸發 research → 觀察是否 chain 到 planning"

sub_metrics:
  - name: "convert success rate"
    current: 0%
    target: 100%
    proxy_confidence: high
    decoupling_detection: "convert pass 但 install 後 Codex 無法載入 → convert 驗證不足"
  - name: "install success rate"
    current: 0%
    target: 100%
    proxy_confidence: high
    decoupling_detection: "install pass 但 skill 不出現在 Codex session → 路徑或 config 錯誤"
  - name: "skill trigger rate on Codex"
    current: 0%
    target: 100%
    proxy_confidence: medium
    decoupling_detection: "trigger rate high 但 workflow 行為錯誤 → implicit matching 觸發了但內容不適配"
```

## Stakeholders

- **Decision maker:** Roymond Liao
- **Impacted teams:** 所有 samsara 使用者（現為 Claude Code only）
- **Damage recipients:** 維護者（每次 skill 更新需 convert + 驗證 N 個平台）；Codex 使用者（如果體驗有落差）
