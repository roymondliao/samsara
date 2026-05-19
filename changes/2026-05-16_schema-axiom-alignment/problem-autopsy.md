# Problem Autopsy: samsara-manifesto-v1

## original_statement

> 根據目前 Samsara 的開發理念，在我測試多個不同的 project 後，我發現一件事，Samsara 的機制不容許有 death path 沒有被 cover，但我發現在軟體開發上，有些 death path 是必然要發生，比如說 config setting 沒有設定，這就是 user 自己的問題，自己把事情做死了，所以有些 death path 是必然要呈現，而不是所有都要被解決

（後續關鍵澄清，原文逐字保留）

> Samsara 是面向 system，而不是面向 user。

> 不管是 loud failure or silent failure 都是需要檢驗出來，而檢驗出來的 failure 是能被 system 接受與否才是重點，像是 config 設定錯誤這類就是 loud failure 必須要要顯示出來，爾 silent failure 是不能被接受，因為沒有被說出來，所以要修復，修復的程度就要從 system 角度來看，這個問題不被修復是否 system 會整個壞掉，或是 system 可以明確呈現這件事，而這件事本身是 user 該負責，而不是 system 來替 user cover。

> Samsara 有更強的準則跟要求，system fragility budget 有時候會因為 human/user 的偷懶而有 workround 的處理方式，但 Samsara 不接受這樣的狀況，workround 最後會影響的是 system，要就是在 system 前啟動前明確的死亡，而不能讓 system 啟動後默默的死亡，這是差異。

> TDD 對 AI 來說只是一個 coding 遊戲而已，只要改對 code 就可以 pass。

## reframed_statement

Samsara 在 v0.9.x 缺乏明文 manifesto，導致 framework 身份模糊；schema 使用 `type: death_path` 這個寬泛名稱來描述「只測 silent failure」的內容，造成 implementer 把「合法的、user 該負責的 loud failure（如 missing config）」誤分類為「必須修復的 silent rot」。本次升級為 manifesto v1：(1) 明文宣告 Samsara 面向 system 而非 developer——對抗 AI 時代「TDD 被降級為 coding game」的盲區；(2) 把 failure 分類軸從主觀的 loud/silent 改為可觀測的時間軸（boundary 之前死 vs system 啟動後死）；(3) 明文化 workaround 的精確定義（= 把 boundary-fail 推遲為 runtime-fail）；(4) 以 deprecated alias 提供 ≥6 個月的向後相容路徑，使 framework 演進本身遵守 Samsara 公理。

## translation_delta

```yaml
translation_delta:
  - original: "有些 death path 是必然要呈現，而不是所有都要被解決"
    reframed: "All death paths must be verified; the question is only whether the system can accept them post-verification"
    delta: "Original 字面暗示『某些 death path 不需驗證即可放生』；reframed 保留 Samsara 公理（所有死必須被檢驗），把『接受與否』移為下游決策。此 delta 防止讀者把 manifesto 誤讀為『放寬 framework』——這是最危險的翻譯損失"

  - original: "config setting 沒有設定，這就是 user 自己的問題"
    reframed: "boundary-fail (system 啟動前明確死亡，user 該負責)"
    delta: "Original 用『user fault』描述責任歸屬，是主觀判斷；reframed 用『時間軸位置』描述結構特徵，可被觀測。Schema 必須基於可觀測軸，否則 implementer 永遠在猜『這算誰的錯』"

  - original: "Samsara 是面向 system，而不是面向 user"
    reframed: "Samsara is system-facing; verification axis is whether the system can truly live, not whether the developer feels productive"
    delta: "Original 是宣告；reframed 把宣告操作化（驗證軸不同）。Manifesto 不能只是口號，必須附帶可執行的操作軸——這是宣告與規則的橋"

  - original: "workaround 最後會影響的是 system"
    reframed: "workaround = the act of postponing boundary-fail into runtime-fail"
    delta: "Original 描述後果；reframed 給出結構定義。讓『禁止 workaround』從道德訴求（『別偷懶』）變成可驗證的時序要求（『boundary 之後才死的都算 workaround』）——這是 Samsara 對 SRE fragility budget 的精確化"

  - original: "TDD 對 AI 來說只是一個 coding 遊戲而已，只要改對 code 就可以 pass"
    reframed: "Samsara's anti-thesis: AI-era test-gaming"
    delta: "Original 是 user 觀察；reframed 升格為 framework 的對立物。讓 Samsara 有了清楚的『不是什麼』——對任何 framework 而言，明確的反命題比正命題更能定義邊界"

  - original: "假裝活著，但其實已經快死了的狀態"
    reframed: "zombie system — operationally responding but structurally dead"
    delta: "Original 是隱喻；reframed 給隱喻一個術語位置。Glossary 必須收錄這個詞——它比『silent failure』更傳達哲學立場"
```

## kill_conditions

```yaml
kill_conditions:
  - condition: "C1 — Empirical evidence 不足：尚無 ≥3 個獨立 case study（含具體誤分類的 scar report、誤導 implementer 行為的紀錄）證明 schema 誤分類確實導致實質傷害"
    rationale: "Manifesto-level 升級的觸發條件是『多個案例驗證痛點不可解』；當前僅 cross-project anecdotal 觀察。可能 framework 在哲學上完備、實務上未真正崩壞——若如此，升級就是 over-engineering。Planning 階段必須先補齊案例 evidence"

  - condition: "C2 — 既有 v0.9.1 user 對當前版本已建立穩定工作模式，且 M4 migration path 證明不可行（例：deprecated alias 機制過於複雜、無法穩定保留 6 個月）"
    rationale: "Framework 演進必須自我遵守 Samsara——若升級必須讓既有工作流從『活著』變成『假裝活著』才能完成，那升級本身就是 anti-pattern（system 啟動後默默死亡）。M4 是這條 kill condition 的緩解；M4 失敗則整個升級必須取消"
```

## damage_recipients

```yaml
damage_recipients:
  - who: "既有 v0.9.1 user with already-generated plan/scar files"
    cost: "歷史檔案使用 `type: death_path` 詞彙，schema 升級後格式變成 deprecated。由 M4 (deprecated alias ≥6 個月 + migration 指引) 緩解。這是唯一真實的 damage"

  - who: "(主動拒絕受損地位) 想用 Samsara 當『更嚴格 TDD』的潛在採用者"
    cost: "Manifesto 明文宣告 system-facing 後，這類採用者可能勸退。Samsara 主動接受『市場縮小、純度提高』的 trade-off——這不是 damage，是 framework 邊界宣告"

  - who: "(無 damage，user 已確認) Skill 作者、CLI/agent/hook 機制、framework maintainer 自己"
    cost: "User 已明確判定不會受影響；skill 作者反而受益於更清晰 vocabulary"
```

## observable_done_state

「解決」狀態同時滿足三個可觀測條件：**(A) Framework 文件層**——core docs 明文宣告 system-facing、glossary 定義 zombie/dead/workaround、failure schema 以 boundary-vs-runtime 為軸；**(B) Implementer 行為層**——implementer 寫 acceptance.yaml 與 scar report 時能準確分辨 boundary-fail vs runtime-fail 且 boundary-fail 比例 < 30%；**(C) Maintainer 解釋負擔層**——未來 user 來問「我這個 case 算 cover 了嗎」，maintainer 可指 glossary + 規則一句話打發，不必再花 30 分鐘解釋。

「沒解決」狀態 = 文件仍只說「禁止靜默失敗」、`type: death_path` 涵義含糊、AI-era 對抗點未明寫；implementer 持續把 loud crash 誤塞進 silent_failure_conditions；maintainer 持續每 1-2 週對不同 user 重複解釋同一概念。
