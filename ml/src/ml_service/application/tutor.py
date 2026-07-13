from __future__ import annotations

import json
from typing import Any

from ..domain.models import LearningResource, StudentProfile
from ..infrastructure.content_generator import LLMClient, QwenMaxClient, TemplateLLMClient
from ..infrastructure.rag import ResourceRetriever
from ..infrastructure.safety import ContentSafetyGuard, SafetyReview


class TutorAgent:
    """Grounded, multi-turn Socratic tutoring agent.

    The agent always returns retrieval evidence. When a real LLM is unavailable,
    the deterministic fallback still provides hints and a verifiable next step.
    """

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        retriever: ResourceRetriever | None = None,
        safety_guard: ContentSafetyGuard | None = None,
    ) -> None:
        self.llm_client = llm_client or QwenMaxClient.from_env() or TemplateLLMClient()
        self.retriever = retriever or ResourceRetriever()
        self.safety_guard = safety_guard or ContentSafetyGuard()

    def ask(
        self,
        question: str,
        profile: StudentProfile,
        resources: list[LearningResource],
        history: list[dict[str, str]] | None = None,
        knowledge_point: str | None = None,
    ) -> dict[str, Any]:
        safe_question, question_review = self.safety_guard.sanitize_text(question)
        safe_history, history_review = self.safety_guard.sanitize_payload(history or [])
        safe_point, point_review = self.safety_guard.sanitize_text(knowledge_point or "")
        safe_profile, profile_review = self.safety_guard.sanitize_payload(
            {"weak_points": profile.weak_points, "learning_stage": profile.learning_stage}
        )
        query = " ".join(part for part in (safe_point, safe_question) if part)
        evidence = self.retriever.retrieve(query, resources, top_k=4)
        evidence, evidence_review = self.safety_guard.sanitize_contexts(evidence)
        input_review = self._combine_reviews(
            question_review,
            history_review,
            point_review,
            profile_review,
            evidence_review,
        )
        fallback_point = safe_point or (safe_profile["weak_points"][0] if safe_profile["weak_points"] else None)
        fallback = self._fallback(safe_question, profile, evidence, safe_history, fallback_point)
        if isinstance(self.llm_client, TemplateLLMClient):
            return self._finalize(fallback, input_review)

        try:
            generated = json.loads(
                self.llm_client.generate(
                    self._prompt(
                        safe_question,
                        safe_profile["weak_points"],
                        safe_profile["learning_stage"],
                        evidence,
                        safe_history,
                    )
                )
            )
            answer = self._validated_result(generated, fallback, evidence)
            answer["generation_meta"] = {
                "provider": self.llm_client.model if isinstance(self.llm_client, QwenMaxClient) else "custom",
                "fallback_used": False,
            }
            return self._finalize(answer, input_review)
        except Exception as exc:  # pragma: no cover - network/model protection
            fallback["generation_meta"] = {
                "provider": "template",
                "fallback_used": True,
                "fallback_reason": str(exc),
            }
            return self._finalize(fallback, input_review)

    def _combine_reviews(self, *reviews: SafetyReview) -> SafetyReview:
        violations = tuple(dict.fromkeys(item for review in reviews for item in review.violations))
        return SafetyReview(
            safe=not violations,
            violations=violations,
            redaction_count=sum(review.redaction_count for review in reviews),
        )

    def _finalize(self, answer: dict[str, Any], input_review: SafetyReview) -> dict[str, Any]:
        sanitized, output_review = self.safety_guard.sanitize_payload(answer)
        post_review = self.safety_guard.review_payload(sanitized)
        sanitized["safety_meta"] = {
            "safe": post_review.safe,
            "input_violations": list(input_review.violations),
            "output_violations": list(output_review.violations),
            "redaction_count": input_review.redaction_count + output_review.redaction_count,
        }
        return sanitized

    def _prompt(
        self,
        question: str,
        weak_points: list[str],
        learning_stage: str,
        evidence: list[dict],
        history: list[dict[str, str]],
    ) -> str:
        evidence_text = (
            "\n".join(f"[{item['chunk_id']}] {item['title']}: {item['snippet']}" for item in evidence)
            or "[no-evidence] 当前资源库没有可靠证据。"
        )
        history_text = (
            "\n".join(f"{turn.get('role', 'student')}: {turn.get('content', '')}" for turn in history[-6:])
            or "无历史对话"
        )
        return (
            "你是苏格拉底式学习辅导 Agent。严格返回 JSON，字段为 answer、hints、follow_up_question、"
            "next_action、evidence_refs、knowledge_check。不得编造证据；evidence_refs 只能引用方括号中的 chunk_id。"
            "先解释关键概念，再给分层提示，最后用一个问题检查理解。\n"
            f"学生问题：{question}\n"
            f"学生薄弱点：{weak_points[:5]}\n"
            f"学习阶段：{learning_stage}\n"
            f"对话历史：\n{history_text}\n"
            f"检索证据：\n{evidence_text}"
        )

    def _validated_result(self, generated: dict, fallback: dict, evidence: list[dict]) -> dict[str, Any]:
        valid_refs = {item["chunk_id"] for item in evidence}
        requested_refs = generated.get("evidence_refs") or []
        if isinstance(requested_refs, str):
            requested_refs = [requested_refs]
        refs = [str(ref) for ref in requested_refs if str(ref) in valid_refs]
        hints = generated.get("hints") or fallback["hints"]
        if isinstance(hints, str):
            hints = [hints]
        return {
            **fallback,
            "answer": str(generated.get("answer") or fallback["answer"]),
            "hints": [str(item) for item in hints][:4],
            "follow_up_question": str(generated.get("follow_up_question") or fallback["follow_up_question"]),
            "next_action": str(generated.get("next_action") or fallback["next_action"]),
            "knowledge_check": str(generated.get("knowledge_check") or fallback["knowledge_check"]),
            "evidence_refs": refs,
            "grounded": bool(refs) if evidence else False,
        }

    def _fallback(
        self,
        question: str,
        profile: StudentProfile,
        evidence: list[dict],
        history: list[dict[str, str]],
        knowledge_point: str | None,
    ) -> dict[str, Any]:
        point = knowledge_point or (profile.weak_points[0] if profile.weak_points else "当前知识点")
        source = evidence[0]["title"] if evidence else "当前课程资源库"
        prior_context = "你已经进行过多轮讨论，先回顾上一轮结论。" if history else "先确认题目中的输入、目标和限制。"
        return {
            "answer": f"结合《{source}》，可以把问题拆成“概念—条件—步骤—验证”四部分。{prior_context}",
            "hints": [
                f"先用自己的话定义“{point}”。",
                f"找出问题“{question}”中的已知条件和期望结果。",
                "写出最小可验证步骤，并用一个反例检查边界条件。",
            ],
            "follow_up_question": f"如果改变一个输入条件，{point} 的处理步骤中哪一步必须随之改变？",
            "knowledge_check": f"请用不超过三句话解释 {point}，并给出一个适用场景。",
            "next_action": "先回答追问；若仍不确定，再查看证据片段并完成一道同类小题。",
            "evidence": evidence,
            "evidence_refs": [item["chunk_id"] for item in evidence],
            "grounded": bool(evidence),
            "generation_meta": {"provider": "template", "fallback_used": True},
        }
