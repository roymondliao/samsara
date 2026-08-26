# docs/ 索引與版本分類

本目錄同時存放 V1 的設計來源、對 V1 的稽核、V2 的新畫布，以及版本無關的核心教義。
每份文件的版本歸屬列於下方。**分類本身以本檔為準**；各文件頭部的標頭是本檔的 derived view。

> **先讀 [`v2/00-canvas-rule.md`](./v2/00-canvas-rule.md)。** V2 不是 V1 的優化，而是從空白畫布開始。
> 該規範先於所有 V2 設計內容成立，並使本目錄下所有 V1 文件從**設計輸入**降為**歷史檔案**。
> V2 討論已依高度分層，入口是 [`v2/README.md`](./v2/README.md)。

```
docs/
├── 共同核心 — 版本無關，V2「精神不變」的來源
│   ├── philosophy.md         向死而驗的命名與根據（海德格爾 + 道德經）
│   ├── example.md            負空間工程 v0.1 — 公理、七問、失敗分級 1-4、狀態誠實
│   └── thinking.md           陰陽對照表（哲學/軟體/規範）+ §4 結構誠實
├── V1 — 已實作管線的設計來源
│   ├── design.md             陽面原型，自帶 HISTORICAL 標頭
│   └── develop.md            陰面管線藍圖 — V1 六階段的直接祖先
├── V1 稽核
│   └── comparison-mattpocock-skills.md   基準為 Samsara v1.0.1
├── V2 — 新畫布（分層，見 v2/README.md）
│   ├── v2/
│   │   ├── README.md                 分層索引 + 內容所有權
│   │   ├── 00-canvas-rule.md         約束層 — 空白畫布
│   │   ├── 01-philosophy.md          理念層 — 公理、太極、減法
│   │   ├── 02-method.md              方法層 — 終點回推法
│   │   ├── 03-system.md              系統層 — V2 的 End/Origin、封裝約束
│   │   ├── 04-skills-subagents.md    執行層 — skill 與 subagent 切分
│   │   └── 90-open-questions.md      未決項
│   ├── development_workflow.md       通用方法論（外部來源，非 samsara）
│   ├── v2-canvas-rule.md             【已取代】內容遷入 v2/00，可刪
│   └── v2-redesign-backward-derivation.md 【已取代】內容遷入 v2/，可刪
└── 外部參照 — 版本無關
    └── karpathy_claude_rules.md
```

## 核心三份裡混著 V1 綁定

核心不等於整份都活過 V2。兩處例外：

- `thinking.md` §4 末尾「誠實標記」點名 planning 的 structure spec、implementer 的全局結構 context、iteration 的 structural rot signal。V2 重建後這三個落點會消失。它標記的斷層（doc-presence ≠ runtime obedience）是核心，指涉的機制名不是。
- `example.md` 的 STEP 0 三問是 V1 的入口儀式。回推法的開放問題正是要不要取代它。三問的內容是教義，它作為入口儀式的地位待決。

## V1 稽核裡活過 V2 的部分

`comparison-mattpocock-skills.md` 的 P0/P1 隨 V1 刪除而失效（README 安裝路徑、validator 依賴、`implement/SKILL.md` 重寫）。背後原則存活：

- 成本帳本（每條指令值多少 context load / cognitive load）
- user-invoked / model-invoked 二分
- 正向陳述取代 `Never:` 條列
- leading words 勝過生造代號
- 「It's working if」的可觀測生效訊號

P2 的能力缺口清單（prototype、wayfinder、triage、domain-modeling、tracker）本身就是 V2 可組合性要涵蓋的 skill 種類。

## 已知的跨文件衝突（V2 要解掉）

**1. 簡潔的地位有四種立場。** `example.md:262`「簡潔不是美德，可追責才是美德」；`karpathy_claude_rules.md` §III「寫最少的程式」；`thinking.md:158`「簡單優先與 production 優先是同一個錯誤的兩個方向，都是偏好」；`v2-redesign-backward-derivation.md` §8 的奧坎剃刀。`thinking.md` §4 的判準能收斂四者——簡單不是預設立場，是在可追責這個硬約束下、驗證過的候選裡的勝出者。這句話目前沒寫在任何一份文件裡。

**2. 兩套入口儀式並存。** `example.md` 的 STEP 0 是三問（最想聽到的實作先不走／什麼條件不該實作／靜默失敗誰先發現）。`develop.md:55-58` 的 Interrogate 是四問（問題形狀誰給的／何時不該解／誰受損／完成長什麼樣）。V2 需決定保留哪一套，或由回推法取代。

**3. 公理與測試清單三處重複。** 「存在即責任」在 `example.md`、`thinking.md`、`develop.md` 各寫一次。測試優先順序在 `example.md` §7、`thinking.md` 測試表、`develop.md` Planning §2 各有一版。這正是 LLM 自建 harness 失效模式 5（DRY）發生在自己的文件上。V2 要指定單一 owner。
