from __future__ import annotations

import os

os.environ.setdefault("DATABASE_MODE", "mysql")

from backend.app import models as _models  # noqa: F401
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


def init_mysql_schema() -> None:
    Base.metadata.create_all(bind=engine)
    ensure_user_columns()
    ensure_student_profile_columns()
    ensure_course_resource_columns()
    ensure_resource_center_columns()
    ensure_producer_columns()
    ensure_learning_path_columns()
    ensure_ml_profile_answer_columns()
    print("MySQL schema initialized. ML integration columns are compatible.")


if __name__ == "__main__":
    init_mysql_schema()
