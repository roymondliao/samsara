# 設計筆記 5 — 證據可見的載體形式

對應 `0-design-direction.md` 3.5（學習載體＝證據可見，非主動教）與第 8 節開放項。承接
`4-format-vs-judgment.md` 第 5 節：judgment 的 teeth ＝ 證據可見 ＋ 對抗式 review ＋
consumption。本筆記定：**結構決定的推理，寫在哪、寫成什麼形、怎麼不膨脹。**

---

## 1. 要可見的是什麼

不是所有東西都要留痕——要留的是 **codebase-craft 的判斷推理**。對一個結構決定
（選 pattern、畫邊界、刻意不抽象），要可見：

- **選了什麼**（結構選擇本身）
- **什麼 force/證據要求它**（引用哪條 seam〔L1〕、哪條 affects/已計畫 task〔L2〕）
- **刻意沒做什麼、為什麼**（refusal：「本可抽成 X，但只有 1 個 consumer，故不抽」）
- **全局→局部的連結**：這個局部選擇怎麼服務核心身分與接縫

`4-format-vs-judgment` 第 3 節說過：**judgment 略過不留痕**——「我判斷過了」與真判過長一樣。
證據可見就是把這個「不留痕」補上：略過判斷＝推理鏈空白，看得出來。

---

## 2. 機制 / 原則分流

| 現行做法 | 機制 or 原則 | 處置 |
|---|---|---|
| scar report（陰面：shortcut/assumption/silent-failure）durable per-task | **原則**（向死而驗載體） | 保留 |
| implementer.md「說出 refusal」進 scar narrative | **原則**（結構誠實已在此） | 保留 |
| pre-thinking 三格＋「為何不選別的」痕跡 | **原則** | 保留 |
| 結構決定的**正向理由**（選了什麼、什麼證據要求） | **機制缺口**：沒有 durable 的具名家園 | **補** |

---

## 3. 核心洞察：一個結構決定有陰陽兩面，是同一個決定

正向理由與 refusal 不是兩件事，是**同一個結構決定的兩面**：

- **陽面**：這道牆為什麼在這（選了 pattern X，因為 seam S ＋ affects task-7 要求）。
- **陰面**：這道牆若判錯會怎樣（本可不抽象/本可抽象，refusal ＋ 殘留風險）。

現行只留了陰面（scar 的 refusal/risk）；陽面（為什麼這結構是對的）沒 durable 家園。
把兩面**合成一條「結構決定」記錄**——記錄「牆為何在這」同時記錄「牆錯了會怎樣」——
既補上陽面，又不丟掉陰面紀律（風險仍在正中央）。這也符合向死而驗：**存在（陽）即責任
（陰）**，一條記錄同時回答「你為什麼存在」與「你消失/判錯什麼會痛」。

---

## 4. 家園：擴充 durable per-task 記錄，不新增檔

決定（我的提案，待 user 確認第 8 節 Q1）：**在 scar report 加一類「結構決定」條目**
（dual-face），不另開新檔。理由：

- **單一 durable per-task artifact**（不 proliferate，呼應筆記 3 單一來源精神）。
- scar 已 host 陰面 refusal——陽面理由與它是同一決定的兩面（第 3 節），自然同居。
- scar 是既有 durable 載體（survive session），implement 報告是 transient（會逝去）。

每條「結構決定」條目（compact）：
```
- decision: "在 exporter 與 core 間放一個 port 介面"
  serves_seam: parser-boundary          # L1：坐落哪條接縫
  forced_by:                            # 陽面證據（引用，非空話）
    - "affects task-7：將加第二個 exporter（已計畫變動）"
  refused: "沒有為『未來可能的第三種輸出』預留泛型參數"   # 陰面
  risk_if_wrong: "若 task-7 的 exporter 形狀與假設不同，port 介面要改一次"
```

---

## 5. auto-first、不膨脹：write-filter ＋ consumption

證據可見**不等於**每個決定都寫長篇——那會膨脹，違反 auto-first。兩道閘：

- **write-filter**（沿用 scar Rule 13）：「未來讀者會因為讀了這條而改變行動嗎？」否＝不寫。
  只有**結構賭注**（pattern 選擇、邊界、refusal）值得留痕，不是每一行。
- **consumption 紀律**（筆記 1 第 9 節）：`forced_by` 必須引用真的證據（seam〔L1〕/
  affects〔L2〕/git-history〔已發生〕之一）；引用不到任何證據的「理由」＝空話＝噪音，該被
  review 抓。**指不出任何可查證證據的結構決定，不該有這條記錄**（要嘛它其實不是結構賭注、
  要嘛它在憑感覺）。

`★ 同一 artifact 部分雙用`（修正原稿的全稱宣稱）：**當一條結構決定的 `forced_by` 引用了
affects 時**，這條記錄同時就是筆記 1 第 9 節的 **L2 consumption 追溯**（implementer 引用
「affects task-7」justify 留柔軟接縫＝該投影被消費）。但**不是每條結構決定都消費 affects**
——純由 git-history（已發生）或 domain 本質驅動的決定，讓證據可見卻不貢獻 consumption
資訊。所以精確講：**結構決定記錄 ⊋ affects-consumption 追溯**——是「affects-linked 的那部分
雙用」，不是全稱恆等。（反過來，被 affects 塑形卻只引 git 的決定，review 別誤判成
over-projection。）

---

## 6. 全局→局部，可讀

user（3.5）：User 從證據看**全局→局部**。條目的欄位順序就編碼了這條路徑：

```
核心身分（L1，feature 級，overview）
  → serves_seam（這決定坐落哪條接縫）
    → decision（局部選了什麼）
      → forced_by（哪條證據逼出來）
```

讀者順著念，就是「這系統本質是 X → 這塊是它的 parser 邊界 → 所以這裡放 port → 因為
task-7 要加 exporter」。**不必另寫教材**：讀懂這條鏈＝看懂一個 staff 怎麼做結構決定。
「learn your style」是這個的**湧現結果**，不是一個獨立的教學裝置。

---

## 7. review 側的證據可見（已有家園）

證據可見橫跨 implement 與 review 兩側：

- **implement 側**：本筆記的「結構決定」記錄（scar 內）。
- **review 側**：reviewer 的 **verdict 推理**（不只 PASS/FAIL）——家園已存在：
  `review-record.md`（本次 iteration F-A fix 已建立的 durable 逐字摘錄慣例）。1.0.0 沿用，
  只是內容從「發現的問題」擴到「結構判斷的推理」。

兩側都 durable，合起來讓「判斷略過會露餡」跨越產出與審查。

---

## 8. 死亡拷問（death cases ＋ 偵測）

| 死法 | 靜默失敗長怎樣 | 偵測/防線 |
|---|---|---|
| 理由膨脹（每個決定寫長篇） | scar 爆量、auto 變慢、真訊號被淹 | write-filter：只有結構賭注留痕；consumption：引用不到證據＝噪音 |
| 理由腐化成罐頭句（跨案複製貼上「為何不選別的」）| 看似有推理、實則儀式（0-design 第 5 節健康指標已列） | review 抓罐頭句；forced_by 要指真 seam/affects（每案不同，複製不了） |
| 事後合理化（post-hoc 補一個好看的理由） | scar 在實作後寫，可能retrofit justification | forced_by 只能引用**決定當下已存在**的 L1/L2 證據（file:line/task id 造不了假）；見 Q2 |
| 陽面理由蓋掉陰面 debt | 只寫「為什麼對」，不寫「錯了會怎樣」 | 條目 dual-face 強制：refused/risk_if_wrong 欄缺＝記錄不完整 |
| 推理不是全局→局部（只有局部「我選了 X」）| 讀者看不出它怎麼服務全局 | 欄位順序強制 serves_seam；指不出坐落哪條接縫＝要嘛不是結構決定、要嘛接縫沒識別（退回上游）|

---

## 9. 開放問題（給 user 定）

1. **家園** ——【已定，2026-07-06 user】**擴充 scar**，加 dual-face「結構決定」條目，不另
   開新檔（單一 durable artifact、陰陽同居）。
2. **記錄時機** ——【已定，2026-07-06 user】接受「**forced_by 只准引用決定當下已存在的證據
   （file:line / task id，造不了假）**」為防線；不強制下筆當下記（證據錨定已足夠防 post-hoc
   合理化）。
3. **粒度門檻** ——【已定，2026-07-06 user】值得留痕的結構賭注＝**pattern 選擇 / 邊界·接縫的
   建立或偏離 / 明確 refusal**；**不含**一般函式切分、命名（粒度地板以下）。

> **狀態：本筆記封版**。結構決定的推理＝scar 內的 dual-face「結構決定」條目（陽 forced_by
> ＋ 陰 refused/risk）；forced_by 只引用當下已存在證據（防 post-hoc）；write-filter＋
> consumption 防膨脹；欄位順序編碼全局→局部；review 側沿用 review-record.md。此條目同時
> 是 L2 consumption 追溯（同一 artifact 雙用）。「learn your style」為湧現，非獨立裝置。

---

## 10. 決策記錄

- **2026-07-06**（來源：本設計筆記對話，user 逐點確認）：
  1. **結構決定有陰陽兩面、是同一決定**：陽（forced_by 證據）＋陰（refused/risk）合成一條
     記錄——存在（陽）即責任（陰）（第 3 節）。
  2. **家園＝擴充 scar**，不另開新檔（user 定 Q1，第 4 節）。
  3. **forced_by 只引用決定當下已存在的證據**（file:line/task id 造不了假）為防 post-hoc
     合理化的防線（user 定 Q2）。
  4. **粒度門檻＝結構賭注**（pattern/邊界·接縫/refusal），不含函式切分命名（user 定 Q3）。
  5. **防膨脹＝write-filter＋consumption**：只有結構賭注留痕；引用不到證據＝噪音（第 5 節）。
  6. **同一 artifact 雙用**：「結構決定」記錄 ＝ L2 consumption 追溯（第 5 節）。
  7. **證據可見橫跨兩側**：implement＝scar 結構決定條目；review＝review-record.md（F-A 慣例，
     1.0.0 沿用）（第 7 節）。
  8. **「learn your style」為湧現**：讀全局→局部推理鏈即看懂 staff 做決定，非獨立教學裝置
     （第 6 節）。
