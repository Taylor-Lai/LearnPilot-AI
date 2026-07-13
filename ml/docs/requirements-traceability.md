# A3 赛题 ML 要求追踪矩阵

本文件只覆盖团队中 ML 模块负责的范围。前端交互、用户权限、课程管理和业务持久化由主后端负责。

| 赛题能力 | ML 实现 | 可验证入口 |
| --- | --- | --- |
| 学习状态诊断 | `DiagnosticEngine` 使用题目难度、区分度、得分、用时、提示次数、作答次数和置信度估计掌握度 | `POST /assessment/diagnose`、`DiagnosticEngineTest` |
| 动态学生画像 | `StudentProfiler` 融合历史掌握度、诊断、行为时序、偏好、投入度、稳定性和遗忘风险 | `POST /student/update-profile`、`StudentProfilerTest` |
| 多智能体协作 | 诊断、画像、推荐、规划、生成评估、辅导 Agent 输出可解释 trace | `/recommend`、`/tutor/ask` |
| 个性化资源推荐 | 规则基线 + 可训练排序器；包含薄弱点、难度、偏好、质量、时长、知识图距离、反馈、新颖度等特征 | `POST /recommend`、`/train/status` |
| 学习路径规划 | 基于知识图谱先修关系、掌握缺口和知识点重要度生成路径、阶段检查点与预计时长 | `POST /path` |
| 多形态 RAG 内容生成 | BM25 + TF-IDF + 轻量重排召回证据，生成讲义、网页幻灯片、SVG/Mermaid 思维导图、题库、视频分镜、实验和项目任务书 | `POST /generate`、`ResourceBundleBuilder` |
| 幻觉抑制与质量检查 | 零相关证据过滤、引用白名单、知识点/练习/答案/错因/难度/安全检查 | `GenerationEvaluationAgent`、`RagAndGenerationTest` |
| 生成审核闭环 | 内容未达到审核阈值时执行确定性补全、引用修复、安全清洗和多形态重建，再次审核并保留全过程 | `review_cycle`、生成修复测试 |
| 内容与隐私安全 | 课程材料、问题和历史对话按不可信输入处理，拦截中英文提示注入并脱敏密钥、令牌、手机号、邮箱和证件号 | `ContentSafetyGuard`、`safety_meta` |
| 智能辅导 | 基于画像、对话历史和课程证据的苏格拉底式多轮辅导 | `POST /tutor/ask` |
| 学习效果评估 | Recall/NDCG/MAP/MRR、覆盖度、多样性、先修合理性、生成质量、证据率、多形态覆盖率、安全率、审核通过率、可解释率 | `GET /evaluate`、`learnpilot-ml-evaluate` |
| 动态反馈闭环 | 新行为更新掌握度和画像，重新推荐并重规划路径，输出前后差异 | `POST /feedback` |
| 可复现训练 | 固定随机种子、按学生分组留出验证、防止目标事件泄漏、模型元数据和数据指纹 | `learnpilot-ml-generate`、`learnpilot-ml-train` |

## ML 交付验收顺序

```powershell
conda env create -f environment.yml
conda activate learnpilot-ml
learnpilot-ml-generate
learnpilot-ml-train
learnpilot-ml-evaluate
python -m unittest discover -s ml/tests -v
learnpilot-ml-demo
```

真实大模型联调需将根目录 `.env.example` 复制为 `.env` 并配置 `DASHSCOPE_API_KEY`；自动化测试默认使用模板模式，不依赖外网。
