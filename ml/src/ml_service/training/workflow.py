"""Leakage-safe construction and training of ranking datasets."""

from __future__ import annotations

from pathlib import Path

from ..application.profiler import StudentProfiler
from ..config import ARTIFACT_DIR, GENERATED_DATA_DIR
from ..datasets.synthetic import load_synthetic_dataset
from ..infrastructure.ranker import RankingFeatureExtractor, train_ranker_artifacts


def build_training_rows(data_dir: Path = GENERATED_DATA_DIR) -> tuple[list[tuple[dict[str, float], int]], list[str]]:
    graph, resources, students, events = load_synthetic_dataset(data_dir)
    resources_by_id = {resource.resource_id: resource for resource in resources}
    events_by_student: dict[str, list] = {}
    for event in events:
        events_by_student.setdefault(event.student_id, []).append(event)

    extractor = RankingFeatureExtractor(graph)
    profiler = StudentProfiler()
    rows: list[tuple[dict[str, float], int]] = []
    groups: list[str] = []
    for student in students:
        history = sorted(events_by_student.get(student["student_id"], []), key=lambda event: event.timestamp or 0)
        for index, target_event in enumerate(history):
            score = target_event.score or 0.0
            if target_event.liked is True or score >= 0.68:
                label = 1
            elif target_event.liked is False or score < 0.45:
                label = 0
            else:
                continue
            resource = resources_by_id.get(target_event.resource_id)
            if resource is None:
                continue

            # Excluding the target event prevents feedback features from leaking
            # the label into the corresponding training row.
            prior_history = history[:index]
            profile = profiler.build_profile(
                student_id=student["student_id"],
                diagnostics=student["diagnostics"],
                events=prior_history,
                goals=student.get("goals", []),
                preferred_styles=student.get("preferred_styles", []),
            )
            rows.append((extractor.extract(profile, resource, prior_history), label))
            groups.append(student["student_id"])
    return rows, groups


def train_from_generated_data(
    data_dir: Path = GENERATED_DATA_DIR,
    artifact_dir: Path = ARTIFACT_DIR,
) -> dict:
    rows, groups = build_training_rows(data_dir)
    return train_ranker_artifacts(rows, artifact_dir, groups=groups)
