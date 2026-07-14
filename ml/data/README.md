# ML 数据目录

本目录只提交可审查的评测基准、数据契约说明和少量人工构造测试样例，不提交学生隐私数据、OULAD 原始文件或大体积预处理结果。

## 目录边界

- `benchmarks/`：进入 Git 的确定性离线评测用例。
- `../../data/external/`：仓库级只读外部输入，按 `datasets/` 和 `course-materials/` 分类，已由 `.gitignore` 排除。
- `processed/`：预处理后的统一训练数据，已由 `.gitignore` 排除。
- `generated/`：项目生成的合成训练数据，已由 `.gitignore` 排除。

## 准备 OULAD

1. 从 OULAD 官方页面下载数据：<https://analyse.kmi.open.ac.uk/open_dataset>。
2. 将 ZIP 文件或解压目录放到仓库根目录的 `data/external/datasets/oulad/`。
3. 运行：

```powershell
learnpilot-ml-prepare-oulad data/external/datasets/oulad/anonymisedData.zip ml/data/processed/oulad
```

4. 使用预处理数据训练：

```powershell
$env:LEARNPILOT_TRAINING_DATA_DIR="ml/data/processed/oulad"
learnpilot-ml-train
```

训练默认从每名学生的正负标签中均匀抽取最多 80 个代表性时点，并只回看最近 50 条行为。这样既覆盖全部有行为的学生、维持标签平衡，又避免逐条重建无限历史导致近似二次复杂度。可使用 `LEARNPILOT_MAX_TRAINING_EVENTS_PER_STUDENT` 和 `LEARNPILOT_TRAINING_HISTORY_WINDOW` 调整，并应在实验结果中记录取值。

预处理器会生成统一的 `knowledge_graph.json`、`resources.json`、`students.json`、`events.json` 和 `dataset_manifest.json`。默认最多保留 200,000 条按源文件顺序读取且受每名学生上限约束的交互，避免普通开发机产生数 GB JSON；可通过命令参数调整。

## 数据解释限制

- OULAD 的 `sum_click` 只代表 VLE 参与度。本项目将其对数缩放为排序训练的参与度代理分数，不能写成“真实知识掌握度”。
- `sum_click × 90 秒` 只是停留时长代理并设有上限，不是平台实测时长。
- 性别、地区、年龄、残障、贫困指数等字段不进入训练文件和排序特征。
- 学生标识经过稳定散列，只用于同一数据集内的分组切分。
- OULAD 课程模块不是人工智能课程。它用于验证行为建模方法；人工智能课程的知识内容来自项目自建课程库。
