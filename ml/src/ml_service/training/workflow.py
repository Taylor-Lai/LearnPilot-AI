"""Leakage-safe construction and training of ranking datasets."""

from __future__ import annotations

import json
import os
from pathlib import Path

from ..application.profiler import StudentProfiler
from ..config import ARTIFACT_DIR, GENERATED_DATA_DIR, TRAINING_DATA_DIR
from ..datasets.io import load_dataset
from ..datasets.synthetic import write_synthetic_dataset
from ..infrastructure.ranker import RankingFeatureExtractor, train_ranker_artifacts

DEFAULT_MAX_EVENTS_PER_STUDENT = 80
DEFAULT_HISTORY_WINDOW = 50


def build_training_rows(
    data_dir: Path = TRAINING_DATA_DIR,
    *,
    max_events_per_student: int | None = None,
    history_window: int | None = None,
) -> tuple[list[tuple[dict[str, float], int]], list[str]]:
    max_events_per_student = max_events_per_student or int(
        os.getenv("LEARNPILOT_MAX_TRAINING_EVENTS_PER_STUDENT", str(DEFAULT_MAX_EVENTS_PER_STUDENT))
    )
    history_window = history_window or int(os.getenv("LEARNPILOT_TRAINING_HISTORY_WINDOW", str(DEFAULT_HISTORY_WINDOW)))
    if max_events_per_student < 2 or history_window < 1:
        raise ValueError("training event limit must be >= 2 and history window must be >= 1")
    if data_dir == GENERATED_DATA_DIR and not (data_dir / "knowledge_graph.json").is_file():
        write_synthetic_dataset(data_dir)
    graph, resources, students, events = load_dataset(data_dir)
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
        targets = _bounded_targets(history, max_events_per_student)
        for index, label in targets:
            target_event = history[index]
            resource = resources_by_id.get(target_event.resource_id)
            if resource is None:
                continue

            # Excluding the target event prevents feedback features from leaking
            # the label into the corresponding training row. A bounded recent
            # window keeps construction linear enough for real behavior logs.
            prior_history = history[max(0, index - history_window) : index]
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


def _bounded_targets(history: list, limit: int) -> list[tuple[int, int]]:
    by_label: dict[int, list[int]] = {0: [], 1: []}
    for index, event in enumerate(history):
        score = event.score or 0.0
        if event.liked is True or score >= 0.68:
            by_label[1].append(index)
        elif event.liked is False or score < 0.45:
            by_label[0].append(index)
    if sum(len(indices) for indices in by_label.values()) <= limit:
        return sorted((index, label) for label, indices in by_label.items() for index in indices)

    selected: list[tuple[int, int]] = []
    per_label = max(1, limit // 2)
    for label, indices in by_label.items():
        selected.extend((index, label) for index in _evenly_spaced(indices, min(per_label, len(indices))))
    if len(selected) < limit:
        already = {index for index, _ in selected}
        remaining = [
            (index, label)
            for label, indices in by_label.items()
            for index in indices
            if index not in already
        ]
        selected.extend(_evenly_spaced(remaining, min(limit - len(selected), len(remaining))))
    return sorted(selected[:limit])


def _evenly_spaced(values: list, count: int) -> list:
    if count <= 0:
        return []
    if count >= len(values):
        return list(values)
    if count == 1:
        return [values[len(values) // 2]]
    positions = [round(index * (len(values) - 1) / (count - 1)) for index in range(count)]
    return [values[position] for position in positions]


def train_from_data(
    data_dir: Path = TRAINING_DATA_DIR,
    artifact_dir: Path = ARTIFACT_DIR,
) -> dict:
    rows, groups = build_training_rows(data_dir)
    manifest_path = data_dir / "dataset_manifest.json"
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        dataset_meta = {
            "dataset": str(manifest.get("dataset", "unknown")),
            "label_semantics": str(manifest.get("label_semantics", "unspecified")),
        }
    else:
        dataset_meta = {
            "dataset": "unknown legacy dataset",
            "label_semantics": "unspecified",
        }
    result = train_ranker_artifacts(rows, artifact_dir, groups=groups, dataset_meta=dataset_meta)
    result["training_data_dir"] = str(data_dir)
    return result


# Backward-compatible name for existing local scripts.
train_from_generated_data = train_from_data
