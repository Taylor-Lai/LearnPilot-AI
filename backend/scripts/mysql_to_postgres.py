from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, create_engine, func, inspect, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import Engine
from sqlalchemy.sql.schema import Column, Table

from backend.app.core.config import get_settings
from backend.app.core.database import Base
from backend.app.models import entities  # noqa: F401

TABLES = [
    "user",
    "course",
    "knowledge_point",
    "resource_center",
    "learning_resource",
    "student_profile",
    "student_weakness",
    "learning_path",
    "learning_path_node",
    "path_feedback",
    "producer_task",
    "producer_artifact",
    "ml_profile_answer",
]


def normalize_postgres_url(url: str) -> str:
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg2://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url


def mysql_url() -> str:
    settings = get_settings()
    return (
        f"mysql+pymysql://{settings.mysql_user}:{settings.mysql_password}"
        f"@{settings.mysql_host}:{settings.mysql_port}/{settings.mysql_database}?charset=utf8mb4"
    )


def postgres_url() -> str:
    value = os.getenv("DATABASE_URL", "").strip()
    if not value:
        raise RuntimeError("DATABASE_URL must be set before running the MySQL-to-PostgreSQL migration")
    return normalize_postgres_url(value)


def is_json_column(column: Column[Any]) -> bool:
    return isinstance(column.type, JSON) or column.type.__class__.__name__ == "UnicodeJSONType"


def is_tinyint_one(source_column: dict[str, Any] | None) -> bool:
    if not source_column:
        return False
    column_type = str(source_column.get("type", "")).lower().replace(" ", "")
    return column_type.startswith("tinyint") and "(1)" in column_type


def to_boolean(value: Any) -> bool | None:
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, (bytes, bytearray)):
        value = value.decode("utf-8", errors="ignore")
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "t", "yes", "y", "on"}:
            return True
        if lowered in {"0", "false", "f", "no", "n", "off", ""}:
            return False
    return bool(value)


def to_json(value: Any) -> Any:
    if value is None or isinstance(value, (dict, list, int, float, bool)):
        return value
    if isinstance(value, (bytes, bytearray)):
        value = value.decode("utf-8", errors="ignore")
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            return stripped
    return value


def default_value(column: Column[Any]) -> Any:
    if column.default is None:
        return None
    if column.default.is_scalar:
        return column.default.arg
    if callable(column.default.arg):
        try:
            return column.default.arg()
        except TypeError:
            return column.default.arg(None)
    return None


def convert_value(value: Any, target_column: Column[Any], source_column: dict[str, Any] | None) -> Any:
    if target_column.name == "is_admin":
        return to_boolean(value)
    if isinstance(target_column.type, Boolean) or is_tinyint_one(source_column):
        return to_boolean(value)
    if is_json_column(target_column):
        return to_json(value)
    if isinstance(target_column.type, DateTime):
        return value
    return value


def source_columns_by_name(inspector: Any, table_name: str) -> dict[str, dict[str, Any]]:
    return {column["name"]: column for column in inspector.get_columns(table_name)}


def target_columns(pg_inspector: Any, table: Table) -> list[Column[Any]]:
    existing = {column["name"] for column in pg_inspector.get_columns(table.name)}
    return [column for column in table.columns if column.name in existing]


def build_row(
    raw_row: dict[str, Any],
    target_table: Table,
    target_columns_: list[Column[Any]],
    source_columns: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    converted: dict[str, Any] = {}
    for column in target_columns_:
        if column.name in raw_row:
            converted[column.name] = convert_value(raw_row[column.name], column, source_columns.get(column.name))
            continue

        value = default_value(column)
        if value is not None:
            converted[column.name] = value
        elif isinstance(column.type, DateTime) and not column.nullable:
            converted[column.name] = datetime.utcnow()

    return converted


def migrate_table(mysql_engine: Engine, pg_engine: Engine, table_name: str) -> None:
    print(f"Migrating {table_name}")

    target_table = Base.metadata.tables[table_name]
    mysql_inspector = inspect(mysql_engine)
    pg_inspector = inspect(pg_engine)

    if table_name not in mysql_inspector.get_table_names():
        print("Inserted 0 rows")
        return
    if table_name not in pg_inspector.get_table_names():
        print("Inserted 0 rows")
        return

    source_columns = source_columns_by_name(mysql_inspector, table_name)
    usable_target_columns = target_columns(pg_inspector, target_table)
    selectable_columns = [
        target_table.c[column.name] for column in usable_target_columns if column.name in source_columns
    ]

    with mysql_engine.connect() as mysql_connection:
        if selectable_columns:
            rows = mysql_connection.execute(select(*selectable_columns)).mappings().all()
        else:
            rows = []

    converted_rows = [build_row(dict(row), target_table, usable_target_columns, source_columns) for row in rows]
    converted_rows = [row for row in converted_rows if row]

    if converted_rows:
        pk_columns = [column.name for column in target_table.primary_key.columns]
        statement = pg_insert(target_table).values(converted_rows)
        update_values = {
            column.name: statement.excluded[column.name]
            for column in usable_target_columns
            if column.name not in pk_columns and column.name in converted_rows[0]
        }
        if update_values:
            statement = statement.on_conflict_do_update(
                index_elements=pk_columns,
                set_=update_values,
            )
        else:
            statement = statement.on_conflict_do_nothing(index_elements=pk_columns)

        with pg_engine.begin() as pg_connection:
            pg_connection.execute(statement)

    print(f"Inserted {len(converted_rows)} rows")


def verify_counts(pg_engine: Engine) -> None:
    with pg_engine.connect() as connection:
        for table_name in ["user", "resource_center", "learning_path"]:
            result = connection.execute(select(func.count()).select_from(Base.metadata.tables[table_name])).scalar_one()
            print(f'SELECT COUNT(*) FROM "{table_name}"; -> {result}')


def main() -> None:
    mysql_engine = create_engine(mysql_url(), pool_pre_ping=True)
    pg_engine = create_engine(
        postgres_url(),
        pool_pre_ping=True,
        connect_args={"sslmode": "require"},
    )

    for table_name in TABLES:
        migrate_table(mysql_engine, pg_engine, table_name)

    verify_counts(pg_engine)
    print("DONE")


if __name__ == "__main__":
    main()
