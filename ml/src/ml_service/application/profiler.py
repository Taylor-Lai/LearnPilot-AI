from __future__ import annotations

import math
from collections import Counter, defaultdict

from ..domain.models import InteractionEvent, StudentProfile


class StudentProfiler:
    """Builds a compact student profile from diagnostics and behavior logs."""

    def build_profile(
        self,
        student_id: str,
        diagnostics: dict[str, float],
        events: list[InteractionEvent] | None = None,
        goals: list[str] | None = None,
        preferred_styles: list[str] | None = None,
        previous_mastery: dict[str, float] | None = None,
    ) -> StudentProfile:
        mastery = {point: self._clamp(value) for point, value in (previous_mastery or {}).items()}
        for point, value in diagnostics.items():
            previous = mastery.get(point)
            mastery[point] = self._clamp(value if previous is None else previous * 0.65 + value * 0.35)
        events = events or []

        point_evidence: Counter[str] = Counter()
        for index, event in enumerate(events):
            signal = self._event_signal(event)
            recency = math.exp(-0.08 * (len(events) - index - 1))
            for point in event.knowledge_points:
                previous = mastery.get(point, 0.5)
                update_rate = 0.12 + 0.18 * recency
                mastery[point] = self._clamp(previous * (1.0 - update_rate) + signal * update_rate)
                point_evidence[point] += 1

        average_mastery = sum(mastery.values()) / max(len(mastery), 1)
        risk_level = "high" if average_mastery < 0.45 else "medium" if average_mastery < 0.7 else "low"
        target_difficulty = self._clamp(average_mastery + 0.12, lower=0.25, upper=0.85)
        weak_points = [point for point, _ in sorted(mastery.items(), key=lambda item: item[1]) if mastery[point] < 0.7]
        recent_focus = self._recent_focus(events, weak_points)
        engagement_score = self._engagement(events)
        learning_velocity = self._learning_velocity(events)
        stability_score = self._stability(events)
        preference_confidence = self._preference_confidence(events, preferred_styles or [])
        forgetting_risk = self._forgetting_risk(average_mastery, stability_score, engagement_score)
        learning_stage = self._learning_stage(average_mastery, weak_points, events)
        mastery_confidence = {
            point: round(self._clamp(0.25 + point_evidence[point] * 0.16 + (0.2 if point in diagnostics else 0.0)), 4)
            for point in mastery
        }
        cognitive_preferences = self._cognitive_preferences(events, preferred_styles or [])
        ability_estimate = self._ability_estimate(average_mastery)
        recommended_pace_minutes = self._recommended_pace(events, engagement_score, risk_level)

        return StudentProfile(
            student_id=student_id,
            mastery=mastery,
            goals=goals or [],
            preferred_styles=list(preferred_styles or []),
            target_difficulty=target_difficulty,
            risk_level=risk_level,
            weak_points=weak_points,
            recent_focus=recent_focus,
            learning_velocity=learning_velocity,
            engagement_score=engagement_score,
            stability_score=stability_score,
            preference_confidence=preference_confidence,
            forgetting_risk=forgetting_risk,
            learning_stage=learning_stage,
            mastery_confidence=mastery_confidence,
            cognitive_preferences=cognitive_preferences,
            ability_estimate=ability_estimate,
            recommended_pace_minutes=recommended_pace_minutes,
        )

    def _event_signal(self, event: InteractionEvent) -> float:
        score_signal = 0.5 if event.score is None else self._clamp(event.score)
        completion_signal = 0.75 if event.completed else 0.35
        dwell_signal = self._clamp(event.dwell_seconds / 900)
        like_signal = 0.6 if event.liked is None else 0.8 if event.liked else 0.25
        return score_signal * 0.5 + completion_signal * 0.25 + dwell_signal * 0.15 + like_signal * 0.1

    def _clamp(self, value: float, lower: float = 0.0, upper: float = 1.0) -> float:
        return max(lower, min(upper, float(value)))

    def _recent_focus(self, events: list[InteractionEvent], weak_points: list[str]) -> list[str]:
        if not events:
            return weak_points[:3]
        counts: Counter[str] = Counter()
        for event in events[-8:]:
            for point in event.knowledge_points:
                counts[point] += 1
        ordered = [point for point, _ in counts.most_common()]
        return (ordered + [point for point in weak_points if point not in ordered])[:3]

    def _engagement(self, events: list[InteractionEvent]) -> float:
        if not events:
            return 0.5
        signals = []
        for event in events:
            completion = 1.0 if event.completed else 0.35
            dwell = self._clamp(event.dwell_seconds / 900)
            liked = 0.6 if event.liked is None else 1.0 if event.liked else 0.2
            signals.append(completion * 0.45 + dwell * 0.35 + liked * 0.2)
        return round(sum(signals) / len(signals), 4)

    def _learning_velocity(self, events: list[InteractionEvent]) -> float:
        scored = [event.score for event in events if event.score is not None]
        if not scored:
            return 0.5
        recent = scored[-3:]
        return round(self._clamp(sum(recent) / len(recent)), 4)

    def _stability(self, events: list[InteractionEvent]) -> float:
        scored = [float(event.score) for event in events if event.score is not None]
        if len(scored) < 2:
            return 0.5
        mean = sum(scored) / len(scored)
        variance = sum((score - mean) ** 2 for score in scored) / len(scored)
        return round(self._clamp(1.0 - variance * 4), 4)

    def _preference_confidence(self, events: list[InteractionEvent], preferred_styles: list[str]) -> float:
        if not preferred_styles:
            return 0.0
        evidence = len([event for event in events if event.liked is not None or event.completed])
        return round(self._clamp(0.35 + evidence / 12), 4)

    def _forgetting_risk(self, average_mastery: float, stability_score: float, engagement_score: float) -> float:
        risk = (1.0 - average_mastery) * 0.5 + (1.0 - stability_score) * 0.3 + (1.0 - engagement_score) * 0.2
        return round(self._clamp(risk), 4)

    def _learning_stage(self, average_mastery: float, weak_points: list[str], events: list[InteractionEvent]) -> str:
        project_events = [event for event in events if "项目实践" in event.knowledge_points]
        if project_events and average_mastery >= 0.72:
            return "project"
        if average_mastery >= 0.68 and len(weak_points) <= 3:
            return "integration"
        if average_mastery >= 0.45:
            return "practice"
        return "foundation"

    def _cognitive_preferences(self, events: list[InteractionEvent], declared_styles: list[str]) -> dict[str, float]:
        scores: defaultdict[str, float] = defaultdict(float)
        for style in declared_styles:
            scores[str(style)] += 1.0
        for event in events:
            if not event.resource_style:
                continue
            signal = 0.4
            signal += 0.35 if event.completed else 0.0
            signal += 0.35 if event.liked is True else -0.25 if event.liked is False else 0.0
            signal += 0.2 * ((event.score or 0.5) - 0.5)
            scores[event.resource_style] += max(0.0, signal)
        total = sum(scores.values())
        if total <= 0:
            return {}
        return {style: round(value / total, 4) for style, value in sorted(scores.items())}

    def _ability_estimate(self, average_mastery: float) -> float:
        probability = max(1e-6, min(1.0 - 1e-6, average_mastery))
        return round(max(-4.0, min(4.0, math.log(probability / (1.0 - probability)))), 4)

    def _recommended_pace(self, events: list[InteractionEvent], engagement: float, risk_level: str) -> int:
        dwell_minutes = sorted(event.dwell_seconds / 60 for event in events if event.dwell_seconds > 0)
        if dwell_minutes:
            middle = len(dwell_minutes) // 2
            median = (
                dwell_minutes[middle] if len(dwell_minutes) % 2 else sum(dwell_minutes[middle - 1 : middle + 1]) / 2
            )
        else:
            median = 25.0
        risk_factor = 0.8 if risk_level == "high" else 1.0 if risk_level == "medium" else 1.15
        engagement_factor = 0.85 + engagement * 0.3
        return int(round(max(10.0, min(60.0, median * risk_factor * engagement_factor))))
