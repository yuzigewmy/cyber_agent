# Cyber Agent Guarded

面向授权攻防演练、蓝队应急响应、漏洞治理和安全运营的网络安全攻防智库 Agent 平台。当前版本采用 **前后端分离架构**：后端为 FastAPI + LangChain/LangGraph 预留编排 + RAG + 策略安全门；前端为 Vue 3 + Vite + Pinia + Vue Router 的简洁控制台。

> 安全边界：本项目只面向企业自有资产和授权演练。红队模式仅输出授权范围内的高层攻击面建模、验证计划、检测点和修复建议，不输出 exploit payload、0day 武器化、绕过、持久化、凭据窃取或其他可直接滥用的攻击执行内容。

## 1. 核心能力

- 登录认证：MVP 内置 HMAC Bearer Token，生产建议替换为企业 OIDC / SAML / LDAP / 零信任网关。
- Vue 前端：登录页、仪表盘、功能入口、大模型聊天页面、历史会话列表。
- 聊天持久化：默认 SQLite，本地零配置；生产建议 PostgreSQL。
- 防守模式：攻击流量研判、应急响应动作、溯源分析、漏洞修复建议。
- 威胁情报模式：组件版本、CVE/KEV/EPSS、业务暴露面和修复优先级分析。
- 授权红队模式：授权范围校验、高层路径建模、人工审批提示、蓝队检测点。
- RAG：基于内部架构、应急流程、红队规则等知识库进行检索增强生成。
- 策略安全门：对越权、未授权红队、敏感攻击能力请求进行拦截。

## 2. 技术栈

### 后端

- Python 3.11+
- FastAPI
- Pydantic v2
- SQLAlchemy 2.x
- SQLite / PostgreSQL
- LangChain / LangGraph 预留
- ChromaDB 预留向量库

### 前端

- Vue 3
- Vite
- Pinia
- Vue Router
- Axios
- 原生 CSS，Apple / ChatGPT 风格的简洁玻璃态视觉

## 3. 工程目录

```text
cyber_agent_guarded
├── app/
│   └── main.py                         # FastAPI 入口
├── src/cyber_agent_guarded/
│   ├── agent/graph.py                  # Agent 编排入口
│   ├── auth.py                         # MVP 登录与 Bearer Token
│   ├── config.py                       # 配置加载
│   ├── policies.py                     # 策略安全门
│   ├── rag/                            # RAG 文档加载与检索
│   ├── storage/                        # SQLAlchemy 数据库模型与仓储
│   └── tools/                          # 流量研判、Runbook、攻击路径建模等工具
├── frontend-vue/
│   ├── src/
│   │   ├── views/LoginView.vue         # 登录页
│   │   ├── views/FeatureView.vue       # 仪表盘/功能入口
│   │   ├── views/ChatView.vue          # 大模型聊天页面
│   │   ├── stores/                     # Pinia 状态
│   │   ├── router/                     # Vue Router
│   │   └── assets/main.css             # 全局样式
│   ├── package.json
│   ├── Dockerfile
│   └── nginx.conf
├── data/knowledge/                     # 示例知识库
├── config/config.example.yaml          # Agent/RAG/Safety/Auth 配置
├── docker-compose.yml
├── Dockerfile
└── tests/
```

## 4. 本地开发启动

### 4.1 启动后端

```bash
cd cyber_agent_guarded
python -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'

export CYBER_AGENT_DEMO_PASSWORD='ChangeMe123!'
export CYBER_AGENT_AUTH_SECRET='please-change-this-secret'
export CYBER_AGENT_DATABASE_URL='sqlite:///data/runtime/cyber_agent.db'
export CYBER_AGENT_CORS_ORIGINS='http://localhost:5173,http://127.0.0.1:5173'

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端健康检查：

```bash
curl http://127.0.0.1:8000/health
```

### 4.2 启动前端

```bash
cd frontend-vue
npm install
cp .env.example .env
npm run dev
```

浏览器访问：

```text
http://127.0.0.1:5173/login
```

默认开发账号：

```text
username: security-admin
password: ChangeMe123!
```

## 5. 数据库配置

### 5.1 默认 SQLite

默认配置：

```bash
export CYBER_AGENT_DATABASE_URL='sqlite:///data/runtime/cyber_agent.db'
```

启动后端时会自动创建数据表：

- `chat_sessions`
- `chat_messages`

### 5.2 生产 PostgreSQL

推荐生产使用 PostgreSQL：

```bash
export CYBER_AGENT_DATABASE_URL='postgresql+psycopg://cyber_agent:strong_password@postgres:5432/cyber_agent'
```

生产建议：

- 独立 PostgreSQL 实例或托管数据库。
- 开启定期备份和 PITR。
- 使用 Alembic 管理迁移。
- 对聊天内容、RAG 引用、审计日志配置保留周期。
- 为租户字段、用户字段、会话更新时间建立索引。

当前 MVP 使用 `Base.metadata.create_all()` 自动建表，便于原型和内网演示。正式生产建议替换为 Alembic migration。

## 6. Docker Compose 启动

```bash
cd cyber_agent_guarded
cp .env.example .env
# 修改 .env 中的 CYBER_AGENT_AUTH_SECRET 和 CYBER_AGENT_DEMO_PASSWORD
docker compose up --build
```

访问：

```text
前端：http://127.0.0.1:8080
后端：http://127.0.0.1:8000
```

Docker Compose 默认使用 SQLite 并将 `./data` 挂载到后端容器 `/app/data`，聊天数据会保存在：

```text
data/runtime/cyber_agent.db
```

## 7. API 示例

### 7.1 登录

```bash
curl -s http://127.0.0.1:8000/v1/auth/login \
  -H 'content-type: application/json' \
  -d '{"username":"security-admin","password":"ChangeMe123!"}'
```

### 7.2 调用聊天接口

```bash
TOKEN='<替换为登录返回的 access_token>'

curl -s http://127.0.0.1:8000/v1/chat \
  -H "authorization: Bearer ${TOKEN}" \
  -H 'content-type: application/json' \
  -d '{
    "mode":"defense",
    "question":"请研判这些可疑流量，并给出处置建议。",
    "assets":["api-gateway","user-service"],
    "evidence":["GET /.env 404", "GET /login?user=admin or 1=1"]
  }'
```

### 7.3 查询会话列表

```bash
curl -s http://127.0.0.1:8000/v1/chat/sessions \
  -H "authorization: Bearer ${TOKEN}"
```

### 7.4 查询会话消息

```bash
curl -s http://127.0.0.1:8000/v1/chat/sessions/<session_id>/messages \
  -H "authorization: Bearer ${TOKEN}"
```

## 8. 需要重点修改的配置

### 8.1 后端环境变量

```bash
CYBER_AGENT_CONFIG_PATH=config/config.example.yaml
CYBER_AGENT_DATABASE_URL=sqlite:///data/runtime/cyber_agent.db
CYBER_AGENT_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
CYBER_AGENT_DEMO_PASSWORD=ChangeMe123!
CYBER_AGENT_AUTH_SECRET=change-me-to-a-long-random-secret
NVD_API_KEY=<可选>
```

### 8.2 前端环境变量

`frontend-vue/.env`：

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000
```

如果走 Vite dev proxy，也可以把请求发到同源 `/v1`，但生产建议显式配置 API 网关地址。

### 8.3 Agent 配置

`config/config.example.yaml`：

```yaml
agent:
  require_scope_for_redteam: true
  require_human_approval_for_intrusive_actions: true
  max_retrieved_docs: 6

safety:
  allow_exploit_code: false
  allow_payload_generation: false
  allow_credential_theft: false
  allow_evasion_or_persistence: false
  restrict_zero_day_to_defensive_triage: true
```

红队能力必须保持授权门禁开启。

## 9. 前端页面说明

### 登录页

- 居中卡片式布局。
- 极简视觉、柔和渐变、玻璃态阴影。
- 默认展示开发账号提示。

### 仪表盘

- 左侧功能导航。
- 顶部状态栏。
- 中部功能卡片。
- 功能包括：防守策略、攻击流量研判、应急响应、溯源定位、漏洞发现与修复、授权红队规划、RAG 知识库检索。

### 聊天页

- 左侧历史会话列表。
- 中间聊天流。
- 支持模式切换：防守方、威胁情报、授权红队。
- 支持资产范围和证据输入。
- 红队模式显示授权审批字段。
- 聊天数据写入数据库。

## 10. 测试

```bash
pytest -q
```

当前通过：

```text
10 passed
```

前端构建测试：

```bash
cd frontend-vue
npm install
npm run build
```

## 11. 生产化建议

1. 认证替换：接入 OIDC / SAML / LDAP / 企业零信任网关。
2. 数据库：SQLite 切换到 PostgreSQL，并引入 Alembic。
3. 前端部署：Vue 构建产物部署到 Nginx / CDN / 对象存储，API 经网关转发。
4. RAG：接入 Qdrant / OpenSearch / Milvus，增加混合检索和 rerank。
5. 审计：所有登录、查询、聊天、策略拦截、人审动作写入审计日志。
6. 权限：按 SOC Analyst、Incident Commander、Red Team Lead、Knowledge Admin 等角色细粒度授权。
7. 模型：接入企业模型网关，统一限流、脱敏、提示词审计和输出安全检查。
8. 可观测：接入 OpenTelemetry，记录 API latency、RAG recall、LLM latency、拦截率和错误率。

## 12. 常见问题

### 登录成功但聊天失败

检查：

- 后端是否启动在 `8000`。
- `frontend-vue/.env` 中 `VITE_API_BASE_URL` 是否正确。
- `CYBER_AGENT_CORS_ORIGINS` 是否包含前端地址。
- 浏览器 localStorage 中 token 是否过期。

### 数据库没有生成

检查：

```bash
ls -lah data/runtime
```

后端启动时会自动建表。如果目录无权限，修改 `CYBER_AGENT_DATA_DIR` 或 `CYBER_AGENT_DATABASE_URL`。

### 红队模式被拦截

红队模式需要授权字段：

```json
{
  "scope": {
    "approved": true,
    "approver": "ciso",
    "ticket_id": "RT-2026-001",
    "rules_of_engagement": "Authorized internal exercise."
  }
}
```

即使授权通过，系统仍不会输出 payload、武器化利用细节、绕过、持久化或凭据窃取步骤。
