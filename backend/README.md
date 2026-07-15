# LearnPilot Backend

Backend 是系统唯一面向 Web 的业务入口，负责认证与权限、课程数据、学生画像、学习记录、多智能体业务编排、异步任务、正式文件导出和 MP4 微课渲染。算法能力通过稳定 HTTP 契约调用 ML Service，ML Service 不直接访问业务数据库。

## 代码结构

```text
backend/
├─ src/backend/app/
│  ├─ api/                 HTTP 路由与鉴权
│  ├─ services/            学习闭环和资源用例
│  ├─ agents/              后端业务智能体
│  ├─ adapters/            ML 与大模型适配器
│  ├─ models/              SQLAlchemy 实体
│  ├─ schemas/             请求与响应 DTO
│  └─ core/                配置、数据库和安全
├─ data/knowledge_base/    结构化课程种子
├─ data/course_materials/  固定版本课程文档包
├─ migrations/mysql/       MySQL 初始化迁移
├─ scripts/                数据库和知识库运维工具
├─ tests/                  业务、集成与接口契约测试
└─ pyproject.toml          包和命令定义
```

## 本地启动

优先使用根目录统一环境：

```powershell
conda env create -f environment.yml
conda activate learnpilot-ai
Copy-Item .env.example .env
learnpilot-backend
```

默认地址：<http://127.0.0.1:8001>，Swagger：<http://127.0.0.1:8001/docs>。

只安装本模块时可运行：

```powershell
pip install -e backend
learnpilot-backend
```

## 数据与外部服务

- 本地零配置运行使用 SQLite；Docker Compose 使用 MySQL、Redis 和 RQ Worker。
- `DATABASE_MODE` 和数据库连接信息统一来自根目录 `.env`。
- `USE_ML_SERVICE=true` 时通过 `ML_SERVICE_URL` 调用 ML Service。
- 资源生成任务持久化进度、Agent 轨迹和产物，Worker 失败时保留可重试状态。
- DOCX、PPTX、PDF 与 MP4 下载均执行任务所有者鉴权。

公开注册只能创建学生账号。管理员通过 `scripts/reset_admin_password.py` 在受控环境中创建或重置，生产密码不得进入仓库或命令历史。

## 验证

```powershell
python -m pytest backend/tests -q
python -m ruff check backend/src backend/tests
```

`tests/test_api_contract.py` 锁定前端使用的 Backend 路径和 Backend 调用的 ML 路径。内部重构不得破坏这些接口。

接口字段与联调顺序见[统一 API 参考](../docs/api-reference.md)，服务边界见[工程架构](../docs/architecture.md)。
