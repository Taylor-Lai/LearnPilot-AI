# Data boundary

仓库级 `data/` 只管理外部输入的来源登记和本地落盘约定，不存放服务运行产物。

```text
data/
├─ sources.yaml                    外部来源、许可证、版本和导入策略
└─ external/                       本地只读原始输入（Git / Docker 均忽略）
   ├─ datasets/
   │  └─ oulad/
   └─ course-materials/
      └─ ai-for-beginners/
```

职责边界：

- `data/external/`：从官方来源获得、未经项目修改的原始输入。
- `ml/data/processed/`：ML 将原始行为数据转换后的统一训练契约。
- `ml/data/generated/`：确定性合成数据。
- `backend/data/knowledge_base/`：经过筛选、改写、溯源和测试后可随项目发布的课程知识库。
- `ml/artifacts/`、`ml/reports/`：重新训练与评测运行产物。

禁止把第三方原始仓库、下载 ZIP、学生行为明细或不透明模型序列化文件强制加入 Git。正式入库内容必须先通过许可证策略、来源元数据和内容测试；`ml/models/ranker/` 仅保存可审查文本模型及哈希元数据。

## 来源同步

```powershell
python tools/manage_sources.py verify
python tools/manage_sources.py sync microsoft-ai-for-beginners --proxy http://127.0.0.1:7897
```

代理参数可省略。Microsoft AI for Beginners 使用固定提交的 Git 树作为文件清单，只同步清单允许的文本、Notebook、代码与测验文件；每个文件按 Git blob SHA 校验，并在 `.learnpilot-source.json` 中记录提交、许可证和文件清单摘要。该目录仍属于原始输入边界，正式课程资源通过 `backend/scripts/seed_ai_course.py` 转换后写入数据库。
