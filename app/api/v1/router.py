"""API v1 Router aggregation."""
from fastapi import APIRouter
from app.api.v1.endpoints import convert, documents, health

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(convert.router, tags=["Conversion"])
api_router.include_router(documents.router, tags=["Documents"])
