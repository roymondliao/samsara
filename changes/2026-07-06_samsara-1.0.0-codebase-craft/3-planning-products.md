# 設計筆記 3 — planning 的 codebase-craft 產物

收口 `1-global-thinking-channel.md`（L1 per-task 位置、L2 反向投影）與
`2-thinking-codebase-craft.md`（接縫的「已計畫」證據由 planning 補）懸著的下游落點。
本筆記定：planning 為 codebase-craft 產出什麼、放哪、以及它與 pre-thinking 的職責邊界。

---

## 1. planning 產三樣，全都是「消費 pre-thinking」，不是創造

| 產物 | 是什麼 | 來源 |
|---|---|---|
| **per-task 接縫映射（L1 位置）** | 每個 task 坐落/創造在哪條接縫上 | 映射既有接縫（pre-thinking 產），不新增 |
| **接縫證據加強** | 把某接縫的證據階從 domain 本質 → 已計畫（task 7/12 會擴充） | task 分解後才拿得到的「已計畫」證據（筆記 2 第 7 節） |
| **L2 反向投影（affects）** | 每個 task：誰會踩我這塊、要什麼 | 從 task DAG ＋ 接縫共用關係反轉 |

三樣的共同點：**planning 不創造接縫、不重新推導設計決定**——它只是把 pre-thinking 的接縫
**映射到 task、用 task 級證據加強、投影成 task 間關係**。呼應 redesign 定案「pre-thinking
的設計決定是 planning Key Decisions 唯一來源」。

---

## 2. 機制 / 原則分流

| 現行做法 | 機制 or 原則 | 處置 |
|---|---|---|
| pre-thinking 設計決定＝Key Decisions 唯一來源；planning 不重新推導、不新增 placement 決定 | **原則**（redesign 定案、防 ISSUE-001 病灶） | **保留** |
| index.yaml 承載 task 級 metadata（depends_on / scar_count …） | **機制**（落點對，欄位不足） | **擴充**（加 seam / affects） |
| overview.md Key Decisions 承載設計決定 | **機制** | 擴充成接縫的具名宣告處（帶 id ＋ 證據階） |

---

## 3. 單一來源守則：planning 映射與標註，不創造接縫

關鍵邊界，防止「換個階段偷渡設計決定」：

- 接縫**只在 overview.md 的 Key Decisions 具名宣告**（帶 id ＋ 證據階，內容來自 pre-thinking）。
- index.yaml 的 task 用 **seam id 引用**既有接縫；不在 index.yaml 就地定義新接縫。
- planning 對接縫只做兩件事：**(a) 映射** task→seam、**(b) 用已計畫證據加強**既有接縫。
- **若 planning 發現需要一條 pre-thinking 沒識別的接縫** → 這是**設計決定缺口**，
  **退回 pre-thinking 補**（像 File Map Consistency STOP gate 遇矛盾就停），**不准在 planning
  就地發明**。理由：接縫是設計決定，單一來源；planning 就地發明＝ISSUE-001 病灶復辟
  （同一決定兩處、無 cross-check）。

`★ format vs judgment 的第一個落地實例`：「task 引用的 seam id 解不解析得到（是否 dangling）」
是 **format**——機械、無歧義；「這條接縫對不對、該不該存在」是 **judgment**——留
pre-thinking/reviewer。同一個守則，format 那半機器守、judgment 那半人/agent 判。

**但「機器守」≠「samsara-cli 守」**：feature 產物層的 format 檢查（seam-id 解析等）的家園
是 **per-skill 的 format-validate 腳本**（`4-format-vs-judgment.md` §4 定案）；**samsara-cli
只是把 Samsara 整合進不同 coding agent service 的整合層，不是 format 檢查的家園——沒有
「兩個家園」這回事**。此處只需知道 seam-id 解析屬 format（機械可判），由 planning 自帶的
validate 腳本在寫完 index.yaml 後跑；完整分類與 teeth 政策見筆記 4。

---

## 4. index.yaml schema 擴充（草案）

```yaml
tasks:
  - id: task-1
    title: "..."
    status: open
    depends_on: []              # 既有：順序前置（我需要誰先完成）
    seam: parser-boundary       # 新：L1 per-task 位置——我坐落/創造在哪條接縫上
                               #     語意名（非代號），引用 overview.md Key Decisions 宣告的接縫
    affects:                    # 新：L2 反向投影——誰會建立在我的結構上、需要什麼
      - task: task-7
        needs: "在這條邊界後面加第二個 exporter"
      - task: task-12
        needs: "讀這個 module 的輸出格式"
```

- `seam`：**語意名**引用（`parser-boundary`，非 `SEAM-1` 代號）——user 定案 Q1：代號逼人
  去查「這代號是什麼」，是對證據可見（3.5）的摩擦；self-documenting 名字本身就是證據可見。
  單一 id（一個 task 主要坐落一條接縫；若真的橫跨多條，是 decomposition 訊號——task 可能切
  太大，考慮再拆）。
- `affects`：每條 = 下游 task id ＋ 一句「它要從你的邊界得到什麼」。**不帶 `via:<seam>`**
  （user 定案 Q2：踩哪條接縫在該下游 task 自己的 `seam` 欄已呈現，不重複帶進 affects）。
  體積小、由 consumption 紀律管控（筆記 1 第 9 節）。

---

## 5. affects vs depends_on：兩種不同關係，別混

| | `depends_on`（既有） | `affects`（新） |
|---|---|---|
| 語意 | **順序**：我需要誰先完成 | **結構影響**：誰會建立在我的結構上、需要我的邊界怎麼形 |
| 方向 | 正向（我 → 前置） | 反向（我 → 下游消費者） |
| 用途 | 執行排序、平行判斷 | 讓 implementer 選 pattern 時看見「已計畫的未來」 |

兩者**不可互相取代**：task 可以 affect 另一個而無硬 depends_on（例：兩個姊妹 task 踩同一個
module）；depends_on 也不必然是結構擴充（只是要它先跑完）。

**affects 的來源（planning 怎麼填）**：(a) 共用同一 seam 的 tasks 天然互相 affect；
(b) 正向 depends_on 中「下游會擴充上游結構」的那些；(c) planning 對 decomposition 的認知。
**防噪音**：affects 若只是「task-7 在我之後跑」而無結構需求（needs 空/等同 depends_on）→
噪音，consumption 紀律（沒被 implementer 決定消費）會抓出來。

---

## 6. 接縫證據加強（planning 補「已計畫」階）

pre-thinking 產的接縫標 已發生/domain 本質（筆記 2 第 4.2）。planning 分解 task 後：

- 對每條接縫，看 `affects` 有沒有下游 task 會擴充它 → 有，則**把該接縫的證據升到「已計畫」**
  （在 overview.md Key Decisions 的該接縫條目加一行「已計畫：task 7/12 會擴充」）。
- 這是**標註（annotation）不是新決定**：接縫本身仍是 pre-thinking 的；planning 只加它那階
  才拿得到的證據（證據逐階累積，筆記 2 第 7 節）。
- implementer 於是在下筆時看到「這條接縫有已計畫 task 要擴充」→ 留柔軟接縫**正當**
  （筆記 1 第 6 節）。

---

## 7. 死亡拷問（death cases ＋ 偵測）

| 死法 | 靜默失敗長怎樣 | 偵測/防線 |
|---|---|---|
| planning 就地發明接縫 | 設計決定偷渡到 planning，無 cross-check（ISSUE-001 形狀） | seam 只由 overview Key Decisions 宣告；index.yaml 只引用；dangling seam id＝format 錯（workflow 內機械檢查，家園見 Q3，非 samsara-cli）；缺接縫→退回 pre-thinking |
| affects 淪為 depends_on 副本 | 投影灌水、implementer 收到噪音 | needs 欄必須是結構需求；空/等同 depends_on＝噪音，consumption 紀律抓 |
| 接縫證據被「想像的未來 task」加強 | 把想像當已計畫（灌水投影） | 只有真的在 index.yaml 的 task 才算已計畫；affects 指向不存在的 task id＝format 錯 |
| 一個 task 橫跨多條 seam | decomposition 切太大、職責不清 | `seam` 設計為單一 id；需要多條＝重切 task 的訊號（軟訊號，非硬擋） |
| over/under projection | （見筆記 1 第 9 節） | 沿用筆記 1 consumption 雙訊號 |

---

## 8. 開放問題（給 user 定）

1. **seam id 命名** ——【已定，2026-07-06 user】**語意名**（`parser-boundary`），非代號；
   理由：代號逼人查內容，是對證據可見的摩擦。
2. **affects 帶不帶 `via:<seam>`** ——【已定，2026-07-06 user】**不帶**；踩哪條接縫在下游
   task 自己的 `seam` 欄已呈現，不重複。
3. **feature 工作產物層 format 檢查（如 seam-id 解析）的執行家園** ——【重構為開放問題，
   2026-07-06】原稿誤設為 samsara-cli；已修正：samsara-cli 只驗框架安裝/轉換輸出，不驗
   進行中 feature 的 changes/ 產物。seam-id 解析是 format（機械可判），但家園未定，**不是
   samsara-cli**。候選：交棒時強制跑的實測程序（類比 F-B 報數紀律）、hook、workflow 內
   輕量 validator。**轉交後續的 format vs judgment 清單那份筆記統一處理**（因為它同時要
   回答「這類 workflow 內 format 檢查如何有 teeth 又不落回 prose 服從」——doc-vs-runtime-
   obedience 的核心）。

> **狀態：本筆記封版**（Q3 明確轉交 format/judgment 筆記，非懸空）。planning 為 codebase-craft
> 產三樣（seam 映射、證據加強、affects 投影），全是消費 pre-thinking；單一來源守則＋缺接縫
> 退回 pre-thinking 的 STOP gate；index.yaml 加 `seam`（語意名）＋`affects`（不帶 via）。

---

## 9. 決策記錄

- **2026-07-06**（來源：本設計筆記對話，user 逐點確認）：
  1. planning 產三樣（seam 映射、接縫證據加強、affects 投影），全是**消費 pre-thinking**，
     不創造接縫（第 1 節）。
  2. **單一來源守則 ＋ STOP gate**：接縫只由 overview Key Decisions 具名宣告；planning 只
     映射與標註；發現缺接縫→退回 pre-thinking，不就地發明（第 3 節）。
  3. **seam 用語意名**（`parser-boundary`），非代號——代號是對證據可見的摩擦（user 定 Q1）。
  4. **affects 不帶 `via:<seam>`**——下游 task 的 seam 欄已呈現（user 定 Q2）。
  5. **affects ≠ depends_on**：順序 vs 結構影響，不可互換（第 5 節）。
  6. **接縫證據加強＝標註非新決定**：planning 補「已計畫」階（第 6 節，證據逐階累積）。
  7. **format ≠ samsara-cli（修正 overreach）**：samsara-cli 只驗框架安裝/轉換輸出；
     feature 工作產物層的 format 檢查（seam-id 解析等）家園未定、非 samsara-cli，轉交
     format/judgment 筆記（第 3、8 節 Q3）。
