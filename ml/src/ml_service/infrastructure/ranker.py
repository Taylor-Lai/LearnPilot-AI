from __future__ import annotations

import hashlib
import json
import math
import os
import random
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ..application.recommender import ResourceRecommender
from ..config import ARTIFACT_DIR
from ..domain.models import InteractionEvent, KnowledgeNode, LearningResource, Recommendation, StudentProfile

FEATURE_VERSION = "learning-ranker-v2"
DEFAULT_ARTIFACT_DIR = ARTIFACT_DIR
os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")


@dataclass(frozen=True)
class RankerMeta:
    model_type: str
    feature_version: str
    trained_at: str | None
    samples: int
    metrics: dict[str, float]
    fallback_reason: str | None = None
    train_samples: int = 0
    validation_samples: int = 0
    dataset_fingerprint: str | None = None


class RankingFeatureExtractor:
    def __init__(self, knowledge_graph: list[KnowledgeNode] | None = None) -> None:
        self.knowledge_graph = {node.name: node for node in knowledge_graph or []}

    def extract(
        self,
        profile: StudentProfile,
        resource: LearningResource,
        history: list[InteractionEvent] | None = None,
    ) -> dict[str, float]:
        history = history or []
        weakness = self._weakness(profile, resource)
        difficulty_gap = abs(profile.target_difficulty - resource.difficulty)
        style_preference = (
            1.0
            if resource.style in profile.preferred_styles
            else profile.cognitive_preferences.get(resource.style, 0.0)
        )
        pace = max(10, profile.recommended_pace_minutes)
        duration_fit = max(0.0, 1.0 - abs(resource.estimated_minutes - pace) / max(pace, 20))
        graph_distance = self._graph_distance(resource.knowledge_points, profile.weak_points)
        positive_feedback = self._feedback_ratio(history, resource, liked=True)
        negative_feedback = self._feedback_ratio(history, resource, liked=False)
        novelty = 0.0 if any(event.resource_id == resource.resource_id for event in history) else 1.0
        confidence = self._mastery_confidence(profile, resource)
        return {
            "weakness": round(weakness, 6),
            "difficulty_fit": round(1.0 - difficulty_gap, 6),
            "style_preference": style_preference,
            "quality": resource.quality,
            "duration_fit": duration_fit,
            "graph_distance_fit": round(1.0 / (1.0 + graph_distance), 6),
            "positive_feedback": positive_feedback,
            "negative_feedback": negative_feedback,
            "novelty": novelty,
            "engagement": profile.engagement_score,
            "forgetting_risk": profile.forgetting_risk,
            "mastery_confidence": round(confidence, 6),
        }

    def feature_names(self) -> list[str]:
        return [
            "weakness",
            "difficulty_fit",
            "style_preference",
            "quality",
            "duration_fit",
            "graph_distance_fit",
            "positive_feedback",
            "negative_feedback",
            "novelty",
            "engagement",
            "forgetting_risk",
            "mastery_confidence",
        ]

    def _weakness(self, profile: StudentProfile, resource: LearningResource) -> float:
        if not resource.knowledge_points:
            return 0.0
        return sum(1.0 - profile.mastery.get(point, 0.5) for point in resource.knowledge_points) / len(
            resource.knowledge_points
        )

    def _graph_distance(self, points: tuple[str, ...], weak_points: list[str]) -> float:
        if not weak_points:
            return 1.0
        if set(points) & set(weak_points):
            return 0.0
        prerequisites = set()
        for point in points:
            prerequisites.update(self.knowledge_graph.get(point, KnowledgeNode(point)).prerequisites)
        return 1.0 if prerequisites & set(weak_points) else 2.0

    def _feedback_ratio(self, history: list[InteractionEvent], resource: LearningResource, liked: bool) -> float:
        related = [
            event
            for event in history
            if event.resource_id == resource.resource_id or set(event.knowledge_points) & set(resource.knowledge_points)
        ]
        if not related:
            return 0.0
        hits = [event for event in related if event.liked is liked or ((event.score or 0.0) >= 0.7) is liked]
        return round(len(hits) / len(related), 6)

    def _mastery_confidence(self, profile: StudentProfile, resource: LearningResource) -> float:
        if not resource.knowledge_points:
            return 0.0
        values = [profile.mastery_confidence.get(point, 0.25) for point in resource.knowledge_points]
        return sum(values) / len(values)


class TrainableRanker:
    def __init__(
        self,
        artifact_dir: Path | None = None,
        knowledge_graph: list[KnowledgeNode] | None = None,
    ) -> None:
        self.artifact_dir = artifact_dir or DEFAULT_ARTIFACT_DIR
        self.extractor = RankingFeatureExtractor(knowledge_graph)
        self.model: Any | None = None
        self.weights: dict[str, float] | None = None
        self.meta = RankerMeta(
            model_type="rule",
            feature_version=FEATURE_VERSION,
            trained_at=None,
            samples=0,
            metrics={},
            fallback_reason="no trained artifact loaded",
        )
        self._load()

    def recommend(
        self,
        profile: StudentProfile,
        resources: list[LearningResource],
        top_k: int,
        history: list[InteractionEvent] | None = None,
    ) -> list[Recommendation]:
        if not resources:
            return []
        scored = []
        rule_recommender = ResourceRecommender()
        for resource in resources:
            features = self.extractor.extract(profile, resource, history)
            model_score = self._predict_score(features)
            rule_score = rule_recommender.score_resource(profile, resource).score
            score = self._blend_score(model_score, rule_score)
            reasons = (
                f"模型评分 {score:.3f}",
                f"薄弱度 {features['weakness']:.2f}",
                f"难度适配 {features['difficulty_fit']:.2f}",
            )
            scored.append(Recommendation(resource=resource, score=round(score, 4), reasons=reasons, features=features))
        scored.sort(key=lambda item: item.score, reverse=True)
        return ResourceRecommender()._diversify(scored, top_k)

    def status(self) -> dict:
        return asdict(self.meta)

    def _predict_score(self, features: dict[str, float]) -> float:
        if self.model is not None:
            try:
                values = _feature_frame([features], self.extractor.feature_names())
                if hasattr(self.model, "predict_proba"):
                    return float(self.model.predict_proba(values)[0][1])
                return float(self.model.predict(values)[0])
            except Exception:
                pass
        if self.weights:
            bias = self.weights.get("bias", 0.0)
            raw = bias + sum(self.weights.get(name, 0.0) * features[name] for name in self.extractor.feature_names())
            return 1.0 / (1.0 + math.exp(-raw))
        return (
            features["weakness"] * 0.32
            + features["difficulty_fit"] * 0.18
            + features["style_preference"] * 0.12
            + features["quality"] * 0.12
            + features["duration_fit"] * 0.06
            + features["graph_distance_fit"] * 0.08
            + features["positive_feedback"] * 0.08
            - features["negative_feedback"] * 0.06
            + features["novelty"] * 0.04
            + features["mastery_confidence"] * 0.03
        )

    def _blend_score(self, model_score: float, rule_score: float) -> float:
        if self.meta.model_type == "lightgbm-classifier":
            return model_score * 0.25 + rule_score * 0.75
        if self.meta.model_type.startswith("sklearn"):
            return model_score * 0.2 + rule_score * 0.8
        if self.meta.model_type == "weighted-fallback":
            return model_score * 0.15 + rule_score * 0.85
        return rule_score

    def _load(self) -> None:
        meta_path = self.artifact_dir / "ranker_meta.json"
        weights_path = self.artifact_dir / "ranker_weights.json"
        model_path = self.artifact_dir / "ranker_model.joblib"
        if meta_path.exists():
            data = json.loads(meta_path.read_text(encoding="utf-8"))
            self.meta = RankerMeta(**data)
            if self.meta.feature_version != FEATURE_VERSION:
                self.meta = RankerMeta(
                    model_type="rule",
                    feature_version=FEATURE_VERSION,
                    trained_at=None,
                    samples=0,
                    metrics={},
                    fallback_reason=f"artifact feature version mismatch: {self.meta.feature_version}",
                )
                return
        if model_path.exists():
            try:
                import joblib

                self.model = joblib.load(model_path)
                return
            except Exception as exc:
                self.meta = RankerMeta(**{**asdict(self.meta), "fallback_reason": f"joblib model load failed: {exc}"})
        if weights_path.exists():
            self.weights = json.loads(weights_path.read_text(encoding="utf-8"))


def train_ranker_artifacts(
    rows: list[tuple[dict[str, float], int]],
    artifact_dir: Path | None = None,
    groups: list[str] | None = None,
    validation_fraction: float = 0.2,
    random_seed: int = 42,
) -> dict:
    if len(rows) < 4:
        raise ValueError("at least four labeled samples are required to train the ranker")
    if groups is not None and len(groups) != len(rows):
        raise ValueError("groups length must match rows length")
    artifact_dir = artifact_dir or DEFAULT_ARTIFACT_DIR
    artifact_dir.mkdir(parents=True, exist_ok=True)
    feature_names = RankingFeatureExtractor().feature_names()
    train_indices, validation_indices = _split_indices(rows, groups, validation_fraction, random_seed)
    train_rows = [rows[index] for index in train_indices]
    validation_rows = [rows[index] for index in validation_indices]
    x_train = _feature_frame([features for features, _ in train_rows], feature_names)
    y_train = [label for _, label in train_rows]
    x_validation = _feature_frame([features for features, _ in validation_rows], feature_names)
    y_validation = [label for _, label in validation_rows]
    model_type = "sklearn-logistic"
    metrics: dict[str, float]
    fallback_reason = None

    try:
        try:
            from lightgbm import LGBMClassifier

            model = LGBMClassifier(n_estimators=80, learning_rate=0.05, random_state=42)
            model_type = "lightgbm-classifier"
        except Exception as exc:
            fallback_reason = f"lightgbm unavailable: {exc}"
            from sklearn.tree import DecisionTreeClassifier

            model = DecisionTreeClassifier(max_depth=6, min_samples_leaf=8, random_state=42)
            model_type = "sklearn-decision-tree"
        model.fit(x_train, y_train)
        train_predictions = (
            model.predict_proba(x_train)[:, 1] if hasattr(model, "predict_proba") else model.predict(x_train)
        )
        validation_predictions = (
            model.predict_proba(x_validation)[:, 1] if hasattr(model, "predict_proba") else model.predict(x_validation)
        )
        metrics = _training_metrics(y_train, train_predictions, y_validation, validation_predictions)
        import joblib

        joblib.dump(model, artifact_dir / "ranker_model.joblib")
    except Exception as exc:
        model_type = "weighted-fallback"
        fallback_reason = f"training failed: {exc}"
        weights = _fit_simple_weights(train_rows, feature_names)
        train_predictions = [_weighted_prediction(weights, features, feature_names) for features, _ in train_rows]
        validation_predictions = [
            _weighted_prediction(weights, features, feature_names) for features, _ in validation_rows
        ]
        metrics = _training_metrics(y_train, train_predictions, y_validation, validation_predictions)
        (artifact_dir / "ranker_weights.json").write_text(json.dumps(weights, indent=2), encoding="utf-8")

    meta = RankerMeta(
        model_type=model_type,
        feature_version=FEATURE_VERSION,
        trained_at=datetime.now(UTC).isoformat(),
        samples=len(rows),
        metrics=metrics,
        fallback_reason=fallback_reason,
        train_samples=len(train_rows),
        validation_samples=len(validation_rows),
        dataset_fingerprint=_dataset_fingerprint(rows, feature_names),
    )
    (artifact_dir / "ranker_meta.json").write_text(
        json.dumps(asdict(meta), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return asdict(meta)


def _split_indices(
    rows: list[tuple[dict[str, float], int]],
    groups: list[str] | None,
    validation_fraction: float,
    seed: int,
) -> tuple[list[int], list[int]]:
    fraction = max(0.1, min(0.4, validation_fraction))
    rng = random.Random(seed)
    if groups:
        unique_groups = sorted(set(groups))
        rng.shuffle(unique_groups)
        validation_group_count = max(1, round(len(unique_groups) * fraction))
        validation_groups = set(unique_groups[:validation_group_count])
        validation = [index for index, group in enumerate(groups) if group in validation_groups]
        train = [index for index, group in enumerate(groups) if group not in validation_groups]
    else:
        by_label: dict[int, list[int]] = {}
        for index, (_, label) in enumerate(rows):
            by_label.setdefault(label, []).append(index)
        train, validation = [], []
        for indices in by_label.values():
            rng.shuffle(indices)
            validation_count = max(1, round(len(indices) * fraction)) if len(indices) > 1 else 0
            validation.extend(indices[:validation_count])
            train.extend(indices[validation_count:])
    if not train or not validation:
        indices = list(range(len(rows)))
        rng.shuffle(indices)
        boundary = max(1, min(len(indices) - 1, round(len(indices) * (1.0 - fraction))))
        train, validation = indices[:boundary], indices[boundary:]
    return sorted(train), sorted(validation)


def _training_metrics(y_train, train_scores, y_validation, validation_scores) -> dict[str, float]:
    train = _binary_metrics(list(y_train), [float(item) for item in train_scores])
    validation = _binary_metrics(list(y_validation), [float(item) for item in validation_scores])
    return {
        "train_accuracy": train["accuracy"],
        "train_auc": train["auc_proxy"],
        "validation_accuracy": validation["accuracy"],
        "validation_auc": validation["auc_proxy"],
        "generalization_gap": round(train["auc_proxy"] - validation["auc_proxy"], 4),
    }


def _weighted_prediction(weights, features, feature_names) -> float:
    return _sigmoid(weights.get("bias", 0.0) + sum(weights.get(name, 0.0) * features[name] for name in feature_names))


def _dataset_fingerprint(rows: list[tuple[dict[str, float], int]], feature_names: list[str]) -> str:
    payload = [([round(features[name], 8) for name in feature_names], label) for features, label in rows]
    return hashlib.sha256(json.dumps(payload, separators=(",", ":")).encode("utf-8")).hexdigest()[:16]


def _binary_metrics(y: list[int], scores: list[float]) -> dict[str, float]:
    if not y:
        return {"accuracy": 0.0, "auc_proxy": 0.0}
    predictions = [1 if score >= 0.5 else 0 for score in scores]
    accuracy = sum(int(pred == label) for pred, label in zip(predictions, y, strict=True)) / len(y)
    positives = [score for score, label in zip(scores, y, strict=True) if label == 1]
    negatives = [score for score, label in zip(scores, y, strict=True) if label == 0]
    if not positives or not negatives:
        auc_proxy = accuracy
    else:
        pairs = [(pos > neg) + 0.5 * (pos == neg) for pos in positives for neg in negatives]
        auc_proxy = sum(pairs) / len(pairs)
    return {"accuracy": round(accuracy, 4), "auc_proxy": round(auc_proxy, 4)}


def _fit_simple_weights(rows: list[tuple[dict[str, float], int]], feature_names: list[str]) -> dict[str, float]:
    weights = {"bias": -0.2}
    for name in feature_names:
        pos = [features[name] for features, label in rows if label == 1]
        neg = [features[name] for features, label in rows if label == 0]
        weights[name] = (sum(pos) / max(len(pos), 1)) - (sum(neg) / max(len(neg), 1))
    return weights


def _sigmoid(value: float) -> float:
    return 1.0 / (1.0 + math.exp(-value))


def _feature_frame(rows: list[dict[str, float]], feature_names: list[str]):
    values = [[features[name] for name in feature_names] for features in rows]
    try:
        import pandas as pd

        return pd.DataFrame(values, columns=feature_names)
    except Exception:
        return values
