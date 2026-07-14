# LearnPilot Backend

LearnPilot 的主业务服务，负责用户与权限、课程资源、题库、学生画像持久化、学习路径、辅导记录、多智能体编排，以及与 ML 服务的 HTTP 集成。

## 结构

```text
backend/
├─ src/backend/app/
│  ├─ api/                 HTTP 路由与统一路由装配
│  ├─ services/            学习闭环和资源导入用例
│  ├─ agents/              后端智能体编排单元
│  ├─ adapters/            ML 与大模型提供方适配器（星火默认、Qwen 可选）
│  ├─ models/              SQLAlchemy 实体
│  ├─ schemas/             HTTP DTO
│  └─ core/                配置、数据库和安全
├─ data/knowledge_base/    LearnPilot 课程目录与结构化知识种子
├─ data/course_materials/  固定版本、带许可证与哈希的 37 份课程文档
├─ migrations/mysql/       MySQL 初始化迁移
├─ scripts/                数据库与知识库运维命令
├─ tests/                  业务、集成和接口契约测试
└─ pyproject.toml          包元数据与依赖声明
```

## 安装与启动

推荐使用仓库根目录统一环境：

```powershell
conda env create -f environment.yml
conda activate learnpilot-ai
Copy-Item .env.example .env
learnpilot-backend
```

也可以只安装后端：

```powershell
pip install -e backend
learnpilot-backend
```

默认端口为 `8001`。Swagger：`http://127.0.0.1:8001/docs`。

## 数据库

零配置本地运行使用 SQLite：

```powershell
$env:DATABASE_MODE="sqlite"
python backend/scripts/init_sqlite_demo.py
```

生产或 Docker Compose 使用 MySQL；建表和种子数据位于 `backend/migrations/mysql/`。PostgreSQL 初始化入口为 `backend/scripts/init_postgres.py`。`mysql_to_postgres.py` 用于受控迁移，执行前必须显式设置 `DATABASE_URL`，仓库不保存数据库口令或数据库导出。

公开注册只创建学生账号。管理员账号使用 `scripts/reset_admin_password.py` 创建或重置，密码通过 `LEARNPILOT_ADMIN_PASSWORD` 或 `--password` 提供；生产环境不要把密码写入命令历史。

## ML 集成

```text
USE_ML_SERVICE=true
ML_SERVICE_URL=http://127.0.0.1:8000
ML_SERVICE_TIMEOUT_SECONDS=90
```

当服务发现只提供不含协议的 `host:port` 时，客户端会自动补全 `http://`。

## 测试

```powershell
python -m unittest discover -s backend/tests -v
```

`test_api_contract.py` 锁定前端使用的后端路径和后端调用的 ML 路径，结构调整不得改变这些接口。

接口详情见 [docs/api-reference.md](docs/api-reference.md)。
