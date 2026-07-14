SET NAMES utf8mb4;

INSERT INTO `user` (id, username, display_name, role)
VALUES (1, 'demo_student', '演示学生', 'student')
ON DUPLICATE KEY UPDATE
  username = VALUES(username),
  display_name = VALUES(display_name),
  role = VALUES(role);

INSERT INTO course (id, name, description)
VALUES
  (1, '人工智能', '人工智能课程包含机器学习、神经网络、CNN等内容'),
  (2, '机器学习', '机器学习课程包含监督学习、无监督学习、模型评估等内容')
ON DUPLICATE KEY UPDATE
  name = VALUES(name),
  description = VALUES(description);

INSERT INTO knowledge_point (id, course_id, name, description, parent_id, difficulty)
VALUES
  (1, 1, 'CNN', '卷积神经网络，包含卷积、池化、特征图和图像分类等核心内容。', NULL, 'hard'),
  (2, 1, '反向传播', '神经网络训练中的梯度计算方法，用于根据损失函数更新模型参数。', NULL, 'hard'),
  (3, 2, '决策树', '基于特征划分构建树形分类或回归模型，具有较强可解释性。', NULL, 'medium'),
  (4, 2, '支持向量机', '通过最大化分类间隔寻找最优超平面的监督学习算法。', NULL, 'hard'),
  (5, 2, '聚类算法', '无监督学习方法，用于根据样本相似度自动发现数据中的群组结构。', NULL, 'medium')
ON DUPLICATE KEY UPDATE
  course_id = VALUES(course_id),
  name = VALUES(name),
  description = VALUES(description),
  parent_id = VALUES(parent_id),
  difficulty = VALUES(difficulty);

INSERT INTO course_resource (id, course_id, knowledge_point_id, title, resource_type, content, source)
VALUES
  (
    1,
    1,
    1,
    'CNN 讲义',
    'lecture',
    '本讲义介绍 CNN 的基本结构，包括卷积层、池化层、激活函数和全连接层，并说明 CNN 如何从图像中提取局部特征。',
    'init_data'
  ),
  (
    2,
    1,
    1,
    'CNN 练习题',
    'exercise',
    '练习内容包括计算卷积输出尺寸、解释池化作用、分析卷积核数量与特征图通道数之间的关系。',
    'init_data'
  ),
  (
    3,
    1,
    2,
    '反向传播讲义',
    'lecture',
    '本讲义讲解反向传播的链式法则、梯度计算流程，以及学习率对神经网络训练效果的影响。',
    'init_data'
  ),
  (
    4,
    2,
    3,
    '决策树案例',
    'code_example',
    '通过一个学生成绩预测案例演示决策树建模流程，包括特征选择、树结构生成、预测结果解释和过拟合控制。',
    'init_data'
  ),
  (
    5,
    2,
    NULL,
    '机器学习拓展阅读',
    'reading',
    '拓展阅读覆盖监督学习、无监督学习、模型评估、泛化能力、交叉验证和常见机器学习应用场景。',
    'init_data'
  )
ON DUPLICATE KEY UPDATE
  course_id = VALUES(course_id),
  knowledge_point_id = VALUES(knowledge_point_id),
  title = VALUES(title),
  resource_type = VALUES(resource_type),
  content = VALUES(content),
  source = VALUES(source);

INSERT INTO resource_center
  (title, description, resource_type, category, content, author, status, open_type,
   knowledge_point, tags, difficulty, summary)
VALUES
  ('CNN 基础讲义', '系统理解 CNN 的局部特征提取机制。', 'document', '深度学习',
   '学习目标：理解卷积、池化、特征图。核心概念：卷积核、步幅、填充。例题：计算卷积输出尺寸。',
   'LearnPilot AI', 'published', 'content', 'CNN', '人工智能,CNN,卷积神经网络', '入门',
   'CNN 核心概念、输出尺寸与典型图像任务。'),
  ('CNN 练习与复盘', '围绕卷积、池化和特征图完成分层练习。', 'document', '计算机视觉',
   '选择题：卷积核的作用是什么？填空题：池化常用于降低____。简答题：说明 CNN 的局部连接。',
   'LearnPilot AI', 'published', 'content', 'CNN', 'CNN,练习题,计算机视觉', '基础',
   '用于检查 CNN 基础掌握度的练习材料。'),
  ('反向传播原理讲义', '通过链式法则理解损失如何驱动参数更新。', 'document', '深度学习',
   '学习目标：理解链式法则。核心概念：损失函数、梯度、学习率。关键流程：前向计算、反向求导、参数更新。',
   'LearnPilot AI', 'published', 'content', '反向传播', '反向传播,梯度,神经网络', '进阶',
   '反向传播、损失函数、梯度与学习率。'),
  ('决策树实践案例', '用可解释分类案例学习特征划分。', 'document', '机器学习',
   '使用 sklearn DecisionTreeClassifier 完成分类案例，观察 max_depth 对过拟合的影响。',
   'LearnPilot AI', 'published', 'content', '决策树', '机器学习,决策树,代码案例', '基础',
   '决策树建模流程与过拟合控制。'),
  ('聚类算法拓展阅读', '比较常见聚类算法的适用条件和评估方式。', 'document', '机器学习',
   '拓展阅读主题：K-Means、DBSCAN、层次聚类。推荐关键词：无监督学习、距离度量、轮廓系数。',
   'LearnPilot AI', 'published', 'content', '聚类算法', '机器学习,聚类,无监督学习', '进阶',
   '常见聚类算法、距离度量与轮廓系数。')
ON DUPLICATE KEY UPDATE
  description = VALUES(description),
  resource_type = VALUES(resource_type),
  category = VALUES(category),
  content = VALUES(content),
  author = VALUES(author),
  status = VALUES(status),
  open_type = VALUES(open_type),
  knowledge_point = VALUES(knowledge_point),
  tags = VALUES(tags),
  difficulty = VALUES(difficulty),
  summary = VALUES(summary);
