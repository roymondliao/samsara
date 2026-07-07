# Problem Autopsy: structural-honesty-mechanisms

## 1. original_statement

> Samsara 的理念是在 system level，從系統腐敗的角度去切入現在系統容易崩壞的問題，但在經過多次使用 Samsara 的工作流程後，發現一件事情是就系統的崩壞本質上來執於 codebase 的腐爛。
>
> 在 AI 時代下，Coding agent 的強大無庸置疑，但是帶來的問題就是 codebase 的 quality 不被重視，因為 AI coding 速度太快，所以 human 選擇直接打掉重做，但這只是一個無窮循環的狀況，而且不管打掉重做幾次，codebase 的等級都只停留在 POC 的階段而已。
>
> 反之，在這個時代下，應該是要可以打造出 production 等級的 codebase 才對，AI coding 不是不會寫具有 high quality 的 codebase，而是既定的 system prompt 因為人類的喜好，要求先以 POC 為主。……
>
> High quality 的 codebase 會被具備好的 system design, 使用正確的 design pattern 來建構 codebase、codebase 具備易擴展、可維護、符合 SOLID 原則以及具備 cohesion and coupling 的設計、codebase 的設計上不僅只是根據當前的需求設計，更是為了將來的 feature 拓展保有彈性。
>
> 最終，在經歷過不同的 project 測試後，我體悟到的是 codebase 的腐爛才是根源導致系統的腐爛，而系統的腐爛是可以透過很"髒"的手法來延緩發生腐爛的時間，但最終還是腐爛。

（2026-07-04 對話原文；後續討論定案為 `docs/thinking.md` 第四章「結構誠實」。）

## 2. reframed_statement

結構是行為的上游：Samsara 的 death test / scar report 在行為層抓謊言，但結構層的謊言（不誠實的邊界、混雜的職責、錯亂的依賴）沒有 generation-time 的機制對付——結構品質只存在於 review-time 的 `code-quality-reviewer`，是驗屍不是產前檢查，結構從來沒有被 spec 過。本 feature 在 Samsara workflow 裡建立結構決策的完整證據鏈：planning 生成 structure spec（每個結構投資引用有證據落點的變動理由）、implement 定向注入、review 對照驗證、iteration/reconciliation 度量漂移。

## 3. translation_delta

```yaml
translation_delta:
  - original: "codebase 的設計……為了將來的 feature 拓展保有彈性"
    reframed: "彈性是「牆打掉不拖垮整棟樓」（低改動擴散半徑），不是「預先蓋好未來的房間」（speculative generalization）"
    delta: "原始措辭與公理「存在即責任」牴觸——為假想未來而存在的抽象答不出「消失了什麼會痛」。重定義後「未來」被證據定界：index.yaml 尚未完成的 tasks、kickoff scope、death cases 才是可設計的未來。user 已明確認同此轉化（2026-07-04）"
  - original: "應該是要可以打造出 production 等級的 codebase"
    reframed: "受益者是用 Samsara 開發的專案；Samsara 自己是第一個 dogfooding 對象"
    delta: "理念射程（整個 AI coding 時代）縮到本 feature 射程（Samsara workflow 機制）。已裁決：機制必須是平台無關的 workflow 行為（跟 plugin 走到任何專案），不是 Samsara repo 的內部慣例"
  - original: "使用正確的 design pattern 來建構 codebase……符合 SOLID 原則"
    reframed: "每個 pattern 引用它服務的變動理由；引用不出證據的 pattern 是 cargo cult"
    delta: "pattern 從「目標」（好 codebase 的特徵）變成「被拷問的對象」（要出示證據才准存在）。機制設計上是實質差異：structure spec 要求的是『每個結構投資附證據』，不是『鼓勵設計出 pattern』——後者會帶偏 AI 走向過度設計。user 已認同"
  - original: "既定的 system prompt 因為人類的喜好，要求先以 POC 為主"
    reframed: "simple 偏好是對 AI 過度設計失敗模式的疤痕組織；翻轉成 production 偏好只是換偏誤方向，需要的是判準"
    delta: "歸因修正：偏好的來源不只是人類喜好，也是防禦。加上第二個根因：context 蒸發——就算 prompt 要求 production quality，結構意圖不成為 durable artifact 就會每 session 歸零。這是機制要走 artifact 路線（而非 prompt 路線）的理由"
```

## 4. kill_conditions

```yaml
kill_conditions:
  - condition: "工作是有死期的真 POC（死期寫入 kickoff），或走 fast-track 的小改動"
    rationale: "寫了死期的 POC 有權利保持 POC。機制若無法區分真 POC 與假 POC，就是用新偏好取代判準，把所有小工作的成本一律抬高——這違反機制自己的哲學"
  - condition: "找不到讓 cargo-cult 證據可被偵測的方法（agent 為每個 pattern 自動生成煞有介事但不可解析的變動理由）"
    rationale: "不可偵測的假證據讓結構謊言拿到蓋章，比沒有機制更糟——假安全感是 doc-presence ≠ runtime obedience 的結構版。證據引用必須機器可解析，否則機制不得以必填欄位形式存在"
  - condition: "只能以淨增加無人消費的儀式落地（structure spec 寫完沒有下游讀它）"
    rationale: "噪音會靜默地殺死訊號：沒人讀的 spec 等於沒有 spec（減法 branch 用 73 份 scar / 8239 行換來的教訓）。每個產出物必須有明確的下游消費者，否則按公理不該存在"
  - condition: "全局結構 context 不新鮮（codebase map stale 超過閾值）卻照常注入"
    rationale: "注入腐爛的藍圖比不注入更危險——agent 拿過期全局結構做『全局最優』決策。context 新鮮度是前置條件，不是可假設永遠成立的隱式假設"
```

## 5. damage_recipients

```yaml
damage_recipients:
  - who: "小改動使用者"
    cost: "若進入判準（M4）有漏洞，50 行的 feature 也要寫 module 邊界文件。防線：fast-track 不受影響是硬承諾"
  - who: "每次 implementer/reviewer dispatch"
    cost: "定向注入的 token 稅與延遲，task 越多課稅越重。止血點：只注入 task 觸及的 spec 片段（單 task 上限為整份 spec 的 50%）"
  - who: "框架維護面（doc-contract 測試、dist/ regenerate、多平台 converter）"
    cost: "skill 大改的整條供應鏈成本。裁決：確定淘汰的機制連同測試一起刪，不留 backward-compat；歷史 artifacts 不回填但聚合邏輯不得崩潰"
  - who: "workflow-subtraction-optimization 的北極星"
    cost: "instruction surface 必然上升，與減法目標對撞。裁決：本 feature 開新 change 目錄、北極星獨立計算，並以『儀式淨增量 <= 200 行 loaded-context』sub-metric 自我約束"
  - who: "code-quality-reviewer"
    cost: "角色從單一 9 原則模式變雙模式（有 spec 對照 spec、無 spec 用原則），過渡期對新舊 feature 都必須誠實回報用的是哪種模式"
```

## 6. observable_done_state

解決：用 Samsara 跑完一個 feature 後，repo 裡存在一份被下游實際消費過的 structure spec —— implementer 的 dispatch 記錄有它的片段、reviewer 的 verdict 引用過它的條目、reconciliation 報告了實作與它的漂移量，結構決策第一次有「從生成到驗屍」的完整證據鏈。沒解決：結構品質依然只在 review-time 出現，PASS 之後沒人知道結構是被設計的還是碰巧長成這樣，打掉重做時結構知識隨 session 蒸發。判別問題只有一個：「這個 feature 的結構長這樣，是哪份文件承諾的？」——答得出來就是解決。
