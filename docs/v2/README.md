# Samsara V2 — 分層設計文件

> 狀態：討論中，全部未定案。

討論一次涉及過多範圍會互相纏繞，因此依**高度**分層。這與 [`02-method.md`](./02-method.md) 的高度紀律同源——先看全貌，再看範圍，再看細節。

## 閱讀順序

```
00-canvas-rule.md      約束層 — 先於一切成立，其他文件都受它管
   ↓
01-philosophy.md       理念層 — 公理、太極、減法。不談機制
   ↓
02-method.md           方法層 — 終點回推法。不談實作平台
   ↓
03-system.md           系統層 — V2 自己的 End/Origin、封裝格式、可攜邊界
   ↓
04-skills-subagents.md 執行層 — 執行單位怎麼定義與呼叫
   ↓
05-validation.md       驗證層 — skill 的存活怎麼被判定
   ↓
90-open-questions.md   未決項 — 所有懸而未決的問題集中在此
```

## 內容所有權

一個事實只有一個 owner。其他文件引用，不重述。

| 文件 | 擁有 | 不碰 |
|---|---|---|
| `00-canvas-rule.md` | 空白畫布約束、空白/不空白的層界線、推導方向 | 任何設計內容 |
| `01-philosophy.md` | 公理與其層級提升、陰陽相互滲透的**原則**、物極必反、減法、命名 | 節點規則、樹的形狀 |
| `02-method.md` | End/Origin 定義、雙面節點的**規則**、樹的文法、剪枝、高度、遞迴 | 平台、封裝格式 |
| `03-system.md` | V2 的 End 與 Origin、agent-plugins 封裝約束、可攜層界線 | 單一執行單位的內部設計 |
| `04-skills-subagents.md` | skill 與 subagent 的職責切分、呼叫方式、隔離性 | 上層原則的重述 |
| `05-validation.md` | validation set／baseline 的取得程序、判決規則、重入觸發 | Origin 的定義、skill 的職責切分 |
| `90-open-questions.md` | 全部未決問題與其阻塞對象 | 已決的內容 |

## 分層的判準

要放進哪一層，用一個問題決定：**拿掉這一層，下面幾層還推導得出來嗎？**

- 推導得出來 → 它屬於更下層，往下移。
- 推導不出來 → 它是這一層的必要前提，留著。

這條同樣是公理在文件層的投影，見 [`01-philosophy.md`](./01-philosophy.md)。
