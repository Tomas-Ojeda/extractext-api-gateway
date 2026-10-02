from fastapi import APIRouter

from config.settings import settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    return {"status": "ok", "app": settings.app_name, "version": settings.app_version}
