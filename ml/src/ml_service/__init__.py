"""Machine learning services for personalized learning."""

__version__ = "1.0.0"

from .application.agents import AgentTrace
from .application.pipeline import LearningMLPipeline
from .application.tutor import TutorAgent
from .domain.diagnostics import AssessmentItem, AssessmentResponse, DiagnosticEngine
from .domain.models import (
    InteractionEvent,
    KnowledgeNode,
    LearningResource,
    Recommendation,
    StudentProfile,
)

__all__ = [
    "__version__",
    "InteractionEvent",
    "KnowledgeNode",
    "LearningResource",
    "Recommendation",
    "StudentProfile",
    "LearningMLPipeline",
    "AgentTrace",
    "AssessmentItem",
    "AssessmentResponse",
    "DiagnosticEngine",
    "TutorAgent",
]
