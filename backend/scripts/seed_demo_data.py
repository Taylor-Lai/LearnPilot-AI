"""Seed demo data for LearnPilot-AI (idempotent)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

os.environ.setdefault("DATABASE_MODE", "mysql")

from backend.app.core.database import SessionLocal
from backend.app.core.security import hash_password
from backend.app.models import (
    ProducerArtifact,
    ProducerTask,
    ResourceCenter,
    StudentProfile,
    User,
)

DEMO_PASSWORD = os.getenv("LEARNPILOT_DEMO_PASSWORD", "Demo@2026")
USER_COUNT = 15
PROFILE_COUNT = 10
RESOURCE_COUNT = 15
TASK_COUNT = 15
ARTIFACT_TYPES = ("lecture", "mind_map", "exercise")

MAJORS = ("软件工程", "计算机科学", "人工智能", "数据科学")
GRADES = ("大一", "大二", "大三")
GOALS = (
    "掌握Python基础并完成课程项目",
    "学习机器学习算法",
    "提升深度学习实践能力",
    "理解数据库设计与SQL优化",
    "完成软件工程课程综合实践",
)
PREFERENCES = ("视频学习", "案例驱动", "习题练习")
KNOWLEDGE_LEVELS = ("入门", "进阶")

RESOURCE_THEMES = (
    "Python基础",
    "机器学习",
    "深度学习",
    "数据库",
    "软件工程",
)
RESOURCE_TYPES = ("document", "ppt", "video")

TASK_TOPICS = (
    "Python数据分析入门",
    "机器学习回归模型实践",
    "CNN图像分类学习",
    "数据库设计实践",
    "软件工程需求分析",
    "深度学习优化器对比",
    "Python面向对象编程",
    "聚类算法应用案例",
    "RNN文本生成入门",
    "SQL查询性能优化",
    "敏捷开发流程实践",
    "Transformer注意力机制",
    "NumPy科学计算基础",
    "推荐系统入门",
    "Git版本控制与协作",
)


def _username(index: int) -> str:
    return f"demo_student_{index:02d}"


def _email(index: int) -> str:
    return f"demo_student_{index:02d}@example.com"


def _task_id(index: int) -> str:
    return f"seed_demo_task_{index:02d}"


def _resource_title(theme: str, resource_type: str, index: int) -> str:
    type_label = {"document": "文档", "ppt": "PPT", "video": "视频"}[resource_type]
    return f"[演示]{theme}·{type_label}·{index:02d}"


def _mastery_for_student(index: int) -> dict[str, float]:
    topics = ("Python", "机器学习", "深度学习", "数据库", "软件工程")
    base = 0.35 + (index % 5) * 0.1
    return {topic: round(min(base + offset * 0.08, 0.92), 2) for offset, topic in enumerate(topics)}


def _weak_points(index: int) -> list[str]:
    pools = (
        ["变量与数据类型", "函数封装"],
        ["梯度下降", "过拟合"],
        ["卷积层", "池化层"],
        ["范式化", "索引优化"],
        ["需求建模", "单元测试"],
    )
    return list(pools[index % len(pools)])


def _raw_text(
    *,
    username: str,
    major: str,
    grade: str,
    goal: str,
    preference: str,
    knowledge_level: str,
    weak_points: list[str],
) -> str:
    weak_text = "、".join(weak_points)
    return (
        f"学生 {username} 就读于{major}专业，当前为{grade}学生。"
        f"学习目标：{goal}。"
        f"偏好{preference}方式，当前知识水平为{knowledge_level}。"
        f"薄弱环节包括：{weak_text}。"
        "希望通过系统化学习与练习，逐步建立完整的知识体系并提升项目实践能力。"
    )


def _document_content(theme: str) -> str:
    return f"""# {theme} 学习简介

## 概述
本资料面向课程学习与复习，帮助学习者快速理解 {theme} 的核心概念与实践路径。

## 学习目标
- 掌握 {theme} 的基本术语与典型应用场景
- 能够完成一个最小可运行的练习或实验
- 建立后续深入学习的知识地图

## 内容结构
1. 基础概念与背景
2. 核心原理与关键步骤
3. 典型案例与常见误区
4. 练习建议与复盘清单

## 学习建议
建议先通读全文，再完成 2-3 道练习题，最后用自己的话总结三个关键收获。
"""


def _resource_url(resource_type: str, theme: str, index: int) -> str:
    slug = theme.replace(" ", "-")
    if resource_type == "ppt":
        return f"https://demo.learnpilot.local/ppt/{slug}-{index:02d}.pptx"
    return f"https://demo.learnpilot.local/video/{slug}-{index:02d}.mp4"


def _exercise_items(topic: str) -> list[dict]:
    return [
        {
            "id": 1,
            "type": "choice",
            "question": f"关于「{topic}」，以下哪项描述最准确？",
            "options": ["仅用于理论研究", "可用于解决实际问题", "与编程无关", "无法评估效果"],
            "answer": 1,
        },
        {
            "id": 2,
            "type": "short_answer",
            "question": f"请用一句话说明学习「{topic}」时最先要搞清楚的两个概念。",
            "answer": "应先明确问题定义与输入输出，再理解核心处理流程。",
        },
        {
            "id": 3,
            "type": "short_answer",
            "question": f"结合「{topic}」举一个最小实践案例，并说明验证方式。",
            "answer": "可用一个小数据集或示例代码跑通流程，并检查输出是否符合预期。",
        },
    ]


def _lecture_content(topic: str, requirement: str) -> str:
    return f"""# {topic} 知识点讲解

## 学习目标
理解 {topic} 的基本定义、核心流程与典型应用。

## 核心原理
围绕 {topic} 建立“概念—步骤—案例—复盘”的学习闭环，避免只记结论不记原因。

## 个性化要求
{requirement}

## 学习建议
完成讲解阅读后，尝试用自己的话复述关键步骤，并记录 2 个仍不清楚的问题。
"""


def _mind_map_content(topic: str) -> str:
    return f"""# {topic}
- 基础概念
  - 定义与背景
  - 输入与输出
- 核心原理
  - 关键步骤
  - 参数与结果
- 实践应用
  - 典型案例
  - 代码实验
- 评估复盘
  - 常见误区
  - 自测问题
"""


def _build_result_json(topic: str, requirement: str) -> dict:
    exercises = _exercise_items(topic)
    return {
        "topic": topic,
        "requirement": requirement,
        "status": "completed",
        "requested_types": list(ARTIFACT_TYPES),
        "lecture": {
            "title": f"{topic} 知识点讲解",
            "content": _lecture_content(topic, requirement),
        },
        "mind_map": {
            "title": f"{topic} 思维导图",
            "content": _mind_map_content(topic),
        },
        "exercises": exercises,
        "agent_traces": [
            {
                "agent": "需求分析Agent",
                "action": "解析主题与生成要求",
                "output": f"主题为 {topic}，计划生成讲义、思维导图与练习题。",
            },
            {
                "agent": "质量评估Agent",
                "action": "检查产物完整性",
                "output": "结构检查通过，产物可用于学习与复习。",
            },
        ],
    }


def _artifact_rows(task_id: str, topic: str, result_json: dict) -> list[ProducerArtifact]:
    exercises_json = json.dumps(result_json["exercises"], ensure_ascii=False)
    rows = [
        ProducerArtifact(
            task_id=task_id,
            artifact_type="lecture",
            title=result_json["lecture"]["title"],
            content=result_json["lecture"]["content"],
            metadata_json={"topic": topic, "source": "seed_demo_data"},
        ),
        ProducerArtifact(
            task_id=task_id,
            artifact_type="mind_map",
            title=result_json["mind_map"]["title"],
            content=result_json["mind_map"]["content"],
            metadata_json={"topic": topic, "source": "seed_demo_data"},
        ),
        ProducerArtifact(
            task_id=task_id,
            artifact_type="exercise",
            title=f"{topic} 练习题",
            content=exercises_json,
            metadata_json={"topic": topic, "source": "seed_demo_data"},
        ),
    ]
    return rows


def seed_users(session, password_hash: str) -> tuple[int, list[User]]:
    created = 0
    users: list[User] = []
    for index in range(1, USER_COUNT + 1):
        email = _email(index)
        existing = session.query(User).filter(User.email == email).first()
        if existing is not None:
            users.append(existing)
            continue

        username = _username(index)
        user = User(
            username=username,
            display_name=f"演示学生{index:02d}",
            nickname=f"学生{index:02d}",
            email=email,
            password_hash=password_hash,
            role="student",
            is_admin=False,
            status="active",
        )
        session.add(user)
        session.flush()
        users.append(user)
        created += 1
    return created, users


def seed_profiles(session, users: list[User]) -> int:
    created = 0
    for index, user in enumerate(users[:PROFILE_COUNT], start=1):
        if session.query(StudentProfile).filter(StudentProfile.user_id == user.id).first():
            continue

        major = MAJORS[(index - 1) % len(MAJORS)]
        grade = GRADES[(index - 1) % len(GRADES)]
        goal = GOALS[(index - 1) % len(GOALS)]
        preference = PREFERENCES[(index - 1) % len(PREFERENCES)]
        knowledge_level = KNOWLEDGE_LEVELS[(index - 1) % len(KNOWLEDGE_LEVELS)]
        weak_points = _weak_points(index - 1)
        mastery = _mastery_for_student(index - 1)

        profile = StudentProfile(
            user_id=user.id,
            major=major,
            grade=grade,
            course=major,
            goal=goal,
            preference=preference,
            cognitive_style="实践型" if index % 2 else "理论型",
            knowledge_level=knowledge_level,
            raw_text=_raw_text(
                username=user.username,
                major=major,
                grade=grade,
                goal=goal,
                preference=preference,
                knowledge_level=knowledge_level,
                weak_points=weak_points,
            ),
            mastery=mastery,
            weak_points_json=weak_points,
            engagement_score=round(0.55 + (index % 4) * 0.1, 2),
            forgetting_risk=round(0.25 + (index % 3) * 0.08, 2),
            learning_stage="基础巩固" if knowledge_level == "入门" else "强化训练",
        )
        session.add(profile)
        created += 1
    return created


def seed_resources(session) -> int:
    created = 0
    for index in range(1, RESOURCE_COUNT + 1):
        theme = RESOURCE_THEMES[(index - 1) % len(RESOURCE_THEMES)]
        resource_type = RESOURCE_TYPES[(index - 1) % len(RESOURCE_TYPES)]
        title = _resource_title(theme, resource_type, index)

        if session.query(ResourceCenter).filter(ResourceCenter.title == title).first():
            continue

        is_document = resource_type == "document"
        resource = ResourceCenter(
            title=title,
            description=f"面向{theme}课程的演示{resource_type}资源，适用于课堂学习与课后复习。",
            resource_type=resource_type,
            category=theme,
            content=_document_content(theme) if is_document else f"{theme} 配套学习资料（{resource_type}）。",
            url="" if is_document else _resource_url(resource_type, theme, index),
            cover_url=f"https://demo.learnpilot.local/cover/{theme}-{index:02d}.png",
            author="LearnPilot 演示库",
            views=index * 3,
            likes=index,
            status="published",
            open_type="content" if is_document else "url",
            knowledge_point=theme,
            tags=f"{theme},演示,课程资源",
            difficulty=["easy", "medium", "hard"][(index - 1) % 3],
            summary=f"{theme} 核心知识速览与练习指引。",
        )
        session.add(resource)
        created += 1
    return created


def seed_tasks_and_artifacts(session, users: list[User]) -> tuple[int, int]:
    tasks_created = 0
    artifacts_created = 0

    if not users:
        return tasks_created, artifacts_created

    for index in range(1, TASK_COUNT + 1):
        task_id = _task_id(index)
        if session.query(ProducerTask).filter(ProducerTask.task_id == task_id).first():
            continue

        user = users[(index - 1) % len(users)]
        topic = TASK_TOPICS[(index - 1) % len(TASK_TOPICS)]
        requirement = f"围绕「{topic}」完成讲义、思维导图与练习题三类产物，兼顾概念理解与实践应用。"
        result_json = _build_result_json(topic, requirement)

        task = ProducerTask(
            task_id=task_id,
            user_id=user.id,
            topic=topic,
            requirement=requirement,
            task_type="multi_agent_generation",
            status="completed",
            progress=100,
            result_json=result_json,
            error_message=None,
        )
        session.add(task)
        tasks_created += 1

        for artifact in _artifact_rows(task_id, topic, result_json):
            session.add(artifact)
            artifacts_created += 1

    return tasks_created, artifacts_created


def seed_demo_data() -> None:
    password_hash = hash_password(DEMO_PASSWORD)
    counts = {
        "users": 0,
        "profiles": 0,
        "resources": 0,
        "tasks": 0,
        "artifacts": 0,
    }

    with SessionLocal() as session:
        try:
            counts["users"], users = seed_users(session, password_hash)
            counts["profiles"] = seed_profiles(session, users)
            counts["resources"] = seed_resources(session)
            counts["tasks"], counts["artifacts"] = seed_tasks_and_artifacts(session, users)
            session.commit()
        except Exception:
            session.rollback()
            raise

    print("演示数据填充完成。")
    print(f"新增用户数量: {counts['users']}")
    print(f"新增画像数量: {counts['profiles']}")
    print(f"新增资源数量: {counts['resources']}")
    print(f"新增任务数量: {counts['tasks']}")
    print(f"新增产物数量: {counts['artifacts']}")


if __name__ == "__main__":
    seed_demo_data()
