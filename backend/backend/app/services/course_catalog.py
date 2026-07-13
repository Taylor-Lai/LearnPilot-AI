from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from backend.app.models import Course, CourseResource, KnowledgePoint, Question, ResourceCenter

CATALOG_PATH = Path(__file__).resolve().parents[3] / "data" / "knowledge_base" / "ai_course_seed.json"


def load_ai_course_catalog() -> dict[str, Any]:
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    validate_ai_course_catalog(catalog)
    return catalog


def validate_ai_course_catalog(catalog: dict[str, Any]) -> None:
    chapters = catalog.get("chapters") or []
    if len(chapters) < 8:
        raise ValueError("AI course catalog must contain at least 8 chapters")
    points = [point for chapter in chapters for point in chapter.get("knowledge_points") or []]
    if len(points) < 24:
        raise ValueError("AI course catalog must contain at least 24 knowledge points")
    names = [str(point.get("name") or "").strip() for point in points]
    if not all(names) or len(names) != len(set(names)):
        raise ValueError("knowledge point names must be present and unique")
    known: set[str] = set()
    for point in points:
        prerequisites = [str(item) for item in point.get("prerequisites") or []]
        unknown = set(prerequisites) - known
        if unknown:
            raise ValueError(f"prerequisites must precede {point['name']}: {sorted(unknown)}")
        known.add(str(point["name"]))
    question_count = sum(len(chapter.get("questions") or []) for chapter in chapters)
    if question_count < 16:
        raise ValueError("AI course catalog must contain at least 16 assessment questions")


def ai_prerequisites() -> dict[str, list[str]]:
    catalog = load_ai_course_catalog()
    return {
        point["name"]: list(point.get("prerequisites") or [])
        for chapter in catalog["chapters"]
        for point in chapter["knowledge_points"]
    }


def seed_ai_course(session: Session) -> dict[str, int]:
    catalog = load_ai_course_catalog()
    course_data = catalog["course"]
    session.flush()
    course = session.query(Course).filter(Course.name == course_data["name"]).first()
    if course is None:
        course = Course(name=course_data["name"])
        session.add(course)
        session.flush()
    course.description = course_data["description"]

    points_by_name: dict[str, KnowledgePoint] = {}
    resource_count = 0
    question_count = 0
    for chapter in catalog["chapters"]:
        for point_data in chapter["knowledge_points"]:
            point = (
                session.query(KnowledgePoint)
                .filter(KnowledgePoint.course_id == course.id, KnowledgePoint.name == point_data["name"])
                .first()
            )
            if point is None:
                point = KnowledgePoint(course_id=course.id, name=point_data["name"])
                session.add(point)
                session.flush()
            point.description = point_data["description"]
            point.difficulty = point_data["difficulty"]
            prerequisites = point_data.get("prerequisites") or []
            point.parent_id = points_by_name[prerequisites[0]].id if prerequisites else None
            points_by_name[point.name] = point

        chapter_point_names = [item["name"] for item in chapter["knowledge_points"]]
        chapter_content = _chapter_markdown(course_data, chapter)
        resource_count += _upsert_course_resource(
            session,
            course.id,
            points_by_name[chapter_point_names[-1]].id,
            f"第{chapter['order']}章 {chapter['title']}课程讲义",
            "lecture",
            chapter_content,
            {"chapter_id": chapter["id"], "hours": chapter["hours"], "knowledge_points": chapter_point_names},
        )
        resource_count += _upsert_course_resource(
            session,
            course.id,
            points_by_name[chapter_point_names[-1]].id,
            f"第{chapter['order']}章 {chapter['title']}实验任务书",
            "lab",
            _lab_markdown(chapter),
            {"chapter_id": chapter["id"], "knowledge_points": chapter_point_names},
        )
        _upsert_resource_center(session, chapter, chapter_content, chapter_point_names[-1])

        for question_data in chapter.get("questions") or []:
            exists = (
                session.query(Question.id)
                .filter(Question.course_id == course.id, Question.stem == question_data["stem"])
                .first()
            )
            if exists:
                continue
            point = points_by_name.get(question_data.get("knowledge_point"))
            session.add(
                Question(
                    course_id=course.id,
                    knowledge_point_id=point.id if point else None,
                    question_type=question_data["type"],
                    stem=question_data["stem"],
                    answer=question_data["answer"],
                    explanation=question_data["explanation"],
                    difficulty=float(question_data["difficulty"]),
                    source="ai_course_catalog:v1",
                )
            )
            question_count += 1

    return {
        "course_id": course.id,
        "chapters": len(catalog["chapters"]),
        "knowledge_points": len(points_by_name),
        "resources_written": resource_count,
        "questions_created": question_count,
    }


def _upsert_course_resource(
    session: Session,
    course_id: int,
    point_id: int,
    title: str,
    resource_type: str,
    content: str,
    metadata: dict[str, Any],
) -> int:
    resource = session.query(CourseResource).filter(CourseResource.title == title).first()
    created = resource is None
    if resource is None:
        resource = CourseResource(course_id=course_id, knowledge_point_id=point_id, title=title)
        session.add(resource)
    resource.course_id = course_id
    resource.knowledge_point_id = point_id
    resource.resource_type = resource_type
    resource.content = content
    resource.source = "ai_course_catalog:v1"
    resource.source_type = "catalog"
    resource.status = "published"
    resource.version = "v1"
    resource.resource_metadata = metadata
    return int(created)


def _upsert_resource_center(
    session: Session,
    chapter: dict[str, Any],
    content: str,
    knowledge_point: str,
) -> None:
    title = f"人工智能·第{chapter['order']}章 {chapter['title']}"
    item = session.query(ResourceCenter).filter(ResourceCenter.title == title).first()
    if item is None:
        item = ResourceCenter(title=title, resource_type="document")
        session.add(item)
    item.description = "；".join(chapter["objectives"])
    item.category = "人工智能课程"
    item.content = content
    item.author = "LearnPilot AI 课程组"
    item.status = "published"
    item.open_type = "content"
    item.knowledge_point = knowledge_point
    item.tags = "人工智能," + ",".join(point["name"] for point in chapter["knowledge_points"])
    item.difficulty = "进阶" if any(point["difficulty"] == "hard" for point in chapter["knowledge_points"]) else "基础"
    item.summary = f"第{chapter['order']}章课程讲义、知识点和实验任务。"


def _chapter_markdown(course: dict[str, Any], chapter: dict[str, Any]) -> str:
    objectives = "\n".join(f"- {item}" for item in chapter["objectives"])
    points = "\n\n".join(
        f"### {item['name']}\n\n{item['description']}\n\n"
        f"先修知识：{'、'.join(item.get('prerequisites') or ['无'])}；难度：{item['difficulty']}。"
        for item in chapter["knowledge_points"]
    )
    outcomes = "\n".join(f"- {item}" for item in course["learning_outcomes"])
    return (
        f"# 第{chapter['order']}章 {chapter['title']}\n\n"
        f"课程：{course['name']}｜建议学时：{chapter['hours']} 学时\n\n"
        f"## 本章目标\n\n{objectives}\n\n"
        f"## 知识点\n\n{points}\n\n"
        f"## 实验与迁移任务\n\n{chapter['lab']}\n\n"
        f"## 课程总目标对齐\n\n{outcomes}\n"
    )


def _lab_markdown(chapter: dict[str, Any]) -> str:
    return (
        f"# {chapter['title']}实验任务书\n\n"
        f"## 实验目标\n\n{chapter['lab']}\n\n"
        "## 提交物\n\n"
        "1. 可运行代码或可验证过程记录。\n"
        "2. 输入数据、参数配置和运行环境说明。\n"
        "3. 结果截图或指标表。\n"
        "4. 误差分析、风险说明和改进建议。\n\n"
        "## 评价标准\n\n正确性 40%，过程可解释性 25%，实验复现性 20%，反思与改进 15%。\n"
    )
