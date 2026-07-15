# LearnPilot ML Service

ML Service 提供无状态算法能力，覆盖学习诊断、动态画像、个性化排序、知识图谱路径、RAG 资源生成、多轮辅导、反馈闭环、训练和离线评估。业务身份、课程持久化和任务管理由 Backend 负责。

## 代码结构

```text
ml/
├─ src/ml_service/
│  ├─ api/                 FastAPI 与请求契约
│  ├─ application/         学习闭环和 Agent 编排
│  ├─ domain/              领域模型与诊断逻辑
│  ├─ infrastructure/      排序、RAG、安全和 LLM
│  ├─ datasets/            OULAD、合成数据和统一契约
│  ├─ training/            防泄漏训练工作流
│  └─ evaluation/          离线指标与评估报告
├─ data/benchmarks/        可审查评估基准
├─ models/ranker/          已验证部署模型
├─ tests/                  单元和闭环测试
└─ pyproject.toml          包、依赖和命令定义
```

运行时生成的 `data/generated/`、`data/processed/`、`artifacts/` 和 `reports/` 均被 Git 忽略。部署模型采用 LightGBM 文本格式，元数据记录数据语义、分组验证指标、特征版本与 SHA-256。

## 常用命令

```powershell
conda activate learnpilot-ai
learnpilot-ml-api
learnpilot-ml-generate
learnpilot-ml-train
learnpilot-ml-evaluate
learnpilot-ml-demo
```

API 默认地址：<http://127.0.0.1:8000/docs>。

| 接口 | 作用 |
| --- | --- |
| `GET /health` | 服务与排序模型状态 |
| `POST /assessment/diagnose` | 原始作答诊断 |
| `POST /student/update-profile` | 动态更新学生画像 |
| `POST /recommend` | 推荐、路径与学习卡闭环 |
| `POST /path` | 基于知识图谱规划路径 |
| `POST /generate` | 生成带证据和审核轨迹的多形态资源 |
| `POST /tutor/ask` | 多轮、有据的智能辅导 |
| `POST /feedback` | 根据行为和评测更新闭环 |

## 模型与数据边界

- 默认正式模型基于 OULAD 构建参与度代理排序；点击量不能解释为知识掌握度。
- 训练按学生划分验证集，并排除目标事件，避免行为标签泄漏。
- 训练产物先写入 `ml/artifacts/`，不会自动覆盖部署模型。
- 课程内容来自项目人工智能知识库，OULAD 不提供人工智能教材内容。
- 生成内容必须引用实际召回切片，并经过教学完整性、引用、安全、隐私和多形态审核。

详细数据语义和准备命令见[ML 数据说明](data/README.md)，算法设计见[ML 服务设计](../docs/ml-design.md)。

## 大模型模式

```text
LEARNPILOT_LLM_MODE=template   # 离线测试，不调用外部模型
LEARNPILOT_LLM_MODE=auto       # 使用配置的提供方并保留安全降级
```

正式联调默认使用科大讯飞星火：

```powershell
learnpilot-ml-spark-check
```

自动化评估固定使用离线模板，即使 `.env` 存在 API Key 也不会产生在线调用。

## 验证

```powershell
python -m pytest ml/tests -q
python -m ruff check ml/src ml/tests
learnpilot-ml-evaluate
```

赛题能力与实现入口的对应关系见[ML 技术追踪矩阵](../docs/ml-requirements-traceability.md)。
