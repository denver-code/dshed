from fastapi import APIRouter, Depends

from app.core.authorization import auth_required

private_router = APIRouter(
    prefix="/private",
    tags=["private"],
    dependencies=[
        Depends(auth_required),
    ],
)


@private_router.get("/")
async def private_root():
    return {
        "message": "Hello in Private World",
        "latest_version": "v1",
    }
