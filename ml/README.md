# LearnPilot ML

LearnPilot 的机器学习服务，实现 A3 赛题中的学习诊断、学生画像、资源排序、学习路径、多形态 RAG 内容生成、多轮辅导和学习效果反馈。

## 分层

```text
ml/
├─ src/ml_service/
│  ├─ api/                 FastAPI 应用和请求契约
│  ├─ application/         学习闭环、Agent 编排和多形态资源构建
│  ├─ domain/              领域模型和诊断逻辑
│  ├─ infrastructure/      LightGBM、RAG、内容安全和大模型提供方适配器
│  ├─ datasets/            内置资源、演示和合成数据
│  ├─ training/            防泄漏训练工作流
│  └─ evaluation/          离线评估与报告
├─ data/benchmarks/        小型、可审查的评估基准
├─ docs/                   ML 设计与赛题追踪文档
├─ tests/                  单元、API 和训练测试
└─ pyproject.toml          包元数据、依赖和命令入口
```

生成数据、模型和报告不会提交：

```text
ml/data/generated/
ml/artifacts/
ml/reports/
```

## 工作流

```powershell
conda activate learnpilot-ai
learnpilot-ml-generate
learnpilot-ml-train
learnpilot-ml-evaluate
learnpilot-ml-demo
```

训练流程固定随机种子，按学生划分验证集，并在构造特征时排除目标交互，避免行为标签泄漏。

## 启动 API

```powershell
learnpilot-ml-api
```

默认地址：`http://127.0.0.1:8000/docs`。

关键接口：

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| GET | `/health` | 服务和排序模型状态 |
| POST | `/diagnose` | 聚合知识点分数诊断 |
| POST | `/assessment/diagnose` | 原始题目作答诊断 |
| POST | `/recommend` | 画像、推荐、路径和学习卡闭环 |
| POST | `/path` | 基于知识图谱规划路径 |
| POST | `/generate` | 生成带 RAG 证据、审核轨迹和多形态资源包的学习内容 |
| POST | `/feedback` | 根据学习反馈更新闭环 |
| POST | `/student/update-profile` | 更新学生画像 |
| POST | `/tutor/ask` | 多轮、有据、分层智能辅导 |

## 大模型提供方

离线测试使用：

```text
LEARNPILOT_LLM_MODE=template
```

正式参赛在线能力默认使用科大讯飞星火。在根目录 `.env` 配置 `SPARK_API_PASSWORD` 后执行：

```powershell
learnpilot-ml-spark-check
```

Qwen 仅作为可选兼容提供方；将 `LEARNPILOT_LLM_PROVIDER` 设为 `qwen`，配置 `DASHSCOPE_API_KEY` 后执行：

```powershell
learnpilot-ml-qwen-check
```

生成内容必须引用实际召回的资源切片；引用不合法时会被过滤。每组内容会经过教学完整性、引用、安全、隐私和多形态覆盖审核，不通过时执行确定性修复并复审。

每张学习卡的 `resource_bundle` 提供七种可直接渲染或继续导出的资源：

- Markdown 讲义
- 可下载 PPTX 及逐页结构
- SVG 与 Mermaid 思维导图
- 带答案和评分规则的题库
- PDF/DOCX、视频分镜、字幕 SRT 和无障碍文本稿
- 实验指导书
- 项目任务书

课程内容、学生问题和对话历史均按不可信输入处理。系统会识别提示注入，并脱敏手机号、邮箱、证件号、API Key 和访问令牌。

## 测试

```powershell
python -m unittest discover -s ml/tests -v
```

设计细节见 [docs/design.md](docs/design.md)，赛题覆盖关系见 [docs/requirements-traceability.md](docs/requirements-traceability.md)。
