<!-- Prospera SYSTEM HEADER (ADR-0032/SBOM) | 性質:idea | 設計:Kevin 架構 | 執行:AI 工具(claude.ai+Claude Code) | 驗證:無機制驗證 | IP:創造性歸 Kevin(發明人), AI 為執行工具 -->
# CONTRACT | prospera-client-xinyuan
Ring: R5 Products (Client Repo)
Version: v1.0
Date: 2026-06-02
tenant_id: xinyuan

## Role
欣轅室內工程客戶專屬品牌 KB。
Platform repos 透過 tenant_id=xinyuan 存取此 repo 的品牌設定。

## Connected Services
| Platform | 用途 |
|----------|------|
| prospera-product-consulting | 室內設計案件策略、內容、社群文案 |
| prospera-product-gengrant | 設計業政府補助申請 |

## Boundary
- 不直接執行 AI 任務
- 不儲存 API key
- 品牌設定更新需透過 brand_config.json
