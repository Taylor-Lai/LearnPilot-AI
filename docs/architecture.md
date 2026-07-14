# LearnPilot AI 工程架构

## 服务边界

LearnPilot 由一个 Web 前端和两个可独立安装、部署的 Python 服务组成：

- Web 是 Vue 3 单页应用，只调用 Backend，不直接暴露 ML Service。
- Backend 是唯一面向前端的业务入口，负责身份、课程、资源、记录、持久化和业务 Agent 编排。
- ML Service 提供无状态算法能力，负责诊断、画像、排序、路径、RAG 生成、辅导和评估。
- Backend 通过稳定 HTTP 契约调用 ML Service；ML Service 不访问后端数据库。

```text
Browser / Vue Web
  │
  ▼
Backend API ──────► MySQL / SQLite
  │                       │
  ├──────────────► Redis / RQ Worker
  │
  └── HTTP ──────► ML Service ──────► Spark / optional Qwen / template fallback
```

## 仓库结构

```text
LearnPilot-AI/
├─ backend/                     主后端可安装包
│  ├─ src/backend/app/
│  │  ├─ api/                   路由与传输层
│  │  ├─ services/              业务用例
│  │  ├─ agents/                业务 Agent
│  │  ├─ adapters/              外部服务适配器
│  │  ├─ models/                持久化实体
│  │  ├─ schemas/               DTO
│  │  └─ core/                  配置、安全和数据库
│  ├─ data/knowledge_base/      LearnPilot 课程目录与结构化知识种子
│  ├─ data/course_materials/    可离线校验并随服务分发的精选课程文档
│  ├─ migrations/mysql/         数据库初始化迁移
│  └─ tests/
├─ web/                         Vue 3 前端
│  ├─ src/api/                  Backend 接口适配
│  ├─ src/components/           通用组件
│  ├─ src/views/                学生端与管理端页面
│  └─ src/router/               路由与权限守卫
├─ ml/                          ML 可安装包
│  ├─ src/ml_service/
│  │  ├─ api/                   FastAPI 与请求契约
│  │  ├─ application/           学习闭环编排与多形态资源构建
│  │  ├─ domain/                领域模型与纯逻辑
│  │  ├─ infrastructure/        排序、检索、内容安全和 LLM
│  │  ├─ datasets/              统一数据契约、OULAD 预处理、内置与合成数据
│  │  ├─ training/              训练工作流
│  │  └─ evaluation/            离线评估
│  ├─ data/benchmarks/          小型评估基准
│  ├─ data/processed/           统一训练数据（不进入 Git）
│  └─ tests/
├─ data/
│  ├─ sources.yaml              外部来源、许可证、版本与导入策略
│  └─ external/                 完整外部数据与课程原始材料（不进入 Git）
├─ tools/                       仓库级来源校验与同步工具
├─ docs/                        仓库级文档
├─ Dockerfile                   多阶段镜像
├─ docker-compose.yml           本地完整服务栈
├─ environment.yml              锁定的项目环境
└─ .env.example                 环境变量模板
```

## ML 依赖规则

```text
api ─────► application ─────► domain
               │
               └────────────► infrastructure

datasets / training / evaluation
               └────────────► application + domain + infrastructure
```

- `domain` 不依赖 FastAPI、文件系统或外部网络。
- `application` 只编排用例，不硬编码项目路径。
- `infrastructure` 封装 LightGBM、检索与外部 LLM。
- `api.schemas` 独占 Pydantic 请求验证，避免传输模型污染领域模型。
- `config.py` 是 ML 路径和环境配置的唯一入口。

## 配置来源

| 文件 | 职责 |
| --- | --- |
| `.env.example` | 所有服务的环境变量模板 |
| `environment.yml` | 本地可复现 Python 环境和 editable 包安装 |
| `backend/pyproject.toml` | 后端运行依赖与启动命令 |
| `ml/pyproject.toml` | ML 运行依赖与训练/服务命令 |
| `docker-compose.yml` | MySQL、Redis、ML、Backend、Worker 编排 |
| `web/.env.example` | Vite 构建地址与本地代理配置 |

不再维护重复 requirements 或多个 Dockerfile。根环境模板服务于 Python 服务；`web/.env.example` 仅包含 Vite 构建变量。

## 生成物策略

以下目录完全由命令生成，不提交到 Git：

```text
ml/data/generated/
ml/artifacts/
ml/reports/
```

任何干净检出都能依次执行 `learnpilot-ml-generate`、`learnpilot-ml-train`、`learnpilot-ml-evaluate` 重建这些内容。

`ml/models/ranker/` 是例外：这里只保存经过验证的只读部署模型及其元数据。当前模型采用 LightGBM 文本格式，镜像构建和服务加载都会验证来源字段、特征版本及 SHA-256；运行时重新训练仍写入被忽略的 `ml/artifacts/`。

## 接口稳定性

`backend/tests/test_api_contract.py` 锁定前端和 Backend-to-ML 的关键路径及方法。内部目录和类可以演进，但既有 HTTP 路径、请求字段、响应字段和以下导入入口保持稳定：

```text
backend.app.main:app
ml_service.api:app
```
