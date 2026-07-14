# Data boundary

仓库级 `data/` 管理外部输入的来源登记和本地落盘约定，不存放服务运行产物。服务可直接使用的精选课程包位于后端数据目录。

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
- `backend/data/knowledge_base/`：LearnPilot 自主维护的课程目录与结构化知识种子。
- `backend/data/course_materials/`：经许可证审查、固定版本和逐文件哈希校验后随服务分发的课程文档子集。
- `ml/artifacts/`、`ml/reports/`：重新训练与评测运行产物。

禁止把第三方原始仓库、下载 ZIP、学生行为明细或不透明模型序列化文件强制加入 Git。正式入库内容必须先通过许可证策略、来源元数据和内容测试；`ml/models/ranker/` 仅保存可审查文本模型及哈希元数据。

## 来源同步

```powershell
python tools/manage_sources.py verify
python tools/build_course_bundle.py verify
```

干净克隆已经包含 37 份 Microsoft AI for Beginners 中文课程与实验文档，不依赖 `data/external/` 或网络即可初始化数据库。课程包保留上游 MIT License、固定提交和逐文件 SHA-256，后端会在导入前强制校验清单，随后生成 37 条资源和 337 个 RAG 分块。

只有更新上游固定版本时才需要重建课程包：

```powershell
python tools/manage_sources.py sync microsoft-ai-for-beginners --proxy http://127.0.0.1:7897
python tools/build_course_bundle.py build
python tools/build_course_bundle.py verify
```

代理参数可省略。完整同步目录仍属于被 Git 和 Docker 忽略的原始输入边界；构建工具只提取课程映射需要的 37 份文档及许可证。
