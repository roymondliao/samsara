# Samsara 1.0.0 — 設計方向（codebase-craft）

## 這份文件是什麼

一份**設計方向**，是多輪設計對話收斂後的結果——不是正式的 research / plan，而是把
「Samsara 為什麼要走向 1.0.0、要改什麼」想清楚、固定下來，當作之後正式改寫
`skills/{research,pre-thinking,planning,implement}/` 與 `agents/` 的總圖。

- 日期：2026-07-06（對話收斂）
- 狀態：需求已與 user 逐輪確認（見第 9 節決策記錄）；六大需求定案，開放項留給各 skill
  正式重寫時處理（見第 8 節）。
- 下一步：依第 6 節檔案清單，分頭正式化——先 research/pre-thinking（含既有的
  pre-thinking dynamic redesign），再 planning，再 implement。
- 前置關係：本方向 **supersede** in-flight 的 `2026-07-04_structural-honesty-mechanisms`
  iteration（含 ISSUE-003、#1-4 改 Defer 等 commit）——那些擱置、待本方向翻盤（見第 7 節）。
- 併入依據：`changes/2026-06-13_pre-thinking-dynamic-redesign/0-design-direction.md`
  是本方向的 thinking 階段基礎，1.0.0 將它實作出來並延伸 codebase-craft（見第 3 節第二步）。

---

## 1. 為什麼要 1.0.0：從 system 推導到 codebase

原本的 Samsara 站在 **system level**——它的 yin 面問「這個系統會不會靜默失敗」「這個
feature 消失了什麼會痛」「向死而驗」。它從來不是 unit-testing 的精神（death test ≠
unit test，存在即責任 ≠ 覆蓋率）。

1.0.0 的驅動力來自一個**跨專案的經驗發現**：

> system level 的腐敗，根源在 **codebase 本身**。在 system 層再怎麼加驗證、防護、檢查，
> 都擋不住「一段實作寫錯了」所種下的慢性腐敗。system 層的防禦只能**延緩**——把出事
> 時間往後推；它**消滅不了**問題，因為問題不在它守的那道邊界，在程式被寫下的那個點。

所以 1.0.0 要把同一套哲學，從 system **往下推導到 codebase / 實作 craft 層**。

**關鍵推論（治癒 vs 延緩）**：要消滅 codebase 腐敗，唯一介入點是「作者下筆的當下」的
判斷。任何事後檢查（不論放在 system 或 codebase 層）本質都是 symptom catcher——只能在
腐敗**寫出來之後**抓到（延緩），無法讓它**不被寫出來**（消滅）。讓腐敗不被寫下的唯一
手段，是**提升作者當下的判斷力**。

---

## 2. 這些決定的證據來自哪

- **thinking 階段的三鐵律**：來自 `2026-06-13_pre-thinking-dynamic-redesign` 翻了三個
  真 repo（samsara / xnexus-infra / vicone-secondsight）歸納的結論——問題不是 LLM 想不到、
  沒有結構性壓力的深度約一週腐化成儀式、不同工作要想的東西大半不一樣。
- **codebase-craft 的必要性**：來自本輪對 `2026-07-04_structural-honesty-mechanisms`
  feature 的 dogfood 與迭代——發現該 feature 方向對（把結構品質從 review-time 提前到
  generation-time）、手段錯（實作成 generation-time 多一道閘門，parse-failure/
  unconditional-FAIL 的機械語氣把判斷變儀式）。
- **implementer 隔離的病灶**：來自對現行 dispatch 模型的觀察——fresh subagent ＋ 逐 task
  貼 task-N.md ＋ curated overview 切片，全局思考從 thinking 到 implementer 之間被壓縮
  兩次，等傳到手上已很薄。

---

## 3. 核心理念（六條，整個設計建在這上面）

### 3.1 上游決定品質，不在鍵盤決定

好的實作是一條鏈做好的結果，不是打字的瞬間決定的：

```
深度理解/定義問題  ──  知道真正要解什麼、涉及哪些、哪些現在不做（research）
      ↓
廣度+深度的思考    ──  從已定義的問題出發，dynamic thinking（pre-thinking）
      ↓
規劃 tasks+細節    ──  依 thinking 結果規劃（planning）
      ↓
帶全局視野的實作    ──  依 planning + thinking 全局思考，選合適 pattern（implement）
```

這四個方向（thinking / design / develop / review）就是 software / research engineer 的
日常。1.0.0 要讓 codebase-craft 判斷流過這四段，重心在上游三段——因為品質在那裡被決定、
消滅在那裡發生。

### 3.2 兩層權責，互補不重疊

| | **System level（整體）** | **Codebase level（細粒度）** |
|---|---|---|
| yin 拷問對象 | feature/service 消失什麼痛；系統邊界靜默失敗；unknown 一等狀態 | 函式/模組/**抽象邊界**消失什麼痛；結構能否說出自己怎麼死；抽象是否投機 |
| 介入時機 | 多為事後/邊界（death-first acceptance、驗屍） | **authorship-time**：作者下筆畫邊界的當下 |
| 治理性質 | 延緩（守邊界、抓症狀） | 消滅（讓腐敗不被寫下） |
| 判準 | 存在即責任（施於 system 組件） | 存在即責任（施於 function/module/abstraction）＋結構誠實 |
| 手段 | 可含 format enforce | **純判斷＋證據可見**，不可 code enforce |

**粒度地板**：codebase 層下探到「函式/模組/抽象**邊界**」為止，不再往下（行文/命名/控制流
不是要治的病，也非要傳遞的東西）——這一層仍需對整體專案的理解與高維 system design 思考，
是判斷的最低層。

> **釐清「拷問範圍」vs「留痕門檻」是兩件事**（F2）：粒度地板指的是 **yin 拷問/review 看得
> 到的最低層**——reviewer 可以看到函式**邊界**是否誠實。但**值得留痕（寫進 scar 結構決定
> 條目）的門檻更窄**：只有**結構賭注**（pattern 選擇／邊界·接縫的建立或偏離／明確 refusal）
> 才留痕；一般的函式切分、命名雖在拷問範圍內，但不構成結構賭注、不留痕（筆記 5 §9、
> 筆記 6 §2.3）。所以「函式」在**邊界**意義上屬地板（被看），在**一般切分**意義上不留痕
> ——兩處講的是不同動作，不衝突。

### 3.3 design pattern 的正確定義（codebase-craft 的核心）

design pattern **不是為了 module / class / 抽象而做**，也不是裝飾。它是：

> 在實作當下這個 task 的時候，理解「未來哪些 tasks 要做什麼」＋「目前 project 已經有
> 什麼」，然後選出**合適的** pattern 來實作。

證據錨定是關鍵分界：

- **計畫裡的未來 tasks ＝已計畫的變動（證據第二階）**，不是想像。為它們選 pattern
  **正當**。
- 為**想像**中的未來預留擴充點 **禁止**——想像不是證據（違反公理：存在即責任）。
- 同一個「為未來設計」的動作，**證據等級決定它是 staff 還是 junior**。

這就是彈性定義的落地：**「牆打掉時不拖垮整棟樓」而非「預先蓋好未來的房間」**。而要做
這個 staff/junior 的區分，implementer **必須看得到 task 的依賴圖**（哪些後續 task 會踩
到這塊、project 現在長怎樣）——這正是下一條要修的病灶。

### 3.4 implementer 的全局思考通道（develop 樞紐）

現行 dispatch 把 implementer 餵成 task-local 切片，拿不到全局思考與 task 依賴，於是被
**架構性地逼成 junior**（局部最優、全局不連貫——junior code 的定義）。

1.0.0 要重新設計 thinking→implement 的傳遞，讓 implementer 在下筆時擁有：

1. **全局架構意圖**（來自 thinking：domain 真接縫、核心是什麼）
2. **task 依賴圖**（哪些後續 task 依賴/會踩到當前 task）
3. **當前 project 結構**（已經有什麼可重用、什麼 pattern 已在用）

有了這三者，implementer 才選得出 3.3 定義的、證據錨定的 pattern。

### 3.5 學習載體：不主動教，讓證據可見

**不主動教人。** 產出高品質內容 ＋ 讓證據可見（**全局→局部**的推理鏈），User 自己從
證據看懂「為什麼這樣做」。這就是 Samsara 既有的證據紀律（scar report、決策痕跡、
「為何不選別的」），延伸到 codebase-craft 決策。

這條同時消解了「教學 vs 自主」的張力：既然不主動教、只讓證據可見，auto 模式能全自動跑，
human 在場時靠讀證據學——**同一份證據兩用**。

### 3.6 format vs judgment 分界

> 完整設計見 `4-format-vs-judgment.md`。本節為總圖摘要（2026-07-06 回修：原稿把 format
> 錯掛給 samsara-cli，已修正）。

- **Format（事實/機械）** → **per-skill 的 format-validate 腳本**：YAML 解析、ref/seam-id
  解析、affects 指向真 task、數字實測等——feature 產物的機械形狀。由**產出該 artifact 的
  skill 自帶一支驗證腳本**，寫完後跑、回 feedback（deterministic 真程式＝真 teeth，非
  prose 服從）。**分類即 teeth 政策**：format 因不碰判斷，安全給硬 teeth。
- **Judgment（判斷/craft）** → agents：boundary 值不值得存在、抽象是否投機、pattern 選
  得對不對、結構誠實。**不可 code enforce**——code-enforce 判斷＝把判斷變儀式，訓練
  服從、殺死學習（structural-honesty feature 手段之所以錯、ISSUE-003 之所以該撤回）。
  judgment 的 teeth ＝ 證據可見 ＋ 對抗式 review ＋ consumption 紀律。
- **samsara-cli 的定位**：**只是把 Samsara 整合進不同 coding agent service（claude/codex/
  gemini…）的整合層**，**不是 format 檢查的家園**。「什麼在驗」是 per-skill 腳本，「怎麼讓
  它在各平台跑得起來」是 samsara-cli——分工，不是都在驗。

---

## 4. 貫穿全程的設計原則

1. **凡是會被「感覺」蒙混的判斷，一律換成「指得出可查證的證據」**（沿用 pre-thinking
   redesign 原則一）——把握、做完、推導、pattern 選擇，全用這個手法。
2. **消滅優先於延緩**：能在 authorship-time 讓腐敗不被寫下的，不要留到 review 才抓。
3. **證據可見即學習**：每個結構決定帶「為什麼這樣切、什麼 force 要求它、不這樣會怎麼
   腐、為何不選別的」，全局→局部——auto 拿來自我驗證，human 拿來看懂。
4. **auto 優先、human-in-the-loop 次之**：所有機制先保證能自主跑，human gate 是次要
   路徑，不是前提。
5. **證據等級決定正當性**：已發生的變動 > 已計畫的變動 > domain 本質分界 > 想像
   （想像不是證據）。為已計畫 task 設計正當、為想像預留禁止。
6. **format 歸機器、judgment 歸判斷**：不把判斷寫成閘門，也不讓機械檢查冒充判斷。

---

## 5. 怎麼知道這套機制壞了（上線後定期看）

- **owner**：samsara repo maintainer。
- **trigger**：每次 release 前，或對 samsara repo 自身跑 validate-and-ship 時核對一輪。

任一條長期成立，代表對應機制已死：

- implementer 產出的結構長期是 task-local 局部最優、跨 task 不連貫 → 全局思考通道沒真
  傳到（3.4 失效）。
- design pattern 的選擇理由長期指不出「哪個已計畫 task 要求它」→ 要嘛在憑空蓋（想像
  當證據），要嘛在裝飾（3.3 失效）。
- 出現「為了將來擴充」卻指不出計畫依據的擴充點 → 投機一般化復辟（違反公理）。
- 證據鏈開始出現跨案複製貼上的罐頭句（「為何不選別的」腐化）→ 證據可見退化成儀式
  （3.5 失效）。
- 出現 parse-failure / unconditional-FAIL 語氣的「判斷」規則 → judgment 又被寫成閘門
  （3.6 失效）。
- codebase-craft 的判斷只出現在 review 階段、上游三段從不觸及 → 又退回「延緩」模式
  （3.1 失效）。

---

## 6. 要改哪些檔案（分頭正式化的總圖）

> 以下為方向級指認，各檔的具體改法留給正式重寫時依 Samsara 自身 workflow 產出。

| 方向 | 檔案 | 改什麼 |
|---|---|---|
| thinking | `skills/research/` | 深度問題定義：真正要解什麼、涉及哪些、哪些現在不做（強化 scope 減法） |
| thinking | `skills/pre-thinking/`（含 flow.md, references/, templates/）| **實作 `2026-06-13` dynamic redesign 六步**，並延伸 codebase-craft：把「domain 真接縫」當成未來 module/abstraction 邊界的來源 |
| design | `skills/planning/` | task 依賴圖成為一等產物（供 implementer 選 pattern）；Key Decisions 唯一來源沿用；把 structure 決策從閘門改成證據錨定的判斷 |
| develop | `skills/implement/` + `dispatch-template.md` | **全局思考通道**：dispatch 傳全局架構意圖＋task 依賴圖＋當前 project 結構，不只 task 切片 |
| develop | `agents/implementer.md` | codebase-craft 判斷（依當前 project＋已計畫 tasks 選 pattern）成為下筆紀律；證據可見（結構決定附推理鏈） |
| review | `agents/code-reviewer.md`（yin）| 補 seam 擺放維度：檔案是否坐落在 index.yaml 宣告的 seam 上（Architectural Placement 的延伸）（筆記 6 §4）|
| review | `agents/code-quality-reviewer.md` | 九原則沿用；從 verdict 導向調整為證據可見（推理，非只判決）；format vs judgment 分界對齊 |
| format | `skills/*/`（各 skill 自帶 format-validate 腳本）| feature 產物機械形狀驗證的家園（seam-id 解析、affects、數字實測…）；寫完 artifact 跑、回 feedback（筆記 4） |
| 整合 | `samsara_cli/` | **只是**跨 coding agent service 整合層（讓 Samsara＋各 skill 腳本在各服務跑起來）；**非 format 家園**、不碰判斷 |

**怎麼驗證改得對不對**（照 writing-skills 流程，拿歷史案當對照——待正式化時定案）：
- 用一個真實 feature 全程跑一次，檢查 implementer 是否拿到全局思考、pattern 選擇是否
  指得出已計畫 task 依據、證據鏈是否全局→局部可讀。

---

## 7. 對 in-flight 工作的處置

- `2026-07-04_structural-honesty-mechanisms` 的 **iteration 擱置、待翻盤**：ISSUE-003
  撤回（code-enforce 判斷違背 3.6）、#1-4 應回歸 Accept（prose-only 是設計不是債務）。
- 該 feature 的 **generation-time 方向被 1.0.0 繼承並修正**（3.1/3.3）；**閘門手段被
  取代**（3.6）。
- 已 commit 的 iteration fix 中，對齊 1.0.0 的（報數紀律＝事實誠實、domain router＝
  消除摩擦、獨立稽核＝判斷手段）可保留為既成事實；違背的（ISSUE-003 及其連帶 Defer
  分類）在正式化 planning 時明確翻盤並記錄。

---

## 8. 還沒決定的（留給正式化處理）

> 進度：以下數項已由設計筆記 1-4 收斂（標 ✅），落地細節留正式化；其餘仍開放。

- ✅ **全局思考通道的傳遞形式** → `1-global-thinking-channel.md`（四層 context（三推一拉）、廣覺察×窄內容、
  consumption 軟上限）。
- ✅ **thinking 如何延伸 codebase-craft** → `2-thinking-codebase-craft.md`（L1 升為六步具名輸出、
  證據逐階累積）。
- ✅ **task 依賴圖的產物形式** → `3-planning-products.md`（擴充 index.yaml：`seam`＋`affects`）。
- ✅ **format vs judgment 的精確清單** → `4-format-vs-judgment.md`（分類即 teeth 政策；format＝
  per-skill 腳本、judgment＝可見＋review；samsara-cli 只是整合層）。
- ✅ **證據可見的載體形式** → `5-evidence-visibility.md`（scar 內 dual-face「結構決定」條目：
  陽 forced_by＋陰 refused/risk；write-filter＋consumption 防膨脹；同時是 L2 consumption 追溯）。
- ✅ **implement/review 端落地** → `6-implement-review-landing.md`（不新增 agent；implementer
  消費 L1/L2→證據錨定選 pattern→dual-face 留痕；reviewer verdict→證據可見；yin＝seam 擺放、
  quality＝結構品質；reviewer 擋≠code gate）。
- ✅ **1.0.0 的 Evaluation Contract** → `7-evaluation-contract.md`（Primary evaluator＝用新 1.0.0
  跑真實跨 task 結構 feature、檢查因果鏈可觀測後果：留痕解析／零非預期拆牆／零投機出貨／
  獨立 agent 追得通鏈；量 proxy 非終極目標；「判斷力提升」列長期健康指標）。

**設計方向階段完成**：七份設計筆記全封版，開放項全數收斂（落地細節留正式化）。下一步進入
分頭正式化各 skill 的實作階段（第 6 節總圖 ＋ 各筆記結論為依據）。

**正式化進度（實作階段）：**
- ✅ **pre-thinking**（commit `0c41e2d`，2026-07-06）：六步 redesign 實作 ＋ codebase-craft L1
  嫁接。落地 6 檔——`skills/pre-thinking/{SKILL.md,flow.md}` 六步重寫、`templates/pre-thinking.md`
  含 L1 輸出、新增 `templates/lens-report.md`（搜尋者回傳格式）、新增 `references/lenses.md`
  （角度清單）、`skills/planning/SKILL.md` 契約同步（Step C→Step 6、L1 消費行）。全套件 938
  passed。**兩個實作期發現**：(1) `references/` 落點——build（`engine.py` `_copy_referenced_refs_to_skills`）
  以 **repo-root `references/`** 為唯一來源、按引用打包進各 skill，故 lenses.md 放 repo-root 非
  skill-local（redesign §6 字面路徑會被 build 靜默忽略）；(2) 測試分流——`Step B/C` 名是機制、
  隨六步設計移動更新測試 heading，auto-mode「雙路徑四 token」斷言是原則、原封保留並補回被精簡
  掉的 token（atomic-context 的 auto-initiate/Phase 4/escape clause 亦補回 flow.md）。
- ✅ **planning**（2026-07-06 本輪）：Step 5「Codebase-Craft Products」——task→seam 映射（L1
  位置）、affects＋anchors（L2 投影＋拉取起點錨，含 F3 上游 interface live-code 錨）、seam 證據
  加強至 planned-change、缺接縫退回 pre-thinking 的單一來源 STOP gate、consumption-driven 軟
  上限。templates/index.yaml 加 `seam`/`affects`/`anchors`；templates/overview.md 加 Core
  Identity＋Real Seams（單一宣告處）。筆記 1-3。
- ✅ **implement / agents**（2026-07-06 本輪）：dispatch-template 四層 context（三推一拉）——
  Global Position (L1)＋Context Projection (L2) prompt 段、copy-never-compose 規則、舊 plan
  顯式 `global_channel: absent`；implementer.md 消費 L1/L2/錨（read-before-write 鄰居清單改由
  錨供給，順序契約不變）、pattern 選擇＝f(project, 已計畫 tasks) 證據錨定、scar 加 dual-face
  `structural_decisions`（schema Rules 15-17：粒度地板 write-filter、雙面完整、forced_by 只引
  決定當下已存在證據）。筆記 1、5、6。
- ✅ **review**（2026-07-06 本輪）：yin（code-reviewer.md）補 seam 擺放維度（resolve＝format
  歸 validator、坐落真不真＝judgment 歸 yin）；quality（code-quality-reviewer.md）加
  Structural Decision Review lane（forced_by 相關性、soft seam 有據 vs 投機、缺留痕＝finding、
  推理 payload durable 進 review-record）＋「block 是論證非 gate」；F6 仲裁路徑落在
  implement SKILL（human／auto-gatekeeper 仲裁，非 reviewer 自動勝、非自我豁免）。筆記 6。
- ✅ **format-validate 腳本**（2026-07-06 本輪）：per-skill 共置——`skills/planning/scripts/
  validate_format.py`（index 解析、seam/affects/depends/planned 解析、needs 非空）＋
  `skills/implement/scripts/validate_format.py`（scar 解析、dual-face 完整、forced_by/seam
  解析、systemic_ref dangling、debt 一致）。回 line-level feedback；輸出貼交棒＝visible
  missing。**實作期發現**：跑腳本／測試 import 會在 skill 目錄產生 `__pycache__`，converter
  以 UTF-8 讀全部 companion 檔會炸 build——converter 已補 skip（含 death test）、測試載入端
  `dont_write_bytecode`。筆記 4。
- ✅ **research 強化**（2026-07-06 本輪）：Step 0.5 問題本質（需求語言，具名產物）＋ Boundary
  Scope 三清單（真正要解什麼／涉及哪些／哪些現在不做，附 not-now 理由）；kickoff 模板同步。
  與 pre-thinking flow.md 既有的「research problem-essence」消費行接上。筆記 2 §3。
- ⏳ **evaluation dogfood**：用新 1.0.0 全程跑一個真實跨 task 結構 feature、查因果鏈四訊號
  ——筆記 7。機制已就位，待真實 feature 演練。
- ✅（部分）**auto 模式怎麼接**：各 skill 既有 Auto Mode Gate 未動；新增的仲裁路徑（F6）已
  接 auto-gatekeeper＋auto-decisions.md。dogfood 時驗證全鏈。
- ⏳ **structural-honesty feature 重分類的清理**（`4-format-vs-judgment.md` 第 8 節）：
  【user 定 2026-07-06】**回頭再清理**——先立 1.0.0 正向骨架，之後再拆那幾條「judgment
  假裝 format」的遺留規則。

---

## 9. 決策記錄

- **2026-07-06**（來源：本輪多輪需求重新討論，user 逐點確認）：
  1. **方向 supersede**：Samsara 1.0.0 精神＝system→codebase；起因是 system 層只能
     延緩、消滅不了 codebase 腐敗（user 定案）。
  2. **prose 架構是設計不是債務**：runtime enforcement 只該用於 format/事實；判斷/craft
     不可 code enforce（否則 AI 進化時成枷鎖、且把判斷變儀式）。ISSUE-003 該撤回。
  3. **粒度地板＝函式/模組/抽象邊界**，不再往下（user 定案，理由：這層仍需全局與 system
     design 思考，是判斷最低層）。
  4. **兩層權責互補**：system 管整體、codebase 管細粒度，非保留 vs 取代（user 定案）。
  5. **四方向＝engineer 日常**：thinking/design/develop/review，重心在上游三段（user 定案）。
  6. **pre-thinking dynamic redesign 納入 1.0.0 範圍**：這次實作出來並延伸 codebase-craft
     （user 定案）。
  7. **implementer 隔離是 develop 樞紐**：缺全局思考與 task 依賴 → 被逼成 junior
     （user 認同）。
  8. **design pattern 定義**：依當前 project＋已計畫 tasks 選，證據錨定，非投機非裝飾
     （user 定案）。
  9. **學習載體＝證據可見，非主動教**：User 從證據看全局→局部（user 定案）。
  10. **auto 優先、human-in-the-loop 次之**（user 定案）。
- **2026-07-06（設計筆記細化，逐點 user 確認）**：
  11. 3.6 回修：format＝**per-skill validate 腳本**（非 samsara-cli）；samsara-cli 只是
      跨 coding agent service 整合層、非 format 家園（見 `4-format-vs-judgment.md`）。
  12. 設計筆記 1-4 封版：全局思考通道（四層 context（三推一拉））、thinking codebase-craft（L1 具名
      輸出、證據逐階累積）、planning 產物（index.yaml `seam`＋`affects`）、format vs judgment
      （分類即 teeth 政策）。
  13. structural-honesty feature 的「judgment 假裝 format」重分類：**回頭再清理**（user 定）。
