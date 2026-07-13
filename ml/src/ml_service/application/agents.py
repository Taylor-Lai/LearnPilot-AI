from __future__ import annotations

import re
from dataclasses import dataclass

from ..domain.models import InteractionEvent, LearningStep, StudentProfile
from ..infrastructure.content_generator import ContentGenerator
from ..infrastructure.rag import ResourceRetriever
from ..infrastructure.ranker import TrainableRanker
from .path_planner import LearningPathPlanner
from .profiler import StudentProfiler
from .recommender import ResourceRecommender
from .resource_formats import ResourceBundleBuilder
from .tutor import TutorAgent as GroundedTutor


@dataclass(frozen=True)
class AgentTrace:
    agent: str
    action: str
    output: str


class DiagnosisAgent:
    def analyze(self, answers: dict[str, float]) -> tuple[dict[str, float], AgentTrace]:
        diagnostics = {point: max(0.0, min(1.0, float(score))) for point, score in answers.items()}
        weak = [point for point, score in diagnostics.items() if score < 0.6]
        output = "发现薄弱点：" + ("、".join(weak) if weak else "暂无明显薄弱点")
        return diagnostics, AgentTrace("诊断 Agent", "分析测评答案并输出知识点掌握度", output)


class ProfileAgent:
    def __init__(self, profiler: StudentProfiler | None = None) -> None:
        self.profiler = profiler or StudentProfiler()

    def update(
        self,
        student_id: str,
        diagnostics: dict[str, float],
        events: list[InteractionEvent] | None,
        goals: list[str] | None,
        preferred_styles: list[str] | None,
        previous_mastery: dict[str, float] | None = None,
    ) -> tuple[StudentProfile, AgentTrace]:
        profile = self.profiler.build_profile(
            student_id, diagnostics, events, goals, preferred_styles, previous_mastery
        )
        weakest = sorted(profile.mastery, key=profile.mastery.get)[:2]
        output = f"风险等级 {profile.risk_level}，优先关注 {'、'.join(weakest) if weakest else '目标知识点'}"
        return profile, AgentTrace("画像 Agent", "融合诊断、行为和偏好，维护学生画像", output)


class RecommendationAgent:
    def __init__(self, recommender: ResourceRecommender | None = None, ranker: TrainableRanker | None = None) -> None:
        self.recommender = recommender or ResourceRecommender()
        self.ranker = ranker or TrainableRanker()

    def recommend(self, profile: StudentProfile, resources, top_k: int, history: list[InteractionEvent] | None = None):
        recommendations = self.ranker.recommend(profile, resources, top_k=top_k, history=history)
        if not recommendations:
            recommendations = self.recommender.recommend(profile, resources, top_k=top_k)
        titles = [item.resource.title for item in recommendations[:3]]
        trace = AgentTrace(
            "推荐 Agent",
            "根据薄弱点、难度、偏好、质量、反馈和排序模型分数推荐资源",
            "Top 推荐：" + "、".join(titles),
        )
        return recommendations, trace

    def status(self) -> dict:
        return self.ranker.status()


class PlanningAgent:
    def __init__(self, planner: LearningPathPlanner | None = None) -> None:
        self.planner = planner or LearningPathPlanner()

    def plan(self, profile: StudentProfile, knowledge_graph, resources) -> tuple[list[LearningStep], AgentTrace]:
        path = self.planner.plan(profile, knowledge_graph, resources)
        points = [step.knowledge_point for step in path[:4]]
        trace = AgentTrace("规划 Agent", "基于知识图谱和先修关系生成学习路径", "路径：" + " → ".join(points))
        return path, trace


class GenerationEvaluationAgent:
    def __init__(
        self,
        generator: ContentGenerator | None = None,
        retriever: ResourceRetriever | None = None,
        bundle_builder: ResourceBundleBuilder | None = None,
    ) -> None:
        self.generator = generator or ContentGenerator()
        self.retriever = retriever or ResourceRetriever()
        self.bundle_builder = bundle_builder or ResourceBundleBuilder()

    def generate_cards(
        self, profile: StudentProfile, steps: list[LearningStep], resources
    ) -> tuple[list[dict], AgentTrace]:
        cards: list[dict] = []
        repaired_count = 0
        for step in steps[:3]:
            contexts = self.retriever.retrieve(step.knowledge_point, resources, top_k=3)
            card = self.generator.generate_study_card(profile, step, contexts)
            self._attach_resource_bundle(card, step, profile)
            initial_review = self.evaluate_card(step.knowledge_point, card)
            reviews = [initial_review]
            if not initial_review["passed"]:
                card = self.generator.repair_study_card(
                    profile,
                    step,
                    card,
                    contexts,
                    initial_review["failed_checks"],
                )
                self._attach_resource_bundle(card, step, profile)
                reviews.append(self.evaluate_card(step.knowledge_point, card))
                repaired_count += 1
            card["quality_check"] = reviews[-1]
            card["review_cycle"] = {
                "attempts": len(reviews),
                "repaired": len(reviews) > 1,
                "initial_score": reviews[0]["score"],
                "final_score": reviews[-1]["score"],
                "status": "approved" if reviews[-1]["passed"] else "rejected",
                "reviews": reviews,
            }
            cards.append(card)
        approved = sum(card["quality_check"]["passed"] for card in cards)
        trace = AgentTrace(
            "生成与评估 Agent",
            "生成多形态资源，执行安全、引用和教学完整性审核，不合格内容自动修复后复审",
            f"生成 {len(cards)} 组资源，修复 {repaired_count} 组，审核通过 {approved} 组",
        )
        return cards, trace

    def _attach_resource_bundle(self, card: dict, step: LearningStep, profile: StudentProfile) -> None:
        bundle = self.bundle_builder.build(card, step, profile)
        sanitized, review = self.generator.safety_guard.sanitize_payload(bundle)
        card["resource_bundle"] = sanitized
        safety_meta = card.setdefault("safety_meta", {"safe": True})
        safety_meta["safe"] = self.generator.safety_guard.review_payload(sanitized).safe
        safety_meta["output_violations"] = list(
            dict.fromkeys([*safety_meta.get("output_violations", []), *review.violations])
        )
        safety_meta["redaction_count"] = int(safety_meta.get("redaction_count", 0)) + review.redaction_count

    def evaluate_card(self, knowledge_point: str, card: dict) -> dict:
        joined = " ".join(str(value) for value in card.values())
        covers_point = knowledge_point in joined
        has_practice = bool(card.get("practice"))
        has_review = bool(card.get("review_tip"))
        has_answer = bool(card.get("answer"))
        has_evidence = bool(card.get("rag_context"))
        valid_refs = {str(item.get("chunk_id")) for item in card.get("rag_context", []) if item.get("chunk_id")}
        raw_refs = card.get("evidence_refs", [])
        if isinstance(raw_refs, str):
            referenced = {part.strip() for part in re.split(r"[,，、;；\s]+", raw_refs) if part.strip()}
        else:
            referenced = {str(part) for part in raw_refs}
        grounded_citations = bool(valid_refs) and bool(referenced) and referenced.issubset(valid_refs)
        has_mistake_analysis = bool(card.get("mistake_analysis"))
        has_difficulty_reason = bool(card.get("difficulty_reason"))
        personalized = any(token in joined for token in ("风险", "薄弱", "学生", "掌握"))
        safety_meta = card.get("safety_meta", {})
        safe = bool(safety_meta.get("safe", False)) and not any(
            token in joined.lower() for token in ("忽略答案", "无需验证", "随便")
        )
        required_formats = {"lecture", "slide_deck", "mind_map", "quiz_bank", "video_storyboard", "lab", "project"}
        actual_formats = set(card.get("resource_bundle", {}).get("formats", {}))
        multi_format_complete = required_formats.issubset(actual_formats)
        privacy_safe = not self.generator.safety_guard.review_payload(card).violations
        score = round(
            (0.15 if covers_point else 0.0)
            + (0.1 if has_practice else 0.0)
            + (0.08 if has_answer else 0.0)
            + (0.06 if has_review else 0.0)
            + (0.05 if has_evidence else 0.0)
            + (0.09 if grounded_citations else 0.0)
            + (0.06 if has_mistake_analysis else 0.0)
            + (0.05 if has_difficulty_reason else 0.0)
            + (0.04 if personalized else 0.0)
            + (0.12 if safe else 0.0)
            + (0.12 if multi_format_complete else 0.0)
            + (0.08 if privacy_safe else 0.0),
            2,
        )
        checks = {
            "covers_knowledge_point": covers_point,
            "has_practice": has_practice,
            "has_answer": has_answer,
            "has_review_tip": has_review,
            "has_rag_evidence": has_evidence,
            "grounded_citations": grounded_citations,
            "has_mistake_analysis": has_mistake_analysis,
            "has_difficulty_reason": has_difficulty_reason,
            "personalized": personalized,
            "safe": safe,
            "multi_format_complete": multi_format_complete,
            "privacy_safe": privacy_safe,
        }
        return {
            "passed": score >= 0.8 and safe and multi_format_complete and (grounded_citations or not has_evidence),
            "score": score,
            "checks": checks,
            "failed_checks": [name for name, passed in checks.items() if not passed],
        }


class TutoringAgent:
    def __init__(self, tutor: GroundedTutor | None = None) -> None:
        self.tutor = tutor or GroundedTutor()

    def ask(self, question, profile, resources, history=None, knowledge_point=None) -> tuple[dict, AgentTrace]:
        result = self.tutor.ask(
            question=question,
            profile=profile,
            resources=resources,
            history=history,
            knowledge_point=knowledge_point,
        )
        evidence_count = len(result.get("evidence", []))
        trace = AgentTrace(
            "辅导 Agent",
            "结合学生画像、对话历史和课程检索证据进行苏格拉底式辅导",
            f"返回 {len(result.get('hints', []))} 条提示，引用 {evidence_count} 条证据",
        )
        return result, trace
