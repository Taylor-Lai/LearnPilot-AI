from __future__ import annotations

from ..datasets.catalog import DEFAULT_KNOWLEDGE_GRAPH, DEFAULT_RESOURCES
from ..domain.diagnostics import AssessmentItem, AssessmentResponse, DiagnosticEngine
from ..domain.models import InteractionEvent, KnowledgeNode, LearningResource
from .agents import (
    DiagnosisAgent,
    GenerationEvaluationAgent,
    PlanningAgent,
    ProfileAgent,
    RecommendationAgent,
    TutoringAgent,
)


class LearningMLPipeline:
    def __init__(
        self,
        resources: list[LearningResource] | None = None,
        knowledge_graph: list[KnowledgeNode] | None = None,
    ) -> None:
        self.resources = DEFAULT_RESOURCES if resources is None else resources
        self.knowledge_graph = DEFAULT_KNOWLEDGE_GRAPH if knowledge_graph is None else knowledge_graph
        self.diagnosis_agent = DiagnosisAgent()
        self.profile_agent = ProfileAgent()
        self.recommendation_agent = RecommendationAgent()
        self.recommendation_agent.ranker.extractor.knowledge_graph = {node.name: node for node in self.knowledge_graph}
        self.planning_agent = PlanningAgent()
        self.generation_agent = GenerationEvaluationAgent()
        self.tutoring_agent = TutoringAgent()
        self.diagnostic_engine = DiagnosticEngine()

    def run_learning_loop(
        self,
        student_id: str,
        diagnostics: dict[str, float],
        events: list[InteractionEvent] | None = None,
        goals: list[str] | None = None,
        preferred_styles: list[str] | None = None,
        previous_mastery: dict[str, float] | None = None,
        top_k: int = 6,
    ) -> dict:
        normalized_diagnostics, diagnosis_trace = self.diagnosis_agent.analyze(diagnostics)
        profile, profile_trace = self.profile_agent.update(
            student_id=student_id,
            diagnostics=normalized_diagnostics,
            events=events,
            goals=goals,
            preferred_styles=preferred_styles,
            previous_mastery=previous_mastery,
        )
        recommendations, recommendation_trace = self.recommendation_agent.recommend(
            profile, self.resources, top_k=top_k, history=events
        )
        path, planning_trace = self.planning_agent.plan(profile, self.knowledge_graph, self.resources)
        cards, generation_trace = self.generation_agent.generate_cards(profile, path, self.resources)

        return {
            "profile": self._profile_payload(profile),
            "recommendations": [
                {
                    "resource_id": item.resource.resource_id,
                    "title": item.resource.title,
                    "score": item.score,
                    "style": item.resource.style,
                    "difficulty": item.resource.difficulty,
                    "knowledge_points": list(item.resource.knowledge_points),
                    "reasons": list(item.reasons),
                    "ranking_features": item.features,
                }
                for item in recommendations
            ],
            "learning_path": [
                {
                    "knowledge_point": step.knowledge_point,
                    "target_mastery": step.target_mastery,
                    "rationale": step.rationale,
                    "resources": [rec.resource.title for rec in step.resources],
                    "estimated_minutes": step.estimated_minutes,
                    "checkpoint": step.checkpoint,
                    "prerequisites": list(step.prerequisites),
                }
                for step in path
            ],
            "generated_cards": cards,
            "generated_resources": [card["resource_bundle"] for card in cards if card.get("resource_bundle")],
            "retrieval_evidence": [context for card in cards for context in card.get("rag_context", [])],
            "generation_quality": self._generation_quality(cards),
            "model_meta": self.recommendation_agent.status(),
            "counterfactual_explanations": self._counterfactuals(profile, recommendations[:3]),
            "knowledge_graph": [
                {
                    "name": node.name,
                    "prerequisites": list(node.prerequisites),
                    "importance": node.importance,
                    "mastery": profile.mastery.get(node.name, 0.5),
                }
                for node in self.knowledge_graph
            ],
            "agent_traces": [
                diagnosis_trace.__dict__,
                profile_trace.__dict__,
                recommendation_trace.__dict__,
                planning_trace.__dict__,
                generation_trace.__dict__,
            ],
        }

    def recommend(self, *args, **kwargs) -> dict:
        return self.run_learning_loop(*args, **kwargs)

    def diagnose(self, answers: dict[str, float]) -> dict:
        diagnostics, trace = self.diagnosis_agent.analyze(answers)
        return {"diagnostics": diagnostics, "agent_trace": trace.__dict__}

    def diagnose_assessment(
        self,
        items: list[AssessmentItem],
        responses: list[AssessmentResponse],
        previous_mastery: dict[str, float] | None = None,
    ) -> dict:
        result = self.diagnostic_engine.evaluate(items, responses, previous_mastery)
        return {
            **result,
            "diagnostics": result["mastery"],
            "agent_trace": {
                "agent": "诊断 Agent",
                "action": "融合题目难度、区分度、作答得分、用时、提示和置信度估计知识点掌握度",
                "output": f"识别 {len(result['weak_points'])} 个薄弱知识点，处理 {len(result['evidence'])} 条作答证据",
            },
        }

    def update_profile(
        self,
        student_id: str,
        diagnostics: dict[str, float],
        events: list[InteractionEvent] | None = None,
        goals: list[str] | None = None,
        preferred_styles: list[str] | None = None,
        previous_mastery: dict[str, float] | None = None,
    ) -> dict:
        normalized_diagnostics, diagnosis_trace = self.diagnosis_agent.analyze(diagnostics)
        profile, profile_trace = self.profile_agent.update(
            student_id=student_id,
            diagnostics=normalized_diagnostics,
            events=events,
            goals=goals,
            preferred_styles=preferred_styles,
            previous_mastery=previous_mastery,
        )
        return {
            "profile": self._profile_payload(profile),
            "agent_traces": [diagnosis_trace.__dict__, profile_trace.__dict__],
        }

    def tutor(
        self,
        student_id: str,
        question: str,
        diagnostics: dict[str, float],
        history: list[dict[str, str]] | None = None,
        goals: list[str] | None = None,
        preferred_styles: list[str] | None = None,
        previous_mastery: dict[str, float] | None = None,
        events: list[InteractionEvent] | None = None,
        knowledge_point: str | None = None,
    ) -> dict:
        profile, profile_trace = self.profile_agent.update(
            student_id,
            diagnostics,
            events,
            goals,
            preferred_styles,
            previous_mastery,
        )
        answer, tutor_trace = self.tutoring_agent.ask(
            question,
            profile,
            self.resources,
            history=history,
            knowledge_point=knowledge_point,
        )
        return {
            **answer,
            "profile": self._profile_payload(profile),
            "agent_traces": [profile_trace.__dict__, tutor_trace.__dict__],
        }

    def feedback_loop(
        self,
        student_id: str,
        diagnostics: dict[str, float],
        feedback_events: list[InteractionEvent],
        goals: list[str] | None = None,
        preferred_styles: list[str] | None = None,
        previous_mastery: dict[str, float] | None = None,
        top_k: int = 6,
    ) -> dict:
        before = self.run_learning_loop(
            student_id,
            diagnostics,
            goals=goals,
            preferred_styles=preferred_styles,
            previous_mastery=previous_mastery,
            top_k=top_k,
        )
        after = self.run_learning_loop(
            student_id,
            diagnostics,
            events=feedback_events,
            goals=goals,
            preferred_styles=preferred_styles,
            previous_mastery=before["profile"]["mastery"],
            top_k=top_k,
        )
        return {
            "before": before,
            "after": after,
            "delta": {
                point: round(
                    after["profile"]["mastery"].get(point, 0.0) - before["profile"]["mastery"].get(point, 0.0), 4
                )
                for point in set(before["profile"]["mastery"]) | set(after["profile"]["mastery"])
            },
            "path_adjustment": self._path_adjustment(before, after),
        }

    def _path_adjustment(self, before: dict, after: dict) -> str:
        before_path = [step["knowledge_point"] for step in before["learning_path"]]
        after_path = [step["knowledge_point"] for step in after["learning_path"]]
        if before_path == after_path:
            return "学习路径保持稳定，系统将根据掌握度变化微调资源难度。"
        return f"路径从 {' → '.join(before_path[:4])} 调整为 {' → '.join(after_path[:4])}。"

    def _generation_quality(self, cards: list[dict]) -> dict:
        if not cards:
            return {"mean_score": 0.0, "passed": False}
        scores = [card.get("quality_check", {}).get("score", 0.0) for card in cards]
        return {
            "mean_score": round(sum(scores) / len(scores), 4),
            "passed": all(card.get("quality_check", {}).get("passed", False) for card in cards),
            "approved_count": sum(card.get("quality_check", {}).get("passed", False) for card in cards),
            "repaired_count": sum(card.get("review_cycle", {}).get("repaired", False) for card in cards),
            "multi_format_coverage": round(
                sum(
                    card.get("quality_check", {}).get("checks", {}).get("multi_format_complete", False)
                    for card in cards
                )
                / len(cards),
                4,
            ),
            "safe_generation_rate": round(
                sum(card.get("quality_check", {}).get("checks", {}).get("safe", False) for card in cards) / len(cards),
                4,
            ),
        }

    def _counterfactuals(self, profile, recommendations) -> list[dict]:
        explanations = []
        for item in recommendations:
            features = item.features or {}
            suggestions = []
            if features.get("style_preference", 0.0) == 0.0:
                suggestions.append(f"若学生偏好 {item.resource.style}，该资源排序会进一步上升。")
            if features.get("difficulty_fit", 1.0) < 0.75:
                suggestions.append("若选择更接近目标难度的资源，推荐分可能更高。")
            if features.get("weakness", 0.0) < 0.35:
                suggestions.append("若该资源覆盖更明显薄弱点，推荐分可能更高。")
            explanations.append(
                {
                    "resource_id": item.resource.resource_id,
                    "title": item.resource.title,
                    "explanations": suggestions or ["当前资源已较好匹配学生画像。"],
                }
            )
        return explanations

    def _profile_payload(self, profile) -> dict:
        return {
            "student_id": profile.student_id,
            "mastery": profile.mastery,
            "mastery_confidence": profile.mastery_confidence,
            "goals": profile.goals,
            "preferred_styles": profile.preferred_styles,
            "cognitive_preferences": profile.cognitive_preferences,
            "target_difficulty": profile.target_difficulty,
            "ability_estimate": profile.ability_estimate,
            "risk_level": profile.risk_level,
            "weak_points": profile.weak_points,
            "recent_focus": profile.recent_focus,
            "learning_velocity": profile.learning_velocity,
            "engagement_score": profile.engagement_score,
            "stability_score": profile.stability_score,
            "preference_confidence": profile.preference_confidence,
            "forgetting_risk": profile.forgetting_risk,
            "learning_stage": profile.learning_stage,
            "recommended_pace_minutes": profile.recommended_pace_minutes,
        }
