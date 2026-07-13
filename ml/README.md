# LearnPilot ML

LearnPilot 的机器学习服务，实现 A3 赛题中的学习诊断、学生画像、资源排序、学习路径、RAG 内容生成、多轮辅导和学习效果反馈。

## 分层

```text
ml/
├─ src/ml_service/
│  ├─ api/                 FastAPI 应用和请求契约
│  ├─ application/         学习闭环与 Agent 编排
│  ├─ domain/              领域模型和诊断逻辑
│  ├─ infrastructure/      LightGBM、RAG 和 Qwen 适配器
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
conda activate learnpilot-ml
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
| POST | `/generate` | 生成带 RAG 证据的学习内容 |
| POST | `/feedback` | 根据学习反馈更新闭环 |
| POST | `/student/update-profile` | 更新学生画像 |
| POST | `/tutor/ask` | 多轮、有据、分层智能辅导 |

## Qwen

离线测试使用：

```text
LEARNPILOT_LLM_MODE=template
```

真实生成在根目录 `.env` 配置 `DASHSCOPE_API_KEY`，并执行：

```powershell
learnpilot-ml-qwen-check
```

生成内容必须引用实际召回的资源切片；引用不合法时会被过滤并由确定性模板兜底。

## 测试

```powershell
python -m unittest discover -s ml/tests -v
```

设计细节见 [docs/design.md](docs/design.md)，赛题覆盖关系见 [docs/requirements-traceability.md](docs/requirements-traceability.md)。
