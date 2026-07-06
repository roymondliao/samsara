# 設計筆記 6 — implement / review 端落地

把筆記 1-5 的結論翻譯成 agent 的下筆紀律與 review 視角。**不新增 agent**（沿用結構-honesty
feature 的 KD-3 精神）——升級既有 `agents/implementer.md` 與 `agents/code-quality-reviewer.md`，
`agents/code-reviewer.md` 補一個維度。

---

## 1. 機制 / 原則分流

| 現有 | 機制 or 原則 | 處置 |
|---|---|---|
| implementer.md「結構誠實—generation 時驗」（拒投機、說出 refusal）| **原則** | 保留、**接上證據機制**（affects） |
| implementer.md「read before you write（讀鄰居）」 | **原則** | 保留、**鄰居清單改由 L2 錨提供**（筆記 1 §10）|
| code-quality-reviewer 九原則（S/O/L/I/D＋內聚耦合 DRY Pattern）| **原則**（本就是 codebase-craft 判斷）| 保留 |
| reviewer 產 verdict（PASS/FAIL＋file:line）| **機制**（verdict 導向、推理不 durable）| **轉證據可見** |
| implementer 消費「task 切片＋curated overview」| **機制**（隔離盲點）| **改消費 L1/L2/錨** |
| 結構決定無正向理由的 durable 記錄 | **機制缺口** | **加 dual-face scar 條目**（筆記 5）|

---

## 2. implementer 端落地（`agents/implementer.md`）

### 2.1 消費 L1 / L2 / 拉取錨（新輸入）

下筆前，除了 task 本體，implementer 讀 dispatch 帶來的：
- **L1 全局定位**：核心身分 ＋ 本 task 坐落的接縫（筆記 1 §5、筆記 2）。
- **L2 脈絡投影**：`affects`（誰會踩我這塊、要什麼）＋ 拉取錨（至少該讀的鄰近檔）。
- **read-before-write 的鄰居清單改由 L2 錨給**（筆記 1 §10）——不再靠 implementer 自己猜
  「直接鄰居」（那是盲點）。錨是起點非白名單，仍要沿線自取。

### 2.2 pattern 選擇 ＝ f(當前 project, 已計畫 tasks)（升級既有拒投機）

既有「拒投機一般化」升級成**帶證據的判準**（筆記 1 §6、筆記 3）：
- 看到 `affects` 有已計畫 task 會擴充這塊 → 為它**留柔軟接縫正當**（已計畫＝證據）。
- `affects` 沒說的未來 → **想像，拒絕預留**（憑空蓋走廊、違反公理）。
- 邊界：affects 說「接縫留在哪」，**不授權**現在就把未來 task 的抽象蓋好——先寫具體，
  第二個真實 force 出現才抽象（結構誠實準則不變）。

### 2.3 結構決定 dual-face 留痕（scar 擴充，筆記 5）

對每個**結構賭注**（pattern 選擇／邊界·接縫建立或偏離／明確 refusal）——不含函式切分命名
——在 scar 加一條 dual-face 條目：
```
- decision: "…"
  serves_seam: <語意名>       # L1：坐落哪條接縫
  forced_by: ["affects task-7：…（已計畫）", "git:…（已發生）"]   # 陽，只引用決定當下已存在的證據
  refused: "…"                # 陰
  risk_if_wrong: "…"          # 陰
```
- `forced_by` **只准引用決定當下已存在的證據**（file:line / task id，造不了假）——防 post-hoc
  合理化（筆記 5 §8）。
- write-filter＋consumption：指不出真證據的「理由」＝噪音，不寫（筆記 5 §5）。

---

## 3. reviewer 端落地（`agents/code-quality-reviewer.md`）

### 3.1 verdict → verdict ＋ 可見推理（durable）

九原則沿用，但輸出從「PASS/FAIL＋file:line」升成「**verdict ＋ 推理**」，且推理 durable 進
`review-record.md`（F-A 慣例，筆記 5 §7）。verdict 仍要下（review 得有結論），但**payload 是
推理**——為什麼判這個抽象投機、怎麼看出來的——這是 human learn your style 的教學面，也是
判斷能被對抗式挑戰的前提。

### 3.2 對照 L1/L2 查結構決定（review 側 consumption）

reviewer 現在也拿得到 seam＋affects（經 dispatch 的 `## Feature`／注入），於是能查：
- implementer 的 `forced_by` 引用的 affects/seam **真的存在**嗎？（假引用＝format 錯，本該
  被 planning validator 擋在前面；review 是最後一道）
- 「留了柔軟接縫」是**真有 affects 撐**，還是投機？（O—marked bet 的 review 側落點）
- 有沒有結構賭注**該留痕卻沒留**？（陰面 refusal 缺）

### 3.3 format / judgment 紀律（筆記 4）

- **不把 format 當 judgment 重做**：YAML 解析、seam-id/affects 解析這類，交 per-skill
  validator；reviewer 不浪費判斷力重驗機械項，看 validator 的 feedback 即可。
- **不把 judgment 當 gate**：reviewer 的結論是**論證**、可被挑戰、推理可見——不是 deterministic
  機械閘門。

`★ 關鍵區分：reviewer 擋 ≠ code gate`。reviewer 對 Critical 結構判斷擋下要求修，**不是**
筆記 4 禁止的「code-enforce judgment」——它是**對抗式 review**（一個判斷說另一個判斷錯了，
附可見、可反駁的推理），正是 judgment 的 teeth。code gate 是 deterministic 機械擋（枷鎖）；
reviewer 擋是被論證、可爭辯的判斷（健康）。兩者的差別是「可不可以爭辯」。

---

## 4. yin（`agents/code-reviewer.md`）補一個維度

兩個 reviewer 對 codebase-craft 的分工：
- **yin ＝ 架構擺放**：本 task 的檔案是否坐落在 index.yaml 宣告的 `seam` 上（既有
  Architectural Placement 維度的自然延伸——現在對照的是 seam，不只 Key Decisions）。
- **quality ＝ 結構品質**：pattern 是不是好賭注、抽象投不投機（九原則）。

seam 的 dangling 是 format（planning validator 擋）；「坐落對不對」是 yin 的判斷。

---

## 5. 「learn your style」的兩個教學面（都 durable）

- **implement 面**：scar 的 dual-face 結構決定條目（為什麼這樣切、什麼證據、refusal）。
- **review 面**：review-record.md 的 verdict 推理（為什麼判投機、怎麼看出來的）。

兩面合起來，讀者順著全局→局部就看懂「一個 staff 怎麼做、以及怎麼審結構決定」——湧現，
非獨立教學裝置（筆記 5 §6）。

---

## 6. 死亡拷問（death cases ＋ 偵測）

| 死法 | 靜默失敗長怎樣 | 偵測/防線 |
|---|---|---|
| implementer 拿到 L1/L2 卻仍 task-local | 結構決定條目 serves_seam/forced_by 空或指不到 affects | review 3.2 查；空推理＝visible |
| reviewer 退回純 verdict（無推理） | review-record 推理空白 | 缺推理＝review-record 條目不完整（F-A DC-5：absent＝finding）|
| reviewer 把 judgment 當機械 gate | 判斷被壓成 binary，扼殺學習與爭辯 | 3.3 區分：reviewer 結論須為可爭辯論證；binary 無推理＝退化訊號 |
| reviewer 拿判斷力重做 format | 浪費、且可能與 validator 判讀不一致 | 3.3：format 交 per-skill validator，reviewer 看 feedback |
| pattern 為想像的未來預留 | 過度抽象、憑空擴充點 | forced_by 指不到已計畫 affects＝投機，review 擋（O—marked bet）|
| agent 定義膨脹超既有預算 | KD-5 類超標 | 實測 net-add、如實揭露、不砍既有 guard 湊數（見 Q3）|

---

## 7. 開放問題（給 user 定）

1. **兩 reviewer 的 codebase-craft 分工** ——【已定，2026-07-06 user】**yin＝架構擺放
   （檔案坐落對的 seam）、quality＝結構品質（pattern/抽象九原則）**。
2. **reviewer 擋 ≠ code gate** ——【已定，2026-07-06 user】reviewer **可以**對 Critical 結構
   判斷擋下要求修（對抗式 review，非枷鎖）——這本就是 code review 的任務之一。
3. **agent 定義 net-add 預算** ——【已定，2026-07-06 user】**先擴展**（實測揭露、不砍既有
   guard 湊數，KD-5 精神），content 的精簡優化留之後再做。

> **狀態：本筆記封版**。不新增 agent：implementer 消費 L1/L2/錨→證據錨定選 pattern→dual-face
> 留痕；code-quality-reviewer verdict→證據可見＋對照 L1/L2 查結構決定；yin＝seam 擺放；
> reviewer 可爭辯地擋（非 code gate）；agent 先擴展、後優化。

---

## 8. 決策記錄

- **2026-07-06**（來源：本設計筆記對話，user 逐點確認）：
  1. **不新增 agent**：升級既有 implementer.md／code-quality-reviewer.md，yin 補 seam 維度
     （第 1 節）。
  2. **implementer 落地**：消費 L1/L2/拉取錨；pattern 選擇＝f(project, 已計畫 tasks) 證據
     錨定；dual-face 結構決定進 scar（forced_by 只引當下已存在證據）（第 2 節）。
  3. **reviewer 落地**：verdict→verdict＋可見推理（durable review-record）；對照 L1/L2 查
     結構決定；format 交 validator、judgment 不當 gate（第 3 節）。
  4. **兩 reviewer 分工**：yin＝架構擺放（seam 坐落）、quality＝結構品質（九原則）
     （user 定 Q1，第 4 節）。
  5. **reviewer 擋 ≠ code gate**：對抗式 review 可爭辯地擋 Critical，是 code review 本務、
     非枷鎖（user 定 Q2，第 3.3 節）。
  6. **agent net-add 先擴展、後優化**：實測揭露、不砍 guard 湊數（user 定 Q3）。
