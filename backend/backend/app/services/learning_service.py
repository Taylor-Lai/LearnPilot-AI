from typing import Any

from sqlalchemy.orm import Session

from backend.app.adapters.ml_adapter import MLAdapter
from backend.app.agents.diagnosis_agent import DiagnosisAgent
from backend.app.agents.evaluator_agent import EvaluatorAgent
from backend.app.agents.planner_agent import PlannerAgent
from backend.app.agents.profile_agent import ProfileAgent
from backend.app.agents.resource_agent import ResourceAgent
from backend.app.agents.retriever_agent import RetrieverAgent
from backend.app.agents.review_agent import ReviewAgent
from backend.app.agents.tutor_agent import TutorAgent
from backend.app.models import (
    ChatMessage,
    CourseResource,
    EvaluationResult,
    FeedbackEvent,
    KnowledgePoint,
    LearningPath,
    LearningPathNode,
    LearningResource,
    Question,
    ResourceCenter,
    ResourceChunk,
    StudentProfile,
    StudentWeakness,
)


class LearningService:
    REQUIRED_RESOURCE_TYPES = (
        "lecture",
        "exercise",
        "mind_map",
        "reading",
        "code_example",
        "video_script",
    )

    def __init__(self) -> None:
        self.profile_agent = ProfileAgent()
        self.diagnosis_agent = DiagnosisAgent()
        self.retriever_agent = RetrieverAgent()
        self.resource_agent = ResourceAgent()
        self.review_agent = ReviewAgent()
        self.planner_agent = PlannerAgent()
        self.tutor_agent = TutorAgent()
        self.evaluator_agent = EvaluatorAgent()
        self.ml_adapter = MLAdapter()
        self.last_ml_result: dict[str, Any] | None = None

    def analyze_profile(self, db: Session, user_id: int, text: str) -> tuple[StudentProfile, dict]:
        try:
            profile = self._normalize_profile_payload(self.profile_agent.run(text))
            db_profile = (
                db.query(StudentProfile)
                .filter(StudentProfile.user_id == user_id)
                .order_by(StudentProfile.id.desc())
                .first()
            )

            if db_profile is None:
                db_profile = StudentProfile(user_id=user_id, raw_text=text)

            db_profile.major = profile.get("major")
            db_profile.grade = profile.get("grade")
            db_profile.course = profile.get("course")
            db_profile.goal = profile.get("goal")
            db_profile.preference = profile.get("preference")
            db_profile.cognitive_style = profile.get("cognitive_style")
            db_profile.knowledge_level = profile.get("knowledge_level")
            db_profile.raw_text = text

            db.add(db_profile)
            db.flush()

            db.query(StudentWeakness).filter(StudentWeakness.profile_id == db_profile.id).delete(
                synchronize_session=False
            )
            weaknesses = self.diagnosis_agent.run(profile)
            for weakness in weaknesses:
                db.add(
                    StudentWeakness(
                        user_id=user_id,
                        profile_id=db_profile.id,
                        knowledge_point=weakness["knowledge_point"],
                        weakness_level=weakness["weakness_level"],
                        evidence=weakness["evidence"],
                    )
                )

            db.flush()
            db.commit()
            db.refresh(db_profile)
            profile["weak_points"] = [item["knowledge_point"] for item in weaknesses]
            return db_profile, profile
        except Exception:
            db.rollback()
            raise

    def generate_resources(
        self,
        db: Session,
        user_id: int,
        course_id: int | None,
        topic: str,
        weak_points: list[str],
        resource_types: list[str],
        reference_titles: list[str] | None = None,
    ) -> list[LearningResource]:
        try:
            if reference_titles:
                reference_hint = f"{topic} (reference resources: {', '.join(reference_titles[:3])})"
            else:
                reference_hint = topic

            generated = self.resource_agent.run(reference_hint, weak_points, resource_types)
            resources = []
            for item in generated:
                reviewed = self.review_agent.run(item)
                resource = LearningResource(
                    user_id=user_id,
                    course_id=course_id,
                    title=reviewed["title"],
                    resource_type=reviewed["resource_type"],
                    content=reviewed["content"],
                    review_status=reviewed["review_status"],
                    review_notes=reviewed.get("review_notes"),
                )
                db.add(resource)
                resources.append(resource)

            db.flush()
            db.commit()
            for resource in resources:
                db.refresh(resource)
            return resources
        except Exception:
            db.rollback()
            raise

    def save_resource_items(
        self,
        db: Session,
        user_id: int,
        course_id: int | None,
        items: list[dict],
    ) -> list[LearningResource]:
        try:
            resources = []
            for item in items:
                reviewed = self.review_agent.run(item)
                resource = LearningResource(
                    user_id=user_id,
                    course_id=course_id,
                    title=reviewed["title"],
                    resource_type=reviewed["resource_type"],
                    content=reviewed["content"],
                    review_status=reviewed["review_status"],
                    review_notes=reviewed.get("review_notes"),
                )
                db.add(resource)
                resources.append(resource)

            db.flush()
            db.commit()
            for resource in resources:
                db.refresh(resource)
            return resources
        except Exception:
            db.rollback()
            raise

    def retrieve_course_resources(self, db: Session, course_id: int | None, weak_points: list[str]) -> list[str]:
        resources = self.retriever_agent.run(db, course_id, weak_points)
        return [item.title for item in resources]

    def plan_path(
        self,
        db: Session,
        user_id: int,
        course_id: int | None,
        goal: str,
        weak_points: list[str],
        resource_ids: list[int],
    ) -> tuple[LearningPath, list[LearningPathNode]]:
        try:
            plan = self.planner_agent.run(goal, weak_points, resource_ids)
            path = LearningPath(user_id=user_id, course_id=course_id, title=plan["title"], goal=goal)
            db.add(path)
            db.flush()

            nodes = []
            for node in plan["nodes"]:
                db_node = LearningPathNode(
                    path_id=path.id,
                    resource_id=node.get("resource_id"),
                    step_order=node["step_order"],
                    title=node["title"],
                    objective=node["objective"],
                    estimated_minutes=node["estimated_minutes"],
                )
                db.add(db_node)
                nodes.append(db_node)

            db.flush()
            db.commit()
            db.refresh(path)
            for node in nodes:
                db.refresh(node)
            return path, nodes
        except Exception:
            db.rollback()
            raise

    def start_learning(
        self,
        db: Session,
        user_id: int,
        course_id: int | None,
        requirement: str,
    ) -> tuple[dict, list[LearningResource], LearningPath, list[LearningPathNode]]:
        ml_result = self.ml_adapter.recommend_learning(
            db=db,
            user_id=user_id,
            course_id=course_id,
            requirement=requirement,
        )
        self.last_ml_result = ml_result
        if not ml_result:
            return self._start_learning_with_local_agents(db, user_id, course_id, requirement)

        profile = self._normalize_profile_payload(
            self._extract_ml_profile(ml_result) or self.profile_agent.run(requirement)
        )
        weak_points = self._extract_ml_weak_points(ml_result, profile)
        if not weak_points:
            weak_points = [item["knowledge_point"] for item in self.diagnosis_agent.run(profile)]
        profile["weak_points"] = weak_points

        self._save_profile_and_weaknesses(db, user_id, requirement, profile, weak_points)

        resource_items = self._extract_ml_resources(ml_result)
        if resource_items:
            resource_items = self._ensure_resource_type_coverage(
                resource_items,
                profile.get("course") or "课程学习",
                weak_points,
            )
            resources = self.save_resource_items(db, user_id, course_id, resource_items)
        else:
            reference_titles = self.retrieve_course_resources(db, course_id, weak_points)
            resources = self.generate_resources(
                db,
                user_id,
                course_id,
                profile.get("course") or "课程学习",
                weak_points,
                list(self.REQUIRED_RESOURCE_TYPES),
                reference_titles,
            )

        path_payload = self._extract_ml_path(ml_result)
        if path_payload:
            path, nodes = self._save_path_payload(
                db,
                user_id,
                course_id,
                path_payload,
                profile.get("goal") or "提升课程掌握度",
                [item.id for item in resources],
                weak_points,
            )
        else:
            path, nodes = self.plan_path(
                db,
                user_id,
                course_id,
                profile.get("goal") or "提升课程掌握度",
                weak_points,
                [item.id for item in resources],
            )

        return profile, resources, path, nodes

    @staticmethod
    def _normalize_profile_payload(profile: dict) -> dict:
        normalized = dict(profile or {})
        text_fields = (
            "major",
            "grade",
            "course",
            "goal",
            "preference",
            "cognitive_style",
            "knowledge_level",
        )
        for field in text_fields:
            value = normalized.get(field)
            if value is None:
                normalized[field] = ""
            elif isinstance(value, (list, tuple, set)):
                normalized[field] = "、".join(str(item) for item in value if item)
            elif isinstance(value, dict):
                normalized[field] = "、".join(f"{key}: {item}" for key, item in value.items() if item)
            else:
                normalized[field] = str(value)

        weak_points = normalized.get("weak_points") or []
        if isinstance(weak_points, str):
            weak_points = [
                item.strip()
                for item in weak_points.replace("，", ",").replace("、", ",").replace("；", ",").split(",")
                if item.strip()
            ]
        elif not isinstance(weak_points, list):
            weak_points = [str(weak_points)]
        normalized["weak_points"] = [str(item) for item in weak_points if item]
        return normalized

    def _start_learning_with_local_agents(
        self,
        db: Session,
        user_id: int,
        course_id: int | None,
        requirement: str,
    ) -> tuple[dict, list[LearningResource], LearningPath, list[LearningPathNode]]:
        _, profile = self.analyze_profile(db, user_id, requirement)
        topic = profile.get("course") or "课程学习"
        weak_points = profile.get("weak_points", [])
        reference_titles = self.retrieve_course_resources(db, course_id, weak_points)
        resources = self.generate_resources(
            db,
            user_id,
            course_id,
            topic,
            weak_points,
            list(self.REQUIRED_RESOURCE_TYPES),
            reference_titles,
        )
        path, nodes = self.plan_path(
            db,
            user_id,
            course_id,
            profile.get("goal") or "提升课程掌握度",
            weak_points,
            [item.id for item in resources],
        )
        return profile, resources, path, nodes

    def _save_profile_and_weaknesses(
        self,
        db: Session,
        user_id: int,
        raw_text: str,
        profile: dict,
        weak_points: list[str],
    ) -> StudentProfile:
        try:
            db_profile = (
                db.query(StudentProfile)
                .filter(StudentProfile.user_id == user_id)
                .order_by(StudentProfile.id.desc())
                .first()
            )
            if db_profile is None:
                db_profile = StudentProfile(user_id=user_id, raw_text=raw_text)

            db_profile.major = profile.get("major")
            db_profile.grade = profile.get("grade")
            db_profile.course = profile.get("course")
            db_profile.goal = profile.get("goal")
            db_profile.preference = profile.get("preference")
            db_profile.cognitive_style = profile.get("cognitive_style")
            db_profile.knowledge_level = profile.get("knowledge_level")
            db_profile.mastery = profile.get("mastery") if isinstance(profile.get("mastery"), dict) else None
            db_profile.weak_points_json = weak_points
            db_profile.engagement_score = profile.get("engagement_score")
            db_profile.forgetting_risk = profile.get("forgetting_risk")
            db_profile.learning_stage = profile.get("learning_stage")
            db_profile.raw_text = raw_text
            db.add(db_profile)
            db.flush()

            db.query(StudentWeakness).filter(StudentWeakness.profile_id == db_profile.id).delete(
                synchronize_session=False
            )
            for index, point in enumerate(weak_points):
                db.add(
                    StudentWeakness(
                        user_id=user_id,
                        profile_id=db_profile.id,
                        knowledge_point=str(point),
                        weakness_level=max(0.45, 0.85 - index * 0.08),
                        evidence="LearnPilot AI recommendation" if weak_points else "Local diagnosis",
                    )
                )

            db.flush()
            db.commit()
            db.refresh(db_profile)
            return db_profile
        except Exception:
            db.rollback()
            raise

    def _extract_ml_profile(self, data: dict[str, Any]) -> dict | None:
        profile = (
            data.get("profile")
            or data.get("student_profile")
            or data.get("learner_profile")
            or data.get("result", {}).get("profile")
            or data.get("data", {}).get("profile")
        )
        if not isinstance(profile, dict):
            return None
        return {
            "major": profile.get("major"),
            "grade": profile.get("grade"),
            "course": profile.get("course") or profile.get("subject"),
            "goal": profile.get("goal") or profile.get("learning_goal"),
            "weak_points": profile.get("weak_points")
            or profile.get("weaknesses")
            or profile.get("knowledge_gaps")
            or [],
            "preference": profile.get("preference") or profile.get("learning_preference"),
            "cognitive_style": profile.get("cognitive_style"),
            "knowledge_level": profile.get("knowledge_level") or profile.get("level"),
            "mastery": profile.get("mastery") if isinstance(profile.get("mastery"), dict) else {},
            "engagement_score": profile.get("engagement_score"),
            "forgetting_risk": profile.get("forgetting_risk"),
            "learning_stage": profile.get("learning_stage"),
        }

    def _extract_ml_weak_points(self, data: dict[str, Any], profile: dict) -> list[str]:
        raw_items = (
            profile.get("weak_points")
            or data.get("weak_points")
            or data.get("weaknesses")
            or data.get("knowledge_gaps")
            or data.get("diagnosis", {}).get("weak_points")
            or data.get("diagnosis", {}).get("weaknesses")
            or []
        )
        if isinstance(raw_items, dict):
            raw_items = list(raw_items.values())

        weak_points = []
        for item in raw_items:
            if isinstance(item, str):
                weak_points.append(item)
            elif isinstance(item, dict):
                point = item.get("knowledge_point") or item.get("point") or item.get("name") or item.get("topic")
                if point:
                    weak_points.append(str(point))
        return weak_points

    def _extract_ml_resources(self, data: dict[str, Any]) -> list[dict]:
        raw_items = []
        containers = [
            data,
            data.get("result") if isinstance(data.get("result"), dict) else {},
            data.get("data") if isinstance(data.get("data"), dict) else {},
        ]
        for container in containers:
            for key in ("resources", "generated_cards", "cards", "learning_resources", "recommendations"):
                value = container.get(key)
                if isinstance(value, dict):
                    raw_items.extend(value.values())
                elif isinstance(value, list):
                    raw_items.extend(value)

        resources = []
        seen = set()
        for index, item in enumerate(raw_items, start=1):
            if isinstance(item, str):
                resource = {
                    "title": f"ML 生成资源 {index}",
                    "resource_type": "reading",
                    "content": item,
                }
            elif isinstance(item, dict):
                content = (
                    item.get("content")
                    or item.get("body")
                    or item.get("text")
                    or item.get("summary")
                    or self._ml_card_to_content(item)
                )
                if not content:
                    continue
                resource = {
                    "title": str(item.get("title") or item.get("name") or f"ML 生成资源 {index}"),
                    "resource_type": str(item.get("resource_type") or item.get("type") or "reading"),
                    "content": str(content),
                }
            else:
                continue

            identity = (resource["title"], resource["resource_type"], resource["content"])
            if identity not in seen:
                seen.add(identity)
                resources.append(resource)
        return resources

    def _ensure_resource_type_coverage(
        self,
        ml_resources: list[dict],
        topic: str,
        weak_points: list[str],
    ) -> list[dict]:
        resources = list(ml_resources)
        existing_types = {
            str(item.get("resource_type") or "").strip().lower() for item in resources if isinstance(item, dict)
        }
        missing_types = [
            resource_type for resource_type in self.REQUIRED_RESOURCE_TYPES if resource_type not in existing_types
        ]
        if not missing_types:
            return resources

        generated = self.resource_agent.run(topic, weak_points, missing_types)
        resources.extend(generated)
        return resources

    def _ml_card_to_content(self, item: dict) -> str:
        parts = [
            item.get("explanation"),
            item.get("example"),
            item.get("practice"),
            item.get("answer"),
            item.get("mistake_analysis"),
            item.get("review_tip"),
        ]
        return "\n\n".join(str(part) for part in parts if part)

    def _extract_ml_path(self, data: dict[str, Any]) -> dict | None:
        path_payload = (
            data.get("learning_path")
            or data.get("path")
            or data.get("study_path")
            or data.get("result", {}).get("learning_path")
            or data.get("data", {}).get("learning_path")
        )
        if isinstance(path_payload, list):
            return {"nodes": path_payload}
        if isinstance(path_payload, dict):
            return path_payload
        return None

    def _save_path_payload(
        self,
        db: Session,
        user_id: int,
        course_id: int | None,
        path_payload: dict,
        fallback_goal: str,
        resource_ids: list[int],
        weak_points: list[str],
    ) -> tuple[LearningPath, list[LearningPathNode]]:
        try:
            goal = str(path_payload.get("goal") or fallback_goal)
            title = str(path_payload.get("title") or path_payload.get("name") or f"{goal} 个性化学习路径")
            raw_nodes = path_payload.get("nodes") or path_payload.get("steps") or path_payload.get("items") or []
            if isinstance(raw_nodes, dict):
                raw_nodes = list(raw_nodes.values())

            local_plan = self.planner_agent.run(goal, weak_points, resource_ids)
            normalized_nodes = []
            for index, item in enumerate(raw_nodes, start=1):
                if not isinstance(item, dict):
                    continue
                normalized_nodes.append(
                    {
                        "step_order": int(item.get("step_order") or item.get("order") or index),
                        "title": str(item.get("title") or item.get("name") or f"第 {index} 步"),
                        "objective": str(item.get("objective") or item.get("description") or item.get("task") or goal),
                        "estimated_minutes": int(item.get("estimated_minutes") or item.get("duration_minutes") or 40),
                        "resource_id": item.get("resource_id"),
                    }
                )

            if len(normalized_nodes) < 6:
                used_orders = {node["step_order"] for node in normalized_nodes}
                for node in local_plan["nodes"]:
                    if len(normalized_nodes) >= 6:
                        break
                    if node["step_order"] not in used_orders:
                        normalized_nodes.append(node)

            for index, node in enumerate(normalized_nodes, start=1):
                node["step_order"] = index
                if not node.get("resource_id") and resource_ids:
                    node["resource_id"] = resource_ids[(index - 1) % len(resource_ids)]

            path = LearningPath(user_id=user_id, course_id=course_id, title=title, goal=goal)
            db.add(path)
            db.flush()

            nodes = []
            for node in normalized_nodes:
                db_node = LearningPathNode(
                    path_id=path.id,
                    resource_id=node.get("resource_id"),
                    step_order=node["step_order"],
                    title=node["title"],
                    objective=node["objective"],
                    estimated_minutes=node["estimated_minutes"],
                )
                db.add(db_node)
                nodes.append(db_node)

            db.flush()
            db.commit()
            db.refresh(path)
            for node in nodes:
                db.refresh(node)
            return path, nodes
        except Exception:
            db.rollback()
            raise

    def ask_tutor(self, db: Session, user_id: int, question: str, profile: dict | None, history: list[str]) -> dict:
        try:
            user_message = ChatMessage(user_id=user_id, role="user", content=question, agent_name="TutorAgent")
            db.add(user_message)
            db.flush()

            evidence = self._retrieve_tutor_evidence(db, question, limit=3)
            answer = self.tutor_agent.run(question, profile, list(history or []), evidence)
            if evidence:
                answer["evidence"] = evidence
            answer["grounded"] = bool(evidence)
            answer["visual_aid"] = self._build_tutor_visual_aid(question, profile)
            assistant_message = ChatMessage(
                user_id=user_id,
                role="assistant",
                content=answer["answer"],
                agent_name="TutorAgent",
            )
            db.add(assistant_message)
            db.flush()
            db.commit()
            db.refresh(user_message)
            db.refresh(assistant_message)
            return answer
        except Exception:
            db.rollback()
            raise

    def _build_tutor_visual_aid(self, question: str, profile: dict | None) -> dict:
        """Return a presentation-safe concept flow without embedding executable markup."""
        topic = question.strip().rstrip("？?。！!")[:36] or "当前知识点"
        weak_points = list((profile or {}).get("weak_points") or [])
        focus = str(weak_points[0])[:24] if weak_points else "关键前置概念"
        return {
            "title": f"{topic} · 理解路径",
            "nodes": [
                {"label": "前置概念", "detail": focus},
                {"label": "核心机制", "detail": "明确条件、步骤与因果关系"},
                {"label": "最小案例", "detail": "用数值、图示或代码验证"},
                {"label": "迁移自测", "detail": "改变一个条件并解释结果"},
            ],
        }

    def evaluate(
        self,
        db: Session,
        user_id: int,
        path_id: int | None,
        correct_count: int,
        total_count: int,
        completed_resource_count: int,
        study_minutes: int,
        course_id: int | None = None,
        assessed_knowledge_points: list[str] | None = None,
    ) -> EvaluationResult:
        try:
            latest_path = db.get(LearningPath, path_id) if path_id else None
            course_id = latest_path.course_id if latest_path else course_id
            path_points = self._knowledge_points_from_path(db, path_id)
            knowledge_points = list(dict.fromkeys([*(assessed_knowledge_points or []), *path_points]))[:8]
            score = correct_count / total_count
            feedback_event = FeedbackEvent(
                user_id=user_id,
                course_id=course_id,
                path_id=path_id,
                knowledge_points=knowledge_points,
                score=score,
                completed=completed_resource_count > 0,
                dwell_seconds=study_minutes * 60,
                liked=True if score >= 0.75 else False if score < 0.45 else None,
                event_metadata={
                    "correct_count": correct_count,
                    "total_count": total_count,
                    "completed_resource_count": completed_resource_count,
                },
            )
            db.add(feedback_event)
            db.flush()

            result = self.evaluator_agent.run(correct_count, total_count, completed_resource_count, study_minutes)
            ml_feedback = self.ml_adapter.feedback_learning(db, user_id, course_id, [feedback_event])
            if isinstance(ml_feedback, dict):
                after = ml_feedback.get("after", {})
                profile = after.get("profile", {}) if isinstance(after, dict) else {}
                if isinstance(profile, dict):
                    result["profile_update"] = {
                        **result.get("profile_update", {}),
                        "mastery": profile.get("mastery", {}),
                        "weak_points": profile.get("weak_points", []),
                        "learning_stage": profile.get("learning_stage"),
                        "engagement_score": profile.get("engagement_score"),
                        "forgetting_risk": profile.get("forgetting_risk"),
                        "path_adjustment": ml_feedback.get("path_adjustment"),
                    }
            result["profile_update"]["adaptation"] = self._build_evaluation_adaptation(
                db=db,
                user_id=user_id,
                path=latest_path,
                course_id=course_id,
                score=score,
                knowledge_points=knowledge_points,
                profile_update=result["profile_update"],
                ml_feedback=ml_feedback,
            )
            evaluation = EvaluationResult(
                user_id=user_id,
                path_id=path_id,
                mastery_score=result["mastery_score"],
                feedback=result["feedback"],
                profile_update=result["profile_update"],
            )
            db.add(evaluation)
            db.flush()

            if result.get("profile_update"):
                db_profile = (
                    db.query(StudentProfile)
                    .filter(StudentProfile.user_id == user_id)
                    .order_by(StudentProfile.id.desc())
                    .first()
                )
                knowledge_level = result["profile_update"].get("knowledge_level")
                if db_profile is not None:
                    if knowledge_level:
                        db_profile.knowledge_level = knowledge_level
                    if isinstance(result["profile_update"].get("mastery"), dict):
                        db_profile.mastery = result["profile_update"]["mastery"]
                    if isinstance(result["profile_update"].get("weak_points"), list):
                        db_profile.weak_points_json = result["profile_update"]["weak_points"]
                    db_profile.learning_stage = (
                        result["profile_update"].get("learning_stage") or db_profile.learning_stage
                    )
                    db_profile.engagement_score = (
                        result["profile_update"].get("engagement_score") or db_profile.engagement_score
                    )
                    db_profile.forgetting_risk = (
                        result["profile_update"].get("forgetting_risk") or db_profile.forgetting_risk
                    )
                    db.add(db_profile)

            db.commit()
            db.refresh(evaluation)
            return evaluation
        except Exception:
            db.rollback()
            raise

    def _build_evaluation_adaptation(
        self,
        db: Session,
        user_id: int,
        path: LearningPath | None,
        course_id: int | None,
        score: float,
        knowledge_points: list[str],
        profile_update: dict,
        ml_feedback: dict | None,
    ) -> dict:
        before_profile = {}
        if isinstance(ml_feedback, dict):
            before = ml_feedback.get("before")
            if isinstance(before, dict) and isinstance(before.get("profile"), dict):
                before_profile = before["profile"]

        before_mastery = before_profile.get("mastery") if isinstance(before_profile.get("mastery"), dict) else {}
        if not before_mastery:
            latest_profile = (
                db.query(StudentProfile)
                .filter(StudentProfile.user_id == user_id)
                .order_by(StudentProfile.id.desc())
                .first()
            )
            if latest_profile is not None and isinstance(latest_profile.mastery, dict):
                before_mastery = dict(latest_profile.mastery)
        after_mastery = profile_update.get("mastery") if isinstance(profile_update.get("mastery"), dict) else {}
        if not after_mastery:
            target_points = knowledge_points or list(before_mastery)
            for point in target_points:
                before_mastery.setdefault(point, 0.5)
            after_mastery = dict(before_mastery)
            for point in target_points:
                previous = float(after_mastery.get(point, 0.5))
                after_mastery[point] = round(max(0.0, min(1.0, previous * 0.7 + score * 0.3)), 4)
            profile_update["mastery"] = after_mastery
        weak_points = [str(item) for item in profile_update.get("weak_points") or knowledge_points if item]
        if not weak_points and after_mastery:
            weak_points = [point for point, _ in sorted(after_mastery.items(), key=lambda item: item[1])[:3]]
        profile_update["weak_points"] = weak_points
        weak_points = list(dict.fromkeys(weak_points))[:6]

        if score < 0.6:
            strategy = "remediation"
            strategy_label = "补弱重学"
            reason = f"本次正确率为 {score:.0%}，优先回到薄弱知识点，补充讲解、示例和基础练习。"
        elif score < 0.8:
            strategy = "consolidation"
            strategy_label = "巩固提升"
            reason = f"本次正确率为 {score:.0%}，保留当前学习阶段并增加针对性练习与错题复盘。"
        else:
            strategy = "advancement"
            strategy_label = "进阶拓展"
            reason = f"本次正确率为 {score:.0%}，缩短基础复习并加入综合实践与进阶资源。"

        point_rows = []
        if course_id is not None:
            point_rows = db.query(KnowledgePoint).filter(KnowledgePoint.course_id == course_id).all()
        point_by_id = {item.id: item.name for item in point_rows}
        resource_query = db.query(CourseResource)
        if course_id is not None:
            resource_query = resource_query.filter(CourseResource.course_id == course_id)
        candidates = resource_query.order_by(CourseResource.id.asc()).all()

        def resource_priority(item: CourseResource) -> tuple[int, int, int]:
            point_name = point_by_id.get(item.knowledge_point_id, "")
            weak_match = any(weak in point_name or point_name in weak for weak in weak_points if point_name)
            preferred = item.resource_type in {"lecture", "exercise", "code_example", "video", "lab"}
            return (0 if weak_match else 1, 0 if preferred else 1, item.id)

        recommendations = []
        used_types: set[str] = set()
        for item in sorted(candidates, key=resource_priority):
            if len(recommendations) >= 5:
                break
            if item.resource_type in used_types and len(candidates) > 5:
                continue
            used_types.add(item.resource_type)
            recommendations.append(
                {
                    "resource_id": item.id,
                    "title": item.title,
                    "resource_type": item.resource_type,
                    "knowledge_point": point_by_id.get(item.knowledge_point_id),
                    "url": f"/resources/{item.id}/view",
                    "reason": "匹配当前薄弱点" if resource_priority(item)[0] == 0 else "匹配当前学习阶段",
                }
            )

        existing_nodes = []
        if path is not None:
            existing_nodes = (
                db.query(LearningPathNode)
                .filter(LearningPathNode.path_id == path.id, LearningPathNode.status != "completed")
                .order_by(LearningPathNode.step_order.asc())
                .all()
            )
        revised_steps = [
            {
                "order": index,
                "title": title,
                "action": strategy,
                "estimated_minutes": 35 if strategy == "remediation" else 25,
            }
            for index, title in enumerate(weak_points[:3], start=1)
        ]
        for node in existing_nodes:
            if len(revised_steps) >= 5:
                break
            if node.title not in {item["title"] for item in revised_steps}:
                revised_steps.append(
                    {
                        "order": len(revised_steps) + 1,
                        "title": node.title,
                        "action": "continue",
                        "estimated_minutes": node.estimated_minutes,
                    }
                )

        shared_points = set(before_mastery) | set(after_mastery)
        mastery_delta = {
            point: round(float(after_mastery.get(point, 0)) - float(before_mastery.get(point, 0)), 4)
            for point in shared_points
        }
        return {
            "trigger": "evaluation_submitted",
            "strategy": strategy,
            "strategy_label": strategy_label,
            "reason": reason,
            "path_id": path.id if path else None,
            "before_mastery": before_mastery,
            "after_mastery": after_mastery,
            "mastery_delta": mastery_delta,
            "weak_points": weak_points,
            "revised_steps": revised_steps,
            "recommended_resources": recommendations,
        }

    def _retrieve_tutor_evidence(self, db: Session, question: str, limit: int = 3) -> list[dict]:
        known_terms = (
            "CNN",
            "卷积神经网络",
            "卷积层",
            "卷积",
            "池化",
            "反向传播",
            "梯度下降",
            "决策树",
            "支持向量机",
            "聚类",
            "过拟合",
            "机器学习",
        )
        tokens = [term for term in known_terms if term.casefold() in question.casefold()]
        tokens.extend(token for token in question.replace("？", " ").replace("?", " ").split() if token)
        query = db.query(ResourceChunk)
        chunks = query.limit(80).all()
        scored = []
        for chunk in chunks:
            score = sum(1 for token in tokens if token.lower() in chunk.content.lower())
            if score or any(char in chunk.content for char in question[:12]):
                scored.append((score, chunk))
        scored.sort(key=lambda item: item[0], reverse=True)
        evidence = [
            {
                "chunk_id": chunk.id,
                "resource_id": chunk.resource_id,
                "title": f"课程资源 {chunk.resource_id}",
                "source": f"resource_chunk:{chunk.id}",
                "snippet": chunk.content[:180],
            }
            for _, chunk in scored[:limit]
        ]
        if evidence:
            return evidence

        resource_candidates = []
        for resource in db.query(CourseResource).limit(80).all():
            text = f"{resource.title} {resource.content or ''}"
            score = sum(len(token) for token in tokens if token.casefold() in text.casefold())
            if score:
                resource_candidates.append(
                    (
                        score,
                        {
                            "chunk_id": f"course-resource-{resource.id}",
                            "resource_id": resource.id,
                            "title": resource.title,
                            "source": resource.source or f"course_resource:{resource.id}",
                            "snippet": (resource.content or "")[:180],
                        },
                    )
                )
        for resource in db.query(ResourceCenter).filter(ResourceCenter.status == "published").limit(80).all():
            text = f"{resource.title} {resource.description or ''} {resource.content or ''}"
            score = sum(len(token) for token in tokens if token.casefold() in text.casefold())
            if score:
                resource_candidates.append(
                    (
                        score,
                        {
                            "chunk_id": f"resource-center-{resource.id}",
                            "resource_id": resource.id,
                            "title": resource.title,
                            "source": f"resource_center:{resource.id}",
                            "snippet": (resource.content or resource.description or "")[:180],
                        },
                    )
                )
        for question_item in db.query(Question).limit(80).all():
            text = f"{question_item.stem} {question_item.explanation or ''}"
            score = sum(len(token) for token in tokens if token.casefold() in text.casefold())
            if score:
                resource_candidates.append(
                    (
                        score,
                        {
                            "chunk_id": f"question-{question_item.id}",
                            "resource_id": question_item.id,
                            "title": "课程题库解析",
                            "source": question_item.source or f"question:{question_item.id}",
                            "snippet": text[:180],
                        },
                    )
                )
        resource_candidates.sort(key=lambda item: item[0], reverse=True)
        return [item for _, item in resource_candidates[:limit]]

    def _knowledge_points_from_path(self, db: Session, path_id: int | None) -> list[str]:
        if path_id is None:
            return []
        nodes = db.query(LearningPathNode).filter(LearningPathNode.path_id == path_id).all()
        points = []
        for node in nodes:
            title = node.title or node.objective
            if title:
                points.append(title.split()[0])
        return points[:5]


learning_service = LearningService()
