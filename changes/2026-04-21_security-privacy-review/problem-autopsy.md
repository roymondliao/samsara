# Problem Autopsy: Security & Privacy Review Gate

## original_statement

「目的是為了做 security & privacy review，避免任何資安的洩漏到 repo，所以需要再 push 前去檢測整個 feature / bugfix 完成後 commit 的修改內容。而檢測到問題該如何處理？需要讓 human 之後有 security & privacy issue 被檢測出來，並且提出該如何修復，並與 human 確認。」

「會採用內建工具是因為都是大廠開發的，所以大廠不會拿石頭砸自己的腳，而大廠對於 security & privacy 的處理，會比我們自己弄一個新的來的夠有用。」

## reframed_statement

在 samsara 的 implement/iteration 完成後、validate-and-ship 之前，加入一個獨立的 security & privacy review gate。這個 gate 使用當前平台（coding agent）內建的 security review 能力，檢查所有 committed changes。發現問題時，呈現 issue list 和修復建議給 human，human 確認後修復，修復後重新 review 直到通過。通過後才進入 validate-and-ship。

## translation_delta

```yaml
translation_delta:
  - original: "避免任何資安的洩漏到 repo"
    reframed: "在 push 前攔截 security/privacy issues"
    delta: "'任何' 是理想目標；實際只能攔截平台內建工具能偵測到的 attack vectors。明確化為 'push 前攔截' 而非 '避免任何'"

  - original: "使用內建工具"
    reframed: "platform-agnostic 描述，不綁定特定 coding agent"
    delta: "原始意圖是用大廠工具；延伸為 platform-agnostic 是因為 Phase 7 multi-platform 計畫。如果 Phase 7 取消，可退回 Claude Code 專用"

  - original: "檢測到問題該如何處理"
    reframed: "human gate + fix loop"
    delta: "原始是問句；具體化為 blocking gate with human confirmation + iterative fix until pass"
```

## kill_conditions

```yaml
kill_conditions:
  - condition: "所有目標平台（Claude Code、Codex、Gemini CLI、Windsurf）都沒有內建 security review 能力"
    rationale: "核心前提是不自建工具。如果平台都不提供，這個 skill 變成空殼"

  - condition: "CI/CD pipeline 已有完善的 security scanning（GitHub Advanced Security、Snyk、etc），且覆蓋率和 response time 都優於 dev workflow 層的 gate"
    rationale: "重複防線的成本（developer velocity）超過邊際收益"
```

## damage_recipients

```yaml
damage_recipients:
  - who: "開發者"
    cost: "每次 push 前多一個 gate，增加等待時間和認知負擔"

  - who: "Human 的注意力"
    cost: "需要判讀 security review 結果，尤其是 false positives。Security 領域 false positive 率天生較高"
```

## observable_done_state

Samsara 的 skill chain 中，implement/iteration 完成後、validate-and-ship 之前，有一個明確的 security & privacy review step。這個 step 使用平台內建能力檢查 committed changes，發現問題時 human 必須確認修復方案才能繼續。沒有這個 step 時，security issues 直接隨 push 進入 repo，唯一的防線是 CI/CD（如果有的話）。
