# 設計筆記 4 — format vs judgment：分類即 teeth 政策

對應 `0-design-direction.md` 3.6，並收 `3-planning-products.md` Q3 轉來的難題：
**「機械可判的 format 檢查，如何在 workflow 內取得 teeth，而不淪為 prose 服從、也不越界去
enforce judgment？」** 本筆記主張：這個難題的解，就藏在「把每個檢查分類分對」這件事本身。

> 修正上游：`0-design-direction` 3.6 寫「Format → samsara-cli」是錯的歸屬。正解（2026-07-06
> user）：feature 產物的 format 驗證＝**per-skill 的 format-validate 腳本**（第 4 節）；
> **samsara-cli 只是把 Samsara 整合進不同 coding agent service 的整合層**，不是 format 檢查
> 的家園。沒有「兩個家園」這回事。3.6 待回修（見第 10 節 Q3）。

---

## 1. 分類的試金石

對任一個「檢查」，問一句：

> **一台不懂這個 domain 的機器，能不能每次都得到正確答案？**

- **能 → FORMAT（事實/機械）**：答案唯一、可查證、機器與人結果一致。
  例：YAML 解不解析？seam-id 解析得到嗎？affects 指向的 task 存在嗎？報告裡的數字符合
  某指令的實測輸出嗎？
- **不能 → JUDGMENT（判斷/craft）**：需要對 project/domain 的理解；兩個有能力的 reviewer
  可能合理地不同意；答案是被論證的立場，不是查表。
  例：這條接縫是不是對的邊界？這個抽象是不是投機？這個 pattern 適不適合？

第三類是病灶：**judgment 假裝成 format**——用 binary pass/fail、parse-failure 的語氣寫，
骨子裡是判斷。structural-honesty feature 的手段錯正是這類（見第 8 節）。

---

## 2. 核心主張：分類即 teeth 政策

「teeth 難題」之所以難，是因為把「要不要給 teeth」當成一個獨立問題。其實**分類一旦分對，
teeth 政策就自動確定**：

| 類別 | teeth 政策 | 為什麼 |
|---|---|---|
| **FORMAT** | **儘量給最硬的可得 teeth**——per-skill validate 腳本；**腳本內容 deterministic**（結果唬不了），**是否被跑**基線靠 skill 指令＋visible-missing、平台有 hook 可升為自動觸發（見 §4） | format 檢查**不約束作者的判斷**——它只抓機械錯誤。給它硬 gate 不是枷鎖（枷鎖只發生在 enforce judgment 時）。 |
| **JUDGMENT** | **永遠不給 code gate**；teeth ＝ 證據可見 ＋ 對抗式 review ＋ consumption 紀律 | code-enforce 判斷＝把判斷變儀式、訓練服從、殺死學習（3.6、`0-design-direction` 全篇核心）。 |
| **judgment 假裝 format** | **拆開重分類**：format 核心給 teeth，judgment 殘餘移交 reviewer | 不拆就兩頭皆輸——既有 gate 的僵硬、又扼殺判斷。 |

`★ 關鍵反轉`：3.6 一直說「judgment 不可 code enforce」，容易被誤讀成「所以什麼都別給
硬 teeth」。錯。**format 不但可以、而且應該給最硬的 teeth**——因為它天生不碰判斷。真正
的紀律不是「少給 teeth」，是「**給對地方**」：format 那半儘量硬，judgment 那半一點 gate
都不給。

---

## 3. 為什麼 format 安全、judgment 不安全（更深一層）

差別在**留不留下可證偽的痕跡**：

- **format 檢查產出可證偽的 artifact**（指令輸出、解析結果）。就算只用最弱的執法（prose
  「請跑這個檢查」），一旦被略過，**痕跡是缺的/可對照的**——下游任何人看得出「這個檢查
  沒跑」。silent skip 被轉成 **visible missing**。
- **judgment 略過不留痕**：「我判斷過了，沒問題」——略過與認真判過，表面一模一樣。所以
  對 judgment 設 gate，只會訓練人生產「看起來判過」的儀式；真正防退化的是讓**推理本身
  可見、可被對抗式挑戰**。

這就是為什麼 format 可以往下壓、judgment 不行：**format 把「靜默失敗」變成「看得見的
缺漏」，judgment 不會。** 這也解釋了 doc-vs-runtime-obedience 為什麼對 format 傷害小、
對 judgment 致命。

---

## 4. FORMAT 的執行機制：per-skill 的 format-validate 腳本

teeth 不靠全局 hook——hook 是 session 全局，觸發階段對不上「我剛寫完這個 artifact」的粒度，
還要靠 file-path 過濾，脆弱（user Q1）。改用**與 skill 共置的 format-validate 腳本**：

- **每個會產出 artifact 的 skill，帶一支 format-validate 腳本**（Python），驗它自己產物的
  機械形狀（planning 的腳本驗 index.yaml：seam-id 解析、affects 指向真 task；implement 的
  腳本驗 scar 解析、數字實測；等等）。
- **skill 指令寫明**：寫完 artifact 後跑這支腳本，拿它的**驗證 feedback**。
- 腳本是 **deterministic 真程式** → 這就是 teeth（不是 prose 服從）；且它回**feedback**
  （哪條 seam-id 解不到、哪個 affects 指向空）而非只有 pass/fail → agent 能據以修。
- 腳本輸出貼進交棒記錄＝**可證偽證據**；沒跑＝輸出缺＝**visible missing**（第 3 節）。

**為什麼比全局 hook 好**：
- **粒度對**：綁在「skill 寫完自己的 artifact」這一刻，不是 session 全局事件。
- **單一職責**：產物的 owner skill 也 own 它的 format 驗證，co-located、好維護、好演化。
- **可攜**：腳本隨 skill 走；讓它在各 coding agent service 上跑得起來，是 samsara-cli 的
  整合職責（見下）。

**（可選增強）** 平台若支援 PostToolUse 類 hook，可**自動觸發**對應腳本，把「agent 要記得
跑」的殘餘 skip 也消掉——加分項，非基線；基線就是 skill 指令 ＋ 共置腳本。

### samsara-cli 的定位（修正點 2）

samsara-cli **只是把 Samsara 整合進不同 coding agent service** 的那層（claude / codex /
gemini …）。它**不是** feature 產物 format 檢查的家園——**沒有「兩個家園」這回事**（修正
筆記 3 與本筆記原稿措辭）。feature 產物的 format 驗證＝per-skill 腳本，就這一種；samsara-cli
做的是讓 Samsara（含各 skill 的驗證腳本）能在各服務上跑起來的整合工作。「什麼在驗」是
per-skill 腳本，「怎麼讓它在各平台跑得起來」是 samsara-cli——分工，不是都在驗。

---

## 5. JUDGMENT 的 teeth（不是 gate，是可見＋對抗）

judgment 拿不到 gate，但不是沒有 teeth：

1. **證據可見（3.5）**：判斷附推理鏈（為何這樣切、什麼 force、不這樣會怎麼腐），全局→局部。
   略過判斷＝推理鏈空白，看得出來。
2. **對抗式 review**：獨立 reviewer 用不同 lens 挑戰（本次 iteration 的 F-G 獨立稽核就是
   實例——用獨立 agent 判斷去驗，不用 code gate）。
3. **consumption 紀律**：判斷產物（如接縫、投影）沒被下游消費＝噪音（筆記 1 第 9 節）。

三者合起來讓 judgment「略過會露餡」，但**不凍結**判斷內容——這正是 format gate 做不到、
也不該做的。

---

## 6. 1.0.0 已設計機制的 format/judgment 歸類

| 檢查 | 類別 | teeth |
|---|---|---|
| artifact YAML 解析 | format | 該 skill 的 validate 腳本 |
| seam-id 解析到 Key Decisions 宣告的接縫 | format | planning 的 validate 腳本 |
| affects task-id 指向真 task | format | planning 的 validate 腳本 |
| 報告數字＝實測（F-B） | format | implement 的 validate 腳本（F-B 已落地雛型） |
| （samsara-cli 的轉換整合是否正確）| 非 workflow format | samsara-cli 自身整合職責，不在此表 |
| 接縫是不是對的邊界 / 該不該存在 | judgment | 可見＋review |
| 核心身分是否可操作（非空話） | judgment | 可見（可操作性準則，筆記 2 第 4.1） |
| pattern 選得對不對（依 project＋已計畫 task） | judgment | 可見＋review＋consumption |
| 抽象是否投機 vs 證據錨定 | judgment | 可見＋review |
| 九大結構原則 | judgment | 可見＋review |
| 接縫證據階標得誠不誠實 | judgment | 可見＋review |

---

## 7. workflow 內 format 檢查的執行點

feature 產物層的 format 檢查落在**交棒點**（最自然的 gate）：

- **planning → implement**：seam-id 全解析、affects 全指向真 task、index.yaml 解析。
- **implement → review／iteration**：scar 解析、數字實測。

執行方式：交棒時由該 skill 的 format-validate 腳本跑、貼 feedback（第 4 節），平台有
PostToolUse hook 則可自動觸發。**家園是 per-skill 腳本，不是 samsara-cli**（samsara-cli 是
跨服務整合層）。

---

## 8. 重分類 structural-honesty feature 的「judgment 假裝 format」

拆開那幾條 binary/parse-failure 語氣的規則——format 核心留 teeth，judgment 殘餘移 reviewer：

| 原規則 | format 核心（給 teeth） | judgment 殘餘（移 reviewer） |
|---|---|---|
| structure-spec「缺 section = FAIL 無條件」 | 若 schema 宣告某 section 必填，它解不解析得到 | 這個 feature 該不該有 structure-spec（豁免與否是判斷） |
| 「drift_items 缺欄位 = parse failure」 | 欄位在不在 | 零漂移是不是真的對（reviewer 判） |
| 0-dangling 稽查 | 所有 ref 解不解析得到 → **本來就是純 format，給 teeth 正確** | （無殘餘） |
| 50% 注入訊號 | 行數算術（實測） | 「這個比例算不算問題」是啟發式判斷 |

原則：**凡是寫成 binary gate 的，先問它的答案需不需要 domain 理解**。需要→那半是 judgment，
不能用 gate 語氣，移交 reviewer 的可見＋對抗。

---

## 9. 死亡拷問（death cases ＋ 偵測）

| 死法 | 靜默失敗長怎樣 | 偵測/防線 |
|---|---|---|
| format 被當 judgment（留 prose 無 teeth） | 機械錯誤靠人肉抓、時漏時中 | 分類試金石：機器能定答＝format＝該給 teeth，別留 prose |
| judgment 被當 format（給 gate） | 判斷變填表儀式、扼殺學習（1.0.0 最核心的病） | 分類試金石：需 domain 理解＝judgment＝禁 gate；審查任何 binary 規則的答案可證偽性 |
| format 腳本沒被跑（skill 指令被略過） | 驗證 feedback 缺，但若下游不看就漏 | 交棒記錄必含腳本輸出欄；缺＝交棒不完整（visible missing，非 silent）；平台有 hook 則自動觸發消除此 skip |
| 「judgment 假裝 format」沒被拆、整條移走或整條留 | 要嘛丟掉 format 核心的 teeth，要嘛把 judgment 也 gate 了 | 第 8 節逐條拆分，不整條處置 |

---

## 10. 開放問題（給 user 定）

1. **format 執行機制** ——【已定，2026-07-06 user】per-skill 的 format-validate 腳本（寫完
   artifact 後跑、回 feedback），非全局 hook；平台有 PostToolUse hook 則可選擇性自動觸發
   （加分項）。設計見第 4 節。
2. **samsara-cli 定位** ——【已定，2026-07-06 user】只是把 Samsara 整合進不同 coding agent
   service 的整合層，**不是 format 檢查家園**；沒有「兩個家園」。
3. **0-design-direction 3.6 回修** ——【已定並已執行，2026-07-06 user】3.6 已回修為
   「feature 產物 format＝per-skill validate 腳本；samsara-cli＝跨 coding agent service 整合層，
   非驗證家園」；總圖第 6 節 File Map、第 8 節開放項亦同步對齊。
4. **structural-honesty feature 重分類的落地時機** ——【已定，2026-07-06 user】**回頭再清理**：
   先立 1.0.0 正向骨架，之後再拆第 8 節那幾條「judgment 假裝 format」的遺留規則。

> **狀態：本筆記封版**。format vs judgment＝分類即 teeth 政策；format→per-skill 腳本
> （寫完跑、回 feedback）、judgment→可見＋對抗式 review＋consumption；samsara-cli 只是
> 整合層。舊 feature 重分類延後清理。

---

## 11. 決策記錄

- **2026-07-06**（來源：本設計筆記對話，user 逐點確認）：
  1. **分類即 teeth 政策**：format 儘量給硬 teeth（安全，不碰判斷）；judgment 永遠不給 gate
     （會變儀式）；judgment 假裝 format 者拆開重分類（第 2 節）。
  2. **試金石**：不懂 domain 的機器能否每次得到正確答案——能＝format、不能＝judgment（第 1 節）。
  3. **format 安全的根因**：它產出可證偽痕跡，silent skip→visible missing；judgment 略過
     不留痕，故對它設 gate 只訓練儀式（第 3 節）。
  4. **format 執行機制＝per-skill validate 腳本**（寫完 artifact 後跑、回 feedback），非全局
     hook（粒度不對）；平台有 hook 可選擇性自動觸發（user 定 Q1，第 4 節）。
  5. **samsara-cli 只是跨 coding agent service 整合層**，非 format 家園；無「兩個家園」
     （user 定 Q2，第 4、8 節）——修正筆記 3、本筆記原稿與 0-design-direction 3.6 的措辭。
  6. **judgment 的 teeth＝證據可見＋對抗式 review＋consumption 紀律**（第 5 節；F-G 為實例）。
  7. **待 user**：3.6 回修授權（Q3）、structural-honesty 重分類時機（Q4）。
