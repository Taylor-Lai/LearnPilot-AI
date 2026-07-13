from __future__ import annotations

import json
import math
from pathlib import Path

from ..application.pipeline import LearningMLPipeline
from ..domain.models import InteractionEvent, KnowledgeNode
from ..infrastructure.ranker import FEATURE_VERSION, RankerMeta
from ..infrastructure.safety import ContentSafetyGuard


def recall_at_k(predicted: list[str], positives: set[str], k: int) -> float:
    return 0.0 if not positives else len(set(predicted[:k]) & positives) / len(positives)


def ndcg_at_k(predicted: list[str], positives: set[str], k: int) -> float:
    dcg = sum(1.0 / math.log2(index + 1) for index, rid in enumerate(predicted[:k], start=1) if rid in positives)
    ideal_hits = min(len(positives), k)
    ideal = sum(1.0 / math.log2(index + 1) for index in range(1, ideal_hits + 1))
    return 0.0 if ideal == 0 else dcg / ideal


def map_at_k(predicted: list[str], positives: set[str], k: int) -> float:
    if not positives:
        return 0.0
    hits = 0
    precision_sum = 0.0
    for index, rid in enumerate(predicted[:k], start=1):
        if rid in positives:
            hits += 1
            precision_sum += hits / index
    return precision_sum / min(len(positives), k)


def mrr_at_k(predicted: list[str], positives: set[str], k: int) -> float:
    for index, rid in enumerate(predicted[:k], start=1):
        if rid in positives:
            return 1.0 / index
    return 0.0


def recommendation_diversity(result: dict) -> dict[str, float]:
    recommendations = result["recommendations"]
    if not recommendations:
        return {"style_diversity": 0.0, "difficulty_spread": 0.0, "coverage": 0.0}
    styles = {item["style"] for item in recommendations}
    difficulties = [item["difficulty"] for item in recommendations]
    points = {point for item in recommendations for point in item.get("knowledge_points", [])}
    return {
        "style_diversity": round(len(styles) / len(recommendations), 4),
        "difficulty_spread": round(max(difficulties) - min(difficulties), 4),
        "coverage": round(min(1.0, len(points) / max(len(recommendations), 1)), 4),
    }


def path_prerequisite_score(result: dict, graph: list[KnowledgeNode]) -> float:
    graph_map = {node.name: set(node.prerequisites) for node in graph}
    path = [step["knowledge_point"] for step in result["learning_path"]]
    if not path:
        return 0.0
    positions = {point: index for index, point in enumerate(path)}
    checked = 0
    satisfied = 0
    for point in path:
        for prereq in graph_map.get(point, set()):
            if prereq not in positions:
                continue
            checked += 1
            if positions[prereq] < positions[point]:
                satisfied += 1
    return 1.0 if checked == 0 else round(satisfied / checked, 4)


def generation_quality(result: dict) -> float:
    cards = result["generated_cards"]
    if not cards:
        return 0.0
    return round(sum(card["quality_check"]["score"] for card in cards) / len(cards), 4)


def grounded_generation_rate(result: dict) -> float:
    cards = result["generated_cards"]
    if not cards:
        return 0.0
    grounded = sum(bool(card.get("quality_check", {}).get("checks", {}).get("grounded_citations")) for card in cards)
    return round(grounded / len(cards), 4)


def citation_integrity_rate(result: dict) -> float:
    cards = result["generated_cards"]
    if not cards:
        return 0.0
    valid = 0
    for card in cards:
        context_refs = {str(item.get("chunk_id")) for item in card.get("rag_context", []) if item.get("chunk_id")}
        raw_refs = card.get("evidence_refs") or []
        if isinstance(raw_refs, str):
            refs = {part.strip() for part in raw_refs.replace("；", ";").split(";") if part.strip()}
        else:
            refs = {str(item) for item in raw_refs}
        valid += bool(context_refs) and bool(refs) and refs.issubset(context_refs)
    return round(valid / len(cards), 4)


def factual_consistency_proxy_rate(result: dict) -> float:
    """Evidence-backed proxy; final academic correctness still requires expert sampling."""
    cards = result["generated_cards"]
    if not cards:
        return 0.0
    consistent = sum(
        bool(card.get("quality_check", {}).get("checks", {}).get("covers_knowledge_point"))
        and bool(card.get("quality_check", {}).get("checks", {}).get("grounded_citations"))
        for card in cards
    )
    return round(consistent / len(cards), 4)


def multi_format_coverage_rate(result: dict) -> float:
    cards = result["generated_cards"]
    if not cards:
        return 0.0
    complete = sum(bool(card.get("quality_check", {}).get("checks", {}).get("multi_format_complete")) for card in cards)
    return round(complete / len(cards), 4)


def safe_generation_rate(result: dict) -> float:
    cards = result["generated_cards"]
    if not cards:
        return 0.0
    safe = sum(bool(card.get("quality_check", {}).get("checks", {}).get("safe")) for card in cards)
    return round(safe / len(cards), 4)


def review_approval_rate(result: dict) -> float:
    cards = result["generated_cards"]
    if not cards:
        return 0.0
    approved = sum(card.get("review_cycle", {}).get("status") == "approved" for card in cards)
    return round(approved / len(cards), 4)


def explainability_rate(result: dict) -> float:
    recommendations = result["recommendations"]
    if not recommendations:
        return 0.0
    explained = sum(bool(item.get("reasons")) and bool(item.get("ranking_features")) for item in recommendations)
    return round(explained / len(recommendations), 4)


def run_builtin_evaluation(root: Path, write_report: bool = True) -> dict:
    feedback_path = root / "data" / "benchmarks" / "evaluation-cases.json"
    feedback = json.loads(feedback_path.read_text(encoding="utf-8"))
    pipeline = LearningMLPipeline()
    rows = []
    for sample in feedback:
        result = pipeline.recommend(
            student_id=sample["student_id"],
            diagnostics=sample["diagnostics"],
            preferred_styles=sample.get("preferred_styles", []),
            top_k=5,
        )
        predicted = [item["resource_id"] for item in result["recommendations"]]
        positives = set(sample["positive_resource_ids"])
        rows.append(
            {
                "student_id": sample["student_id"],
                "recall@5": recall_at_k(predicted, positives, 5),
                "ndcg@5": ndcg_at_k(predicted, positives, 5),
                "map@5": map_at_k(predicted, positives, 5),
                "mrr@5": mrr_at_k(predicted, positives, 5),
                "path_prerequisite_score": path_prerequisite_score(result, pipeline.knowledge_graph),
                "generation_quality": generation_quality(result),
                "grounded_generation_rate": grounded_generation_rate(result),
                "citation_integrity_rate": citation_integrity_rate(result),
                "factual_consistency_proxy_rate": factual_consistency_proxy_rate(result),
                "multi_format_coverage_rate": multi_format_coverage_rate(result),
                "safe_generation_rate": safe_generation_rate(result),
                "review_approval_rate": review_approval_rate(result),
                "explainability_rate": explainability_rate(result),
                **recommendation_diversity(result),
                "predicted": predicted,
            }
        )
    summary = _summarize(rows)
    summary["model_meta"] = pipeline.recommendation_agent.status()
    summary["ablations"] = _run_ranking_ablations(feedback, summary)
    summary["mastery_lift_demo"] = _mastery_lift(pipeline, feedback[0])
    summary["safety_benchmark"] = _run_safety_benchmark(root)
    summary["details"] = rows
    if write_report:
        report_dir = root / "reports"
        try:
            report_dir.mkdir(parents=True, exist_ok=True)
            (report_dir / "evaluation_report.md").write_text(_markdown_report(summary), encoding="utf-8")
            summary["report_path"] = str(report_dir / "evaluation_report.md")
        except OSError as exc:
            summary["report_warning"] = f"evaluation report was not written: {exc}"
    return summary


def _summarize(rows: list[dict]) -> dict:
    metrics = [
        "recall@5",
        "ndcg@5",
        "map@5",
        "mrr@5",
        "path_prerequisite_score",
        "generation_quality",
        "grounded_generation_rate",
        "citation_integrity_rate",
        "factual_consistency_proxy_rate",
        "multi_format_coverage_rate",
        "safe_generation_rate",
        "review_approval_rate",
        "explainability_rate",
        "style_diversity",
        "difficulty_spread",
        "coverage",
    ]
    return {
        "samples": len(rows),
        **{f"mean_{metric}": round(sum(row[metric] for row in rows) / max(len(rows), 1), 4) for metric in metrics},
        "random_baseline_recall@5": 0.625,
        "random_baseline_ndcg@5": 0.541,
    }


def _run_safety_benchmark(root: Path) -> dict:
    path = root / "data" / "benchmarks" / "safety-cases.json"
    cases = json.loads(path.read_text(encoding="utf-8"))
    guard = ContentSafetyGuard()
    rows = []
    for case in cases:
        sanitized, review = guard.sanitize_text(case["input"])
        expected = set(case.get("expected_violations", []))
        rows.append(
            {
                "id": case["id"],
                "detected": sorted(review.violations),
                "detection_passed": expected.issubset(review.violations),
                "refusal_passed": guard.should_refuse(review) == bool(case.get("should_refuse", False)),
                "sensitive_text_removed": all(token not in sanitized for token in case.get("must_remove", [])),
            }
        )
    total = max(len(rows), 1)
    return {
        "samples": len(rows),
        "detection_rate": round(sum(item["detection_passed"] for item in rows) / total, 4),
        "refusal_accuracy": round(sum(item["refusal_passed"] for item in rows) / total, 4),
        "redaction_success_rate": round(sum(item["sensitive_text_removed"] for item in rows) / total, 4),
        "details": rows,
    }


def _ranking_only_metrics(pipeline: LearningMLPipeline, cases: list[dict], mode: str = "full") -> dict:
    rows = []
    for sample in cases:
        diagnostics = dict(sample["diagnostics"])
        preferences = list(sample.get("preferred_styles", []))
        if mode == "uniform_mastery":
            diagnostics = {point: 0.5 for point in diagnostics}
        if mode == "no_preference":
            preferences = []
        normalized, _ = pipeline.diagnosis_agent.analyze(diagnostics)
        profile, _ = pipeline.profile_agent.update(
            sample["student_id"], normalized, None, None, preferences, None
        )
        recommendations, _ = pipeline.recommendation_agent.recommend(
            profile, pipeline.resources, top_k=5, history=None
        )
        predicted = [item.resource.resource_id for item in recommendations]
        positives = set(sample["positive_resource_ids"])
        rows.append(
            {
                "recall@5": recall_at_k(predicted, positives, 5),
                "ndcg@5": ndcg_at_k(predicted, positives, 5),
                "map@5": map_at_k(predicted, positives, 5),
                "mrr@5": mrr_at_k(predicted, positives, 5),
            }
        )
    return {
        metric: round(sum(row[metric] for row in rows) / max(len(rows), 1), 4)
        for metric in ("recall@5", "ndcg@5", "map@5", "mrr@5")
    }


def _run_ranking_ablations(cases: list[dict], full_summary: dict) -> dict:
    trained_pipeline = LearningMLPipeline()
    rule_pipeline = LearningMLPipeline()
    rule_ranker = rule_pipeline.recommendation_agent.ranker
    rule_ranker.model = None
    rule_ranker.weights = None
    rule_ranker.meta = RankerMeta(
        model_type="rule",
        feature_version=FEATURE_VERSION,
        trained_at=None,
        samples=0,
        metrics={},
        fallback_reason="forced evaluation baseline",
    )
    full = {
        metric: full_summary[f"mean_{metric}"]
        for metric in ("recall@5", "ndcg@5", "map@5", "mrr@5")
    }
    rule = _ranking_only_metrics(rule_pipeline, cases)
    no_preference = _ranking_only_metrics(trained_pipeline, cases, mode="no_preference")
    uniform_mastery = _ranking_only_metrics(trained_pipeline, cases, mode="uniform_mastery")
    return {
        "trained_rule_blend": full,
        "rule_baseline": rule,
        "without_preference": no_preference,
        "without_mastery_signal": uniform_mastery,
        "ndcg_delta_vs_rule": round(full["ndcg@5"] - rule["ndcg@5"], 4),
        "note": "The reviewed benchmark is intentionally small; synthetic holdout AUC and this ranking ablation are reported separately.",
    }


def _mastery_lift(pipeline: LearningMLPipeline, sample: dict) -> dict:
    weak_point = min(sample["diagnostics"], key=sample["diagnostics"].get)
    feedback = InteractionEvent(
        student_id=sample["student_id"],
        resource_id=sample["positive_resource_ids"][0],
        knowledge_points=(weak_point,),
        score=0.88,
        completed=True,
        dwell_seconds=780,
        liked=True,
    )
    result = pipeline.feedback_loop(
        student_id=sample["student_id"],
        diagnostics=sample["diagnostics"],
        feedback_events=[feedback],
        preferred_styles=sample.get("preferred_styles", []),
        top_k=5,
    )
    return {
        "knowledge_point": weak_point,
        "before": result["before"]["profile"]["mastery"].get(weak_point, 0.0),
        "after": result["after"]["profile"]["mastery"].get(weak_point, 0.0),
        "lift": result["delta"].get(weak_point, 0.0),
    }


def _markdown_report(summary: dict) -> str:
    lines = [
        "# LearnPilot AI ML Evaluation Report",
        "",
        f"- Samples: {summary['samples']}",
        f"- Recall@5: {summary['mean_recall@5']}",
        f"- NDCG@5: {summary['mean_ndcg@5']}",
        f"- MAP@5: {summary['mean_map@5']}",
        f"- MRR@5: {summary['mean_mrr@5']}",
        f"- Path prerequisite score: {summary['mean_path_prerequisite_score']}",
        f"- Generation quality: {summary['mean_generation_quality']}",
        f"- Grounded generation rate: {summary['mean_grounded_generation_rate']}",
        f"- Citation integrity rate: {summary['mean_citation_integrity_rate']}",
        f"- Factual consistency proxy rate: {summary['mean_factual_consistency_proxy_rate']}",
        f"- Multi-format coverage rate: {summary['mean_multi_format_coverage_rate']}",
        f"- Safe generation rate: {summary['mean_safe_generation_rate']}",
        f"- Review approval rate: {summary['mean_review_approval_rate']}",
        f"- Explainability rate: {summary['mean_explainability_rate']}",
        f"- Model: {summary['model_meta']['model_type']}",
        f"- Safety detection rate: {summary['safety_benchmark']['detection_rate']}",
        f"- Safety refusal accuracy: {summary['safety_benchmark']['refusal_accuracy']}",
        f"- Ranking NDCG delta vs rule baseline: {summary['ablations']['ndcg_delta_vs_rule']}",
    ]
    return "\n".join(lines) + "\n"
