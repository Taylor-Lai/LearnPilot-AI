from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.app.core.security import hash_password
from backend.app.models import User

DEFAULT_EMAIL = "admin@example.com"
DEFAULT_USERNAME = "admin"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Reset or create the LearnPilot administrator account.")
    parser.add_argument("--email", default=DEFAULT_EMAIL, help=f"Admin email, default: {DEFAULT_EMAIL}")
    parser.add_argument(
        "--password",
        default=os.getenv("LEARNPILOT_ADMIN_PASSWORD", ""),
        help="New admin password; alternatively set LEARNPILOT_ADMIN_PASSWORD",
    )
    parser.add_argument("--username", default=DEFAULT_USERNAME, help=f"Admin username, default: {DEFAULT_USERNAME}")
    return parser.parse_args()


def get_database_url() -> str:
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        raise RuntimeError("DATABASE_URL is required. Set it to the PostgreSQL or MySQL connection string first.")
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+psycopg2://", 1)
    return database_url


def ensure_user_columns(engine) -> None:
    inspector = inspect(engine)
    User.__table__.create(bind=engine, checkfirst=True)
    inspector = inspect(engine)
    if "user" not in inspector.get_table_names():
        raise RuntimeError("user table was not created or cannot be inspected.")

    dialect = engine.dialect.name
    quote = "`" if dialect == "mysql" else '"'
    table_name = f"{quote}user{quote}"
    timestamp_type = "DATETIME" if dialect == "mysql" else "TIMESTAMP"
    existing = {column["name"] for column in inspector.get_columns("user")}
    columns = {
        "display_name": "VARCHAR(64) NULL",
        "nickname": "VARCHAR(100) NULL DEFAULT ''",
        "gender": "VARCHAR(20) NULL DEFAULT ''",
        "phone": "VARCHAR(32) NULL DEFAULT ''",
        "avatar": "TEXT NULL",
        "email": "VARCHAR(255) NULL",
        "password_hash": "VARCHAR(255) NULL",
        "role": "VARCHAR(32) NULL DEFAULT 'student'",
        "is_admin": "BOOLEAN NULL DEFAULT false",
        "status": "VARCHAR(32) NULL DEFAULT 'active'",
        "created_at": f"{timestamp_type} NULL",
        "updated_at": f"{timestamp_type} NULL",
    }

    with engine.begin() as connection:
        for column_name, column_type in columns.items():
            if column_name not in existing:
                quoted_column = f"{quote}{column_name}{quote}"
                connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {quoted_column} {column_type}"))


def reset_admin_account(email: str, username: str, password: str) -> dict:
    engine = create_engine(get_database_url(), pool_pre_ping=True)
    ensure_user_columns(engine)

    normalized_email = email.strip()
    normalized_username = username.strip()
    if not normalized_email:
        raise ValueError("email cannot be empty")
    if not normalized_username:
        raise ValueError("username cannot be empty")
    if not password:
        raise ValueError("password cannot be empty")

    with Session(engine) as session:
        user = session.query(User).filter(User.email == normalized_email).first()
        created = user is None
        if user is None:
            user = User(email=normalized_email)
            session.add(user)

        user.username = normalized_username
        user.display_name = normalized_username
        user.nickname = user.nickname or normalized_username
        user.email = normalized_email
        user.password_hash = hash_password(password)
        user.role = "admin"
        user.is_admin = True
        user.status = "active"

        session.commit()
        session.refresh(user)
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "is_admin": bool(user.is_admin),
            "status": user.status,
            "created": created,
        }


def main() -> None:
    args = parse_args()
    result = reset_admin_account(email=args.email, username=args.username, password=args.password)
    action = "created" if result["created"] else "updated"
    print(f"Admin account {action}.")
    print(f"id={result['id']}")
    print(f"username={result['username']}")
    print(f"email={result['email']}")
    print(f"role={result['role']}")
    print(f"is_admin={result['is_admin']}")
    print(f"status={result['status']}")


if __name__ == "__main__":
    main()
