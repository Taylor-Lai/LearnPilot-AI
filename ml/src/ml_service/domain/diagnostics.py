from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AssessmentItem:
    item_id: str
    knowledge_points: tuple[str, ...]
    difficulty: float = 0.5
    discrimination: float = 1.0
    max_score: float = 1.0
    expected_seconds: int = 120


@dataclass(frozen=True)
class AssessmentResponse:
    item_id: str
    score: float
    elapsed_seconds: int = 0
    confidence: float | None = None
    hint_count: int = 0
    attempts: int = 1


class DiagnosticEngine:
    """Evidence-weighted diagnostic scoring over raw assessment responses.

    The estimator intentionally remains deterministic and explainable for the
    competition demo. A beta prior carries previous mastery across sessions;
    item difficulty, discrimination, hints, attempts, confidence and response
    time determine how much evidence each response contributes.
    """

    def evaluate(
        self,
        items: list[AssessmentItem],
        responses: list[AssessmentResponse],
        previous_mastery: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        item_map = {item.item_id: item for item in items}
        previous_mastery = previous_mastery or {}
        alpha: dict[str, float] = {}
        beta: dict[str, float] = {}
        evidence_weight: dict[str, float] = {}
        evidence: list[dict[str, Any]] = []

        all_points = {point for item in items for point in item.knowledge_points} | set(previous_mastery)
        for point in all_points:
            prior = self._clamp(previous_mastery.get(point, 0.5))
            alpha[point] = 1.0 + prior * 4.0
            beta[point] = 1.0 + (1.0 - prior) * 4.0
            evidence_weight[point] = 0.0

        for response in responses:
            item = item_map.get(response.item_id)
            if item is None or not item.knowledge_points:
                continue
            normalized_score = self._clamp(response.score / max(item.max_score, 1e-9))
            weight = self._response_weight(item, response)
            per_point_weight = weight / len(item.knowledge_points)
            for point in item.knowledge_points:
                alpha.setdefault(point, 3.0)
                beta.setdefault(point, 3.0)
                evidence_weight.setdefault(point, 0.0)
                alpha[point] += normalized_score * per_point_weight
                beta[point] += (1.0 - normalized_score) * per_point_weight
                evidence_weight[point] += per_point_weight
            evidence.append(
                {
                    "item_id": response.item_id,
                    "knowledge_points": list(item.knowledge_points),
                    "normalized_score": round(normalized_score, 4),
                    "evidence_weight": round(weight, 4),
                    "difficulty": round(self._clamp(item.difficulty), 4),
                }
            )

        mastery = {point: round(alpha[point] / (alpha[point] + beta[point]), 4) for point in sorted(alpha)}
        confidence = {point: round(1.0 - math.exp(-evidence_weight.get(point, 0.0) / 2.5), 4) for point in mastery}
        mean_mastery = sum(mastery.values()) / max(len(mastery), 1)
        ability = math.log(max(mean_mastery, 1e-6) / max(1.0 - mean_mastery, 1e-6))
        weak_points = [point for point, score in sorted(mastery.items(), key=lambda pair: pair[1]) if score < 0.65]
        return {
            "mastery": mastery,
            "mastery_confidence": confidence,
            "ability_estimate": round(max(-4.0, min(4.0, ability)), 4),
            "weak_points": weak_points,
            "evidence": evidence,
            "unanswered_item_ids": sorted(set(item_map) - {response.item_id for response in responses}),
        }

    def _response_weight(self, item: AssessmentItem, response: AssessmentResponse) -> float:
        difficulty = 0.7 + self._clamp(item.difficulty) * 0.6
        discrimination = max(0.2, min(2.5, float(item.discrimination)))
        confidence = 0.85 if response.confidence is None else 0.7 + self._clamp(response.confidence) * 0.4
        hints = 1.0 / (1.0 + max(0, response.hint_count) * 0.22)
        attempts = 1.0 / (1.0 + max(0, response.attempts - 1) * 0.18)
        if response.elapsed_seconds <= 0 or item.expected_seconds <= 0:
            time_fit = 1.0
        else:
            ratio = response.elapsed_seconds / item.expected_seconds
            time_fit = max(0.65, 1.0 - abs(math.log(max(ratio, 1e-6))) * 0.12)
        return difficulty * discrimination * confidence * hints * attempts * time_fit

    @staticmethod
    def _clamp(value: float) -> float:
        return max(0.0, min(1.0, float(value)))
