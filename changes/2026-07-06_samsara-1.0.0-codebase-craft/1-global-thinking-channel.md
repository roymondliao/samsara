# 設計筆記 1 — 全局思考通道 vs subagent context 衛生

對應 `0-design-direction.md` 第 3.4 節與第 8 節開放項第三條。這是 develop 樞紐能否落地的關鍵
技術矛盾——若無解，「implementer 依當前 project ＋ 已計畫 tasks 選 pattern」（3.3）就是空話。

---

## 1. 矛盾的表面形狀

- **要選對 pattern（3.3）**，implementer 下筆時需要：全局架構意圖 ＋ task 依賴圖 ＋ 當前
  project 結構。→ 需要**廣**的 context。
- **subagent context 衛生**：fresh subagent、聚焦、乾淨的 context 才不被雜訊稀釋、才便宜。
  → 需要**窄**的 context。

表面上這是一條線上的拉鋸：往廣走犧牲衛生，往窄走犧牲判斷。

---

## 2. 機制 / 原則分流

| 現行做法 | 是機制還是原則 | 處置 |
|---|---|---|
| subagent context 要乾淨、不被無關內容稀釋 | **原則**（subagent 存在的理由本身） | **保留** |
| 由 main agent 在 dispatch 當下**手工 curate** overview 切片 | **機制**（且正是盲點） | **重設計** |
| 每個 task 給「一個 task 全文 ＋ 相關切片」 | **機制** | 重設計 |

關鍵：**context 衛生是原則，手工 curate 是機制**。手工 curate 恰恰是盲點所在——main agent
決定「什麼跟這個 task 相關」，若它漏掉全局視野，implementer 就停在 junior。盲點不能靠「更
努力 curate」修，要換掉這個機制。

---

## 3. 真實證據：隔離盲點已經發作過

- **structural-honesty feature, task-4**（scar 原文，verified: false 的 assumption）：
  > 「No artifact in this feature's file map actually names a persisted location for
  > drift_items... task-4's own Files scope (skills/iteration/SKILL.md,
  > skills/validate-and-ship/SKILL.md only) cannot add a field to index.yaml or
  > scar-schema.yaml (owned by task-1/implement territory) without exceeding this
  > task's scope.」

  這是隔離盲點的教科書案例：implementer **看見了一個跨 task 的結構需求**（drift_items 需要
  一個持久化位置），卻因為**被框在自己 task 的視野與授權裡**，只能做局部決定、把跨 task 的
  結構問題 defer 掉。一個看得到全局的 staff 會直接把它放對位置，或指出這是 decomposition
  本身的問題——而不是在自己的小盒子裡繞過它。

- **ISSUE-001（continuous-learning）**：4 個 task 被實作在錯的位置（`samsara/` 而非 shared），
  因為 implementer 各自照 task 切片執行，沒有人在下筆時對照「shared」這個全局 placement 決定。
  隔離讓正確的全局決定傳不到下筆處。

兩個案例同一根因：**下筆的人看不到全局，於是做出局部最優、全局不連貫或錯位的實作。**

---

## 4. 破題：這不是一條線，是兩個軸

矛盾之所以看似無解，是因為把它當成「context 多 vs 少」的一維拉鋸。真正的破法是拆成**兩個
獨立的軸**：

```
        原始內容量（raw content）
              窄  ←──────────→  廣
結構      廣  ┌─────────────┬─────────────┐
覺察      ↑   │ ★ 要的：     │  全量傾倒    │
(struct-  │   │ 廣覺察+窄內容 │ (context 爆) │
ural      │   ├─────────────┼─────────────┤
aware-    ↓   │ 現行：       │             │
ness)     窄  │ 窄切片(盲點) │             │
              └─────────────┴─────────────┘
```

- **結構覺察（structural awareness）必須廣**——implementer 要知道「這塊牆是不是承重牆、哪些
  已計畫 task 會踩到這裡、鄰近有什麼既有 pattern 可重用」。
- **原始內容（raw content）必須窄**——它不需要未來 task 的**全文**、不需要整份 codebase map。

context 衛生禁止的是**廣的原始內容**（會稀釋、會爆）；它**不禁止廣的結構覺察**——因為結構
覺察**體積很小**（是「結構」不是「內容」）。★ 那一格就是解：**廣覺察 ＋ 窄內容**。

---

## 5. 設計：四層 context 模型（三推一拉）

implementer dispatch 分四層——L1/L2/L3 **推**、L4 **拉**，各有不同的廣窄：

| 層 | 內容 | 廣窄 | 推/拉 | 誰產生 |
|---|---|---|---|---|
| **L1 全局定位** | domain 核心身分、真接縫、這個 task 在架構中的位置 | 廣覺察、體積極小 | **推**（一律給） | thinking → planning |
| **L2 脈絡投影** | 哪些已計畫 task 會踩到這塊（附一句「它們要什麼」）、鄰近可重用的既有 pattern | 廣覺察、體積小（投影到本 task 的鄰域，非全專案） | **推**（一律給） | planning（由 task DAG 投影） |
| **L3 任務本體** | task-N 全文（現行做法） | 窄、全文 | **推** | planning |
| **L4 深層參照** | 實際檔案細節 | 深、按需 | **拉**（implementer 自己讀） | implementer 自取 |

核心兩點：

1. **L1+L2 是「投影」不是「傾倒」**：它把全局結構**投影到當前 task 的鄰域**，所以體積小。
   implementer 不拿未來 task 的全文，只拿「task 7、task 12 會擴充這個 module，你的邊界要讓
   它們接得上」這種**壓縮過的依賴投影**——幾行字，不是幾百行。
2. **L1+L2 由 planning 產生，不由 main agent 當下手工 curate**——這是把盲點機制換掉的關鍵。
   投影是 planning 的**產物**（從 task DAG 推導），不是 dispatch 時的即興發揮。

推/拉的分工也對齊「補盲點」原理：**結構覺察要推**（因為盲點的定義就是你不知道要去拉的
東西）；**深層細節可拉**（你知道要看什麼的東西，按需取就好）。

---

## 6. 這如何讓 3.3 的「證據錨定 pattern 選擇」成立

有了 L2 脈絡投影，implementer 才做得出 staff/junior 的區分：

- L2 說「task 7 會擴充這個 module（已計畫變動＝證據）」→ 為它保留接縫是**正當**的（牆打掉
  不拖垮整棟樓）。
- L2**沒說**的未來 → 那是**想像**，為它預留擴充點**禁止**（憑空蓋走廊）。

換句話說，**L2 投影就是「已計畫變動」這一階證據的實體載體**。沒有它，implementer 分不清
「為證據充分的未來設計」和「為想像設計」，只能二選一地要嘛不設計（junior 局部最優）、
要嘛亂設計（過度抽象）。L2 把證據送到下筆處，pattern 選擇才錨定得了。

**重要邊界**：L2 說的是「接縫要留在哪」，**不是**「現在就把 task 7 的抽象蓋好」。結構誠實
準則仍管轄：先寫具體的，等第二個真實 force 出現才抽象。L2 告訴你**關節該柔軟的位置**，
不授權你預先長出關節。

---

## 7. 死亡拷問（death cases ＋ 偵測）

| 死法 | 靜默失敗長怎樣 | 偵測 |
|---|---|---|
| L1+L2 膨脹成全量傾倒 | context 爆、聚焦被稀釋、fresh subagent 的價值喪失 | 投影體積超過預算 → **這是 decomposition 過度糾纏的訊號**（task 之間耦合太深，投影才會大），反過來當 death signal 用 |
| 投影退回 main agent 即興 curate | 盲點復辟，implementer 又被餵局部切片 | 投影必須是 planning 的具名產物；dispatch 若在組投影＝違規 |
| implementer 把「task 7 會擴充」當成「現在蓋 task 7 的抽象」 | 過度抽象復辟（憑證據之名行投機之實） | review 檢查：新增抽象能否指出「當下已有的第二個 force」，而非「投影裡的未來」 |
| 投影本身錯/過時（planning 對未來 task 猜錯） | implementer 依錯投影選錯 pattern | 投影只引用**已計畫 task**（plan 改則投影改）——它是證據級，非想像；且 plan 變動時投影連帶更新 |

---

## 8. 這一項的開放問題（給 user 定）

1. **L2 脈絡投影的產物形式** ——【已定，2026-07-06 user】**擴充 index.yaml** 每個 task 加
   反向投影欄位（單一來源、不增檔），非另產 orientation 檔。欄位樣式（`affects` /
   `consumed_by` 命名與內欄）留正式化時定。
2. **投影的體積預算** ——【已定，2026-07-06 user】沿用 pre-thinking「深度過剩」的
   consumption-driven 軟上限，非硬 gate。設計見第 9 節。
3. **L4 深層參照的邊界** ——【已定，2026-07-06 user】L2 附「拉取起點錨」（非白名單）。
   設計見第 10 節。
4. **thinking 如何產生 L1** ——【已定契約，2026-07-06 user】L1 契約與交棒通道定於第 10 節；
   內部（落在 pre-thinking 哪一步、確切格式）轉交 thinking 延伸 codebase-craft 的工作
   （`0-design-direction.md` 第 8 節第一條）。

> **狀態：本通道設計封版**。四層 context 模型（三推一拉）（第 5 節）＋ consumption-driven 軟上限
> （第 9 節）＋ L4 起點錨與 L1 契約（第 10 節）構成完整的全局思考通道設計。落地細節
> （index.yaml 欄位樣式、L1 在 thinking 的產生步驟）於各 skill 正式化時實作。

---

## 9. 投影體積的軟上限設計（consumption-driven，非行數 gate）

沿用 pre-thinking「深度過剩」的核心哲學：**真正防膨脹的不是盯行數，是下游強制消費——
沒人消費的東西才會腐化；行數只是附帶的粗略觀察指標。**（pre-thinking 原文：「沒人消費的
深度才會退化；真正防退化的機制不是『盯著行數』，是……下游強制引用規則。」）

套到 L1+L2 投影：

### 真紀律 = 下游強制消費

- 每條 L2 反向投影，必須能追溯到一個 implementer 的結構決定。implementer 的結構決策痕跡
  （選哪個 pattern、哪裡留柔軟接縫）**引用是哪條投影逼出來的**——這正是 3.3 的證據錨定，
  **同一條規則雙用**：對 implementer 是「pattern 選擇要指出已計畫 task 依據」，對投影是
  「沒被指到的投影就是噪音」。
- 一條投影若跨它被注入的所有 task 都沒有任何 implementer 決定消費它 → over-projection。

### 兩個死亡訊號（都基於消費、都是軟的）

1. **過度投影**：投影生成了但沒人消費 → planning 在猜未來 / 灌水。owner 週期性核對。
   （對應根因：把「想像」寫成了「已計畫」——投影本該只載已計畫變動這一階證據。）
2. **投影不足**：某個後續 task 必須**拆掉前一個 task 的結構**才接得上 → 前面的投影漏了一條
   真實 affects 關係。在「拆牆」當下記一筆 scar、回指漏掉的投影。**這就是「牆打掉拖垮樓」
   事件＝投影不足的 death signal**（也是這整個機制存在要防的事，靜默時最貴，所以要讓它
   在發生當下就留痕）。

### 糾纏訊號

某 task 的 L2 投影很大（很多 task 踩它這塊）→ decomposition 耦合過深。訊號浮出時**不硬擋**
（像 pre-thinking 深度過剩），而是提示 planning 也許該重切 task——把責任交回「切得對不對」，
而不是「投影寫得短不短」。

### 為什麼不用硬 gate

跟 pre-thinking 同理、也跟本次 iteration 的 KD-5 教訓同理：**硬行數 gate 會訓練人 game 那個
數字**（把真投影砍掉來過關），反而製造 under-projection 來湊數，把病複製到另一端。
consumption 規則 game 不了，因為它綁的是「有沒有被用」，不是「多大」。

### 體積指標的地位

L1+L2 行數 = **次要、粗略的觀察指標**，owner 在 release 時看中位數趨勢（像 pre-thinking 的
文件長度中位數），不是 per-dispatch 的硬閘門。真正的閘門在「消費追溯」那一側。

---

## 10. 封版：L4 拉取邊界 與 L1 契約

### L4 拉取邊界（Q3）：pull 要有「起點錨」，否則盲點在細節層復辟

純 pull 的問題：「只拉你已經知道要找的」——你拉不到你不知道存在的東西，盲點在細節層
復辟。沿用 pre-thinking 第三步給搜尋者「起點檔（但非只准查這些）」的手法：

- L2 為每個 task 附一小組**拉取起點錨**：下筆前**至少要讀**的鄰近檔（呼叫者、姊妹模組、
  這塊已在用的 pattern）。以**指標形式推送**（檔路徑 + 一句為什麼，非內容——維持窄內容）。
- **上游契約走這裡，不走 L2 摘要（F3，2026-07-06 user）**：當 task 有上游依賴
  （`depends_on` 非空）時，錨清單**包含所依賴 task 的 interface 檔**——implementer 讀**真實
  簽章（live code）**來遵守上游契約，而非讀一份會 drift 的 L2 摘要（違反「map 非真值」）。
  **沒有上游依賴的 task 就沒有這個錨、也沒有上游契約**（user 補：無上游依賴＝無上游契約，
  故上游契約本就不該是 L2 的固定成分）。
- 明確框成「起點，非白名單」——implementer 讀這些 **並**沿線自取，不受限於這幾個。
- 錨由 planning 選（它有全局視野），所以 implementer 被指向它自己想不到要看的地方 →
  補盲點；細節仍自由 pull。

這是**升級現有紀律**：implementer.md 執行順序第 2 步本來就要求「讀你要改的檔＋直接鄰居」，
但「哪些算直接鄰居」是 implementer 自己（帶盲點）判的。1.0.0 把這份錨清單改由 L2 提供——
「讀鄰居」的紀律留，「靠 implementer 自己猜鄰居」的盲點換掉。context 衛生保持（錨是指標
非內容＝廣覺察、窄內容）。

### L1 契約（Q4）：thinking 交什麼給通道

L1 全局定位要載三樣（**契約**，非格式細節）：

1. **domain 核心身分**：這系統本質上是什麼（一兩行）——結構決定要服務的身分。
2. **真接縫（real seams）**：domain 的本質邊界，證據錨定（已發生 > 已計畫 > domain 本質，
   非想像）——這些才是正當的 module/abstraction 邊界來源。
3. **這個 task 在架構中的位置**：相對核心身分與接縫，它落在哪。

**產生與交棒**：其中 (1)(2) 是 **feature 級**、由 thinking 產生一次；(3) 是 **per-task**、
planning 分解時產生。(1)(2) 是「設計決定」，因此**沿用 pre-thinking redesign 既有的
『planning Key Decisions 唯一來源』通道**流下來——不另造機制。dispatch 注入的 L1 = 共享的
(身分+接縫) ＋ 這個 task 的 (位置)。

**留給 thinking-redesign 的內部細節**（不在本通道筆記範圍）：(1)(2) 落在 pre-thinking 六步
的哪一步、確切欄位格式——那屬 thinking 延伸 codebase-craft 的工作（見 `0-design-direction`
第 8 節第一條）；本筆記只定「L1 必須載什麼、經哪條通道下來」。

---

## 11. 決策記錄

- **2026-07-06**（來源：本設計筆記對話，user 逐點確認）：
  1. 矛盾破法＝拆成兩軸（結構覺察廣 × 原始內容窄），非一維多寡拉鋸（第 4 節）。
  2. 四層 context 模型（三推一拉）：L1 全局定位（推/極小）、L2 脈絡投影（推/小/由 DAG 反轉）、
     L3 任務本體（推/全文）、L4 深層參照（拉/按需）（第 5 節）。
  3. L1/L2 由 planning 產生，非 main agent 當下手工 curate——換掉盲點機制、保留 context
     衛生原則（第 2、5 節）。
  4. L2 反向投影＝擴充 index.yaml（單一來源、不增檔）（user 定，第 8 節 Q1）。
  5. 體積管控＝consumption-driven 軟上限（下游強制消費為真紀律，行數僅粗略指標），
     非硬 gate；理由同 KD-5 教訓（game 數字）（user 定，第 9 節）。
  6. L4＝L2 附「拉取起點錨」（非白名單），升級 implementer.md 現有「讀鄰居」紀律
     （user 定，第 10 節）。
  7. L1 契約＝載 domain 核心身分＋真接縫＋task 架構位置；(身分+接縫) 走既有 planning
     Key Decisions 唯一來源通道；內部步驟格式轉交 thinking-redesign（user 定，第 10 節）。
