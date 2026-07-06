# 設計筆記 7 — 1.0.0 的 Evaluation Contract

對應 `0-design-direction.md` 第 8 節最後一項。前六份定「造什麼」，這份定「**怎麼證明造對了**」。
沿用 Samsara 既有 Evaluation Contract 格式（Primary evaluator ＋ pass/fail/feedback/out-of-scope）
＋ research 北極星紀律（失效條件、corruption signature、proxy confidence）。

---

## 1. 難題：成功標準是「判斷力」，量不到

1.0.0 的終極目標是「produce staff 級 code、developer 判斷力提升」。但：

- **不能用「pattern 選對了」當 pass signal**——那需要判斷來判斷判斷（遞迴），而且「對不對」
  本身就是 judgment，沒有機械答案。
- **「developer 判斷力提升」是跨 feature、長期**的結果，一次 run 量不到。

`4-format-vs-judgment` 的試金石在這裡反過來咬自己：核心價值是 judgment，judgment 不可機械
量測。所以 Primary evaluator **不能是**終極目標本身。

---

## 2. 解法：量因果鏈的「可觀測後果」，不量終極目標

1.0.0 是一條因果鏈：

```
給 implementer 全局思考＋task 依賴（L1/L2）
  → 它選證據錨定的 pattern
    → code 跨 task 連貫、無投機過度建構、無 junior 局部最優
      → 且推理可見，人能讀懂
```

終極目標（判斷力提升）量不到，但**鏈的後果可觀測**。Primary evaluator 就盯這些後果——
它們是終極目標的 **proxy**，不是目標本身（proxy confidence 見第 5 節）。

---

## 3. Evaluation Contract（定案草案）

### Primary evaluator（唯一）

**用 1.0.0（非現行 Samsara）全程跑一個「具真實跨 task 結構」的 feature，檢查因果鏈的可觀測
後果是否成立。** 一個 evaluator（dogfood ＋ 鏈檢查），下列為它的複合 pass/fail 訊號。

### Pass signal（全數成立才算過）

1. **（機械／format）結構決定留痕完整且解析得到**：每個結構賭注有 dual-face 條目；`forced_by`
   引用的 seam/affects **解析得到**（per-skill validator 綠）。→ 必要非充分（只證機械跑了）。
2. **（可觀測）零「非預期拆牆」**：沒有後續 task 為了接上而**拆掉**前一個 task 的結構，是
   affects 早該預測卻漏掉的（筆記 1 §9 under-projection 死訊號）。affects 有預測到的擴充，
   下游接得上、不拆。
3. **（可觀測）零投機抽象出貨**：每個出貨的抽象，`forced_by` 都指得到**當下已存在的 force**；
   指不到的（為想像預留）＝投機，不該出貨。review 的 O—marked bet 是**攔截機制**，但
   **硬零量的是「評估時最終有沒有投機出貨」這個可觀測結果，不是 review 中途的 deterministic
   保證**——block 經仲裁（human／auto-gatekeeper，筆記 6 §3.3）仍可能放行，放行了就在這裡
   現形。（「O—marked bet」＝既有九原則的 Open-closed 落點：封閉邊界＝對未來下的賭注。）
4. **（F-G 判官）獨立讀者能追鏈**：一個**獨立 agent**（對抗式，非執行者——F-G 稽核模式）能對
   ≥N 個結構決定，從核心身分→seam→選擇→forced_by **讀通並複述為什麼**。讀不通＝推理不可見。

### Fail signal

出現非預期拆牆／投機抽象出貨／結構決定留痕缺或 forced_by 解不到／獨立讀者追不通鏈。

### Feedback loop（失敗時第一條修正路徑）

**定位是哪一環斷的，修那一環**（對應筆記 1-6 的 death case）：

| 觀測到的 fail | 斷的環 | 去修 |
|---|---|---|
| 留痕缺 / forced_by 空 | implementer 沒消費 L1/L2 或沒留痕 | 筆記 6 §2 |
| forced_by 指到不存在的 ref | planning L2 投影或 validator | 筆記 3 / 4 |
| 非預期拆牆 | L2 投影不足（漏 affects）| 筆記 1 §9、筆記 3 |
| 投機抽象出貨 | review O 沒攔 | 筆記 6 §3.2 |
| 追不通鏈 | 證據可見載體壞 / 罐頭句 | 筆記 5 |

不在失敗時另立新標準——回到既有的鏈去找斷點（呼應 iteration「不發明新成功標準」）。

### Out of scope（誠實劃出）

- **「developer 判斷力提升」**：跨 feature、長期，一次 run 不可 agent 量測 → **不是** Primary
  evaluator，改列**長期健康指標**（release 時看，見第 6 節）。
- **「pattern 是不是最優」**：無機械答案、需遞迴判斷 → 不驗「最優」，只驗「證據錨定且非投機」
  （可觀測的下限，不是最優的上限）。

---

## 4. 為什麼這組 proxy 站得住

每個 pass signal 都**可觀測、可證偽**，且不需要「judge the judgment」：

- 拆牆是**事件**（發生了/沒發生），不是意見。
- 投機抽象＝`forced_by` 指不到已存在 force，是**可查**的（force 在不在 code/plan 裡）。
- 追鏈用**獨立 agent**（F-G 模式），把「執行者自評」偏誤剃掉——且「能不能讀通」比「是不是
  最優」弱得多、接近可判。

它們合起來是「終極目標的必要條件」：判斷力若真提升，這些後果會成立；這些後果不成立，判斷力
一定沒落地。**反向不保證**（見 proxy confidence）。

---

## 5. Corruption signature（proxy 被 game）＋ proxy confidence

| proxy | 被 game 長怎樣 | 偵測 |
|---|---|---|
| 留痕完整 | forced_by 引用**解析得到但不相關**的 ref（cargo-cult：湊一個 affects 過關）| 獨立判官查 forced_by 的**相關性**（judgment），非只解析（format）|
| 零拆牆 | 靠**把 feature 切得太瑣碎**、根本沒真跨 task 結構來規避 | dogfood 目標必須**有真實結構耦合**，否則沒測到機制（見 Q1）|
| 追得通鏈 | 推理是跨案**複製貼上的罐頭句** | 跨 feature copy-paste 檢查（沿用 pre-thinking 罐頭句健康指標）|

**Proxy confidence：medium。** 誠實講：我們能證明「1.0.0 產出連貫、證據錨定、可讀」，
**不能**在一次 run 證明「human 因此學會、判斷力提升」。proxy→終極目標的連結**本身是一個賭注**
——標 medium，靠第 6 節的長期指標去監看它有沒有脫鉤。

---

## 6. 長期健康指標（release 時看，非 Primary evaluator）

owner ＝ samsara maintainer；trigger ＝ 每次 release／對 samsara 自身跑 validate-and-ship。
（與 `0-design-direction` 第 5 節的機制腐化清單合看。）

- 多個 feature 累積下來，非預期拆牆率、投機抽象出貨率是否趨零。
- 後來的 feature，其結構決定 forced_by 的相關性是否維持（沒退化成 cargo-cult）。
- （proxy→目標脫鉤偵測）產出品質指標好、但實際維護者仍反映「code 難維護/難擴充」→ proxy
  在空轉，回頭校準 Evaluation Contract。

---

## 7. 開放問題（給 user 定）

1. **dogfood 目標** ——【已定，2026-07-06 user】**兩個並用**：(a) user 手上一個真實 project
   實際驗證；(b) 用新 1.0.0 對 Samsara 自己（user 之後提優化 require 當測試案）。兩者都用
   **新 1.0.0** 跑，不用舊 Samsara。
2. **拆牆／投機容忍度** ——【已定，2026-07-06 user】對「**非預期拆牆**」與「**投機抽象出貨**」
   **硬零**；「事先由 affects 預測到、有記錄的擴充」與「有記錄的刻意不做（refusal）」**不算
   失敗**——**因為有證據可以擔保**（user 語）。判準綁「非預期／出貨」的**事件**，非意見。
3. **追鏈 N 與判官** ——【已定，2026-07-06 user】**N＝全部，不抽樣**（評估 feature 只跑一個，
   結構賭注按粒度門檻僅個位數，全查得完；抽樣會讓沒被抽到的爛決定躲過，違反不做靜默截斷）。
   **判官＝獨立新 agent（F-G 稽核模式）**：拿 scar 結構決定條目＋review-record＋code，逐條追
   「核心身分→seam→選擇→forced_by」是否讀通；一條追不通或罐頭句即訊號亮。

> **狀態：本筆記封版**。Primary evaluator＝用新 1.0.0 跑真實跨 task 結構 feature、檢查因果鏈
> 可觀測後果（留痕解析／零非預期拆牆／零投機出貨／獨立 agent 追得通鏈）；量 proxy 非終極
> 目標，proxy confidence medium，「判斷力提升」列長期健康指標。dogfood 兩目標並用。

---

## 8. 決策記錄

- **2026-07-06**（來源：本設計筆記對話，user 逐點確認）：
  1. **難題**：成功標準是判斷力、量不到 → Primary evaluator 不能是終極目標本身（第 1 節）。
  2. **解法**：量因果鏈的可觀測後果（proxy），非終極目標（第 2 節）。
  3. **Primary evaluator**：用新 1.0.0 跑一個有真實跨 task 結構的 feature、檢查鏈的後果
     （留痕解析／零非預期拆牆／零投機出貨／獨立 agent 追得通鏈）（第 3 節）。
  4. **Feedback loop＝定位斷環修那環**，不另立新標準（第 3 節對照表）。
  5. **out-of-scope**：「判斷力提升」（長期、不可單次量）降為長期健康指標；不驗「最優」
     只驗「證據錨定且非投機」（第 3 節）。
  6. **dogfood 兩目標並用**：真實 project ＋ 用新 1.0.0 對 Samsara 自己（user 定 Q1）。
  7. **硬零綁事件**：非預期拆牆／投機出貨硬零；有證據擔保的預期擴充與記錄的 refusal 不算
     失敗（user 定 Q2——「有證據可以擔保」）。
  8. **追鏈 N＝全部、判官＝F-G 獨立 agent**（user 定 Q3）。
  9. **proxy confidence＝medium**：proxy→目標連結是賭注，靠長期指標監看脫鉤（第 5 節）。
