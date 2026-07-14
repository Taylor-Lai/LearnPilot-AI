"""Single composition point for all stable HTTP routers."""

from fastapi import APIRouter

from .admin import router as admin_router
from .auth import router as auth_router
from .core_routes import router as core_router
from .feedback import router as feedback_router
from .ml import router as ml_router
from .path import router as path_router
from .producer import router as producer_router
from .profile import router as profile_router
from .profile_builder import router as profile_builder_router
from .resources import router as resources_router
from .user import router as user_router

api_router = APIRouter()
for router in (
    core_router,
    auth_router,
    user_router,
    feedback_router,
    admin_router,
    resources_router,
    profile_builder_router,
    producer_router,
    profile_router,
    path_router,
    ml_router,
):
    api_router.include_router(router)

__all__ = ["api_router"]
