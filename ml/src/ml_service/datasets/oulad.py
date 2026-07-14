"""Convert an OULAD release into the LearnPilot ranking-data contract.

OULAD VLE clicks are treated as engagement proxies, never as direct mastery.
Protected demographic fields are intentionally excluded from emitted students.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import tempfile
import zipfile
from collections import defaultdict
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path

from ..domain.models import InteractionEvent, KnowledgeNode, LearningResource

REQUIRED_CSVS = (
    "studentInfo.csv",
    "assessments.csv",
    "studentAssessment.csv",
    "vle.csv",
    "studentVle.csv",
)
STYLE_BY_ACTIVITY = {
    "quiz": "quiz",
    "externalquiz": "quiz",
    "questionnaire": "quiz",
    "forumng": "example",
    "glossary": "text",
    "homepage": "text",
    "oucontent": "text",
    "page": "text",
    "resource": "text",
    "subpage": "text",
    "url": "text",
    "dataplus": "project",
    "dualpane": "example",
    "folder": "text",
    "htmlactivity": "example",
    "sharedsubpage": "text",
    "repeatactivity": "example",
}


def prepare_oulad_dataset(
    source: Path,
    output_dir: Path,
    *,
    max_events: int = 200_000,
    max_events_per_student: int = 300,
) -> dict[str, object]:
    if max_events < 1 or max_events_per_student < 1:
        raise ValueError("event limits must be positive")
    with _source_directory(source) as source_dir:
        csvs = _find_csvs(source_dir)
        assessment_modules, mastery = _load_assessment_mastery(csvs)
        raw_students = _load_students(csvs["studentInfo.csv"], mastery)
        resources_by_key, graph = _load_resources(csvs["vle.csv"])
        events, used_students, used_resources = _load_events(
            csvs["studentVle.csv"],
            resources_by_key,
            max_events=max_events,
            max_events_per_student=max_events_per_student,
        )

    students = [student for key, student in raw_students.items() if key in used_students]
    missing_students = used_students - raw_students.keys()
    students.extend(_minimal_student(key) for key in sorted(missing_students))
    resources = [resource for key, resource in resources_by_key.items() if key in used_resources]
    used_points = {point for resource in resources for point in resource.knowledge_points}
    used_points.update(f"{point.split(':', 1)[0]}:module" for point in tuple(used_points))
    graph = [node for node in graph if node.name in used_points]
    if not students or not resources or not events:
        raise ValueError("OULAD conversion produced an empty dataset")

    output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(output_dir / "knowledge_graph.json", [asdict(node) for node in graph])
    _write_json(output_dir / "resources.json", [asdict(resource) for resource in resources])
    _write_json(output_dir / "students.json", students)
    _write_json(output_dir / "events.json", [asdict(event) for event in events])
    manifest: dict[str, object] = {
        "schema_version": "1.0",
        "dataset": "Open University Learning Analytics Dataset (OULAD)",
        "source": "https://analyse.kmi.open.ac.uk/open_dataset",
        "license": "CC BY 4.0",
        "purpose": "resource-ranking engagement proxy",
        "label_semantics": "log-scaled VLE clicks; not knowledge mastery",
        "dwell_semantics": "sum_click * 90 seconds capped at 3600; not observed time",
        "protected_attributes_used": False,
        "student_identifier": "SHA-256 pseudonym truncated to 20 hex characters",
        "selection": {
            "order": "source CSV order",
            "max_events": max_events,
            "max_events_per_student": max_events_per_student,
            "limitation": "bounded development subset; report limits with metrics",
        },
        "assessment_modules": len(assessment_modules),
        "counts": {
            "knowledge_points": len(graph),
            "resources": len(resources),
            "students": len(students),
            "events": len(events),
        },
    }
    _write_json(output_dir / "dataset_manifest.json", manifest)
    return manifest


def _load_assessment_mastery(csvs: dict[str, Path]) -> tuple[set[str], dict[tuple[str, str, str], float]]:
    assessment_lookup: dict[str, tuple[str, str]] = {}
    with csvs["assessments.csv"].open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            assessment_lookup[row["id_assessment"]] = (row["code_module"], row["code_presentation"])
    totals: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    with csvs["studentAssessment.csv"].open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            module = assessment_lookup.get(row["id_assessment"])
            score = _float(row.get("score"))
            if module is None or score is None:
                continue
            totals[(module[0], module[1], row["id_student"])].append(max(0.0, min(1.0, score / 100)))
    mastery = {key: round(sum(values) / len(values), 4) for key, values in totals.items()}
    return {f"{module}:{presentation}" for module, presentation in assessment_lookup.values()}, mastery


def _load_students(path: Path, mastery: dict[tuple[str, str, str], float]) -> dict[tuple[str, str, str], dict]:
    students: dict[tuple[str, str, str], dict] = {}
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            key = (row["code_module"], row["code_presentation"], row["id_student"])
            score = mastery.get(key, 0.5)
            previous_attempts = int(row.get("num_of_prev_attempts") or 0)
            students[key] = {
                "student_id": _student_id(key),
                "goals": [f"完成 OULAD {key[0]} {key[1]} 模块"],
                "preferred_styles": [],
                "diagnostics": {f"{key[0]}:module": score},
                "learning_stage": "foundation" if previous_attempts > 0 or score < 0.45 else "practice",
            }
    return students


def _load_resources(path: Path) -> tuple[dict[tuple[str, str, str], LearningResource], list[KnowledgeNode]]:
    resources: dict[tuple[str, str, str], LearningResource] = {}
    point_names: set[str] = set()
    module_names: set[str] = set()
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            key = (row["code_module"], row["code_presentation"], row["id_site"])
            activity = (row.get("activity_type") or "resource").strip().lower()
            point = f"{key[0]}:{activity}"
            module_names.add(f"{key[0]}:module")
            point_names.add(point)
            resources[key] = LearningResource(
                resource_id=_resource_id(key),
                title=f"OULAD {key[0]} {activity} {key[2]}",
                knowledge_points=(point,),
                difficulty=0.5,
                style=STYLE_BY_ACTIVITY.get(activity, "text"),  # type: ignore[arg-type]
                estimated_minutes=20,
                quality=0.8,
                content=f"OULAD VLE activity metadata: module={key[0]}, type={activity}.",
                audience=("higher-education",),
                tags=("oulad", key[0], activity),
            )
    graph = [KnowledgeNode(name=name, importance=1.1) for name in sorted(module_names)]
    graph.extend(
        KnowledgeNode(name=name, prerequisites=(f"{name.split(':', 1)[0]}:module",), importance=1.0)
        for name in sorted(point_names)
    )
    return resources, graph


def _load_events(
    path: Path,
    resources: dict[tuple[str, str, str], LearningResource],
    *,
    max_events: int,
    max_events_per_student: int,
) -> tuple[list[InteractionEvent], set[tuple[str, str, str]], set[tuple[str, str, str]]]:
    events: list[InteractionEvent] = []
    per_student: dict[tuple[str, str, str], int] = defaultdict(int)
    used_students: set[tuple[str, str, str]] = set()
    used_resources: set[tuple[str, str, str]] = set()
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            student_key = (row["code_module"], row["code_presentation"], row["id_student"])
            resource_key = (row["code_module"], row["code_presentation"], row["id_site"])
            resource = resources.get(resource_key)
            if resource is None or per_student[student_key] >= max_events_per_student:
                continue
            clicks = max(0, int(row.get("sum_click") or 0))
            if clicks == 0:
                continue
            score = min(1.0, math.log1p(clicks) / math.log1p(25))
            timestamp = int(row.get("date") or 0)
            events.append(
                InteractionEvent(
                    student_id=_student_id(student_key),
                    resource_id=resource.resource_id,
                    knowledge_points=resource.knowledge_points,
                    score=round(score, 4),
                    completed=clicks >= 3,
                    dwell_seconds=min(3600, clicks * 90),
                    liked=None,
                    timestamp=timestamp,
                    event_type="learning",
                    attempts=1,
                    hint_count=0,
                    confidence=None,
                    resource_style=resource.style,
                    session_id=f"{_student_id(student_key)}:{timestamp}",
                )
            )
            per_student[student_key] += 1
            used_students.add(student_key)
            used_resources.add(resource_key)
            if len(events) >= max_events:
                break
    return events, used_students, used_resources


def _minimal_student(key: tuple[str, str, str]) -> dict:
    return {
        "student_id": _student_id(key),
        "goals": [f"完成 OULAD {key[0]} {key[1]} 模块"],
        "preferred_styles": [],
        "diagnostics": {f"{key[0]}:module": 0.5},
        "learning_stage": "foundation",
    }


def _student_id(key: tuple[str, str, str]) -> str:
    digest = hashlib.sha256("|".join(key).encode("utf-8")).hexdigest()[:20]
    return f"oulad_{digest}"


def _resource_id(key: tuple[str, str, str]) -> str:
    return "oulad_" + "_".join(key)


def _float(value: str | None) -> float | None:
    try:
        return float(value) if value not in (None, "") else None
    except ValueError:
        return None


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def _find_csvs(root: Path) -> dict[str, Path]:
    found: dict[str, Path] = {}
    for name in REQUIRED_CSVS:
        matches = list(root.rglob(name))
        if len(matches) != 1:
            raise FileNotFoundError(f"expected exactly one {name} under {root}, found {len(matches)}")
        found[name] = matches[0]
    return found


@contextmanager
def _source_directory(source: Path) -> Iterator[Path]:
    source = source.expanduser().resolve()
    if source.is_dir():
        yield source
        return
    if not source.is_file() or source.suffix.lower() != ".zip":
        raise FileNotFoundError(f"OULAD source must be a directory or ZIP file: {source}")
    with tempfile.TemporaryDirectory(prefix="learnpilot-oulad-") as temp:
        destination = Path(temp).resolve()
        with zipfile.ZipFile(source) as archive:
            for member in archive.infolist():
                target = (destination / member.filename).resolve()
                if destination not in target.parents and target != destination:
                    raise ValueError(f"unsafe ZIP member: {member.filename}")
            archive.extractall(destination)
        yield destination
