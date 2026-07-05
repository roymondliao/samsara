# Overview: issue-002-validate-live-surface

## Goal

讓 `samsara-cli validate` 的 issue 數可歸零、可被 gate 消費：source-tree 掃描預設排除非 live-surface 路徑。

## Architecture

單點修改：`samsara_cli/validators/target.py` 的掃描入口加 live-surface 排除（單一常數）。零新模組、零新依賴。

## Key Decisions

- **KD-A（placement）**：排除邏輯住在 `samsara_cli/validators/target.py`（TargetValidator 自身）——不在 `main.py`（CLI 層不該擁有掃描語意），不在 config yaml（這是 validator 的本質邊界，不是平台差異）。
- **KD-B（ownership）**：排除清單為 TargetValidator 內單一常數（見 structure-spec.yaml SD-1），任何消費者共用。
- **KD-C**：預設啟用排除（ISSUE-002 證明 CI 從不呼叫 validate，改預設無下游風險）；不加 flag（YAGNI —— 殘餘需求出現再議，kickoff 已列 out of scope）。

## Death Cases Summary

1. 排除清單誤含 live 路徑（例如把 `skills/` 打錯進排除）→ 真實洩漏樣式被靜默漏檢 —— 測試必須斷言 live 路徑仍被掃描。
2. 排除只在 CLI 層生效、直接使用 TargetValidator 的呼叫者（tests、未來 gate）拿到不同行為 —— SD-1 的單一常數即防線。

## File Map

- `samsara_cli/validators/target.py`（modify）— live-surface 排除常數 + 掃描過濾
- `tests/test_validators/`（modify/create）— 死法測試 + 契約測試
