<!-- Prospera SYSTEM HEADER (ADR-0032/SBOM) | 性質:idea | 設計:Kevin 架構 | 執行:AI 工具(claude.ai+Claude Code) | 驗證:git 實證 | IP:創造性歸 Kevin(發明人), AI 為執行工具 -->
# CONTAINER IDENTITY TEMPLATE｜商業事實 Ground Truth 三層 schema

> **真相源中樞 template**（Kevin 裁定 B）。客戶 repo 的商業事實基準（單一真相源）。
> 抽象自唯一實證實例 `prospera-client-phoenix/CONTAINER_IDENTITY.md`，三層分級 + 每欄位「產品線消費標記」。
> **填寫紀律**：`{{ }}` 為待填欄；**L-官方層每欄須附來源**（政府登記/官網 URL）；無法查證者填 `⚠️待補（來源）`，**禁** AI 推測填值。
> **層級分級對齊** `governance/CLIENT_GROUND_TRUTH_SCHEMA.md` §一（事實基準層 SSOT，裁定 C 拆分後）。

## git tenant_id
`{{tenant_id}}`

---

## L-官方登記層（硬事實 · ✅ 可當捏造基準 · Fitness D 比對此層）

> 來源限政府登記 / 官網公開頁。**禁推測**。每欄附來源。

| 欄位 | 值 | 來源（URL/文件） | 產品線消費標記 |
|---|---|---|---|
| 法人正式名稱 | {{法人全名}} | {{來源}} | Consulting · Resource · Brand |
| 帳號主體代號 | {{代號}} | {{來源}} | Resource · 系統 |
| 統一編號 | {{統編}} | {{政府登記}} | Resource（補助資格硬條件） |
| 負責人/院長 姓名·頭銜·專科 | {{姓名/頭銜/專科}} | {{官網 about/team URL}} | Brand（人格映射事實底）· Consulting |
| 設立登記 | {{設立日/類型}} | {{來源}} | Resource · Consulting |
| 資本額 | {{登記資本額/實收}} | {{經濟部 GCIS}} | Resource（補助額度/資格）· Consulting |
| 登記地址 | {{登記地址}} | {{經濟部 GCIS}} | 系統 · Operation · Resource |
| 登記機關 | {{登記機關}} | {{經濟部 GCIS}} | Resource（管轄判定） |
| 登記狀態 | {{核准設立/解散…}} | {{經濟部 GCIS}} | Consulting · Resource（存續查核） |
| 英文名 | {{英文}} | {{來源}} | Brand · 系統 |
| 網域 | {{domain}} | {{官網}} | Brand · Operation · 系統 |

---

## L-品牌自述層（推論/自述 · ❌ 不當捏造基準 · Fitness D 略過）

> 來源 BrandKB.json（推論性質）。屬品牌人格延伸，**非官方事實**。

| 欄位 | 值 | 來源 | 產品線消費標記 |
|---|---|---|---|
| 品牌名 | {{品牌名}} | {{BrandKB}} | Brand · Operation |
| 12 原型評分（榮格，0-20） | Primary {{原型}} {{分}}/20｜Secondary {{}}｜Tertiary {{}} | `<client>_BrandKB_v1.0.json` § archetypes | **Brand（人格骨架）** |
| MIT 四維語調 | Formality {{}}｜Energy {{}}｜Humor {{}}｜Authority {{}} | `brand-voice.md`（由人格推導） | Brand（語調執行） |
| 品牌訊息支柱 / 禁區 | {{支柱}} / {{禁區}} | {{BrandKB}} | Brand · Operation |

> **提醒**：四維量表是語調執行工具，**非人格骨架**（骨架＝12 原型）。本層全部欄位**不得**作為「事實對錯」判準。

---

## L-系統歸屬層（系統真相 · routing）

### 多層身份（同一 Container）
- 法人：{{法人名}}　品牌：{{品牌名}}　據點/別名：{{別名清單}}

### 歸屬規則（asset routing）
> 盤點/搬料時，命中以下任一名稱/代號，一律歸本 Container：
{{別名1｜別名2｜代號｜domain｜tenant_id=...}}

### 隔離原則（Container 隔離 / 承重牆2）
> 多層身份為**同一記憶邊界**；不得與其他 Container（{{其他 tenant 例}}）混料。

---

## 鋪設檢核（J-3 客戶 repo 重修時）
- [ ] L-官方層每欄附真實來源（URL/文件），無 AI 推測值
- [ ] 12 原型 / MIT 四維標明 SSOT＝BrandKB.json（自述層，非事實基準）
- [ ] routing 別名清單涵蓋所有歷史名稱（防搬料混料）
- [ ] 隔離邊界明列不得混料的其他 Container
- [ ] 既有 `CONTRACT.md`/`ECOSYSTEM_ROLE.md` 遷入或指向本檔（搬遷=Tier1；刪既有=Tier0 冷審）
