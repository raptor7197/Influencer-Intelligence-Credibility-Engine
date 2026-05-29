from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import router
from app.core.settings import Settings
from app.db.base import Base
from app.db.session import build_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = build_engine()
    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()


def create_app() -> FastAPI:
    settings = Settings()
    application = FastAPI(title=settings.app_name, lifespan=lifespan)
    application.include_router(router, prefix="/api")
    return application


app = create_app()
