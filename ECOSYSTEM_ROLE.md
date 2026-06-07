# ECOSYSTEM_ROLE | prospera-client-xinyuan
Date: 2026-06-02
Type: CLIENT_REPO (客戶專屬)
Governing: GOVERNANCE_PLAN v3.0

## Unique Role
欣轅室內工程（室內設計公司）的客戶專屬 repo
存放品牌設定、工程案例、歷史內容記錄
透過 tenant_id=xinyuan 接入 Prospera 公版平台

## Client Profile
Client: 欣轅室內工程
Industry: interior_engineering
tenant_id: xinyuan

## Connected Platform Services
- prospera-product-consulting (策略、內容、分析)
- prospera-product-gengrant (設計業補助申請)

## Brand Settings
Tone: 質感、專業、創意
Target: 有室內工程需求的屋主和企業主
Platforms: Facebook, LINE, Instagram

## AI Agent Orchestrator Integration
tenant_id=xinyuan 透過 prospera-agent-orchestrator
路由到 consulting/gengrant 平台服務

## Boundary
STORES: 工程案例描述、客戶風格偏好、歷史文案
DOES NOT: 直接執行 AI（使用平台 repo 服務）
