# LearnPilot AI

面向“中国软件杯”A3 赛题的个性化学习多智能体系统。项目将学习诊断、动态画像、资源推荐、学习路径规划、RAG 内容生成、智能辅导和学习效果反馈串成可解释的闭环。

## 核心能力

| 能力 | 实现 |
| --- | --- |
| 学习诊断 | 根据题目难度、区分度、作答结果、用时、提示和置信度估计知识点掌握度 |
| 动态画像 | 融合诊断、行为、偏好和历史状态，输出能力、节奏、风险和认知偏好 |
| 个性化推荐 | LightGBM 排序结合薄弱度、难度适配、行为反馈、资源质量和知识图谱特征 |
| 学习路径 | 按先修关系生成阶段化路径、学习时长、检查点和补救策略 |
| 多形态 RAG 生成 | 检索课程证据，生成讲义、网页幻灯片、SVG/Mermaid 思维导图、题库、视频分镜、实验和项目任务书 |
| 智能辅导 | 基于学生画像、课程证据和多轮上下文进行苏格拉底式引导 |
| 反馈闭环 | 学习行为和测评结果回写画像，重新规划推荐与学习路径 |
| 内容治理 | 提示注入拦截、密钥与个人信息脱敏、引用白名单、生成审核和失败自动修复 |
| 可验证性 | 防泄漏训练、分学生验证、离线指标、接口契约测试和双服务联调 |

## 系统组成

```text
Frontend / Client
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
├─ docs/                    仓库级架构文档
├─ Dockerfile               backend / ml 多阶段镜像
├─ docker-compose.yml       完整本地服务栈
├─ environment.yml          唯一 Conda 环境定义
├─ render.yaml              Render 双服务 Blueprint
└─ .env.example             唯一环境变量模板
```

## 快速开始

在仓库根目录执行：

```powershell
conda env create -f environment.yml
conda activate learnpilot-ml
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

服务地址：

- ML API：`http://127.0.0.1:8000/docs`
- Backend API：`http://127.0.0.1:8001/docs`

真实 Qwen 联调需要在 `.env` 中设置 `DASHSCOPE_API_KEY`，然后执行：

```powershell
learnpilot-ml-qwen-check
```

未设置密钥时，`LEARNPILOT_LLM_MODE=template` 提供确定性的离线生成，便于测试与演示。

## 测试

```powershell
python -m unittest discover -s ml/tests -v
python -m unittest discover -s backend/tests -v
```

测试覆盖 ML 学习闭环、训练防泄漏、RAG 引用、辅导、后端业务、ML 适配和前后端接口契约。

## 容器部署

仓库只维护一个多阶段 Dockerfile。后端 API 与 RQ Worker 复用同一后端镜像。

```powershell
docker-compose build
docker-compose up
```

完整服务栈包括 `backend`、`ml-service`、`worker`、`mysql` 和 `redis`。

Render 部署使用根目录 [render.yaml](render.yaml)。Blueprint 会创建 ML 和后端两个 Web Service，并通过私有网络连接。

## 文档

- [工程架构](docs/architecture.md)
- [后端说明](backend/README.md)
- [后端 API 参考](backend/docs/api-reference.md)
- [ML 服务说明](ml/README.md)
- [ML 设计](ml/docs/design.md)
- [赛题要求追踪矩阵](ml/docs/requirements-traceability.md)
