# Third-party notices

LearnPilot AI 自主开发代码采用仓库根目录中的 [MIT License](LICENSE)。本文件只记录项目在数据、课程设计和依赖层面的外部来源；外部材料仍由各自许可证约束，LearnPilot AI 的 MIT License 不会覆盖或重新许可它们。

## 数据集

### Open University Learning Analytics Dataset (OULAD)

- 来源：The Open University，<https://analyse.kmi.open.ac.uk/open_dataset>
- 数据说明论文：Kuzilek, Hlosta and Zdrahal, *Open University Learning Analytics dataset*, Scientific Data 4, 170171 (2017)，<https://doi.org/10.1038/sdata.2017.171>
- 许可证：Creative Commons Attribution 4.0 International (CC BY 4.0)
- 本仓库不提交 OULAD 原始数据或学生行为明细；仅提供预处理程序、人工构造的契约测试样例，以及由匿名点击参与度训练得到的 LightGBM 文本排序模型。
- 预处理结果中的点击参与度是推荐标签的代理变量，不等同于知识掌握度；受保护人口统计字段不进入排序模型。

## 课程设计参考

### Microsoft AI for Beginners

- 来源：Microsoft，<https://github.com/microsoft/AI-For-Beginners>
- 许可证：MIT
- 用途：仅用于核对人工智能课程的主题覆盖和实验组织方式。LearnPilot 课程清单和讲义由团队自行编写，没有整包复制该仓库内容。

### Dive into Deep Learning

- 来源：<https://github.com/d2l-ai/d2l-en>
- 许可证：正文 CC BY-SA 4.0；示例代码按其仓库说明适用修改版 MIT License。
- 用途：参考深度学习主题边界。除非单独标注许可证和归属，否则不将其正文或代码并入本仓库。

### MIT OpenCourseWare 6.034 Artificial Intelligence

- 来源：<https://ocw.mit.edu/courses/6-034-artificial-intelligence-fall-2010/>
- 许可证：CC BY-NC-SA 4.0（以 MIT OpenCourseWare 页面当前条款为准）。
- 用途：参考课程范围；不将其课件、视频或题目复制到 MIT 许可的项目源码中。

## 软件依赖

Python 与 JavaScript 依赖及其固定版本分别记录在各包的 `pyproject.toml`、`package-lock.json` 和根目录 `environment.yml` 中。发布作品前应从最终锁定环境生成依赖许可证清单，并人工复核许可证兼容性。
