# LearnPilot AI

面向“中国软件杯”A3 赛题的个性化学习多智能体系统。项目将学习诊断、动态画像、资源推荐、学习路径规划、RAG 内容生成、智能辅导和学习效果反馈串成可解释的闭环。

## 核心能力

| 能力 | 实现 |
| --- | --- |
| 学习诊断 | 根据题目难度、区分度、作答结果、用时、提示和置信度估计知识点掌握度 |
| 动态画像 | 融合诊断、行为、偏好和历史状态，输出能力、节奏、风险和认知偏好 |
| 个性化推荐 | 默认规则基线可离线运行；训练模型存在时使用 LightGBM 排序，结合薄弱度、难度适配、行为反馈、资源质量和知识图谱特征 |
| 学习路径 | 按先修关系生成阶段化路径、学习时长、检查点和补救策略 |
| 多形态 RAG 生成 | 检索课程证据，生成讲义、PPTX、PDF/DOCX、SVG/Mermaid 思维导图、题库、视频分镜、实验和项目任务书 |
| 智能辅导 | 基于学生画像、课程证据和多轮上下文进行苏格拉底式引导 |
| 反馈闭环 | 学习行为和测评结果回写画像，重新规划推荐与学习路径 |
| 全栈管理 | 反馈处理、生成任务审计、用户权限、平台配置和评测历史均持久化 |
| 内容治理 | 提示注入拦截、密钥与个人信息脱敏、引用白名单、生成审核和失败自动修复 |
| 可验证性 | 防泄漏训练、分学生验证、离线指标、接口契约测试和双服务联调 |

## 系统组成

```text
Vue Web :5173 / :8080
        │
        ▼
LearnPilot Backend :8001
  ├─ 用户、课程、题库、资源和学习记录
  ├─ 多智能体业务编排
  └─ 数据持久化与权限控制
        │ HTTP
        ▼
LearnPilot ML :8000
  ├─ 诊断与学生画像
  ├─ 排序推荐与学习路径
  ├─ RAG 内容生成与智能辅导
  └─ 训练、评估与可解释输出
```

详细分层和依赖规则见 [docs/architecture.md](docs/architecture.md)。

## 目录

```text
LearnPilot-AI/
├─ backend/                 主后端 Python 包、数据库脚本和测试
├─ ml/                      ML 服务、训练评估和测试
├─ web/                     Vue 3 学生端与管理端
├─ docs/                    仓库级架构文档
├─ Dockerfile               backend / ml / web 多阶段镜像
├─ docker-compose.yml       完整本地服务栈
├─ environment.yml          唯一 Conda 环境定义
├─ render.yaml              Render 三服务 Blueprint
└─ .env.example             后端与 ML 环境变量模板
```

## 快速开始

在仓库根目录执行：

```powershell
conda env create -f environment.yml
conda activate learnpilot-ai
Copy-Item .env.example .env
```

如果环境已经存在：

```powershell
conda env update -f environment.yml --prune
```

### 生成数据、训练和评估

```powershell
learnpilot-ml-generate
learnpilot-ml-train
learnpilot-ml-evaluate
learnpilot-ml-demo
```

`ml/data/generated/`、`ml/artifacts/` 和 `ml/reports/` 都是可再生输出，不进入 Git。

### 启动服务

终端一：

```powershell
learnpilot-ml-api
```

终端二：

```powershell
learnpilot-backend
```

终端三：

```powershell
cd web
npm ci
npm run dev
```

服务地址：

- ML API：`http://127.0.0.1:8000/docs`
- Backend API：`http://127.0.0.1:8001/docs`
- Web：`http://127.0.0.1:5173`

正式在线生成默认使用科大讯飞星火。在 `.env` 中设置 `SPARK_API_PASSWORD` 后执行：

```powershell
learnpilot-ml-spark-check
```

可选的 Qwen 兼容联调需要将 `LEARNPILOT_LLM_PROVIDER` 设为 `qwen`，配置 `DASHSCOPE_API_KEY`，然后执行：

```powershell
learnpilot-ml-qwen-check
```

未设置密钥时，`LEARNPILOT_LLM_MODE=template` 提供确定性的离线生成，便于测试。Qwen 仅作为可选兼容适配。

## 课程知识库

项目内置一门可复现的完整《人工智能》课程：8 章、64 学时、32 个知识点、16 道基础测评题、8 份章节讲义和 8 份实验任务书。课程清单是 SQLite、MySQL、Docker 和云部署共用的唯一数据源。

```powershell
python backend/scripts/seed_ai_course.py
```

课程播种可重复执行，不会重复创建知识点、资源或题目。

## 正式资源导出

多智能体生成任务完成后，可在资源生成页直接导出 DOCX、PPTX 和 PDF。后端导出接口为 `GET /producer/export/{task_id}?format=docx|pptx|pdf`，并执行与任务结果相同的所有者鉴权。

## 测试

```powershell
python -m unittest discover -s ml/tests -v
python -m unittest discover -s backend/tests -v
cd web
npm run lint
npm run build
```

测试覆盖 ML 学习闭环、训练防泄漏、RAG 引用、辅导、后端业务、ML 适配和前后端接口契约。

## 容器部署

仓库只维护一个多阶段 Dockerfile。后端 API 与 RQ Worker 复用同一后端镜像。

```powershell
docker-compose build
docker-compose up
```

完整服务栈包括 `web`、`backend`、`ml-service`、`worker`、`mysql` 和 `redis`。启动后前端地址为 `http://127.0.0.1:8080`。

Render 部署使用根目录 [render.yaml](render.yaml)。Blueprint 会创建 Web 静态站点、Backend 与 ML 两个 Web Service，Backend 通过私有网络调用 ML。

## 账号与安全

公开注册始终创建普通学生账号，客户端提交的管理员或教师角色不会生效。管理员只能通过受控运维命令创建或重置：

```powershell
$env:DATABASE_URL="postgresql://..."
$env:LEARNPILOT_ADMIN_PASSWORD="使用密码管理器生成的强密码"
python backend/scripts/reset_admin_password.py
```

`.env`、数据库导出、运行数据库、模型产物与前端构建目录均被 Git 忽略。生产环境必须设置独立的 `JWT_SECRET_KEY`，不得使用示例值。

## 文档

- [工程架构](docs/architecture.md)
- [官方赛题要求与验收矩阵](docs/competition-requirements.md)
- [后端说明](backend/README.md)
- [前端说明](web/README.md)
- [后端 API 参考](backend/docs/api-reference.md)
- [ML 服务说明](ml/README.md)
- [ML 设计](ml/docs/design.md)
- [ML 技术追踪矩阵](ml/docs/requirements-traceability.md)
