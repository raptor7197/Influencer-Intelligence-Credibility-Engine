from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.settings import Settings


def build_engine():
    settings = Settings()
    connect_args = {}
    if settings.database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    return create_engine(
        settings.database_url,
        connect_args=connect_args,
        pool_pre_ping=not settings.database_url.startswith("sqlite"),
    )


_session_maker: sessionmaker[Session] | None = None


def get_session_maker() -> sessionmaker[Session]:
    global _session_maker
    if _session_maker is None:
        _session_maker = sessionmaker(autocommit=False, autoflush=False, bind=build_engine())
    return _session_maker


def get_db() -> Generator:
    db = get_session_maker()()
    try:
        yield db
    finally:
        db.close()
