import re
from difflib import SequenceMatcher

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.adapters.ml_service_client import MLServiceClient
from backend.app.core.config import get_settings
from backend.app.core.database import check_database, get_db
from backend.app.core.security import (
    create_access_token,
    get_current_user,
    hash_password,
    optional_user,
    require_role,
    verify_password,
)
from backend.app.models import (
    Course,
    CourseResource,
    EvaluationResult,
    ImportJob,
    KnowledgePoint,
    Question,
    StudentAnswer,
    User,
)
from backend.app.schemas.dto import (
    AssessmentQuestionOut,
    AuthLoginRequest,
    AuthRegisterRequest,
    AuthResponse,
    CourseResourceOut,
    EvaluationSubmitRequest,
    EvaluationSubmitResponse,
    ImportJobOut,
    LearningStartRequest,
    LearningStartResponse,
    PathNodeOut,
    PathPlanRequest,
    PathPlanResponse,
    ProfileAnalyzeRequest,
    ProfileAnalyzeResponse,
    QuestionOut,
    ResourceGenerateRequest,
    ResourceGenerateResponse,
    ResourceImportRequest,
    ResourceOut,
    StudentProfileOut,
    TutorAskRequest,
    TutorAskResponse,
    UserOut,
)
from backend.app.services.import_service import resource_import_service
from backend.app.services.learning_service import learning_service

router = APIRouter()


def _answer_matches(question_type: str, actual: str, expected: str) -> bool:
    def normalize(value: str) -> str:
        return re.sub(r"[^0-9a-zA-Z\u4e00-\u9fff]", "", value).casefold()

    actual_value = normalize(actual)
    expected_value = normalize(expected)
    if not actual_value or not expected_value:
        return False
    if question_type == "true_false":
        truthy = {"true", "正确", "对", "是"}
        falsy = {"false", "错误", "错", "否"}
        if actual_value in truthy:
            actual_value = "true"
        elif actual_value in falsy:
            actual_value = "false"
    if actual_value == expected_value:
        return True
    if min(len(actual_value), len(expected_value)) >= 4 and (
        actual_value in expected_value or expected_value in actual_value
    ):
        return True
    return SequenceMatcher(None, actual_value, expected_value).ratio() >= 0.68


def to_profile_out(profile: dict) -> StudentProfileOut:
    return StudentProfileOut(**profile)


def to_resource_out(resource) -> ResourceOut:
    return ResourceOut(
        id=resource.id,
        title=resource.title,
        resource_type=resource.resource_type,
        content=resource.content,
        review_status=resource.review_status,
        review_notes=resource.review_notes,
    )


def to_path_response(path, nodes) -> PathPlanResponse:
    return PathPlanResponse(
        path_id=path.id,
        title=path.title,
        goal=path.goal,
        nodes=[
            PathNodeOut(
                id=node.id,
                step_order=node.step_order,
                title=node.title,
                objective=node.objective,
                estimated_minutes=node.estimated_minutes,
                resource_id=node.resource_id,
            )
            for node in nodes
        ],
    )


@router.get("/health", tags=["system"])
def health() -> dict:
    settings = get_settings()
    ml_status = False
    if settings.use_ml_service:
        try:
            ml_status = MLServiceClient(timeout=2.0).health().get("status") == "ok"
        except Exception:
            ml_status = False
    redis_status = _check_redis(settings.redis_url)
    qwen_configured = bool(settings.dashscope_api_key) or settings.learnpilot_llm_mode.lower() in {
        "template",
        "offline",
    }
    return {
        "status": "ok",
        "database": check_database(),
        "ml_service": ml_status,
        "redis": redis_status,
        "qwen_configured": qwen_configured,
        "llm_mode": settings.learnpilot_llm_mode,
    }


@router.post("/api/v1/auth/register", response_model=AuthResponse, tags=["auth"])
def register(payload: AuthRegisterRequest, db: Session = Depends(get_db)) -> AuthResponse:
    email = payload.email.strip() if payload.email else None
    if email and db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")
    user = User(
        username=payload.username,
        display_name=payload.display_name or payload.username,
        email=email,
        role="student",
        is_admin=False,
        status="active",
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return AuthResponse(access_token=create_access_token(user), user=to_user_out(user))


@router.post("/api/v1/auth/login", response_model=AuthResponse, tags=["auth"])
def login(payload: AuthLoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    user = db.query(User).filter(User.username == payload.username).first()
    if (
        user is None
        or (user.status or "active") == "deleted"
        or not verify_password(payload.password, user.password_hash)
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    return AuthResponse(access_token=create_access_token(user), user=to_user_out(user))


@router.get("/api/v1/auth/me", response_model=UserOut, tags=["auth"])
def me(user: User = Depends(get_current_user)) -> UserOut:
    return to_user_out(user)


@router.get("/api/v1/courses", tags=["course"])
def list_courses(db: Session = Depends(get_db)) -> list[dict]:
    return [{"id": item.id, "name": item.name, "description": item.description} for item in db.query(Course).all()]


@router.get("/api/v1/knowledge-points", tags=["course"])
def list_knowledge_points(course_id: int | None = None, db: Session = Depends(get_db)) -> list[dict]:
    query = db.query(KnowledgePoint)
    if course_id:
        query = query.filter(KnowledgePoint.course_id == course_id)
    return [
        {
            "id": item.id,
            "course_id": item.course_id,
            "name": item.name,
            "description": item.description,
            "difficulty": item.difficulty,
        }
        for item in query.all()
    ]


@router.post("/api/v1/courses/{course_id}/resources/import", response_model=ImportJobOut, tags=["course"])
def import_course_resource(
    course_id: int,
    payload: ResourceImportRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("teacher", "admin")),
) -> ImportJobOut:
    if db.get(Course, course_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    job = resource_import_service.import_payload(
        db, course_id, user.id, payload.filename, payload.source_type, payload.content
    )
    return to_import_job_out(job)


@router.get("/api/v1/import-jobs/{job_id}", response_model=ImportJobOut, tags=["course"])
def get_import_job(job_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> ImportJobOut:
    job = db.get(ImportJob, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import job not found")
    if user.role == "student" and job.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    return to_import_job_out(job)


@router.get("/api/v1/courses/{course_id}/resources", response_model=list[CourseResourceOut], tags=["course"])
def list_course_resources(course_id: int, db: Session = Depends(get_db)) -> list[CourseResourceOut]:
    return [
        CourseResourceOut(
            id=item.id,
            course_id=item.course_id,
            knowledge_point_id=item.knowledge_point_id,
            title=item.title,
            resource_type=item.resource_type,
            content=item.content,
            source=item.source,
            source_type=item.source_type,
            status=item.status,
            version=item.version,
        )
        for item in db.query(CourseResource).filter(CourseResource.course_id == course_id).all()
    ]


@router.get("/api/v1/courses/{course_id}/questions", response_model=list[QuestionOut], tags=["course"])
def list_course_questions(
    course_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("teacher", "admin")),
) -> list[QuestionOut]:
    return [
        QuestionOut(
            id=item.id,
            course_id=item.course_id,
            knowledge_point_id=item.knowledge_point_id,
            question_type=item.question_type,
            stem=item.stem,
            answer=item.answer,
            explanation=item.explanation,
            difficulty=item.difficulty,
            source=item.source,
        )
        for item in db.query(Question).filter(Question.course_id == course_id).all()
    ]


@router.get(
    "/api/v1/courses/{course_id}/assessment/questions",
    response_model=list[AssessmentQuestionOut],
    tags=["evaluation"],
)
def list_assessment_questions(
    course_id: int,
    limit: int = 5,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[AssessmentQuestionOut]:
    rows = db.query(Question).filter(Question.course_id == course_id).order_by(Question.id.asc()).limit(limit).all()
    return [
        AssessmentQuestionOut(
            id=item.id,
            course_id=item.course_id,
            knowledge_point_id=item.knowledge_point_id,
            question_type=item.question_type,
            stem=item.stem,
            options=[],
            difficulty=item.difficulty,
        )
        for item in rows
    ]


@router.post("/api/v1/profile/analyze", response_model=ProfileAnalyzeResponse, tags=["profile"])
def analyze_profile(
    payload: ProfileAnalyzeRequest, db: Session = Depends(get_db), current_user: User | None = Depends(optional_user)
) -> ProfileAnalyzeResponse:
    db_profile, profile = learning_service.analyze_profile(
        db, resolve_user_id(payload.user_id, current_user), payload.text
    )
    return ProfileAnalyzeResponse(profile_id=db_profile.id, profile=to_profile_out(profile))


@router.post("/api/v1/resources/generate", response_model=ResourceGenerateResponse, tags=["resource"])
def generate_resources(
    payload: ResourceGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(optional_user),
) -> ResourceGenerateResponse:
    user_id = resolve_user_id(payload.user_id, current_user)
    resources = learning_service.generate_resources(
        db,
        user_id,
        payload.course_id,
        payload.topic,
        payload.weak_points,
        payload.resource_types,
    )
    return ResourceGenerateResponse(resources=[to_resource_out(item) for item in resources])


@router.post("/api/v1/paths/plan", response_model=PathPlanResponse, tags=["path"])
def plan_path(payload: PathPlanRequest, db: Session = Depends(get_db)) -> PathPlanResponse:
    path, nodes = learning_service.plan_path(
        db, payload.user_id, payload.course_id, payload.goal, payload.weak_points, payload.resource_ids
    )
    return to_path_response(path, nodes)


@router.post("/api/v1/tutor/ask", response_model=TutorAskResponse, tags=["tutor"])
def ask_tutor(
    payload: TutorAskRequest, db: Session = Depends(get_db), current_user: User | None = Depends(optional_user)
) -> TutorAskResponse:
    answer = learning_service.ask_tutor(
        db,
        resolve_user_id(payload.user_id, current_user),
        payload.question,
        payload.profile.model_dump() if payload.profile else None,
        payload.history,
    )
    return TutorAskResponse(**answer)


@router.post("/api/v1/evaluations/submit", response_model=EvaluationSubmitResponse, tags=["evaluation"])
def submit_evaluation(
    payload: EvaluationSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(optional_user),
) -> EvaluationSubmitResponse:
    user_id = resolve_user_id(payload.user_id, current_user)
    wrong_items: list[dict] = []
    if payload.answers:
        question_ids = [item.question_id for item in payload.answers]
        questions = db.query(Question).filter(Question.id.in_(question_ids)).all()
        question_map = {item.id: item for item in questions}
        correct_count = 0
        for submitted in payload.answers:
            question = question_map.get(submitted.question_id)
            if question is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Question {submitted.question_id} does not exist",
                )
            expected = (question.answer or "").strip()
            actual = submitted.answer.strip()
            correct = _answer_matches(question.question_type, actual, expected)
            correct_count += int(correct)
            db.add(
                StudentAnswer(
                    user_id=user_id,
                    course_id=question.course_id,
                    question_id=question.id,
                    knowledge_point=str(question.knowledge_point_id or ""),
                    answer=actual,
                    score=1.0 if correct else 0.0,
                    correct=correct,
                    elapsed_seconds=submitted.elapsed_seconds,
                )
            )
            if not correct:
                wrong_items.append(
                    {
                        "question_id": question.id,
                        "stem": question.stem,
                        "user_answer": actual,
                        "correct_answer": expected,
                        "explanation": question.explanation or "",
                    }
                )
        total_count = len(payload.answers)
    else:
        if payload.correct_count is None or payload.total_count is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="answers or correct_count/total_count is required",
            )
        correct_count = payload.correct_count
        total_count = payload.total_count

    evaluation = learning_service.evaluate(
        db,
        user_id,
        payload.path_id,
        correct_count,
        total_count,
        payload.completed_resource_count,
        payload.study_minutes,
    )
    accuracy = correct_count / total_count
    evaluation.profile_update = {
        **(evaluation.profile_update or {}),
        "assessment": {
            "correct_count": correct_count,
            "total_count": total_count,
            "accuracy": accuracy,
            "wrong_items": wrong_items,
        },
    }
    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)
    return EvaluationSubmitResponse(
        evaluation_id=evaluation.id,
        mastery_score=evaluation.mastery_score,
        feedback=evaluation.feedback,
        profile_update=evaluation.profile_update or {},
        path_adjustment=(evaluation.profile_update or {}).get("path_adjustment"),
        updated_profile=(evaluation.profile_update or {}).get("mastery") and evaluation.profile_update,
        score=round(accuracy * 100, 1),
        accuracy=accuracy,
        correct_count=correct_count,
        total_count=total_count,
        wrong_items=wrong_items,
    )


def _evaluation_payload(evaluation: EvaluationResult) -> dict:
    profile_update = evaluation.profile_update or {}
    assessment = profile_update.get("assessment") or {}
    accuracy = assessment.get("accuracy")
    return {
        "evaluation_id": evaluation.id,
        "path_id": evaluation.path_id,
        "mastery_score": evaluation.mastery_score,
        "score": round(float(accuracy) * 100, 1) if accuracy is not None else None,
        "accuracy": accuracy,
        "correct_count": assessment.get("correct_count"),
        "total_count": assessment.get("total_count"),
        "wrong_items": assessment.get("wrong_items") or [],
        "feedback": evaluation.feedback,
        "profile_update": profile_update,
        "created_at": evaluation.created_at.isoformat() if evaluation.created_at else None,
    }


@router.get("/api/v1/evaluations/history", tags=["evaluation"])
def evaluation_history(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    rows = (
        db.query(EvaluationResult)
        .filter(EvaluationResult.user_id == current_user.id)
        .order_by(EvaluationResult.id.desc())
        .limit(max(1, min(limit, 100)))
        .all()
    )
    return {"items": [_evaluation_payload(item) for item in rows], "total": len(rows)}


@router.get("/api/v1/evaluations/{evaluation_id}", tags=["evaluation"])
def evaluation_detail(
    evaluation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    evaluation = db.get(EvaluationResult, evaluation_id)
    if evaluation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation not found")
    is_admin = bool(current_user.is_admin) or current_user.role == "admin"
    if evaluation.user_id != current_user.id and not is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Evaluation access denied")
    return _evaluation_payload(evaluation)


@router.post("/api/v1/learning/start", response_model=LearningStartResponse, tags=["workflow"])
def start_learning(
    payload: LearningStartRequest, db: Session = Depends(get_db), current_user: User | None = Depends(optional_user)
) -> LearningStartResponse:
    user_id = resolve_user_id(payload.user_id, current_user)
    profile, resources, path, nodes = learning_service.start_learning(
        db,
        user_id,
        payload.course_id,
        payload.requirement,
    )
    return LearningStartResponse(
        profile=to_profile_out(profile),
        resources=[to_resource_out(item) for item in resources],
        path=to_path_response(path, nodes),
        ml_trace=(learning_service.last_ml_result or {}).get("agent_traces", []),
        retrieval_evidence=(learning_service.last_ml_result or {}).get("retrieval_evidence", []),
        generation_quality=(learning_service.last_ml_result or {}).get("generation_quality"),
    )


def _check_redis(redis_url: str) -> bool:
    try:
        import redis

        client = redis.Redis.from_url(redis_url, socket_connect_timeout=1, socket_timeout=1)
        return bool(client.ping())
    except Exception:
        return False


def to_user_out(user: User) -> UserOut:
    return UserOut(id=user.id, username=user.username, display_name=user.display_name, role=user.role)


def resolve_user_id(payload_user_id: int | None, current_user: User | None) -> int:
    return current_user.id if current_user else payload_user_id or 1


def to_import_job_out(job: ImportJob) -> ImportJobOut:
    return ImportJobOut(
        id=job.id,
        course_id=job.course_id,
        user_id=job.user_id,
        source_type=job.source_type,
        filename=job.filename,
        status=job.status,
        message=job.message,
        result=job.result,
    )
