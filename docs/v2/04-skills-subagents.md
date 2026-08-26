# 04 — Skills 與 Subagent 設計

> 執行層。受 [`03-system.md`](./03-system.md) 的封裝約束管轄，不重述上層原則。

## 先問必要性

依公理在技能層的形狀（見 [`01-philosophy.md`](./01-philosophy.md)）：subagent 消失了，什麼任務會做不成？

| subagent 提供的能力 | 是否非它不可 |
|---|---|
| 平行執行 | 否。加快而已，不影響能否抵達 End |
| Context 隔離 | 否。寫檔案再選擇性讀回可以逼近 |
| 角色約束 | 否。skill 直接陳述角色可以逼近 |
| **檢查者未見過製造者的推理** | **是。同一個 context 裡做不到** |

最後一條是唯一不可替代的。理由是陰面的：**檢查者若看得見製造者的推理，就繼承了它的盲點，於是傾向確認而非挑戰。** 這不是效率問題，是認識論問題——這種 review 的通過訊號是假的。

**結論：V2 需要 subagent 的份量很小。只有一件事需要它。**

上表用判斷回答必要性。同一個問句的實測版本見 [`05-validation.md`](./05-validation.md)。

## Role 與 thinking effort 是正交的兩個槓桿

角色指令會條件化輸出分佈，這是真的。但它與思考預算不能互相替代：

| 槓桿 | 控制什麼 |
|---|---|
| Role instruction | 往**哪裡**搜——條件化分佈，偏向某個區域 |
| Thinking effort | 搜**多少**——在已被條件化的區域裡探索多寬多深 |

錯的 role 配高 effort，是把錯的區域搜得很徹底。對的 role 配低 effort，是對的區域搜得淺。**加 effort 補不了選錯區域。**

用詞誠實標記：「從 prompt latent space 走到 answer latent space」是比喻。實際發生的是條件化收窄下一個 token 的機率分佈，沒有兩個空間在移動。現象為真，路徑的圖像不是。

成本上也不是「subagent 便宜、thinking 貴」。隔離的 context 要重讀檔案，成本一樣上升。兩者都貴，買到的東西不同。

## 由此導出的切分：skill 擁有 role，subagent 是外殼

既然 role priming 不需要獨立 context，把 role 寫進 subagent 定義就是把可攜的東西放進不可攜的層。

| 層 | 放什麼 | 可攜性 |
|---|---|---|
| `skills/<name>/SKILL.md` | 完整 role 定義、方法、判準、輸出契約 | 標準，到哪都在 |
| `<?>/agents/<name>.md` | 只有 `model`、`effort`、`tools`，加一句「開新 context，載入 skill X，只回報 Y」 | 命名空間，換 client 就消失 |

`<?>` 是 `unknown`，不是佔位待填的細節。落點未定的證據見 [`03-system.md`](./03-system.md)「執行層的落點目前是 unknown」。

三個後果：

1. **降級是部分的，不是全滅。** 換 client 時失去隔離，但保住 role。
2. **單一來源。** role 只有一份，skill 文字與 agent 文字不會漂移。
3. **缺席可偵測。** skill 可以寫一條前置條件：「本步驟需要一個未見過實作推理的檢查者。確認不到就停下並回報。」skill 到哪都會執行，於是把規範強制的靜默忽略翻譯成可見的停止。

## 平台事實

以下是環境事實，屬 Origin 的一部分（見 [`00-canvas-rule.md`](./00-canvas-rule.md)）。依 [`02-method.md`](./02-method.md) §3 標型別附 locator。

`fact` `~/.claude/plugins/cache/kaleidoscope-tools/kaleidoscope-tools/1.7.0/agents/code-reviewer.md:1-8` — subagent 定義是 markdown 加 frontmatter，實際欄位：

```yaml
name: code-reviewer
description: Reviews one coherent pull request change unit ...
tools: ["Read", "Glob", "Grep", "Bash(git diff:*)", "Bash(git log:*)"]
model: haiku
effort: high
```

由此得到三條：

- **`effort` 是每個外殼可獨立設定的。** 所以「探索預算」本來就不必寫進 role。
- **`tools` 可限制到參數層級**（`Bash(git diff:*)`），不只工具名。上例的檢查者物理上寫不了檔。
- **`model` 與 `effort` 可分開挑。** 上例用 haiku 配 high effort。

`fact` — skill 呼叫 subagent 沒有正式的綁定原語，只有散文指示主 agent 派發。證據是否定式的：本節引的 frontmatter 無任何綁定欄位，[`03-system.md`](./03-system.md) 記錄規範全文亦無 delegation 語句。**否定式證據弱於肯定式**，若日後出現綁定原語，本條先失效。

## 未閉合的洞：隔離性無法在標準層驗證

因為呼叫只是散文指示，失效模式不只是「換 client 掉了」：

> 同一個 client，主 agent 跳過派發、自己寫完 review。看起來做了，實際在同一個 context 完成，隔離性是假的。

這是假成功——表面完成，關鍵副作用沒有發生。

能想到的擋法是 hook，但 hook 同樣在命名空間層，同樣不可攜。誠實的結論：

> **隔離性的保證在標準層不存在，只能由那個會靜默消失的層提供。**

這個洞目前沒有乾淨解法。決策選項見 [`90-open-questions.md`](./90-open-questions.md)。
