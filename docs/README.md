# LearnPilot 文档中心

项目文档统一从本目录进入。根目录 `README.md` 只提供项目总览和最短运行路径；模块目录中的 `README.md` 只说明该模块的职责、结构和开发命令；跨模块设计、接口与赛题追踪统一放在这里。

## 阅读顺序

| 文档 | 适合场景 |
| --- | --- |
| [工程架构](architecture.md) | 理解服务边界、代码分层、配置与生成物策略 |
| [API 参考](api-reference.md) | 联调 Backend、ML、前端接口 |
| [ML 服务设计](ml-design.md) | 理解诊断、画像、推荐、RAG、智能体与评估方法 |
| [赛题要求与验收矩阵](competition-requirements.md) | 按 A3 赛题逐项核对全项目能力 |
| [ML 技术追踪矩阵](ml-requirements-traceability.md) | 从赛题能力追踪到 ML 实现和测试入口 |

## 模块说明

| 模块 | 文档 |
| --- | --- |
| Backend | [后端开发说明](../backend/README.md) |
| ML Service | [ML 开发说明](../ml/README.md) |
| Web | [前端开发说明](../web/README.md) |
| 外部数据 | [数据边界](../data/README.md) |
| ML 数据 | [ML 数据说明](../ml/data/README.md) |
| 第三方内容 | [许可证与来源](../THIRD_PARTY_NOTICES.md) |

## 文档边界

- 根目录仅保留社区标准文件：项目 `README.md`、`LICENSE` 和 `THIRD_PARTY_NOTICES.md`。
- `docs/` 保存跨模块、架构、接口和赛题追踪文档。
- `backend/README.md`、`ml/README.md`、`web/README.md` 保存模块级开发入口。
- 数据目录中的 `README.md` 就近声明数据来源、隐私和生成物边界，避免数据被错误提交。
- `backend/data/course_materials/**/README.md` 是固定版本的第三方课程正文，不属于工程文档。它们保留上游目录结构、许可证和文件哈希，不应移动或改名。

新增说明前先判断内容归属，避免在根 README、模块 README 和设计文档中重复维护同一段配置或命令。
