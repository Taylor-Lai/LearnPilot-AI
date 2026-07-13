# 第三方软件、来源与许可证

本项目自主开发代码不改变任何第三方组件的许可证。提交、部署或分发前需保留依赖包自带的版权和许可证文件，并以锁文件和镜像摘要为最终版本依据。

## 核心运行依赖

| 组件 | 用途 | 来源 | 许可证 |
| --- | --- | --- | --- |
| FastAPI | Backend/ML HTTP API | <https://github.com/fastapi/fastapi> | MIT |
| Uvicorn | ASGI Server | <https://github.com/encode/uvicorn> | BSD-3-Clause |
| SQLAlchemy | ORM | <https://github.com/sqlalchemy/sqlalchemy> | MIT |
| PyMySQL | MySQL Driver | <https://github.com/PyMySQL/PyMySQL> | MIT |
| psycopg2-binary | PostgreSQL Driver | <https://github.com/psycopg/psycopg2> | LGPL-3.0-or-later with exceptions |
| Pydantic / pydantic-settings | 数据校验与配置 | <https://github.com/pydantic/pydantic> | MIT |
| HTTPX | Backend-to-ML HTTP Client | <https://github.com/encode/httpx> | BSD-3-Clause |
| redis-py / RQ | 缓存、队列与异步任务 | <https://github.com/redis/redis-py>, <https://github.com/rq/rq> | MIT / BSD-2-Clause |
| python-docx / python-pptx | DOCX/PPTX 导出 | <https://github.com/python-openxml/python-docx>, <https://github.com/scanny/python-pptx> | MIT |
| ReportLab | PDF 导出 | <https://www.reportlab.com/dev/opensource/> | BSD-3-Clause |
| NumPy / pandas | 数值计算与数据处理 | <https://github.com/numpy/numpy>, <https://github.com/pandas-dev/pandas> | BSD-3-Clause |
| scikit-learn / joblib | 评估、模型工具与持久化 | <https://github.com/scikit-learn/scikit-learn>, <https://github.com/joblib/joblib> | BSD-3-Clause |
| LightGBM | 个性化资源排序 | <https://github.com/microsoft/LightGBM> | MIT |
| Vue / Vue Router | Web UI | <https://github.com/vuejs/core>, <https://github.com/vuejs/router> | MIT |
| Apache ECharts | 管理端图表 | <https://github.com/apache/echarts> | Apache-2.0 |
| Lucide | UI 图标 | <https://github.com/lucide-icons/lucide> | ISC |
| Marked | Markdown 渲染 | <https://github.com/markedjs/marked> | MIT |
| Vite | 前端构建 | <https://github.com/vitejs/vite> | MIT |

## 基础设施与外部服务

| 组件/服务 | 用途 | 版本约束 | 许可证/使用条件 |
| --- | --- | --- | --- |
| Python | Backend/ML Runtime | 3.11 | PSF-2.0 |
| Node.js | Web Build Runtime | 22 | MIT |
| Nginx | 静态资源服务与反向代理 | 1.27-alpine | BSD-2-Clause |
| MySQL Community | 关系数据库 | 8.4 | GPL-2.0-only；通过网络独立运行 |
| Redis | 任务队列 | 7.2-alpine | BSD-3-Clause；固定在许可证变更前的 7.2 系列 |
| 科大讯飞星火 | 默认在线大模型 | 4.0Ultra | 商业 API，遵循科大讯飞开放平台服务协议；不随源码分发 |
| Qwen 兼容接口 | 可选调试提供方 | 用户配置 | 仅作为兼容层，遵循提供方服务条款 |

## AI Coding 使用说明

开发过程中使用 AI Coding 工具辅助代码检索、重构建议、测试生成、文档整理和缺陷排查。所有修改均纳入 Git 审查，使用静态检查、自动化测试和人工运行验证；AI 工具不拥有项目业务代码或自主开发内容的著作权。涉及赛题规则、第三方许可证、模型输出事实和最终演示材料的内容仍由团队成员人工复核。

## 发布复核

1. Python 以 `backend/pyproject.toml`、`ml/pyproject.toml` 和实际安装元数据为准。
2. Web 以 `web/package-lock.json` 中每个包的 `license` 字段为准。
3. 容器以 `Dockerfile`、`docker-compose.yml` 和构建时解析的镜像摘要为准。
4. 若新增 GPL/AGPL、非商业或来源不明组件，必须在发布前单独评估分发义务。
