# Task 7: 0-design-direction.md 六項修訂與章節一致性核對

## Context

Read: overview.md

對象：`changes/2026-06-13_pre-thinking-dynamic-redesign/0-design-direction.md`（pre-thinking 重設計的設計方向文件；正式重寫 `skills/pre-thinking/` 不在本次 scope，本 task 只修訂設計文件本身）。六項修訂全部經 user 確認。此文件無 pytest 覆蓋（位於 changes/），守護方式是修訂內建的交叉核對步驟＋acceptance 條款。

## Files

- Modify: `changes/2026-06-13_pre-thinking-dynamic-redesign/0-design-direction.md`：

  1. **交棒格式定案**（第 8 節「待討論」第 2 項 → 已解）：新增決定——pre-thinking 第四步產出的設計決定是 planning Key Decisions 的**唯一來源**；planning 逐條引用、不得重新推導、不得新增 placement 決定；planning 既有的 File Map Consistency STOP gate 直接對 pre-thinking 的決定檢查。寫明理由：防 ISSUE-001 病灶形狀（同一決定存在兩處、無 cross-check）複製到 doc 層。
  2. **刪「輕想」層**（改寫第一步深度尺與第 8 節對應已解項）：深度只剩一個真正閘門——fast-track（兩軸歸零證明）；其餘全走同一流程，**搜尋者數量 0..n 是第二步「沒把握假設」數量的湧現結果**（0 個角度＝原輕想情境）。寫明刪除理由：「證明 main agent 沒有盲點」不可證偽——盲點的定義就是自己看不見的東西。
  3. **刪第五步「少數意見安全網」**：搜尋者已被限制只回傳事實、事實不打架，「被丟掉的刺耳候選」防的是被設計排除的問題；「沒丟寫『無』」正是會腐化成罐頭句的強制欄位（違反文件自己的健康指標第 4 條）。
  4. **健康指標補 owner/trigger ＋ 深度過剩指標**（第 5 節）：owner ＝ samsara repo maintainer；trigger ＝ 每次 release 前或對 samsara repo 自身跑 validate-and-ship 時核對一輪。新增腐化訊號：「pre-thinking 文件長度中位數超過上限（暫定 300 行）或其設計決定未被 planning 引用 → 深想在空轉」——沒人消費的深度才會退化，防退化的根本是下游強制引用。
  5. **中斷重啟定案**（第 8 節「待小設計」→ 已解）：沿用現行 `skills/pre-thinking/flow.md` §5 的 K3b 機制；六步只需定義各步完成標記格式，偵測邏輯復用 K3b，不另造新機制。
  6. **刪第一步「成熟度」分類**（user 確認）：第一步只判類型與深度；第四步「自己推導」的根源規則直接寫「依據 ＝ Samsara 公理 ＋ 問題的硬需求 ＋ 既有慣例／契約（若找得到且確認沒爛）」——找慣例的動作本身就得出情境答案，先分類再查與直接查等效。第 8 節「已解」中的成熟度條目同步標記為被本修訂取代。

  **交叉核對步驟（修訂完成後、回報前執行）**：逐節核對第 3 節（六步描述）、第 7 節（否決清單）、第 8 節（已解／待討論清單）與六項修訂的一致性——刪輕想影響第 3 節第一步與第 8 節第 7 項；刪成熟度影響第 3 節第一步/第四步與第 8 節已解清單；任何殘留矛盾修掉並在文件末尾的修訂記錄註明。文件開頭的狀態行（「六步流程已逐步談定…」）與日期同步更新。

## Death Test Requirements

無 pytest 死測（changes/ 內文件不在測試範圍）。等效死測 ＝ 交叉核對步驟的輸出：修訂後文件中 `grep` 不到「輕想」作為現行機制的描述（歷史對照與否決記錄除外）、不到「成熟度」作為第一步產出的描述；第 8 節不再有「待討論（本輪）」下的交棒項。核對結果寫入 scar report。

## Unit Test Contract

- Contract source: 文件化 artifact shape——修訂後 0-design-direction.md 的六個決定文字各自存在且第 3/7/8 節無矛盾（人工核對清單，非 pytest；核對記錄是本 task 的可驗證產出）
- A unit test must assert this named contract source, not implementation details.

## Implementation Steps

- [ ] Step 1: 寫出交叉核對清單（等效死測，先於修訂——列出每項修訂會波及的節）
- [ ] Step 2: 逐項執行六項修訂
- [ ] Step 3: 執行交叉核對，修掉殘留矛盾
- [ ] Step 4: grep 驗證（輕想／成熟度／交棒待討論項）
- [ ] Step 5: Write scar report
- [ ] Step 6: Report back (do not commit)

## Expected Scar Report Items

- Potential shortcut: 「pre-thinking 文件長度上限暫定 300 行」是未經校準的數字——記錄依據（secondsight 533 行過深、50 行過淺的兩端）
- Assumption to verify: 文件第 6 節「要改哪些檔案」表格是否需同步（它描述未來正式重寫的檔案清單——輕想/成熟度刪除會改變 flow.md 該寫的內容）
- Potential shortcut: 交棒格式只定了原則（唯一來源＋逐條引用），輸出檔的具體欄位樣式留給正式重寫——記錄為殘留清單項

## Acceptance Criteria

- Covers: "Degradation - 設計文件修訂與既有章節衝突"
- Covers: happy path 逐項條件之「設計文件六項各有決定文字」
