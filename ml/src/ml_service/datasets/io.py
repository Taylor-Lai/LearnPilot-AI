"""Load datasets that conform to the LearnPilot training contract."""

from __future__ import annotations

import json
from pathlib import Path

from ..domain.models import InteractionEvent, KnowledgeNode, LearningResource

REQUIRED_FILES = ("knowledge_graph.json", "resources.json", "students.json", "events.json")


def load_dataset(
    input_dir: Path,
) -> tuple[list[KnowledgeNode], list[LearningResource], list[dict], list[InteractionEvent]]:
    missing = [name for name in REQUIRED_FILES if not (input_dir / name).is_file()]
    if missing:
        raise FileNotFoundError(f"dataset at {input_dir} is incomplete; missing: {', '.join(missing)}")

    graph = [
        KnowledgeNode(
            **{
                **item,
                "prerequisites": tuple(item.get("prerequisites", [])),
            }
        )
        for item in _read_list(input_dir / "knowledge_graph.json")
    ]
    resources = [
        LearningResource(
            **{
                **item,
                "knowledge_points": tuple(item.get("knowledge_points", [])),
                "prerequisites_covered": tuple(item.get("prerequisites_covered", [])),
                "audience": tuple(item.get("audience", [])),
                "tags": tuple(item.get("tags", [])),
            }
        )
        for item in _read_list(input_dir / "resources.json")
    ]
    students = _read_list(input_dir / "students.json")
    events = [
        InteractionEvent(
            **{
                **item,
                "knowledge_points": tuple(item.get("knowledge_points", [])),
            }
        )
        for item in _read_list(input_dir / "events.json")
    ]
    _validate_references(graph, resources, students, events)
    return graph, resources, students, events


def _read_list(path: Path) -> list[dict]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise ValueError(f"{path.name} must contain a JSON array")
    return value


def _validate_references(
    graph: list[KnowledgeNode],
    resources: list[LearningResource],
    students: list[dict],
    events: list[InteractionEvent],
) -> None:
    point_names = {node.name for node in graph}
    resource_ids = {resource.resource_id for resource in resources}
    student_ids = {str(student.get("student_id") or "") for student in students}
    if "" in student_ids or len(student_ids) != len(students):
        raise ValueError("student_id values must be present and unique")
    if len(resource_ids) != len(resources):
        raise ValueError("resource_id values must be unique")
    unknown_resource_points = {
        point for resource in resources for point in resource.knowledge_points if point not in point_names
    }
    if unknown_resource_points:
        raise ValueError(f"resources reference unknown knowledge points: {sorted(unknown_resource_points)[:5]}")
    unknown_event_resources = {event.resource_id for event in events if event.resource_id not in resource_ids}
    unknown_event_students = {event.student_id for event in events if event.student_id not in student_ids}
    if unknown_event_resources:
        raise ValueError(f"events reference unknown resources: {sorted(unknown_event_resources)[:5]}")
    if unknown_event_students:
        raise ValueError(f"events reference unknown students: {sorted(unknown_event_students)[:5]}")
