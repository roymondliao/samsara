# Problem Autopsy: Multi-Platform Support (Phase 7)

## original_statement

「現在來處理 Phase 7 的部分，但需要修改一下部分內容，先支援 codex 就好，之後再安排 Gemini CLI and Windsurf」

「支援的意思就是完全可以在 codex 上使用所有功能」

「是要一套能擴展到其他平台的 convert/install 框架（只是先只接 Codex）」

「這些處理其實複雜度很高，有些東西應該可以透過 config 的方式來做處理，這樣也容易擴展，然後應該核心的處理都用 python 來實作，也用 python 來實作 cli 可以方式可以 install」

## reframed_statement

建立一套 Python-based 的 config-driven 跨平台轉換框架。框架讀取 samsara 的 Claude Code source（skills、agents、hooks、references）+ 平台特定的 config，產生目標平台格式的檔案，並透過 CLI 提供 convert / install / update 操作。首先實作 Codex platform config，驗證框架可行性後再擴展到 Gemini CLI 和 Windsurf。

## translation_delta

```yaml
translation_delta:
  - original: "先支援 codex 就好"
    reframed: "實作完整的跨平台框架，但第一個 platform config 只接 Codex"
    delta: "原始可能暗示只做 Codex-specific 的東西；實際要求是泛用框架 + Codex 作為第一個驗證"

  - original: "完全可以在 codex 上使用所有功能"
    reframed: "11 個 skills + 6 個 agents + 4 個 references + hooks 全部轉換並可在 Codex 上正確運作"
    delta: "「所有功能」需要具體定義 — 包含 skill chaining 行為、agent dispatch、session-start bootstrap injection，不只是檔案存在"

  - original: "透過 config 的方式來做處理"
    reframed: "平台差異（manifest 路徑、agent 格式、hook 輸出、invocation 語法、tool mapping）抽象為 platform config，converter 讀 config 做轉換"
    delta: "config 的 granularity 未定義 — 是每個平台一個 config file？還是一個 registry 包含所有平台？config 裡放什麼、不放什麼需要在 planning 時定義"

  - original: "用 python 來實作 cli"
    reframed: "Python CLI with subcommands: convert、install、update。可能用 click 或 typer 作為 CLI framework"
    delta: "CLI 的 UX 細節（是否需要 interactive prompts、output format、error reporting）未定義"
```

## kill_conditions

```yaml
kill_conditions:
  - condition: "Codex 在 3 個月內對 skill 系統做 > 2 次 breaking change（format、discovery path、或 loading mechanism）"
    rationale: "維護轉換框架的成本會超過手動適配。等 Codex skill 系統穩定後再投入。"

  - condition: "Codex 的 subagent 或 hook 機制無法支撐 samsara 的 skill chaining + bootstrap injection，且沒有可行的 workaround"
    rationale: "core workflow 斷裂 = degraded experience，比不支援更糟。這時應該等 Codex 補齊機制。"

  - condition: "跨平台框架的 config + converter 代碼量 > samsara 本體的 50%"
    rationale: "尾巴搖狗 — 平台適配工具不應該比被適配的東西更複雜。此時應該簡化策略（例如直接 fork + 手動維護）。"
```

## damage_recipients

```yaml
damage_recipients:
  - who: "維護者（Roymond）"
    cost: "每次 samsara skill 更新需額外跑 convert + 在 Codex 上驗證。N 個平台 = N 倍驗證成本。框架本身也需要維護。"

  - who: "Codex 使用者"
    cost: "如果轉換有 subtle gap（例如 tool name 沒對應到、agent dispatch 行為不同），使用者會遇到『文件說能做但實際做不到』的落差，debug 成本高。"

  - who: "Claude Code 使用者（間接）"
    cost: "如果維護精力被分散到跨平台支援，Claude Code 版本的 skill 改進速度可能變慢。"
```

## observable_done_state

**解決了**：執行 `samsara-cli install codex` 後，在 Codex CLI 啟動新 session，samsara 的所有 skills 可透過 `$samsara-research` 等語法觸發，agents 可被 dispatch，session-start hook 自動注入 bootstrap context，workflow chain（research → planning → implement → iteration → security-review → validate-and-ship）端到端可運行。

**沒解決**：Samsara 只能在 Claude Code 上使用。Codex 使用者沒有任何方式使用 samsara 的 workflow。

**可觀測差異**：存在 `samsara-cli` Python CLI，支援 `convert --platform codex`、`install codex`、`update` 三個指令。存在 `platforms/codex.yaml`（或等價 config）定義 Codex 平台差異。install 後 Codex session 中可觸發並完成完整 samsara workflow。
