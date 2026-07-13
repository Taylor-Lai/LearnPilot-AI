import logging
import time
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.api.router import api_router
from backend.app.core.config import get_settings
from backend.app.core.database import (
    Base,
    engine,
    ensure_course_resource_columns,
    ensure_learning_path_columns,
    ensure_ml_profile_answer_columns,
    ensure_producer_columns,
    ensure_resource_center_columns,
    ensure_student_profile_columns,
    ensure_user_columns,
)

settings = get_settings()
settings.validate_runtime()
logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
logger = logging.getLogger("learnpilot.backend")

app = FastAPI(
    title=settings.app_name,
    description="基于大模型的个性化资源生成与学习多智能体系统后端",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

try:
    Base.metadata.create_all(bind=engine)
    ensure_user_columns()
    ensure_student_profile_columns()
    ensure_course_resource_columns()
    ensure_resource_center_columns()
    ensure_producer_columns()
    ensure_learning_path_columns()
    ensure_ml_profile_answer_columns()
except Exception:
    logger.exception("database schema initialization failed")
    raise


@app.middleware("http")
async def add_request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception as exc:
        logger.exception("request failed", extra={"request_id": request_id})
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "internal_error",
                    "message": str(exc) if settings.app_debug else "Internal server error",
                    "request_id": request_id,
                }
            },
        )
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{time.perf_counter() - start:.4f}"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    logger.info("%s %s %s", request.method, request.url.path, response.status_code)
    return response


def run() -> None:
    import uvicorn

    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=settings.app_port)


if __name__ == "__main__":
    run()
