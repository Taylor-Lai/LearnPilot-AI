from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import optional_user
from backend.app.models import SystemFeedback, User

router = APIRouter(prefix="/api/feedback", tags=["feedback"])


class FeedbackCreateRequest(BaseModel):
    content: str = Field(min_length=5, max_length=5000)
    contact: str = Field(min_length=3, max_length=255)
    feedback_type: str = Field(default="其他", max_length=64, alias="type")
    title: str | None = Field(default=None, max_length=200)
    remark: str | None = Field(default=None, max_length=2000)
    allow_contact: bool = Field(default=True, alias="allowContact")

    model_config = ConfigDict(populate_by_name=True)


def feedback_payload(item: SystemFeedback) -> dict:
    return {
        "id": item.id,
        "userId": item.user_id,
        "type": item.feedback_type,
        "title": item.title,
        "content": item.content,
        "contact": item.contact,
        "remark": item.remark or "",
        "allowContact": item.allow_contact,
        "status": item.status,
        "createTime": item.created_at.isoformat() if item.created_at else None,
        "updateTime": item.updated_at.isoformat() if item.updated_at else None,
    }


@router.post("")
def create_feedback(
    payload: FeedbackCreateRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(optional_user),
) -> dict:
    content = payload.content.strip()
    item = SystemFeedback(
        user_id=current_user.id if current_user else None,
        feedback_type=payload.feedback_type.strip() or "其他",
        title=(payload.title or content[:40]).strip(),
        content=content,
        contact=payload.contact.strip(),
        remark=(payload.remark or "").strip() or None,
        allow_contact=payload.allow_contact,
        status="待处理",
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"success": True, "feedback": feedback_payload(item)}
