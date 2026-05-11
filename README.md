# adnex-bi-be

基於 FastAPI + PostgreSQL 的商業智慧後端服務，實作多租戶階層式存取控制，並整合 WrenAI（AI SQL 生成）、BigQuery、Tableau、Google Cloud Storage 等外部服務。

---

## 目錄

- [系統架構](#系統架構)
- [組織層級與權限設計](#組織層級與權限設計)
- [資料庫 ER 圖](#資料庫-er-圖)
- [專案結構](#專案結構)
- [API 端點總覽](#api-端點總覽)
- [認證流程](#認證流程)
- [外部服務整合](#外部服務整合)
- [快速啟動](#快速啟動)
- [環境變數說明](#環境變數說明)
- [資料庫 Migration](#資料庫-migration)
- [部署](#部署)
- [開發慣例](#開發慣例)

---

## 系統架構

### 分層架構

```
┌─────────────────────────────────────────────────┐
│                  HTTP Client                     │
└───────────────────┬─────────────────────────────┘
                    │ Bearer JWT
┌───────────────────▼─────────────────────────────┐
│              Routers (app/routers/)              │
│  @router_try()  ←  DomainException → HTTPException │
└───────────────────┬─────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────┐
│             Services (app/services/)             │
│  Permission Guard → Domain Logic → @db_tx        │
└──────────┬────────────────────────┬─────────────┘
           │                        │
┌──────────▼──────────┐  ┌──────────▼──────────────┐
│ Repositories        │  │ Domain (app/domain/)     │
│ (app/repositories/) │  │ - access_tree/           │
│ Raw SQL / ORM CRUD  │  │ - check_exist/           │
└──────────┬──────────┘  │ - date/                  │
           │             │ - exception/             │
┌──────────▼──────────┐  └──────────────────────────┘
│ Entities            │
│ (app/entities/)     │
│ SQLAlchemy ORM      │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│   PostgreSQL DB      │
└─────────────────────┘
```

### 外部服務呼叫架構

```
Services
  └── BaseHTTPService (@external_api)
        ├── WrenAiService   → WrenAI API (WREN_API_URL)
        ├── NotifyService   → Notify API (NOTIFY_API_URL)
        ├── InsightService  → WrenAI / BigQuery
        └── AuthService     → Google OAuth2 API
```

---

## 組織層級與權限設計

### 三層租戶層級

```
Super（全局管理員）
  └── SI（Service Instance，系統整合商）
        └── Organization（組織 / 客戶）
              └── Role（角色）
                    └── Permission（權限）
```

### user_roles 關聯表（核心）

| scope_type | scope_id  | role_id  | 說明                                |
| ---------- | --------- | -------- | ----------------------------------- |
| `super`    | 0（固定） | NULL     | 全局管理員，bypass 所有權限檢查     |
| `si`       | si.id     | NULL     | 可管理該 SI 下所有組織              |
| `org`      | org.id    | roles.id | Org 層級，需搭配 Role 與 Permission |

### 權限檢查流程

```
verify_user_permission(db, user, PermissionCheckParams(si_id, org_id, perm))
  │
  ├─ 1. 查 org 是否存在（若帶 org_id）
  ├─ 2. user_repository.check_user_has_permission_fast()
  │       精確 SQL 查詢（效能 1.4x～3.3x vs 全樹建構）
  │       ├─ Super → 直接通過
  │       ├─ SI level → 確認 si_id 匹配
  │       └─ Org level → 確認 org_id + role.permissions 含 perm key
  └─ 3. 不通過 → DomainException(403)
```

**Permission key 命名慣例：**

- `"business.chatbot"` — 功能模組點分隔
- `"report.view"` — 資源.動作
- `"pass"` — 只驗證存取層級，跳過 permission key 比對

---

## 資料庫 ER 圖

```
users
  id, name, email, picture
  │
  ├──[user_roles]────────────────────────────────┐
  │   user_id, scope_type, scope_id, role_id     │
  │                                               │
  └──[user_report_group_set_access]               │
       user_id, report_group_set_id               │
                                                  ▼
si                                            roles
  id, name, logo, description, disabled         id, organization_id, name
  │                                             │
  ├──[si_permissions]                           ├──[role_permissions]
  │   si_id, permission_id                      │   role_id, permission_id
  │                                             │
  └──▶ organizations                           └──▶ permissions
         id, si_id, name, logo                        id, name, key, type
         table_location, type
         contract_start, contract_end           (key 範例: "business.chatbot",
         disabled                                      "report.view")
         │
         ├──[org_permissions]
         │   org_id, permission_id
         │
         ├──[org_business_modules]
         │   org_id, business_modules_id
         │
         ├──▶ roles
         │
         ├──▶ report_group_sets
         │       id, org_id, name
         │       └──▶ report_groups
         │               id, set_id, name, logo, order
         │               └──▶ reports
         │                       id, group_id, name, looker_url, order
         │
         ├──▶ alert_schedules
         │       id, org_id, ...
         │
         └──▶ chatbots（WrenAI）
                 id, org_id, name, wren_key, wren_project_id, wren_models(JSONB)
                 └──▶ threads
                         id(UUID), wren_thread_id, org_id, user_id, chatbot_id, title
                         └──▶ messages
                                 id(UUID), thread_id, role, content_type, status
                                 └──▶ artifacts
                                         id(UUID), thread_id, message_id, type, data(JSONB)

business_modules
  id, key, name, description
  （全局系統模組目錄，透過 org_business_modules 關聯至 org）

chatbot_csv
  id, org_id, chatbot_id, filename, gcs_url, type
  （上傳供 WrenAI 使用的 CSV 資料檔）
```

---

## 專案結構

```
adnex-bi-be/
├── app/
│   ├── main.py                    # FastAPI 入口，CORS、Router 註冊
│   ├── database.py                # DB 連線，get_db()
│   │
│   ├── entities/                  # SQLAlchemy ORM 模型
│   │   ├── __init__.py            # ← 新 entity 必須在這裡 import
│   │   ├── user_entity.py
│   │   ├── si_entity.py
│   │   ├── organization_entity.py
│   │   ├── role_entity.py
│   │   ├── permission_entity.py
│   │   ├── business_module_entity.py
│   │   ├── report_group_set_entity.py
│   │   ├── report_group_entity.py
│   │   ├── report_entity.py
│   │   ├── alert_schedule_entity.py
│   │   ├── chatbot_entity.py
│   │   ├── thread_entity.py
│   │   ├── message_entity.py
│   │   ├── artifact_entity.py
│   │   ├── chatbot_csv_entity.py
│   │   └── associations_entity.py  # 關聯表（user_roles, role_permissions, si/org_permissions, org_business_modules）
│   │
│   ├── dtos/                       # Pydantic request/response schema
│   │   ├── auth_dto.py
│   │   ├── user_dto.py
│   │   ├── si_dto.py
│   │   ├── org_dto.py
│   │   ├── role_dto.py
│   │   ├── permission_dto.py
│   │   ├── business_module_dto.py
│   │   ├── report_dto.py
│   │   ├── insight_dto.py
│   │   ├── notify_dto.py
│   │   ├── tableau_dto.py
│   │   ├── wren_ai_dto.py
│   │   ├── common_dto.py
│   │   ├── date_mixins.py
│   │   └── types.py
│   │
│   ├── repositories/               # 純 DB 操作，無業務邏輯
│   │   ├── user_repository.py      # 含 check_user_has_permission_fast()
│   │   ├── org_repository.py
│   │   ├── si_repository.py
│   │   ├── role_repository.py
│   │   ├── permission_repository.py
│   │   ├── business_module_repository.py
│   │   ├── report_repository.py
│   │   ├── chatbot_repository.py
│   │   ├── thread_repository.py
│   │   ├── message_repository.py
│   │   ├── artifact_repository.py
│   │   └── chatbot_csv_repository.py
│   │
│   ├── services/                   # 業務邏輯層
│   │   ├── auth_service.py         # Google OAuth2
│   │   ├── jwt_service.py          # JWT 簽發 / 驗證 / token_required
│   │   ├── permission_guard_service.py  # verify_user_permission()
│   │   ├── user_service.py
│   │   ├── org_service.py
│   │   ├── si_service.py
│   │   ├── role_service.py
│   │   ├── permission_service.py
│   │   ├── business_module_service.py
│   │   ├── report_service.py
│   │   ├── insight_service.py      # AI 廣告洞察分析
│   │   ├── notify_service.py       # 通知 / Alert
│   │   ├── tableau_service.py      # Tableau JWT
│   │   ├── wren_ai_service.py      # WrenAI + BigQuery
│   │   ├── gcs_uploader.py         # Google Cloud Storage
│   │   ├── google_sheet_service.py
│   │   └── base_http_service.py    # HTTP 基底類別
│   │
│   ├── routers/                    # FastAPI 路由定義
│   │   ├── auth_router.py
│   │   ├── user_router.py
│   │   ├── si_router.py
│   │   ├── org_router.py           # 匯出 org_router + si_router
│   │   ├── role_router.py          # 匯出 role_router + si_router + org_router
│   │   ├── permission_router.py    # 匯出 perm_router + si_router
│   │   ├── business_module_router.py
│   │   ├── report_router.py
│   │   ├── sidebar_router.py
│   │   ├── wren_ai_router.py
│   │   └── notify_router.py
│   │
│   ├── domain/                     # 純業務邏輯，無 FastAPI / SQLAlchemy 依賴
│   │   ├── access_tree/
│   │   │   ├── check_user_access.py   # PermissionCheckParams、can_write_org()
│   │   │   ├── build_si_map.py        # 建立 SI 層級權限樹（用於 /user/info_access）
│   │   │   ├── build_super_tree.py
│   │   │   ├── fill_si_full_access.py
│   │   │   └── merge_org_permissions.py
│   │   ├── check_exist/               # 資源存在性檢查，不存在則拋 DomainException
│   │   ├── csv_validator/             # CSV 欄位驗證
│   │   ├── date/
│   │   │   └── check_contract_expired.py
│   │   ├── org_form/
│   │   │   └── org_form_create_parser.py
│   │   └── exception/
│   │       └── domain_exception.py    # DomainException(msg, type, code)
│   │
│   ├── decorators/
│   │   ├── db_transaction.py    # @db_tx — 自動 commit/rollback
│   │   ├── router_try.py        # @router_try() — 統一錯誤轉換
│   │   └── external_api.py      # @external_api(name) — 外部 API 錯誤統一處理
│   │
│   └── utils/
│       └── validate_sqlstr.py   # SQL 字串安全驗證
│
├── alembic/                     # DB Migration
│   └── versions/
├── alembic.ini
├── Dockerfile
├── requirements.txt
└── .env.example
```

---

## API 端點總覽

Swagger UI：`http://localhost:8000/docs`（所有端點均使用 Bearer JWT）

### Auth

| Method | Path                 | 說明                        |
| ------ | -------------------- | --------------------------- |
| POST   | `/auth/google_login` | Google OAuth2 Code 換取 JWT |

### User

| Method | Path                                                        | 說明                                   |
| ------ | ----------------------------------------------------------- | -------------------------------------- |
| GET    | `/user`                                                     | 取得所有使用者（Super）                |
| POST   | `/user`                                                     | 建立使用者                             |
| GET    | `/user/info_access`                                         | 取得當前使用者完整權限樹（前端顯示用） |
| PUT    | `/si/{si_id}/org/{org_id}/user/{user_id}/report_group_sets` | 設定使用者可存取的 Report Group Set    |

### SI

| Method | Path       | 說明                           |
| ------ | ---------- | ------------------------------ |
| GET    | `/si/list` | 取得當前使用者可存取的 SI 列表 |

### Org

| Method | Path                                | 說明                 |
| ------ | ----------------------------------- | -------------------- |
| GET    | `/si/{si_id}/org/list`              | 取得 SI 下的組織列表 |
| POST   | `/si/{si_id}/org/create`            | 建立組織             |
| PUT    | `/si/{si_id}/org/{org_id}/update`   | 更新組織資訊         |
| PUT    | `/si/{si_id}/org/{org_id}/disabled` | 啟用 / 停用組織      |
| GET    | `/si/{si_id}/org/{org_id}/detail`   | 取得組織詳情         |
| POST   | `/si/{si_id}/org/{org_id}/tableau`  | 取得 Tableau JWT     |
| POST   | `/org/upload_logo`                  | 上傳組織 Logo 至 GCS |

### Role & Permission

| Method | Path                                             | 說明                                        |
| ------ | ------------------------------------------------ | ------------------------------------------- |
| GET    | `/si/{si_id}/org/{org_id}/users`                 | 取得組織成員與角色                          |
| POST   | `/si/{si_id}/org/{org_id}/create_user`           | 指派角色給使用者（建立 org 層級 user_role） |
| PUT    | `/si/{si_id}/org/{org_id}/user/{user_id}/role`   | 更新使用者角色                              |
| DELETE | `/si/{si_id}/orgs/{org_id}/users/{user_id}/role` | 移除使用者角色                              |
| GET    | `/org/{org_id}/roles`                            | 取得組織所有角色                            |
| GET    | `/si/{si_id}/org/{org_id}/role_permissions`      | 取得組織各角色的權限設定                    |
| PUT    | `/si/{si_id}/org/{org_id}/role_permissions`      | 更新角色權限                                |
| GET    | `/permission/org/{org_id}`                       | 取得組織可用的所有 Permission               |

### Business Module

| Method | Path                                                     | 說明                              |
| ------ | -------------------------------------------------------- | --------------------------------- |
| GET    | `/business_module/list`                                  | 取得所有系統業務模組              |
| GET    | `/business_module/{si_id}/org/{org_id}/insight-ads`      | 取得廣告洞察可用清單              |
| POST   | `/business_module/{si_id}/org/{org_id}/insight-analysis` | 送出廣告洞察分析（SSE Streaming） |

### Report

| Method              | Path                                                                      | 說明                  |
| ------------------- | ------------------------------------------------------------------------- | --------------------- |
| GET/POST/PUT/DELETE | `/si/{si_id}/org/{org_id}/report_group_set`                               | Report Group Set CRUD |
| GET/POST/PUT/DELETE | `/si/{si_id}/org/{org_id}/report_group_set/{id}/report_group`             | Report Group CRUD     |
| GET/PUT             | `/si/{si_id}/org/{org_id}/report_group_set/{id}/report_group/{id}/report` | Report 讀取與批次更新 |

### Sidebar

| Method | Path                                                                              | 說明                                               |
| ------ | --------------------------------------------------------------------------------- | -------------------------------------------------- |
| GET    | `/sidebar/si/{si_id}/org/{org_id}`                                                | 取得側邊欄資料（Report Groups + Business Modules） |
| GET    | `/sidebar/si/{si_id}/org/{org_id}/report_group_set/{id}/report_group/{id}/report` | 取得側邊欄 Report 列表                             |

### WrenAI（AI Chatbot）

| Method           | Path                                                                              | 說明                                      |
| ---------------- | --------------------------------------------------------------------------------- | ----------------------------------------- |
| GET              | `/wren_ai/si/{si_id}/org/{org_id}/chatbot`                                        | 取得 Org 的 Chatbot 設定                  |
| GET/PATCH/DELETE | `/wren_ai/si/{si_id}/org/{org_id}/chat/threads`                                   | Thread 列表 / 重新命名 / 刪除             |
| GET              | `/wren_ai/si/{si_id}/org/{org_id}/chat/threads/{id}/messages`                     | 取得 Thread 訊息（分頁）                  |
| GET              | `/wren_ai/si/{si_id}/org/{org_id}/chat/thread/{tid}/message/{mid}/artifact/{aid}` | 取得 Artifact                             |
| POST             | `/wren_ai/ask`                                                                    | 送出問題（SSE Streaming 回傳 SQL + 摘要） |
| POST             | `/wren_ai/generatesql`                                                            | 直接生成 SQL                              |
| POST             | `/wren_ai/runsql`                                                                 | 執行 SQL（BigQuery）                      |
| POST             | `/wren_ai/chart`                                                                  | 生成 Vega Chart                           |
| GET/POST         | `/wren_ai/si/{si_id}/org/{org_id}/upload_csv`                                     | CSV 列表 / 上傳                           |
| POST             | `/wren_ai/si/{si_id}/org/{org_id}/create_wren_ai`                                 | 初始化 WrenAI 專案                        |
| POST             | `/wren_ai/si/{si_id}/org/{org_id}/download_csv_template`                          | 下載 CSV 範本（單檔或 ZIP）               |
| POST             | `/wren_ai/si/{si_id}/org/{org_id}/upsert_model`                                   | 同步 BigQuery schema 至 WrenAI            |
| POST             | `/wren_ai/download_table`                                                         | BigQuery 查詢結果下載（CSV 或 JSON 訊息） |

### Notify（Alert）

| Method | Path                                               | 說明                        |
| ------ | -------------------------------------------------- | --------------------------- |
| GET    | `/notify/si/{si_id}/org/{org_id}/alert`            | 取得 Alert 排程列表（分頁） |
| POST   | `/notify/si/{si_id}/org/{org_id}/alert`            | 建立 Alert 排程             |
| DELETE | `/notify/si/{si_id}/org/{org_id}/alert/{alert_id}` | 刪除 Alert 排程             |

---

## 認證流程

```
Frontend
  │
  ├─ 1. 取得 Google OAuth2 Authorization Code
  │
  ▼
POST /auth/google_login  { code, redirect_uri }
  │
  ├─ 2. 向 Google 換取 access_token
  ├─ 3. 呼叫 Google UserInfo API 取得 email / name / picture
  ├─ 4. 若使用者不存在 → 自動建立
  └─ 5. 簽發 JWT（payload: user_id, email）→ 回傳 { access_token, token_type }

後續所有 API 請求
  Authorization: Bearer <JWT>
  │
  token_required (FastAPI Depends)
  └─ 驗證 JWT → 注入 UserReadDTO
```

---

## 外部服務整合

### WrenAI + BigQuery

- **WrenAI**：AI SQL 生成引擎，透過 `WREN_API_URL` 連接。每個 Org 有獨立的 `wren_project_id` 與 `wren_key`（存於 `chatbots` 表）。
- **BigQuery**：直接執行 SQL 查詢，使用 `BQ_SERVICE_ACCOUNT_KEY`（Base64 編碼的 Service Account JSON）。
- Chatbot 對話歷史（Thread / Message / Artifact）儲存於本地 PostgreSQL。

### Google Cloud Storage (GCS)

- 用於儲存組織/SI Logo、上傳的 CSV 資料檔。
- 設定：`BUCKET_NAME` + `GOOGLE_APPLICATION_CREDENTIALS`。

### Tableau

- 為已設定的 SI 發行 Tableau Connected App JWT。
- 支援多個 SI 的 Tableau 設定（`TABLEAU_BU1_*` / `TABLEAU_BU2_*` 環境變數）。

### Insight API（廣告洞察分析）

- 獨立的 Cloud Run 服務，用於廣告數據 AI 分析。
- URL：`https://insight-api-809785955233.asia-east1.run.app`（由 `CLOUD_RUN_AUDIENCE` 設定）
- 身份驗證：使用 Google Application Default Credentials（ADC）產生 ID Token，帶入 `Authorization: Bearer <token>` header。
- 提供兩支 API：
  - `GET /get_info` — 查詢 BigQuery 可用廣告資訊（`table_location`, `type`）
  - `POST /report` — 送出分析請求，以 NDJSON Streaming 回傳進度與結果
- 超時設定：`TIMEOUT_SECONDS`（一般請求）、`STREAM_TIMEOUT_SECONDS`（串流請求，預設 1800 秒）

### Notify Service

- 透過 `NOTIFY_API_URL` 連接，管理 Alert 排程。

### Google OAuth2

- 使用 `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` 交換 Authorization Code。

---

## 快速啟動

```bash
# 1. Clone
git clone <repo_url>
cd adnex-bi-be

# 2. 建立 Python 虛擬環境
python -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows

# 3. 安裝相依套件
pip install -r requirements.txt

# 4. 複製並填寫環境變數
cp .env.example .env
# 編輯 .env，填入各項設定（見下方環境變數說明）

# 5. 執行 DB Migration
alembic upgrade head

# 6. 啟動開發伺服器
uvicorn app.main:app --reload
```

開啟 `http://localhost:8000/docs` 進入 Swagger UI。

---

## 環境變數說明

| 變數名稱                                 | 必填 | 說明                                                        |
| ---------------------------------------- | ---- | ----------------------------------------------------------- |
| `DATABASE_URL`                           | ✅   | PostgreSQL 連線字串 `postgresql://user:pw@host:5432/dbname` |
| `SECRET_KEY`                             | ✅   | JWT 簽章金鑰                                                |
| `ALGORITHM`                              |      | JWT 演算法（預設 `HS256`）                                  |
| `ACCESS_TOKEN_EXPIRE_MINUTES`            |      | JWT 有效期（預設 `30` 分鐘）                                |
| `GOOGLE_CLIENT_ID`                       | ✅   | Google OAuth2 Client ID                                     |
| `GOOGLE_CLIENT_SECRET`                   | ✅   | Google OAuth2 Client Secret                                 |
| `BQ_SERVICE_ACCOUNT_KEY`                 | ✅   | Base64 編碼的 BigQuery Service Account JSON                 |
| `WREN_API_URL`                           | ✅   | WrenAI API 基底 URL                                         |
| `WREN_TOKEN`                             |      | WrenAI Cloud Token（cloud.getwren.ai）                      |
| `WREN_ORG_ID`                            |      | WrenAI Cloud Organization ID                                |
| `NOTIFY_API_URL`                         |      | 通知服務 API URL                                            |
| `BUCKET_NAME`                            |      | GCS Bucket 名稱                                             |
| `GOOGLE_APPLICATION_CREDENTIALS`         |      | GCS Service Account 憑證路徑                                |
| `APP_ENV`                                |      | 執行環境 (`development` / `production`)                     |
| `CLOUD_RUN_AUDIENCE`                     |      | Cloud Run 服務 Audience URL                                 |
| `TIMEOUT_SECONDS`                        |      | 外部 API 請求超時秒數                                       |
| `TABLEAU_BU1_SI_ID`                      |      | Tableau BU1 對應的 SI ID                                    |
| `TABLEAU_BU1_SUB`                        |      | Tableau BU1 Connected App Subject                           |
| `TABLEAU_BU1_CONNECTED_APP_CLIENT_ID`    |      | Tableau BU1 Client ID                                       |
| `TABLEAU_BU1_CONNECTED_APP_SECRET_ID`    |      | Tableau BU1 Secret ID                                       |
| `TABLEAU_BU1_CONNECTED_APP_SECRET_VALUE` |      | Tableau BU1 Secret Value                                    |
| `TABLEAU_BU2_*`                          |      | 同上，第二組 Tableau 設定                                   |

---

## 資料庫 Migration

```bash
# 自動產生 Migration（比對 entity 與 DB 差異）
alembic revision --autogenerate -m "描述變更內容"

# 套用所有未執行的 Migration
alembic upgrade head

# 回滾一個版本
alembic downgrade -1

# 查看目前版本
alembic current
```

> **注意**：新增 Entity 後，必須先在 `app/entities/__init__.py` 中 import，Alembic 才能偵測到變更。

---

## 部署

### Docker

```bash
docker build -t adnex-bi-be .
docker run -p 8080:8080 --env-file .env adnex-bi-be
```

服務啟動於 `PORT` 環境變數指定的 port（預設 `8080`）。

### Google Cloud Run

部署前確保：

1. 所有環境變數已設定於 Cloud Run Service 的 Secrets / Environment Variables
2. `GOOGLE_APPLICATION_CREDENTIALS` 使用 Workload Identity 或掛載 Secret Volume
3. CORS `allow_origins` 已包含前端的 Cloud Run URL（見 `app/main.py`）

---

## 開發慣例

### 新增端點（標準流程）

```
1. app/entities/         → 新增或更新 Entity
2. app/entities/__init__.py → import 新 Entity
3. alembic revision ... → 產生 Migration
4. app/dtos/             → 新增 Request / Response DTO
5. app/repositories/     → 新增 DB 操作
6. app/services/         → 新增業務邏輯
7. app/routers/          → 新增路由（加上 @router_try()）
8. app/main.py           → 在 Routers 列表中註冊
```

### 需要權限保護的端點範例

```python
from app.services.jwt_service import token_required
from app.services.permission_guard_service import verify_user_permission
from app.domain.access_tree.check_user_access import PermissionCheckParams

@router.post("/si/{si_id}/org/{org_id}/resource")
@router_try()
def create_resource(
    si_id: int,
    org_id: int,
    body: ResourceCreateDTO,
    user: UserReadDTO = Depends(token_required),
    db: Session = Depends(get_db),
):
    verify_user_permission(db, user, PermissionCheckParams(si_id=si_id, org_id=org_id, perm="resource.write"))
    # ... 業務邏輯
```

### 新增外部 HTTP 服務

```python
from app.decorators.external_api import external_api
from app.services.base_http_service import BaseHTTPService

@external_api("my_service")
class MyService(BaseHTTPService):
    def __init__(self):
        super().__init__(
            base_url_env="MY_API_URL",
            default_base_url="http://localhost:9000",
            timeout=30
        )

    async def call_endpoint(self, payload: dict):
        return await self.post("path/to/endpoint", payload)
```

### 錯誤處理

- 業務層拋出 `DomainException(msg, type, code)` → `@router_try()` 自動轉換為 HTTPException
- 所有 API 錯誤回應格式：`{"type": "error_type", "msg": "錯誤訊息"}`
- JWT 錯誤類型：`token_missing` / `token_expired` / `token_invalid`

### 注意事項

- 所有路由 handler 必須加上 `@router_try()` decorator
- 一個 router 檔案可匯出多個 `APIRouter`（如 `org_router.py` 匯出 `org_router` 和 `si_router`），全部需在 `main.py` 的 `Routers` 列表中個別註冊
- DB 交易使用 `@db_tx` decorator，自動處理 commit / rollback
- 效能考量：單一資源的權限檢查使用 `verify_user_permission()`（精確 SQL），完整權限樹僅在 `GET /user/info_access` 時建構
- 程式碼注解使用中文或英文
