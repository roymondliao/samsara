# Problem Autopsy: scar-report-subtraction

## original_statement

> 在 @changes/ 都會發現 scar-report 都寫過長，且寫的內容都不夠具體、清晰、簡潔跟白話，所以久而久之這個 report 就沒有被看的必要性，變成只是留一個證據而已。關於這部分要如何改善？

## reframed_statement

Scar report 的 schema 給了一個無限深的自由文本洞（`description` blob），validator 對長度零檢查，而下游只消費少數結構化欄位。寫的人被「漏寫會被抓、寫長不會被抓」的誘因推向防禦性冗長。要改的不是寫作紀律，是結構（定長槽位）、誘因（機械預算）、與消費契約（明確誰讀什麼、不讀的去別處）。

## translation_delta

```yaml
translation_delta:
  - original: "寫過長、不夠具體、清晰、簡潔跟白話"
    reframed: "schema 結構容許冗長 + validator 不懲罰冗長 + 內容無讀者"
    delta: "使用者描述的是症狀（寫作品質），重述成病因（結構與誘因）。風險：『白話』是語意品質，機械手段只能間接促成（短槽位逼出直述句），無法直接驗證 — 這層翻譯損失明確標記，語意品質仍靠 reviewer。"
  - original: "沒有被看的必要性，變成只是留一個證據"
    reframed: "長敘事欄位是 write-only；唯一機械讀者（iteration Step 1）只消費 deferred/resolved/systemic_ref/parse 狀態"
    delta: "把『沒人看』從感受升級為可查證的消費面事實 — 這個升級若錯（人類其實會回頭讀長敘事），整個減法方向都錯，列入 kill condition。"
```

## kill_conditions

```yaml
kill_conditions:
  - condition: "證實長敘事有真實讀者 — 例如 debugging/iteration 曾靠 narrative 全文救回關鍵脈絡，或 owner 表明會回頭讀完整敘事"
    rationale: "『無讀者』是整個減法的前提。前提倒，該做的是改善敘事的可讀性而非刪除它。"
  - condition: "解法本身變成第 18、19 條 prose 規則（只加規則文字、不加結構或 validator 檢查）"
    rationale: "Rules 9–17 已證明 doc-vs-runtime-obedience：註解規則不改變 agent 行為。重複已失敗的手段即應中止。"
  - condition: "長度預算無法在不傷誠實的閾值下運作 — 試校準後，真疤仍必須被砍才能過 validator"
    rationale: "Scar 的第一義是誠實。可讀性是第二義，不得以第一義為代價。"
  - condition: "改動規模失控 — 從 schema/validator/兩個 skill 擴散到重寫多數 workflow skills"
    rationale: "治冗長的 feature 自己變冗長，是最直接的自我否證。"
```

## damage_recipients

```yaml
damage_recipients:
  - who: "implementer agent（寫入面）"
    cost: "每條疤要壓進定長槽位 — 壓縮是額外思考成本；真正複雜的疤需要 escape hatch（narrative 仍在但有預算）"
  - who: "code reviewers / quality reviewers"
    cost: "失去把 review 裁決史寫進 scar 的習慣位置，必須改用 review record — 過渡期會有找不到地方寫的摩擦"
  - who: "iteration aggregator 與其測試"
    cost: "永久承擔三代格式（plain string / description blob / 定長槽位）的讀取相容"
  - who: "舊 scar reports"
    cost: "不遷移 — 它們保持原樣、依舊冗長；歷史的可讀性明確放棄"
```

## observable_done_state

新制上線後的第一個 feature：每份 scar report 通過 `validate_format.py` 的長度預算（超標 = finding、handoff 擋下），單一條目在 6 行內說完「疤是什麼／何時咬人／在哪」。舊 report 未動且 iteration 聚合對新舊格式都不丟條目。未解決的樣子：report 仍超預算但照樣 handoff，或預算只存在於 schema 註解而 validator 不執行。
