from __future__ import annotations

from datetime import datetime, time

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from backend.app.api.auth import user_payload
from backend.app.api.feedback import feedback_payload
from backend.app.core.database import get_db
from backend.app.core.security import get_current_user
from backend.app.models import (
    LearningPath,
    PathFeedback,
    PlatformSetting,
    ProducerArtifact,
    ProducerTask,
    ResourceCenter,
    SystemFeedback,
    User,
)

router = APIRouter(prefix="/admin", tags=["admin"])


class RoleUpdateRequest(BaseModel):
    isAdmin: bool | None = None
    is_admin: bool | None = None


class FeedbackStatusRequest(BaseModel):
    status: str


def _admin_value(payload: RoleUpdateRequest) -> bool:
    if payload.isAdmin is not None:
        return payload.isAdmin
    return bool(payload.is_admin)


def _is_admin_user(user: User) -> bool:
    return bool(user.is_admin) or user.role == "admin"


def _require_admin(current_user: User = Depends(get_current_user)) -> User:
    if not _is_admin_user(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    return current_user


def _summarize_requirement(text: str | None, max_length: int = 80) -> str:
    value = (text or "").strip()
    if not value:
        return ""
    if len(value) <= max_length:
        return value
    return f"{value[:max_length]}..."


def _iso_datetime(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _artifact_counts(db: Session, task_ids: list[str]) -> dict[str, int]:
    if not task_ids:
        return {}
    rows = (
        db.query(ProducerArtifact.task_id, func.count(ProducerArtifact.id))
        .filter(ProducerArtifact.task_id.in_(task_ids))
        .group_by(ProducerArtifact.task_id)
        .all()
    )
    return {task_id: int(count) for task_id, count in rows}


def _producer_task_list_item(task: ProducerTask, user: User | None, artifact_count: int) -> dict:
    return {
        "taskId": task.task_id,
        "userId": task.user_id or 0,
        "username": user.username if user else "",
        "email": (user.email or "") if user else "",
        "userStatus": user.status if user else "",
        "topic": task.topic,
        "requirementSummary": _summarize_requirement(task.requirement),
        "taskType": task.task_type,
        "status": task.status,
        "progress": int(task.progress or 0),
        "artifactCount": int(artifact_count),
        "errorMessage": task.error_message or "",
        "createdAt": _iso_datetime(task.created_at),
        "updatedAt": _iso_datetime(task.updated_at),
    }


def _apply_producer_task_filters(
    query,
    *,
    keyword: str | None,
    status: str | None,
):
    if status:
        normalized_status = status.strip().lower()
        query = query.filter(func.lower(ProducerTask.status) == normalized_status)
    if keyword:
        pattern = f"%{keyword.strip()}%"
        query = query.filter(
            or_(
                ProducerTask.task_id.ilike(pattern),
                ProducerTask.topic.ilike(pattern),
                ProducerTask.requirement.ilike(pattern),
                User.username.ilike(pattern),
                User.email.ilike(pattern),
            )
        )
    return query


def _task_or_404(db: Session, task_id: str) -> ProducerTask:
    task = db.query(ProducerTask).filter(ProducerTask.task_id == task_id).first()
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producer task not found")
    return task


def _artifact_preview(content: str | None, max_length: int = 400) -> str:
    value = (content or "").strip()
    if not value:
        return ""
    if len(value) <= max_length:
        return value
    return f"{value[:max_length]}..."


def _producer_task_detail(db: Session, task: ProducerTask) -> dict:
    user = db.get(User, task.user_id) if task.user_id else None
    artifacts = (
        db.query(ProducerArtifact)
        .filter(ProducerArtifact.task_id == task.task_id)
        .order_by(ProducerArtifact.id.asc())
        .all()
    )
    result = task.result_json or {}
    artifact_items = [
        {
            "artifactType": row.artifact_type,
            "title": row.title,
            "contentPreview": _artifact_preview(row.content),
            "url": row.url or "",
            "createdAt": _iso_datetime(row.created_at),
        }
        for row in artifacts
    ]
    return {
        "taskId": task.task_id,
        "topic": task.topic,
        "requirement": task.requirement or "",
        "taskType": task.task_type,
        "status": task.status,
        "progress": int(task.progress or 0),
        "createdAt": _iso_datetime(task.created_at),
        "updatedAt": _iso_datetime(task.updated_at),
        "errorMessage": task.error_message or "",
        "artifactCount": len(artifact_items),
        "artifacts": artifact_items,
        "resultSummary": {
            "topic": result.get("topic") or task.topic,
            "agentTraceCount": len(result.get("agent_trace") or []),
            "requestedTypes": result.get("types") or result.get("requested_types") or [],
            "artifactTypes": [item["artifactType"] for item in artifact_items],
        },
        "user": {
            "username": user.username if user else "",
            "email": (user.email or "") if user else "",
            "status": user.status if user else "",
        },
    }


@router.get("/users/page")
def list_users(
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=10, ge=1, le=100),
    keyword: str | None = Query(default=None),
    role: str | None = Query(default=None),
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(_require_admin),
) -> dict:
    query = db.query(User)
    if keyword:
        pattern = f"%{keyword.strip()}%"
        query = query.filter(or_(User.username.like(pattern), User.email.like(pattern)))
    if role:
        normalized = role.strip().lower()
        if normalized == "admin":
            query = query.filter(or_(User.is_admin.is_(True), User.role == "admin"))
        elif normalized == "user":
            query = query.filter(User.role != "admin", User.is_admin.is_(False))
        else:
            query = query.filter(User.role == normalized)
    if status:
        query = query.filter(User.status == status.strip())

    total = query.count()
    users = query.order_by(User.id.desc()).offset((page - 1) * pageSize).limit(pageSize).all()
    return {
        "items": [user_payload(user) for user in users],
        "total": total,
        "page": page,
        "pageSize": pageSize,
    }


@router.get("/users/{id}")
def get_user(
    id: int,
    db: Session = Depends(get_db),
    _: User = Depends(_require_admin),
) -> dict:
    user = db.get(User, id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user_payload(user)


@router.put("/users/{id}/role")
def update_user_role(
    id: int,
    payload: RoleUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
) -> dict:
    user = db.get(User, id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    is_admin = _admin_value(payload)
    if current_user.id == id and not is_admin:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot revoke your own admin role")
    user.is_admin = is_admin
    user.role = "admin" if is_admin else "student"
    db.commit()
    db.refresh(user)
    return {"success": True, "user": user_payload(user)}


@router.delete("/users/{id}")
def delete_user(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
) -> dict:
    if current_user.id == id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete yourself")
    user = db.get(User, id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.status = "deleted"
    db.commit()
    return {"success": True, "id": id}


@router.get("/producer/tasks")
def list_producer_tasks(
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=10, ge=1, le=100),
    keyword: str | None = Query(default=None),
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(_require_admin),
) -> dict:
    query = db.query(ProducerTask, User).outerjoin(User, ProducerTask.user_id == User.id)
    query = _apply_producer_task_filters(query, keyword=keyword, status=status)

    total = query.count()
    rows = query.order_by(ProducerTask.id.desc()).offset((page - 1) * pageSize).limit(pageSize).all()

    task_ids = [task.task_id for task, _user in rows]
    artifact_counts = _artifact_counts(db, task_ids)

    return {
        "items": [_producer_task_list_item(task, user, artifact_counts.get(task.task_id, 0)) for task, user in rows],
        "total": total,
        "page": page,
        "pageSize": pageSize,
    }


@router.get("/producer/tasks/{task_id}")
def get_producer_task_detail(
    task_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(_require_admin),
) -> dict:
    task = _task_or_404(db, task_id)
    return _producer_task_detail(db, task)


def _safe_count(db: Session, model) -> int:
    try:
        return int(db.query(model).count())
    except Exception:
        return 0


@router.get("/statistics")
def statistics(
    db: Session = Depends(get_db),
    _: User = Depends(_require_admin),
) -> dict:
    today_start = datetime.combine(datetime.now().date(), time.min)
    try:
        today_user_count = int(db.query(User).filter(User.created_at >= today_start).count())
    except Exception:
        today_user_count = 0
    return {
        "userCount": _safe_count(db, User),
        "resourceCount": _safe_count(db, ResourceCenter),
        "pathCount": _safe_count(db, LearningPath),
        "feedbackCount": _safe_count(db, PathFeedback) + _safe_count(db, SystemFeedback),
        "producerTaskCount": _safe_count(db, ProducerTask),
        "todayUserCount": today_user_count,
        "todayResourceViewCount": 0,
    }


@router.get("/feedback")
def list_system_feedback(
    pageNum: int = Query(default=1, ge=1),
    pageSize: int = Query(default=10, ge=1, le=100),
    keyword: str | None = Query(default=None),
    feedback_type: str | None = Query(default=None, alias="type"),
    feedback_status: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    _: User = Depends(_require_admin),
) -> dict:
    query = db.query(SystemFeedback)
    if keyword:
        pattern = f"%{keyword.strip()}%"
        query = query.filter(
            or_(
                SystemFeedback.title.ilike(pattern),
                SystemFeedback.content.ilike(pattern),
                SystemFeedback.contact.ilike(pattern),
            )
        )
    if feedback_type:
        query = query.filter(SystemFeedback.feedback_type == feedback_type)
    if feedback_status:
        query = query.filter(SystemFeedback.status == feedback_status)
    total = query.count()
    rows = query.order_by(SystemFeedback.id.desc()).offset((pageNum - 1) * pageSize).limit(pageSize).all()
    return {"items": [feedback_payload(item) for item in rows], "total": total}


@router.put("/feedback/{feedback_id}/status")
def update_system_feedback_status(
    feedback_id: int,
    payload: FeedbackStatusRequest,
    db: Session = Depends(get_db),
    _: User = Depends(_require_admin),
) -> dict:
    if payload.status not in {"待处理", "处理中", "已解决"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid feedback status")
    item = db.get(SystemFeedback, feedback_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found")
    item.status = payload.status
    db.commit()
    db.refresh(item)
    return feedback_payload(item)


@router.delete("/feedback/{feedback_id}")
def delete_system_feedback(
    feedback_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(_require_admin),
) -> dict:
    item = db.get(SystemFeedback, feedback_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found")
    db.delete(item)
    db.commit()
    return {"success": True, "id": feedback_id}


@router.get("/settings")
def get_platform_settings(
    db: Session = Depends(get_db),
    _: User = Depends(_require_admin),
) -> dict:
    item = db.get(PlatformSetting, 1)
    return item.settings_json if item else {}


@router.put("/settings")
def update_platform_settings(
    payload: dict,
    db: Session = Depends(get_db),
    _: User = Depends(_require_admin),
) -> dict:
    item = db.get(PlatformSetting, 1)
    if item is None:
        item = PlatformSetting(id=1, settings_json=dict(payload))
    else:
        item.settings_json = dict(payload)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item.settings_json
