from fastapi import APIRouter

from app.api.meetings import router as meetings_router
from app.api.workspace import router as workspace_router


router = APIRouter()
router.include_router(meetings_router)
router.include_router(workspace_router)


@router.get("/")
def root() -> dict[str, str]:
    return {"message": "Fireflies clone backend"}


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "operational"}
