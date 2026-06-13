<!-- Prospera SYSTEM HEADER (ADR-0032/SBOM) | 性質:idea | 設計:Kevin 架構 | 執行:AI 工具(claude.ai+Claude Code) | 驗證:git 實證 | IP:創造性歸 Kevin(發明人), AI 為執行工具 -->
# 01_ground_truth — 五維度 ground truth（移植母系統 G-SBOM，不簡化）

> Stage J 標準核心：客戶 repo 的 ground truth ＝ 與母系統同一架構（CC-PLAN-stage-J 裁示 B）。`tools/` 為母系統生成器**原樣移植**，不簡化。

## 工具（原樣移植自 prospera-constitution-governance/governance/tools/）
- `tools/system_inventory_gen.py` — 每 repo SYSTEM_INVENTORY 生成器（SBOM/SPDX 對齊）。
- `tools/apply_system_inventory.py` — per-file IP header / IP_NOTICE 套用。

## 五維度判準（不簡化）
1. **EXTS 覆蓋**：.py/.md/.yml/.yaml/.txt/.json/.ps1/.html/.gitignore；具名豁免逐檔列明。
2. **IP 覆蓋**：per-file header + repo 級 IP_NOTICE hybrid（ADR-0032）。
3. **收斂**：`complete_at_head`＝生成時 HEAD hash（HEAD 變動需重跑；持續對帳）。
4. **instant baseline**：`src_gap`＝對照 `git ls-files` 源碼數，gap=0 才完整。
5. **IMPORT_GRAPH**：依賴衝擊（規模大時啟用）。

## 用法（在 repo 根執行）
```
python 01_ground_truth/tools/system_inventory_gen.py . --write   # 產 SYSTEM_INVENTORY.json
python 01_ground_truth/tools/system_inventory_gen.py .           # 只印摘要（不寫）
```

> J-2 第 1 道 fitness 即跑本工具，門檻同母系統（complete=True / src_gap=0）。
