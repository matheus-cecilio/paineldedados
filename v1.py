from fastapi import APIRouter
from app.api.endpoints import imports, dashboard, auth

api_router = APIRouter()
api_router.include_router(imports.router, prefix="/imports", tags=["imports"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])