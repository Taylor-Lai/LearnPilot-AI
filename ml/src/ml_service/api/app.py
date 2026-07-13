from __future__ import annotations

try:
    from fastapi import FastAPI
except ImportError as exc:  # pragma: no cover
    raise RuntimeError("Install the ML package with `pip install -e ml` before starting the API service.") from exc

from ..application.pipeline import LearningMLPipeline
from ..config import ML_ROOT
from ..datasets.demo_cases import DEMO_CASES
from ..domain.diagnostics import AssessmentItem, AssessmentResponse
from ..domain.models import InteractionEvent, KnowledgeNode, LearningResource
from ..evaluation.runner import run_builtin_evaluation
from .schemas import (
    AssessmentDiagnoseRequest,
    CourseContextRequest,
    DiagnoseRequest,
    FeedbackRequest,
    GenerateRequest,
    InteractionEventRequest,
    KnowledgeNodeRequest,
    RecommendRequest,
    ResourceRequest,
    StudentRequest,
    TutorRequest,
    UpdateProfileRequest,
)

app = FastAPI(title="Personalized Learning ML Service", version="2.0.0")
pipeline = LearningMLPipeline()


@app.get("/health")
def health() -> dict:
    model = pipeline.recommendation_agent.status()
    return {
        "status": "ok",
        "service": "learnpilot-ml",
        "version": app.version,
        "ranker": model["model_type"],
        "feature_version": model["feature_version"],
    }


@app.get("/demo-cases")
def demo_cases() -> dict:
    return DEMO_CASES


@app.get("/train/status")
def train_status() -> dict:
    return pipeline.recommendation_agent.status()


@app.get("/evaluate")
def evaluate() -> dict:
    return run_builtin_evaluation(ML_ROOT, write_report=False)


@app.post("/diagnose")
def diagnose(request: DiagnoseRequest) -> dict:
    return pipeline.diagnose(request.answers)


@app.post("/assessment/diagnose")
def diagnose_assessment(request: AssessmentDiagnoseRequest) -> dict:
    return pipeline.diagnose_assessment(
        items=[
            AssessmentItem(
                item_id=item.item_id,
                knowledge_points=tuple(item.knowledge_points),
                difficulty=item.difficulty,
                discrimination=item.discrimination,
                max_score=item.max_score,
                expected_seconds=item.expected_seconds,
            )
            for item in request.items
        ],
        responses=[
            AssessmentResponse(
                item_id=response.item_id,
                score=response.score,
                elapsed_seconds=response.elapsed_seconds,
                confidence=response.confidence,
                hint_count=response.hint_count,
                attempts=response.attempts,
            )
            for response in request.responses
        ],
        previous_mastery=request.previous_mastery,
    )


@app.post("/recommend")
def recommend(request: RecommendRequest) -> dict:
    active_pipeline = _pipeline_for_request(request.resources, request.knowledge_graph)
    return active_pipeline.run_learning_loop(
        student_id=request.student.student_id,
        diagnostics=request.student.diagnostics,
        events=_events_from_dicts(request.student.events, request.student.student_id),
        goals=_student_goals(request.student, request.course_context),
        preferred_styles=request.student.preferred_styles,
        previous_mastery=request.student.previous_mastery,
        top_k=request.top_k,
    )


@app.post("/path")
def path(request: RecommendRequest) -> dict:
    result = recommend(request)
    return {
        "profile": result["profile"],
        "learning_path": result["learning_path"],
        "knowledge_graph": result["knowledge_graph"],
        "agent_traces": [trace for trace in result["agent_traces"] if trace["agent"] == "规划 Agent"],
    }


@app.post("/generate")
def generate(request: GenerateRequest) -> dict:
    active_pipeline = _pipeline_for_request(request.resources, request.knowledge_graph)
    result = active_pipeline.run_learning_loop(
        student_id=request.student.student_id,
        diagnostics=request.student.diagnostics,
        events=_events_from_dicts(request.student.events, request.student.student_id),
        goals=_student_goals(request.student, request.course_context),
        preferred_styles=request.student.preferred_styles,
        previous_mastery=request.student.previous_mastery,
        top_k=5,
    )
    return {
        "generated_cards": result["generated_cards"],
        "agent_traces": [trace for trace in result["agent_traces"] if trace["agent"] == "生成与评估 Agent"],
    }


@app.post("/feedback")
def feedback(request: FeedbackRequest) -> dict:
    active_pipeline = _pipeline_for_request(request.resources, request.knowledge_graph)
    return active_pipeline.feedback_loop(
        student_id=request.student.student_id,
        diagnostics=request.student.diagnostics,
        feedback_events=_events_from_dicts(request.feedback_events, request.student.student_id),
        goals=_student_goals(request.student, request.course_context),
        preferred_styles=request.student.preferred_styles,
        previous_mastery=request.student.previous_mastery,
        top_k=request.top_k,
    )


@app.post("/student/update-profile")
def update_profile(request: UpdateProfileRequest) -> dict:
    return pipeline.update_profile(
        student_id=request.student.student_id,
        diagnostics=request.student.diagnostics,
        events=_events_from_dicts(request.student.events, request.student.student_id),
        goals=request.student.goals,
        preferred_styles=request.student.preferred_styles,
        previous_mastery=request.student.previous_mastery,
    )


@app.post("/tutor/ask")
def tutor_ask(request: TutorRequest) -> dict:
    active_pipeline = _pipeline_for_request(request.resources, request.knowledge_graph)
    return active_pipeline.tutor(
        student_id=request.student.student_id,
        question=request.question,
        diagnostics=request.student.diagnostics,
        history=[turn.model_dump() for turn in request.history],
        goals=_student_goals(request.student, request.course_context),
        preferred_styles=request.student.preferred_styles,
        previous_mastery=request.student.previous_mastery,
        events=_events_from_dicts(request.student.events, request.student.student_id),
        knowledge_point=request.knowledge_point,
    )


def _events_from_dicts(events: list[InteractionEventRequest], fallback_student_id: str) -> list[InteractionEvent]:
    return [
        InteractionEvent(
            student_id=event.student_id or fallback_student_id,
            resource_id=event.resource_id,
            knowledge_points=tuple(event.knowledge_points),
            score=event.score,
            completed=event.completed,
            dwell_seconds=event.dwell_seconds,
            liked=event.liked,
            timestamp=event.timestamp,
            event_type=event.event_type,  # type: ignore[arg-type]
            attempts=event.attempts,
            hint_count=event.hint_count,
            confidence=event.confidence,
            resource_style=event.resource_style,
            session_id=event.session_id,
        )
        for event in events
    ]


def _pipeline_for_request(
    resources: list[ResourceRequest] | None,
    knowledge_graph: list[KnowledgeNodeRequest] | None,
) -> LearningMLPipeline:
    if not resources and not knowledge_graph:
        return pipeline
    return LearningMLPipeline(
        resources=_resources_from_request(resources) if resources else None,
        knowledge_graph=_knowledge_graph_from_request(knowledge_graph) if knowledge_graph else None,
    )


def _resources_from_request(resources: list[ResourceRequest]) -> list[LearningResource]:
    return [
        LearningResource(
            resource_id=item.resource_id,
            title=item.title,
            knowledge_points=tuple(item.knowledge_points),
            difficulty=item.difficulty,
            style=item.style,
            estimated_minutes=item.estimated_minutes,
            quality=item.quality,
            url=item.url,
            content=item.content,
            prerequisites_covered=tuple(item.prerequisites_covered),
            audience=tuple(item.audience),
            tags=tuple(item.tags),
            question=item.question,
            answer=item.answer,
            explanation=item.explanation,
        )
        for item in resources
    ]


def _knowledge_graph_from_request(nodes: list[KnowledgeNodeRequest]) -> list[KnowledgeNode]:
    return [
        KnowledgeNode(
            name=item.name,
            prerequisites=tuple(item.prerequisites),
            importance=item.importance,
        )
        for item in nodes
    ]


def _student_goals(student: StudentRequest, context: CourseContextRequest | None) -> list[str]:
    goals = list(student.goals)
    if context and context.requirement and context.requirement not in goals:
        goals.append(context.requirement)
    return goals
