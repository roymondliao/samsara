# 03 — 整體系統設計

> 系統層。談 V2 自己的 End/Origin 與封裝約束，不談單一執行單位的內部設計（見 [`04-skills-subagents.md`](./04-skills-subagents.md)）。

## 把方法套在框架自己身上

V2 是一個 project，有自己的終點與起點。若回推法連自己的框架都推不出來，它不該被用在別人的專案上。

## V2 的候選 End（未定案）

依 [`02-method.md`](./02-method.md) §9，先給一個候選終點供剪裁：

> agent 面對任何 domain 的任務時，先想清楚這個任務該怎麼處理，組出剛好夠用的處理方式，做完留下能讓下一輪更準的證據。

- **可觀察差異**：使用者不必記得要叫哪個技能，agent 也不靠 description 猜。
- **不存在時誰受損**：使用者被迫自己當索引，或被迫走完不需要的流程。

**這個 End 的黑面**（白中有黑，見 [`01-philosophy.md`](./01-philosophy.md)）：

> 當 base model 不靠任何外部結構就能穩定做到上面那件事時，V2 整個不該存在。

這正是「LLM 越強、harness 越不需要」那個論點。V2 必須自己寫下這條，而不是假裝它不存在。這也是 [`01-philosophy.md`](./01-philosophy.md) 要求的解脫條件。

## V2 的 Origin：缺一份 baseline

[`00-canvas-rule.md`](./00-canvas-rule.md) 讓 V2 的 Origin **不能**是「V1 存在」。誠實的 Origin 是：

> 目前 base model 在沒有任何 harness 時的實際行為。

而這份東西目前只有印象，沒有證據。回推法要求 Origin 是凍結、有證據的快照，所以 V2 缺一份 baseline——一組任務、agent 裸跑的實際結果。

沒有 baseline，上面那條黑面（何時該刪掉 V2）永遠無法判定。取得程序見 [`05-validation.md`](./05-validation.md) 的 Phase B，未決刻度見 [`90-open-questions.md`](./90-open-questions.md)。

## 封裝格式：agent-plugins

V2 採用 [agent-plugins](https://agent-plugins.org/specification) 規範封裝。

本節每條斷言依 [`02-method.md`](./02-method.md) §3 標型別並附 locator。來源為 <https://agent-plugins.org/specification>，取得日期 2026-08-26。

### 規範涵蓋什麼

`fact` §5.2 — `plugin.json` 允許的頂層欄位只有 `$schema`、`name`、`version`、`description`、`author`、`homepage`、`repository`、`license`、`keywords`、`extensions`。

`fact` §5.3 — 必要欄位只有 `$schema` 與 `name`。

`assumption` — `skills/` 的直接子目錄含 `SKILL.md` 者構成一個 skill，client 不得遞迴更深層。**缺章節號**，需回查後升型。

### 規範不涵蓋什麼

`fact` — 規範全文對 subagent 與 agent delegation 沒有任何規範性語句。

`fact` §8 — 反向網域命名空間由**實作 client** 定義與擁有，不是 plugin 作者：

> A client SHOULD base its namespace on a domain name it controls and SHOULD keep the namespace stable. For example, a client that controls `example.com` could use `com.example.client`.

> The extension directory for a namespace is the top-level directory named after it.

`fact` §8.1：

> A client MUST ignore manifest entries for namespaces it does not implement **without validating the contents of their values**.

`fact` §11.3：

> Clients MUST ignore unsupported component types.

兩條都不是報錯，不是警告，是**必須忽略**，且 §8.1 明訂不得檢查內容。

### 執行層的落點目前是 unknown

```
samsara/
├── plugin.json          fact §5.3   標準，必要
├── skills/              fact        標準，可攜
│   └── <name>/SKILL.md
├── mcp.json             fact        標準，可攜
└── <?>/                 unknown     執行層落點未定
    └── agents/
```

`unknown` — Claude Code 是否公布過自己的 agent-plugins 命名空間，未查。

`fact` `~/.claude/plugins/cache/kaleidoscope-tools/kaleidoscope-tools/1.7.0/` — 本機實際安裝的 plugin 用的是 Claude Code 原生格式：`.claude-plugin/plugin.json` 加頂層 `agents/`、`skills/`、`hooks/`、`commands/`，目錄樹中沒有任何反向網域目錄。

`unknown` — 規範是否允許頂層出現它不認識的目錄（例如 `agents/`）。若允許，執行層不需要命名空間包裹；若不允許，在 Claude Code 公布命名空間前執行層無處可放。需回查規範第 11 節全文。

### 由此導出的約束

一個不支援該命名空間的 client 安裝 V2，會成功載入 skills 與 MCP，然後**無聲地丟掉整個執行層**。使用者看到一個看起來正常的 plugin。

這是規範保證會發生的靜默失敗，不是實作瑕疵。**所以問題不是「怎麼調用執行單位」，而是「執行單位不在時，誰會發現」。**

## 設計原則：宣告在標準層，實作在命名空間層

> **能力宣告在標準層，能力實作在命名空間層，實作缺席時標準層必須喊出來。**

skill 是標準化的，到哪個 client 都會被載入與執行。所以 skill 可以承載一條前置條件，把規範強制的靜默忽略翻譯成可見的停止。這是「unknown ≠ pass」套在可攜性上。

落點見 [`04-skills-subagents.md`](./04-skills-subagents.md)。

## 已知未閉合的風險

標準層無法驗證命名空間層是否真的執行了。詳見 [`04-skills-subagents.md`](./04-skills-subagents.md) 的隔離性一節，決策見 [`90-open-questions.md`](./90-open-questions.md)。
