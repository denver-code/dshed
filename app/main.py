from beanie import init_beanie
from fastapi import APIRouter, Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.authorization import auth_required

from app.core.config import settings
from app.core.database import db
from v1.private import BacklogModel, DocumentModel, DocumentState
from v1.router import v1_router


def get_application():
    _app = FastAPI(title=settings.PROJECT_NAME)

    _app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return _app


app = get_application()


@app.on_event("startup")
async def on_startup():
    await init_beanie(
        database=db,
        document_models=[
            # Add your models here
            DocumentModel,
            BacklogModel,
            DocumentState,
        ],
    )


@app.get("/")
def root():
    return {
        "message": "Hello World",
        "latest_version": "v1",
    }


@app.get("/protected")
def protected(user: dict = Depends(auth_required)):
    return {
        "message": "Hello in Protected World",
        "latest_version": "v1",
    }


api_router = APIRouter(
    prefix="/api",
)
api_router.include_router(v1_router)

app.include_router(api_router)
