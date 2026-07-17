# LearnPilot AI

LearnPilot AI 是面向中国软件杯 A3 赛题的个性化学习多智能体系统。系统围绕一门完整的人工智能课程，将对话画像、学习诊断、资源推荐、学习路径、RAG 内容生成、智能辅导和效果评估连接成可解释的自适应学习闭环。

## 能力概览

| 能力 | 用户可见结果 |
| --- | --- |
| 对话式画像 | 从自然语言中提取专业、目标、基础、薄弱点、偏好和认知风格等维度，并随学习更新 |
| 多智能体生成 | 生成讲义、PPTX、PDF/DOCX、思维导图、题库、拓展阅读、代码实验、项目任务和微课 |
| 个性化路径 | 基于画像、掌握度和知识图谱生成阶段、顺序、时长与检查点 |
| 智能辅导 | 使用课程证据、对话历史和学生画像进行多轮苏格拉底式辅导 |
| 学习评估 | 完成判分、错题分析、画像更新、路径重排与资源重推荐 |
| 内容治理 | 执行引用约束、提示注入拦截、隐私脱敏、安全审核和失败降级 |

## 系统组成

```text
Browser
  │
  ▼
Vue Web :8080
  │
  ▼
Backend :8001 ─────► MySQL
  │                   Redis / RQ Worker
  │
  └── HTTP ─────────► ML Service :8000
                         │
                         ├─ Spark LLM / iFlytek TTS
                         └─ verified local fallback
```

- `web/`：Vue 3 学生端和管理端，只访问 Backend。
- `backend/`：认证、持久化、业务编排、资源导出、异步任务和视频渲染。
- `ml/`：诊断、画像、排序、路径、RAG、内容生成、辅导、训练与评估。
- `data/`：外部来源登记和本地只读原始输入边界。
- `scripts/`：仓库级数据来源同步与课程包完整性校验。
- `docs/`：跨模块架构、接口、ML 设计和赛题追踪文档。

完整目录和依赖规则见[工程架构](docs/architecture.md)。

## 快速运行

### Docker 全栈

```powershell
Copy-Item .env.example .env
```

在 `.env` 中配置 `MYSQL_ROOT_PASSWORD`、`MYSQL_PASSWORD`、`JWT_SECRET_KEY` 和所需讯飞凭证，然后启动：

```powershell
docker compose up -d --build
docker compose ps
```

打开以下地址：

- Web：<http://127.0.0.1:8080>
- Backend Swagger：<http://127.0.0.1:8001/docs>
- ML Swagger：<http://127.0.0.1:8000/docs>

停止服务但保留数据：

```powershell
docker compose down
```

### 本地开发

```powershell
conda env create -f environment.yml
conda activate learnpilot-ai
Copy-Item .env.example .env
```

在三个终端中分别启动：

```powershell
learnpilot-ml-api
```

```powershell
learnpilot-backend
```

```powershell
cd web
npm ci
npm run dev
```

模块级命令和配置分别见 [Backend](backend/README.md)、[ML](ml/README.md) 和 [Web](web/README.md)。

## 运行模式

| 场景 | 关键配置 | 说明 |
| --- | --- | --- |
| 离线开发与自动化测试 | `LEARNPILOT_LLM_MODE=template` | 不访问外网，不产生模型费用 |
| 赛题真实联调 | `LEARNPILOT_LLM_MODE=auto`、`LEARNPILOT_LLM_PROVIDER=spark` | 使用科大讯飞星火，失败时保留可解释降级 |
| MP4 微课 | `LEARNPILOT_VIDEO_RENDER_ENABLED=true`、讯飞 TTS APPID | 讯飞配音并由 FFmpeg 渲染 720P MP4 |

所有可配置项以 [.env.example](.env.example) 为唯一模板，真实密钥只写入被 Git 忽略的 `.env`。

## 数据与模型

- 内置《人工智能》课程包含结构化课程种子和 37 份固定版本中文课程/实验文档，可离线导入为 RAG 知识库。
- OULAD 仅用于验证高等教育行为建模和推荐排序；其点击量是参与度代理，不代表知识掌握度。
- 正式排序模型保存在 `ml/models/ranker/`，采用可审查的 LightGBM 文本格式并校验 SHA-256。
- 原始数据、运行时训练产物、评估报告和生成视频不会进入 Git。

数据落盘规则与来源同步见[数据边界](data/README.md)，训练数据解释见[ML 数据说明](ml/data/README.md)。

## 质量检查

```powershell
python scripts/build_course_bundle.py verify
python -m pytest ml/tests -q
python -m pytest backend/tests -q
python -m ruff check ml/src ml/tests backend/src backend/tests
cd web
npm run lint
npm run build
```

自动化评估固定使用离线模式，不会因本地存在 API Key 而产生在线调用。

## 文档入口

所有工程文档从[文档中心](docs/README.md)进入：

- [工程架构](docs/architecture.md)
- [API 参考](docs/api-reference.md)
- [ML 服务设计](docs/ml-design.md)
- [赛题要求与验收矩阵](docs/competition-requirements.md)
- [ML 技术追踪矩阵](docs/ml-requirements-traceability.md)

课程材料目录中的 `README.md` 是第三方课程正文，不是散落的工程说明；其目录和文件名用于上游兼容、许可证归属和哈希校验。

## 许可证

自主开发代码采用 [MIT License](LICENSE)。第三方课程、数据集、工具和服务的来源及许可证边界见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
