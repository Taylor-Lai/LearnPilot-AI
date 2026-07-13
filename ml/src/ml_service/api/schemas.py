"""Versioned HTTP request contracts for the ML service.

Keep transport validation here so application and domain layers stay independent
from FastAPI and Pydantic.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from ..domain.models import LearningStyle


class InteractionEventRequest(BaseModel):
    student_id: str | None = None
    resource_id: str = ""
    knowledge_points: list[str] = Field(default_factory=list)
    score: float | None = Field(default=None, ge=0.0, le=1.0)
    completed: bool = False
    dwell_seconds: int = Field(default=0, ge=0)
    liked: bool | None = None
    timestamp: int | None = None
    event_type: str = "learning"
    attempts: int = Field(default=1, ge=1)
    hint_count: int = Field(default=0, ge=0)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    resource_style: LearningStyle | None = None
    session_id: str | None = None


class StudentRequest(BaseModel):
    student_id: str = Field(examples=["stu_001"])
    diagnostics: dict[str, float] = Field(default_factory=dict)
    goals: list[str] = Field(default_factory=list)
    preferred_styles: list[LearningStyle] = Field(default_factory=list)
    events: list[InteractionEventRequest] = Field(default_factory=list)
    previous_mastery: dict[str, float] = Field(default_factory=dict)

    @field_validator("diagnostics", "previous_mastery")
    @classmethod
    def validate_mastery_scores(cls, value: dict[str, float]) -> dict[str, float]:
        invalid = {point: score for point, score in value.items() if not 0.0 <= score <= 1.0}
        if invalid:
            raise ValueError(f"mastery scores must be in [0, 1], invalid={invalid}")
        return value


class ResourceRequest(BaseModel):
    resource_id: str
    title: str
    knowledge_points: list[str] = Field(default_factory=list)
    difficulty: float = Field(default=0.55, ge=0.0, le=1.0)
    style: LearningStyle = "text"
    estimated_minutes: int = Field(default=25, ge=1, le=600)
    quality: float = Field(default=0.8, ge=0.0, le=1.0)
    url: str | None = None
    content: str = ""
    prerequisites_covered: list[str] = Field(default_factory=list)
    audience: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    question: str = ""
    answer: str = ""
    explanation: str = ""


class KnowledgeNodeRequest(BaseModel):
    name: str
    prerequisites: list[str] = Field(default_factory=list)
    importance: float = Field(default=1.0, ge=0.0, le=3.0)


class CourseContextRequest(BaseModel):
    course_id: int | str | None = None
    course_name: str | None = None
    requirement: str | None = None


class RecommendRequest(BaseModel):
    student: StudentRequest
    top_k: int = Field(default=6, ge=1, le=20)
    resources: list[ResourceRequest] | None = None
    knowledge_graph: list[KnowledgeNodeRequest] | None = None
    course_context: CourseContextRequest | None = None


class DiagnoseRequest(BaseModel):
    answers: dict[str, float]

    @field_validator("answers")
    @classmethod
    def validate_answers(cls, value: dict[str, float]) -> dict[str, float]:
        invalid = {point: score for point, score in value.items() if not 0.0 <= score <= 1.0}
        if invalid:
            raise ValueError(f"answers must be in [0, 1], invalid={invalid}")
        return value


class GenerateRequest(BaseModel):
    student: StudentRequest
    resources: list[ResourceRequest] | None = None
    knowledge_graph: list[KnowledgeNodeRequest] | None = None
    course_context: CourseContextRequest | None = None


class FeedbackRequest(BaseModel):
    student: StudentRequest
    feedback_events: list[InteractionEventRequest]
    top_k: int = Field(default=6, ge=1, le=20)
    resources: list[ResourceRequest] | None = None
    knowledge_graph: list[KnowledgeNodeRequest] | None = None
    course_context: CourseContextRequest | None = None


class UpdateProfileRequest(BaseModel):
    student: StudentRequest


class AssessmentItemRequest(BaseModel):
    item_id: str
    knowledge_points: list[str] = Field(min_length=1)
    difficulty: float = Field(default=0.5, ge=0.0, le=1.0)
    discrimination: float = Field(default=1.0, ge=0.2, le=2.5)
    max_score: float = Field(default=1.0, gt=0.0)
    expected_seconds: int = Field(default=120, ge=1)


class AssessmentResponseRequest(BaseModel):
    item_id: str
    score: float = Field(ge=0.0)
    elapsed_seconds: int = Field(default=0, ge=0)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    hint_count: int = Field(default=0, ge=0)
    attempts: int = Field(default=1, ge=1)


class AssessmentDiagnoseRequest(BaseModel):
    items: list[AssessmentItemRequest] = Field(min_length=1)
    responses: list[AssessmentResponseRequest] = Field(default_factory=list)
    previous_mastery: dict[str, float] = Field(default_factory=dict)


class TutorTurnRequest(BaseModel):
    role: str = Field(pattern="^(student|assistant|system)$")
    content: str = Field(min_length=1, max_length=4000)


class TutorRequest(BaseModel):
    student: StudentRequest
    question: str = Field(min_length=1, max_length=4000)
    knowledge_point: str | None = None
    history: list[TutorTurnRequest] = Field(default_factory=list, max_length=20)
    resources: list[ResourceRequest] | None = None
    knowledge_graph: list[KnowledgeNodeRequest] | None = None
    course_context: CourseContextRequest | None = None
