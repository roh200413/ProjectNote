from pathlib import Path

from django.conf import settings
from django.db import connection
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker


def sqlalchemy_database_url() -> str:
    db_name = connection.settings_dict.get("NAME") or settings.DATABASES["default"]["NAME"]
    db_path = Path(db_name)
    return f"sqlite:///{db_path}"


def sqlalchemy_engine():
    return create_engine(sqlalchemy_database_url(), future=True)


def sqlalchemy_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=sqlalchemy_engine(), autoflush=False, autocommit=False, future=True)


def sqlalchemy_table_names() -> list[str]:
    db_name = connection.settings_dict.get("NAME")
    if db_name == ":memory:":
        with connection.cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            return [row[0] for row in cursor.fetchall()]

    with sqlalchemy_engine().connect() as conn:
        rows = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"))
        return [row[0] for row in rows]
