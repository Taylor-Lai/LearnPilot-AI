from __future__ import annotations

import os

os.environ.setdefault("DATABASE_MODE", "sqlite")
os.environ.setdefault("SQLITE_DATABASE_URL", "sqlite:///./learnpilot.db")
os.environ.setdefault("USE_ML_SERVICE", "false")

from backend.app import models as _models  # noqa: F401
from backend.app.core.database import (
    Base,
    SessionLocal,
    engine,
    ensure_course_resource_columns,
    ensure_learning_path_columns,
    ensure_ml_profile_answer_columns,
    ensure_producer_columns,
    ensure_resource_center_columns,
    ensure_student_profile_columns,
    ensure_user_columns,
)
from backend.app.models import Course, CourseResource, KnowledgePoint, ResourceCenter, User
from backend.app.services.course_catalog import seed_ai_course
from backend.app.services.course_materials import course_materials_available, ingest_ai_for_beginners

COURSES = [
    {
        "id": 1,
        "name": "人工智能",
        "description": "人工智能课程，包含机器学习、神经网络、CNN、反向传播等内容。",
    },
    {
        "id": 2,
        "name": "机器学习",
        "description": "机器学习课程，包含监督学习、无监督学习、模型评估等内容。",
    },
]

KNOWLEDGE_POINTS = [
    {
        "id": 1,
        "course_id": 1,
        "name": "CNN",
        "description": "卷积神经网络，适合图像等网格数据的特征提取。",
        "difficulty": "hard",
    },
    {
        "id": 2,
        "course_id": 1,
        "name": "反向传播",
        "description": "神经网络训练中的梯度计算与参数更新基础。",
        "difficulty": "hard",
    },
    {
        "id": 3,
        "course_id": 2,
        "name": "决策树",
        "description": "基于树结构进行分类或回归的可解释机器学习模型。",
        "difficulty": "medium",
    },
    {
        "id": 4,
        "course_id": 2,
        "name": "支持向量机",
        "description": "通过最大化分类间隔寻找最优超平面的监督学习算法。",
        "difficulty": "hard",
    },
    {
        "id": 5,
        "course_id": 2,
        "name": "聚类算法",
        "description": "无监督学习方法，用于发现样本中的群组结构。",
        "difficulty": "medium",
    },
]

COURSE_RESOURCES = [
    (
        1,
        1,
        1,
        "CNN 基础讲义",
        "lecture",
        "学习目标：理解卷积、池化、特征图。核心概念：卷积核、步幅、填充。例题：计算卷积输出尺寸。",
    ),
    (
        2,
        1,
        1,
        "CNN 练习题",
        "exercise",
        "选择题：卷积核的作用是什么？填空题：池化常用于降低____。简答题：说明 CNN 的局部连接。代码题：搭建最小 CNN。",
    ),
    (
        3,
        1,
        1,
        "CNN 思维导图",
        "mind_map",
        "CNN\n- 基础概念\n  - 卷积核\n  - 特征图\n- 核心流程\n  - 卷积\n  - 激活\n  - 池化",
    ),
    (
        4,
        1,
        2,
        "反向传播讲义",
        "lecture",
        "学习目标：理解链式法则。核心概念：损失函数、梯度、学习率。关键流程：前向计算、反向求导、参数更新。",
    ),
    (
        5,
        1,
        2,
        "反向传播例题",
        "exercise",
        "例题：y=wx，L=(y-t)^2，求 dL/dw。解析：dL/dw=2(wx-t)x。复习建议：手算一次单参数梯度。",
    ),
    (
        6,
        2,
        3,
        "决策树案例",
        "code_example",
        "使用 sklearn DecisionTreeClassifier 完成分类案例，观察 max_depth 对过拟合的影响。",
    ),
    (7, 2, 3, "决策树讲义", "lecture", "核心原理：信息增益、基尼指数、递归划分。常见误区：树越深不一定越好。"),
    (8, 2, 4, "支持向量机讲义", "lecture", "学习目标：理解最大间隔。核心概念：支持向量、超平面、核函数、软间隔。"),
    (
        9,
        2,
        4,
        "SVM 练习题",
        "exercise",
        "选择题：支持向量决定什么？简答题：解释 C 参数。代码题：用 SVC 训练线性分类器。",
    ),
    (
        10,
        2,
        5,
        "聚类算法拓展阅读",
        "reading",
        "拓展阅读主题：K-Means、DBSCAN、层次聚类。推荐关键词：无监督学习、距离度量、轮廓系数。",
    ),
    (
        11,
        2,
        5,
        "聚类算法代码案例",
        "code_example",
        "Python 示例：使用 KMeans(n_clusters=2) 对二维样本聚类，并输出 labels 与 cluster_centers_。",
    ),
]

RESOURCE_CENTER_ITEMS = [
    {
        "title": "CNN 基础讲义",
        "description": "从卷积核、步幅、填充到特征图，系统理解 CNN 的局部特征提取机制。",
        "resource_type": "document",
        "category": "深度学习",
        "content": COURSE_RESOURCES[0][5],
        "author": "LearnPilot AI",
        "knowledge_point": "CNN",
        "tags": "人工智能,CNN,卷积神经网络",
        "difficulty": "入门",
        "summary": "CNN 核心概念、输出尺寸与典型图像任务。",
    },
    {
        "title": "CNN 练习与复盘",
        "description": "围绕卷积、池化和特征图完成分层练习与代码思考题。",
        "resource_type": "document",
        "category": "计算机视觉",
        "content": COURSE_RESOURCES[1][5],
        "author": "LearnPilot AI",
        "knowledge_point": "CNN",
        "tags": "CNN,练习题,计算机视觉",
        "difficulty": "基础",
        "summary": "用于检查 CNN 基础掌握度的练习材料。",
    },
    {
        "title": "反向传播原理讲义",
        "description": "通过链式法则理解损失如何形成梯度并驱动网络参数更新。",
        "resource_type": "document",
        "category": "深度学习",
        "content": COURSE_RESOURCES[3][5],
        "author": "LearnPilot AI",
        "knowledge_point": "反向传播",
        "tags": "反向传播,梯度,神经网络",
        "difficulty": "进阶",
        "summary": "反向传播、损失函数、梯度与学习率。",
    },
    {
        "title": "决策树实践案例",
        "description": "用可解释分类案例学习特征划分，并观察树深度对泛化能力的影响。",
        "resource_type": "document",
        "category": "机器学习",
        "content": COURSE_RESOURCES[5][5],
        "author": "LearnPilot AI",
        "knowledge_point": "决策树",
        "tags": "机器学习,决策树,代码案例",
        "difficulty": "基础",
        "summary": "决策树建模流程与过拟合控制。",
    },
    {
        "title": "聚类算法拓展阅读",
        "description": "比较 K-Means、DBSCAN 与层次聚类的适用条件和评估方式。",
        "resource_type": "document",
        "category": "机器学习",
        "content": COURSE_RESOURCES[9][5],
        "author": "LearnPilot AI",
        "knowledge_point": "聚类算法",
        "tags": "机器学习,聚类,无监督学习",
        "difficulty": "进阶",
        "summary": "常见聚类算法、距离度量与轮廓系数。",
    },
]


def upsert_by_id(session, model, item: dict) -> None:
    instance = session.get(model, item["id"])
    if instance is None:
        session.add(model(**item))
        return
    for key, value in item.items():
        setattr(instance, key, value)


def upsert_resource(session, item: tuple[int, int, int | None, str, str, str]) -> None:
    resource_id, course_id, point_id, title, resource_type, content = item
    resource = session.get(CourseResource, resource_id)
    values = {
        "id": resource_id,
        "course_id": course_id,
        "knowledge_point_id": point_id,
        "title": title,
        "resource_type": resource_type,
        "content": content,
        "source": "sqlite_demo",
    }
    if resource is None:
        session.add(CourseResource(**values))
        return
    for key, value in values.items():
        setattr(resource, key, value)


def upsert_resource_center_item(session, values: dict) -> None:
    resource = session.query(ResourceCenter).filter(ResourceCenter.title == values["title"]).first()
    if resource is None:
        session.add(ResourceCenter(**values, status="published", open_type="content"))
        return
    for key, value in values.items():
        setattr(resource, key, value)
    resource.status = "published"
    resource.open_type = "content"


def init_demo_data() -> None:
    Base.metadata.create_all(bind=engine)
    ensure_user_columns()
    ensure_student_profile_columns()
    ensure_course_resource_columns()
    ensure_resource_center_columns()
    ensure_producer_columns()
    ensure_learning_path_columns()
    ensure_ml_profile_answer_columns()
    with SessionLocal() as session:
        user = session.get(User, 1)
        if user is None:
            session.add(User(id=1, username="demo_student", display_name="演示学生", role="student"))
        else:
            user.username = "demo_student"
            user.display_name = "演示学生"
            user.role = "student"

        for course in COURSES:
            upsert_by_id(session, Course, course)

        for point in KNOWLEDGE_POINTS:
            values = {**point, "parent_id": None}
            upsert_by_id(session, KnowledgePoint, values)

        for resource in COURSE_RESOURCES:
            upsert_resource(session, resource)

        for resource in RESOURCE_CENTER_ITEMS:
            upsert_resource_center_item(session, resource)

        catalog_result = seed_ai_course(session)
        materials_result = (
            ingest_ai_for_beginners(session, int(catalog_result["course_id"]))
            if course_materials_available()
            else None
        )

        session.commit()

        total_resources = session.query(CourseResource).count()
        center_total = session.query(ResourceCenter).count()
        print(
            "SQLite demo database initialized. "
            f"course_resource_total={total_resources}, resource_center_total={center_total}, "
            f"ai_knowledge_points={catalog_result['knowledge_points']}, "
            f"ai_material_documents={materials_result['documents'] if materials_result else 0}"
        )


if __name__ == "__main__":
    init_demo_data()
