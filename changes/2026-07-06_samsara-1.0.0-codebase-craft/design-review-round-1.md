# 設計筆記一致性審查 — Round 1（獨立對抗式）

**Provenance**：設計方向階段完成後（commit 11bee13）的一致性審查。審查者為**獨立 read-only
agent**（與七份筆記的作者分離——避免自審盲點，dogfood 筆記 7 的 F-G 判官模式）。審查指令為
對抗式（獵矛盾、缺口、術語漂移）。主 agent 逐項驗證後處置，記錄於下。

## 驗證與處置總表

| # | 類別 | 嚴重度 | 驗證 | 處置 |
|---|---|---|---|---|
| F1 | samsara-cli 殘留歸屬 | 高（阻塞）| **確認為真**：筆記 3 §3 仍寫「兩種家園／samsara-cli」，筆記 4 卻聲稱已修正 | **已修**：筆記 3 §3 對齊筆記 4（per-skill 腳本；samsara-cli 只是整合層；無兩種家園）|
| F2 | 粒度地板「函式」在地板上 vs 以下 | 中高（阻塞）| **確認為真**：0 §3.2 函式邊界屬地板；5/6 稱函式切分屬地板以下 | **已修**：0 §3.2 加釐清「拷問範圍（看得到函式邊界）vs 留痕門檻（只結構賭注）是兩件事」|
| F3 | L2「上游契約」無載體、被下游丟棄 | 中（阻塞）| **確認為真**：1 §5 列為 L2 成分；3 §4 無此欄、6 §2.1 未提 | **已修**（user 定選項 B）：從 L2 §5 移除；改由 L4 拉取錨含「所依賴 task 的 interface 檔」讀 live；無上游依賴＝無上游契約（user 補）|
| F4 | 總圖 File Map 漏 code-reviewer.md | 中 | **確認為真**：6 要改 yin，0 §6 無該列 | **已修**：0 §6 補 yin 列（seam 擺放維度）|
| F5 | 「結構決定＝consumption 追溯」全稱過強 | 中 | **確認為真**：純 git-history 驅動的決定不消費 affects | **已修**：5 §5 降為「affects-linked 部分雙用」（⊋ 非恆等）|
| F6 | reviewer 擋 vs 不設 gate 在 auto 下無仲裁 | 中（阻塞）| **確認為真**：4 禁 gate、6 可擋、7 倚賴硬零，但 auto 無仲裁者 | **已修**（user 定）：仲裁者＝human／auto-gatekeeper（對稱同一角色）；筆記 6 §3.3 補仲裁路徑、筆記 7 §3 校正硬零為評估時結果 |
| F7 | 「階」兼指 rank 與 pipeline stage | 中低 | 確認：措辭雙義，§4.2 已解釋 | **已修**：2 §7 改「沿 pipeline stage 逐步」＋註明與 rank 脫鉤、非單調 |
| F8 | format「硬 teeth／機器守」過強 | 低 | **確認為真**：基線是 skill 指令＋visible-missing，非機器強制 | **已修**：4 §2 改「腳本內容 deterministic；是否被跑靠指令＋visible-missing、hook 可升」|
| F9 | 「三層 context」實列四層 | 低 | 確認 | **已修**：1 §5 改「四層（三推一拉）」|

## 兩個待 user 定的決策點

### F3 — L2「上游契約」怎麼處理
- 現況：筆記 1 §5 把 L2 定為「已計畫 task＋上游契約＋鄰近 pattern」三成分，但 index.yaml
  `affects` 只有 task＋needs，「上游契約」無欄可放，且筆記 6 重述 L2 時省略了它。
- **主 agent 建議：從 L2 移除「上游契約」，改由 L4 拉取錨覆蓋**。理由：你要遵守的上游契約，
  最準的來源是**依賴 task 的真實 interface（live code）**，不是 planning 事先摘要的一句話
  （摘要會與真 code drift——違反「map 非真值、以 live 為準」）。L4 錨本就指「你至少該讀的
  鄰近檔」，把「你依賴的 task 的 interface 檔」納入錨即可，比在 L2 塞一個會腐的摘要欄好。

### F6 — auto 模式下 reviewer 擋的「可爭辯」由誰仲裁
- 現況：筆記 4「judgment 不設 code gate」、筆記 6「reviewer 可擋 Critical（可爭辯≠枷鎖）」、
  筆記 7「投機出貨硬零、倚賴 review 攔」。但 auto 模式無 human，「可反駁卻無人反駁」的
  block ＝ 功能上的硬 gate，三者的縫合是空的。
- **主 agent 建議：auto 模式的仲裁者＝既有的 `samsara:auto-gatekeeper`（獨立第三判斷）**。
  implementer 不服 reviewer 的 Critical，可附證據 refute → 由 gatekeeper（非 reviewer 自動
  獲勝、非 implementer 自我豁免）裁決，決定寫入 auto-decisions.md。human 模式則 human 仲裁。
  這讓「可爭辯」有實體路徑（有第三方仲裁＝可爭辯；無仲裁的 deterministic 擋＝code gate），
  且筆記 7 的「硬零」語意校正為：**硬零是評估時的可觀測結果（有沒有投機出貨），不是 review
  中途的 deterministic 保證**——review 是攔截機制，仲裁後仍可能放行（但那就會在評估時現形）。

## 總評（審查者原話）

> 有必須先解的矛盾。必解：F1、F2、F3、F6。應解非阻塞：F4、F5、F7、F8、F9。這些多為
> 「方向對、措辭/落點未收乾淨」的縫隙，沒有動搖六大核心理念——但 F1/F2/F3/F6 若不先解，
> 正式化時會被不同 skill 各自演繹成不一致的實作。

主 agent 註記：**9 項全數處置完畢**（F1/F2/F4/F5/F6/F7/F8/F9 已修；F3 已依 user 選項 B 修）。
核心六理念未被審查動搖，方向穩固。**Round 1 一致性審查收尾。**

## 收尾狀態（2026-07-06）

全部 9 findings 已解。修改落在：筆記 1（§5 移除上游契約、§5 標題四層、§10 加 F3 錨）、
筆記 2（§7 F7 措辭）、筆記 3（§3 F1 對齊）、筆記 4（§2 F8 teeth 措辭）、筆記 5（§5 F5 部分
雙用）、筆記 6（§3.3 F6 仲裁路徑）、筆記 7（§3 F6 硬零校正）、筆記 0（§3.2 F2 釐清、§6 F4
補 yin 列）。此審查（獨立對抗式）本身即 dogfood 筆記 7 的 F-G 判官模式——並成功抓到 F1
這種「作者自審會相信自己『已修正』宣稱、實則沒改」的自評偏誤。

---

## 附：審查者完整報告（逐字保存）

（以下為獨立審查 agent 的原始輸出，durable 保存供稽核。）

F1 — 【殘留錯誤歸屬／直接矛盾｜高】筆記 3 仍留「format 有兩種家園（其一＝samsara-cli）」，
被筆記 4 明文宣稱已修正、實際沒改。3 §3「format 檢查至少有兩種家園…samsara-cli」vs 4 §4
「不是…沒有『兩個家園』這回事（修正筆記 3）」——修正沒清乾淨，必解。

F2 — 【術語漂移／矛盾｜中高】0 §3.2 把「函式」邊界放地板上（yin 拷問含函式/模組/抽象邊界），
5 §9/6 §2.3 把「函式切分」標地板以下（不留痕）。可調和但需一句話分清「拷問範圍 vs 留痕門檻」。

F3 — 【缺口 dangling｜中】1 §5 L2 含「上游契約」，但 3 §4 affects 只有 task＋needs、無此欄，
6 §2.1 靜默省略。真缺口——給載體或明刪。

F4 — 【缺口／總圖覆蓋｜中】0 §6 File Map review 列只有 code-quality-reviewer.md，漏
code-reviewer.md（yin），但 6 §4 要改它。補一列。

F5 — 【雙用宣稱不成立｜中】5 §5「結構決定記錄＝L2 consumption 追溯是同一份東西」是洩漏等式：
純 git-history 驅動的結構決定不消費 affects。應降為「affects-linked 部分雙用」（⊋ 非恆等）。
對照：1 §9「pattern 指已計畫依據＝沒被指到的投影＝噪音」是同一規則兩讀，成立；0 §3.5「同一
證據 auto 自驗＋human 學習」成立。

F6 — 【reviewer 擋 vs 不設 gate｜中】4「judgment 永遠不給 code gate」vs 6 §3.3「reviewer 對
Critical 擋…差別是可不可爭辯」，但無筆記定義「爭辯由誰仲裁」。auto 模式（0 原則4）無 human
仲裁，「可反駁但無人反駁」＝功能硬 gate；7 §3 pass signal 3 又把「review 應攔投機」當硬零
依據。需補 auto 下的仲裁/推翻機制。

F7 — 【術語漂移｜中低】「證據逐階累積」的「階」兩義：證據 rank（已發生>已計畫>domain>想像）
vs pipeline stage（research→pre-thinking→planning）。且累積非按 rank 單調（planning 補中間的
rank2）。§4.2 有解釋但「階」雙義易誤解，建議「逐階」改「沿 pipeline 逐步」。

F8 — 【format teeth 措辭過強｜低】4 §2「儘量給硬 teeth／機器守」，但 §3 自承基線是「最弱執法
（prose 請跑）＋visible-missing」、hook 自動觸發是「加分項非基線」。腳本內容 deterministic，
但是否被跑基線靠 prose——「機器守」對基線過實，措辭需自洽。

F9 — 【內部計數漂移｜低】1 §5「三層 context 模型」「分三層」但列 L1/L2/L3/L4；合理讀法＝
「三推一拉」，統一數字即可。

補充：death case 互斥＝無硬互斥。seam／接縫／real seam 指同一物，一致。「O—marked bet」作為
7 §3 硬零攔截機制以外部代號出現、八份筆記內無定義（建議點名確認＝既有九原則之 Open-closed
落點）。
